# Phone auction lifecycle — static review

Обновлено: 2026-11-08. Traced property listing creation, first/subsequent bids, auction end and house/business award settlement. Narrow auction lifecycle slice; no code changes, .NET build, RAGE staging or DB fault injection.

## MONEY-023 — first bid debits the bidder before refunding the no-bid sentinel

**Приоритет: высокий; static control flow confirmed, runtime not reproduced.**

- New auction rows initialize `LastBetUUID = 0` and `LastPrice = price` (`Players/Phone/Auction/Repository.cs:290-305, 309-324`).
- `OnBet` debits `price + 1%` from the bidder before unconditionally calling `ReturnMoney(auctionData.LastBetUUID, auctionData.LastPrice, ...)` (`:525-538`).
- `ReturnMoney` treats the UUID as a connected-player lookup and immediately dereferences the result (`:562-568`); `Main.GetPlayerByUUID` explicitly returns null when the UUID is not connected (`Main.cs:4998-5005`). Thus the first-bid sentinel `0` can throw after the debit, and the same null dereference also makes the intended offline-character DB refund/payout branch unreachable for a real offline previous bidder or offline seller. In an overbid, the new bidder has already been debited before the previous-bid refund call; in house/business/vehicle award methods, seller payout is called before the asset handoff, so an offline seller can interrupt award processing. The event wrapper simply forwards to `OnBet` (`Events.cs:24-25`); no compensation is visible.
- The bidder's own selected bid is the only account debited here; this is not evidence of cross-player debit. The in-memory debit may later be persisted by character save/disconnect. Test the sentinel on a disposable server before reporting as runtime-proven.

**Remediation (not implemented):** refund the previous leader only when `LastBetUUID` identifies an actual prior bidder; settle debit/refund/bid update atomically or compensate on any exception. Require a valid positive starting price and use an explicit nullable/no-bid state rather than UUID zero.

**Regression:** first bid on a fresh auction of each type; offline previous bidder on overbid; offline seller at auction end for house/business/vehicle; confirm exact debit/refund/proceeds and asset handoff after reconnect/restart. Inject refund/update failure and verify durable retry/compensation; no `ReturnMoney(0,...)`.

## MONEY-024 — expired/ended auctions still accept bids while the row remains cached

**Приоритет: средний; conditional stale-cache window, not reproduced.**

- `OnBet` finds by ID but does not reject `auctionData.IsEnd` or compare `auctionData.Time` to current time (`:466-504`).
- `End` marks the record ended and settles the asset (`:426-455`), but the ended auction is removed from `AuctionsData` only after `SaveAuctions` writes it (`:393-418`). That persistence worker sleeps 30 seconds (`Database/Models/Phone.cs:19-42`).
- During the window after settlement and before cache removal, a direct `server.phone.auction.bet` call with the known ID can still debit the caller. With an existing top bidder, `OnBet` can also return that bidder's previous stake, mutate the already-ended auction, and never reassign the already-settled asset. Separately, bids submitted after `Time` but before the periodic `GetEnd` pass can be accepted late. The range is timing-dependent and has not been reproduced.

**Remediation (not implemented):** atomically check both `!IsEnd` and `DateTime.Now < Time` at bid settlement; serialize end/bid transitions on one authoritative lock/state machine and remove or reject ended records immediately.

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


## MONEY-038 — unchecked auction bid fee arithmetic can turn a debit into a credit

**Приоритет: критичный; арифметическая цепочка и положительное зачисление подтверждены статически, runtime не воспроизведён.**

- Remote server.phone.auction.bet accepts price as a client-supplied int and forwards it unchanged to Repository.OnBet (Players/Phone/Auction/Events.cs:23-25).
- OnBet checks only that the new price is greater than LastPrice; it does not enforce a positive value or a maximum bid (Players/Phone/Auction/Repository.cs:466-503).
- At :525, priceAndPercent is calculated as price + Convert.ToInt32(price / 100) in int. The project file does not enable checked arithmetic (NeptuneEvo.csproj has no CheckForOverflowUnderflow property).
- For price = int.MaxValue (2,147,483,647), the mathematical sum is 2,168,958,483, which wraps in the default unchecked int context to -2,126,008,813.
- The next line calls Bank.Change(characterData.Bank, -priceAndPercent). The unary negation therefore becomes positive 2,126,008,813; Bank.Change treats positive amounts as credits and adds them to the bank balance (MoneySystem/Bank.cs:79-115). The caller does not reject the resulting positive credit.
- This is a direct client-controlled remote argument, not a UI-only value. Whether a particular account balance/DB configuration permits the full amount and the exact runtime outcome still require staging; the unsafe arithmetic and credit direction are statically established.
- On a fresh auction, the existing MONEY-023 sentinel path may throw after this bank credit and before the bid state changes; that is a separate compounding failure, not a reason to merge the findings.

**Remediation (not implemented):** validate price > 0 and a server-defined maximum before arithmetic; compute fee/total using checked long arithmetic; reject overflow and values outside the supported bank/economy range; pass a validated negative debit to the bank only. Make the bid reservation and previous-bid refund one serialized, durable settlement.

**Regression:** direct remote bids at int.MaxValue, int.MaxValue-1, the maximum permitted bid, one above maximum, zero, negative and int.MinValue; verify the bank balance never increases from a bid, no integer wrap occurs, and no state/log/notification is committed on rejected input. Inject bank debit failure and first-bid sentinel failure; test concurrency and restart persistence.
