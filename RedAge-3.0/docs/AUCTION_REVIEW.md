# Phone auction lifecycle — static review

Обновлено: 2026-11-07. Traced property listing creation, first/subsequent bids, auction end and house/business award settlement. Narrow auction lifecycle slice; no code changes, .NET build, RAGE staging or DB fault injection.

## MONEY-023 — first bid debits the bidder before refunding the no-bid sentinel

**Приоритет: высокий; static control flow confirmed, runtime not reproduced.**

- New auction rows initialize `LastBetUUID = 0` and `LastPrice = price` (`Players/Phone/Auction/Repository.cs:290-305, 309-324`).
- `OnBet` debits `price + 1%` from the bidder before unconditionally calling `ReturnMoney(auctionData.LastBetUUID, auctionData.LastPrice, ...)` (`:525-538`).
- `ReturnMoney` treats the UUID as a connected-player lookup and immediately dereferences the result (`:562-568`). The first-bid sentinel `0` has no connected player in the normal character model, so the initial bid can throw after the debit and before `LastBetUUID`/`LastPrice` are updated. The event wrapper simply forwards to `OnBet` (`Events.cs:24-25`); no compensating refund is visible.
- The bidder's own selected bid is the only account debited here; this is not evidence of cross-player debit. The in-memory debit may later be persisted by character save/disconnect. Test the sentinel on a disposable server before reporting as runtime-proven.

**Remediation (not implemented):** refund the previous leader only when `LastBetUUID` identifies an actual prior bidder; settle debit/refund/bid update atomically or compensate on any exception. Require a valid positive starting price and use an explicit nullable/no-bid state rather than UUID zero.

**Regression:** first bid on a fresh auction of each type; confirm debit exactly once and state advances, no `ReturnMoney(0,...)`; injected refund/update failure must restore or retain funds consistently.

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
