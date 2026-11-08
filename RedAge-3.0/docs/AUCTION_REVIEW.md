# Phone auction lifecycle — static review

Обновлено: 2026-11-08. Traced property listing creation, first/subsequent bids, auction end and house/business award settlement. Source patch now present on `redage/audit-continuation`; no .NET build, RAGE staging or DB fault injection has been performed.

## MONEY-023 — first bid sentinel and offline previous-bidder lookup

**Приоритет: высокий; source patch applied, offline settlement still needs staging.**

- New auction rows initialize `LastBetUUID = 0` and `LastPrice = price`. UUID zero is a no-bid sentinel, not a funded prior bid.
- `OnBet` now calls `ReturnMoney` only when `LastBetUUID > 0 && LastPrice > 0`, so the first bidder is not charged and then interrupted by a bogus refund to UUID zero.
- `ReturnMoney` now uses `player?.GetCharacterData()`; when the prior bidder/seller is offline, execution can reach the existing asynchronous DB fallback instead of throwing on a null player.
- The offline fallback is not yet a durable idempotent receipt, and online/offline `Bank.Change` / `Wallet.Change` results are still not checked here. The broader refund/payout atomicity problem remains open.

**Patch:** `Players/Phone/Auction/Repository.cs` on `redage/audit-continuation`.

**Regression:** first bid on a fresh auction of each type; overbid while previous bidder is offline; auction end while seller is offline for house/business/vehicle; confirm exact debit/refund/proceeds and asset handoff after reconnect/restart. Inject refund/update failure and verify durable retry/compensation; no `ReturnMoney(0,...)`.

## MONEY-024 — expired/ended auctions still accept bids while the row remains cached

**Приоритет: средний; source guard/serialization patch applied, runtime concurrency pending.**

- `OnBet` now rejects `auctionData.IsEnd` and `DateTime.Now >= auctionData.Time` before any debit.
- `OnBet` and `End` now share `lock (auctionData)`; `End` also rechecks `IsEnd` while holding the lock. This serializes the bid/end transition for the same in-memory auction record.
- The ended row may still remain cached until the existing save worker removes it, but stale IDs now hit the state/deadline guard.
- Other readers/writers of `AuctionsData` and the DB persistence worker have not been proven to share this lock; durable concurrency and restart behavior remain staging tasks.

**Patch:** `Players/Phone/Auction/Repository.cs` on `redage/audit-continuation`.

**Regression:** bid before/at/after deadline, callback after `End` but before DB flush, repeated stale IDs, and concurrent end/bid. Assert no post-end debit/refund or auction-state mutation and exactly one asset transfer.

## PROP-004 — property ownership is cleared before the auction row is durably inserted

**Приоритет: средний; conditional DB-insert failure, not reproduced.**

- `OnCreate` calls `House.Repository.SetAuction` or removes the business from `BizIDs` and calls `Businesses.Repository.SetAuction` before `Insert` (`:202-232, 272-273`). House setup clears the owner; business setup calls `ClearOwner` and marks the business dirty (`House/Repository.cs:11-16`, `Businesses/Repository.cs:17-22`).
- `Insert` runs asynchronously and creates the durable `Auctions` row only afterward (`:276-338`). Its catch logs exceptions but does not restore the house/business owner, resident/business IDs or auction flag.
- If the DB insert fails after these in-memory changes, the house may be saved unowned or the business as government-owned while no auction row exists; the seller has no active auction through which to recover proceeds. This is conditional on insert failure and persistence ordering, not reproduced.

**Remediation (not implemented):** durably create a listing/reservation first, then detach the asset in a transaction or use an idempotent state machine with rollback/reconciliation. Do not acknowledge listing success until both listing and asset state commit.

**Regression:** inject failure before/after auction insert for house and business listings, restart, and reconcile auction row, owner, `BizIDs`, bank/garage state and seller notifications.

## PROP-005 — offline business auction winner may receive owner string but not business ID

**Приоритет: средний; offline-winner path statically identified, runtime not reproduced.**

- `Main.PlayerNames` is populated from the character table at startup, not only from connected players (`Main.cs:665-683`); auction end uses this map to treat a `LastBetUUID` as a valid winner (`Businesses/Repository.cs:29-40`).
- The business award sets `biz.Owner`, initializes its tax bank and then calls online-only `Main.GetPlayerByUUID(uuid)`; it dereferences `player.GetCharacterData()` before reaching the DB fallback intended for missing character data (`Businesses/Repository.cs:44-75`). An offline winner can therefore leave the business owner changed/saved while their `BizIDs` list is not updated. The exception has no local catch in this method.
- Business phone ACLs use `characterData.BizIDs` (for example `Players/Phone/Property/Businesses/Repository.cs:28-36`), so after reconnect the buyer may not have the awarded business in the list needed to manage it. The bidder had already paid through the auction bid path. Exact recovery/admin behavior is not traced.

**Remediation (not implemented):** update the winner's Biz IDs by UUID in the same durable award transaction regardless of online status; only then finalize seller proceeds/auction completion. Reconcile owner and character asset lists on login.

**Regression:** let an offline character win a business auction; end the auction, restart/reconnect, and verify owner, `BizIDs`, tax account, seller proceeds, and access to business phone remotes are consistent.

## Boundaries

House auctions do not need a separate character house-ID list in the inspected `GetHouse` path; the offline winner observation above is specific to business `BizIDs`. Vehicle/other-item auction mutations and auction escrow persistence require separate review.


## MONEY-038 — unchecked auction bid fee arithmetic could turn a debit into a credit

**Приоритет: высокий до прохождения build/RAGE boundary tests. Source patch applied.**

- The remote still supplies `price` as an `int`, but `OnBet` now rejects `price <= 0` before any money/state mutation.
- Fee arithmetic now widens before addition: `long priceAndPercent = (long)price + (price / 100L)`. For `int.MaxValue`, the total is 2,168,958,483 and remains positive; negating it therefore remains a debit when passed to `Bank.Change`, not the previous wrapped positive credit.
- The computed fee is passed to `GameLog.Money` as a `long`; the API supports that type.
- No server-defined maximum auction bid was found in the inspected config/UI path. The patch removes signed-int wraparound but does not invent an economy cap; owner policy for a maximum bid remains open.

**Patch:** `Players/Phone/Auction/Repository.cs` on `redage/audit-continuation`.

**Regression:** direct remote bids at `int.MaxValue`, `int.MaxValue-1`, configured/policy maximum once established, zero, negative and `int.MinValue`; verify the bank balance never increases from a bid, no integer wrap occurs, and no state/log/notification is committed on rejected input. Inject bank debit failure and test concurrency/restart persistence.

## INV-011 — Other-item auction escrow has no end-of-auction award or return path

**Приоритет: высокий; missing settlement branch statically confirmed, runtime item recovery not tested.**

- The public remote server.phone.auction.add casts a client-supplied integer to AuctionType and calls OnCreate (Players/Phone/Auction/Events.cs:17-20).
- OnCreate has an AuctionType.Other branch that reads the character inventory item, clears its inventory slot, and moves its SQL item record to locationName/location `auction` / `auction` via UpdateSqlItemData (Players/Phone/Auction/Repository.cs:253-273; Chars/Repository.cs:4622-4678).
- The auction End method marks the auction ended, but its settlement dispatch handles only House, Biz and Vehicle. There is no Other award/return branch (`Players/Phone/Auction/Repository.cs:426-447`). SaveAuctions later removes ended auctions from the in-memory list after persisting IsEnd (`:393-418`).
- Therefore an Other item can be detached from the seller inventory and placed in the auction location without a corresponding winner grant or no-bid return in the reviewed auction lifecycle. The item may remain orphaned in that storage location after the auction is removed from active memory. Exact persistence/recovery behavior needs disposable DB verification.
- The client-facing item-picker path GetItem also has no AuctionType.Other branch (`:121-185`), so the intended UI workflow is unclear; nevertheless the server add remote and Other mutation branch are present. Do not assume the UI makes this safe.

**Remediation (not implemented):** either disable AuctionType.Other at the server boundary until complete, or implement explicit item settlement for winner/no-bid/cancel paths. Reserve and move the exact owned item with a durable auction ID; atomically grant it to the winner or return it to the seller; support offline recipients, retry and exactly-once receipts. Validate the item ID belongs to the caller and reject unsupported enum values.

**Regression:** direct add remote for Other with valid, foreign, nonexistent and stale item IDs; auction end with and without bids; winner/seller online and offline; DB failure at reserve/grant/return; restart before and after end; verify the item exists exactly once in the correct owner container and never remains stranded in auction storage.
