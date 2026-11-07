# Business phone orders and state persistence — static review

Обновлено: 2026-11-07. Traced business phone `addOrder`, `maxProducts`, confirmation, cancellation, price adjustment and business dirty-save worker. Narrow business inventory/accounting slice; no code changes, build or DB/RAGE tests.

## MONEY-022 — paid business stock orders mutate state without dirtying the business row

**Приоритет: средний; conditional restart/persistence loss, not reproduced.**

- `server.phone.business.addOrder` verifies the selected business is in the caller's `characterData.BizIDs`, validates product/count/stock limits, debits the caller's bank account, then marks the product ordered and appends the order (`Players/Phone/Property/Businesses/Repository.cs:153-225`). The bulk `MaxProductsConfirm` path similarly debits the personal bank for each order and mutates `product.Ordered`/`biz.Orders` (`:300-368`).
- `CancelOrder` removes the order and credits the caller's bank balance (`:369-424`). `ExtraCharge` changes `product.Price` (`:427-478`). None of these methods marks `biz.IsSave=true` in this repository slice.
- `Database.Models.Business.Worker` selects only businesses with `IsSave=true` every 30 seconds (`Database/Models/Business.cs:20-46`). `Business.Save` is what serializes `Products` and `Orders` to the DB and then clears `IsSave` (`Core/Businesses.cs:4132-4155`). Thus, absent an unrelated mutation that marks the business dirty, these order/price state changes are not scheduled for persistence.
- A paid order can be lost on restart if the caller's bank balance is persisted (e.g. character save/disconnect) while the business remains clean. Conversely, a canceled order or price change may be restored from an older DB snapshot if the account credit was saved but the business mutation was not. Exact outcomes depend on independent bank/business save timing and other dirty mutations; no DB scenario was reproduced.

**Remediation (not implemented):** mark the business dirty after every Products/Orders mutation or persist those changes transactionally with the bank debit/refund. Ensure cancellation/confirmation is idempotent and that the business order row and money state converge after a failed write.

**Regression:** add one order and force character save while business remains otherwise clean; restart and verify bank debit/order persistence. Repeat bulk purchase; cancel an order and restart; change product price and restart. Inject bank/business DB failures and concurrent business save ordering; verify no paid order loss, free restored order, duplicate refund or stale price.

## Boundaries

Each owner endpoint checks membership in the caller's server-side `BizIDs`; no other-player business ownership bypass was found here. Full business sale, taxes, delivery-vehicle authorization and stock-sale fulfillment remain outside this slice.
