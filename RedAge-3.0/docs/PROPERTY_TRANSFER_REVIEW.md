# Player-to-player house transfer — static review

Обновлено: 2026-11-07. Traced `sellhouse` → `OfferHouseSell` → `dialogCallback("HOUSE_SELL")` → `acceptHouseSell`. Narrow transaction slice; no code changes, build, RAGE staging or shutdown/fault-injection test.

## MONEY-018 — unchecked buyer debit can mint the seller's transfer payment during shutdown

**Приоритет: средний; conditional shutdown timing, not reproduced.**

- `OfferHouseSell` requires a seller-owned house (`GetHouse(player, true)`), checks buyer has no house, range, offer price bounds, and sets a server-side seller/buyer/price pair in their session data (`HouseManager.cs:2891-2961`). At acceptance the server rechecks the buyer has no house and that the seller still owns the house (`:2969-3000`); this is not evidence of a non-owner transfer bypass.
- After tax/garage/affordability checks, `acceptHouseSell` calls `Wallet.Change(buyer, -price)` but ignores the boolean result, then credits `Wallet.Change(seller, price)` and transfers ownership (`:3019-3038`). The transaction is not atomic, and no failure path reverses the seller credit or prevents the owner change.
- `Wallet.Change` returns `false` for negative amounts while `Admin.IsServerStoping` is true (`MoneySystem/Wallet.cs:20-38`), whereas the positive seller credit is not blocked by that condition. If the confirmation remote is processed during shutdown and the positive credit persists, the seller can receive the agreed price without the buyer's debit; title transfer still proceeds. The RAGE shutdown/event timing and persistence ordering are untested; do not report a reproduced money exploit.

**Remediation (not implemented):** abort and clear the offer unless the buyer debit succeeds; atomically/idempotently settle both balances and the owner/version change, or use a durable transaction/outbox with compensation. Reject new house transfers once shutdown begins.

**Regression:** successful transfer; forged `HOUSE_SELL` callback with no offer; changed seller ownership; buyer acquiring another house before acceptance; insufficient cash; concurrent/repeated acceptance; `Wallet.Change=false` during server stopping; DB failure after debit, after seller credit, and before owner save. Verify exactly-once buyer debit/seller credit/title change and reconcile both balances, house owner/roommates, garage, notifications and restart state. Requires RAGE staging and disposable MySQL fault injection.

## Boundaries

The acceptance path does re-check seller ownership and buyer property eligibility. This slice does not review auctions, business transfers, bank-account ownership or other direct player-to-player trades. Government sale and direct house purchase have separate reviews (`PROPERTY_SALE_REVIEW.md`, `PROPERTY_PURCHASE_REVIEW.md`).
