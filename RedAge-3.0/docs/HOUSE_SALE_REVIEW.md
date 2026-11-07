# Player-to-player house sale review

Updated: 2026-11-08. Scope: `HouseManager.OfferHouseSell` and `HouseManager.acceptHouseSell` (seller offer and buyer confirmation). Static review only; no RAGE:MP/MySQL fault-injection or live transaction tests.

## MONEY-037 — house transfer proceeds when buyer debit or seller credit fails

**Priority: High for money/property consistency. Static evidence: unchecked wallet results and subsequent property transfer are directly confirmed. Runtime trigger frequency and persistence outcomes require staging.**

### Evidence

- `HouseManager.cs:2891-2968` creates the pending offer after checking that both players are online, the seller owns a house, the buyer has no house, proximity and price policy. It stores the seller/buyer/price in both session objects.
- `HouseManager.cs:2980-3043` processes buyer confirmation. It rechecks that the buyer has no house, retrieves the seller's house, checks seller ownership, tax balance, garage capacity and `UpdateData.CanIChange(player, price, true)`.
- Despite the pre-check, the settlement then calls `MoneySystem.Wallet.Change(player, -price)` and `MoneySystem.Wallet.Change(seller, price)` without checking either boolean result. It proceeds to `house.ClearOwner(false, false)`, assigns the buyer as owner with `house.SetOwner(player.Name)`, sends success notifications and clears both pending offer objects.
- `Wallet.Change` can return false (see MONEY-036 and `MoneySystem/Wallet.cs`). `CanIChange` is a precondition check, not a transactional guarantee that a later wallet mutation succeeds. The two wallet operations and house ownership mutation are not one atomic settlement.
- The code also sets `sellerCharacterData = player.GetCharacterData()` rather than reading `seller.GetCharacterData()`; the subsequent money log therefore uses the buyer UUID for both payer and payee. This is a confirmed audit-attribution defect in the same flow.

### Impact / confidence

If the buyer debit fails after the pre-check, the seller credit and property transfer can still proceed. If buyer debit succeeds but seller credit fails, the property transfer still proceeds without the seller receiving the agreed amount. The wrong UUID in the money log makes later reconciliation misleading. These are source-proven unchecked failure paths; no live reproduction is claimed.

### Remediation

1. Replace the three independent mutations (buyer debit, seller credit, house owner update) with a durable transaction/ledger settlement keyed by a unique offer ID.
2. Validate the offer is still pending, buyer/seller identities match, seller still owns the same house, buyer still has no property, and price is unchanged at confirmation.
3. Require exact successful debit and credit; do not transfer ownership or send success notifications on a failed leg.
4. Persist an idempotent state machine (Pending → Debited → SellerCredited → OwnershipTransferred → Completed) with restart reconciliation/compensation, or use a single DB transaction where all affected records can be committed atomically.
5. Read seller character data from `seller`; log distinct buyer/seller UUIDs and correlate all entries with the settlement ID.
6. Clear/expire pending offer state on cancellation, disconnect, stale ownership, timeout and all terminal failures.

### Regression matrix

- Normal buyer debit + seller credit + ownership transfer.
- Buyer wallet debit returns false; assert seller gets nothing and ownership is unchanged.
- Seller wallet credit returns false/throws; assert buyer is refunded or transaction remains recoverable and ownership is not transferred.
- Buyer disconnect, seller disconnect, seller changes ownership, buyer acquires another property, offer replay, concurrent accept callbacks.
- Crash/restart after each settlement state; retry must settle exactly once.
- Verify money logs contain distinct correct buyer/seller UUIDs and matching settlement ID.
- Boundary balances including MONEY-036 Int32/Int64 values; insufficient funds and wallet persistence errors.

**Status:** Open — static review documented; no patch, build or runtime test.
