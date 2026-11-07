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

## MONEY-025 — unchecked order quantity overflow can credit the owner's bank

**Приоритет: высокий; source arithmetic and seeded fixture confirmed, RAGE runtime not reproduced.**

- `server.phone.business.addOrder` is registered in `Players/Phone/Property/Businesses/Events.cs:14-15` and passes a client-supplied `int value` directly to `AddOrder`.
- `AddOrder` checks `value >= CountMinOrder(biz.Type)` and then only rejects when `product.Lefts + value > productsData.MaxCount` (`Repository.cs:186-200`). Both operands are `int`; the project does not enable checked overflow. For a stocked type-0 business product, the sum can wrap negative and pass the maximum check.
- The next calculation `price = value * itemPrice` is also unchecked `int`. The method passes `-price` to `Bank.Change` and does not require `price > 0` (`:198-208`). A negative wrapped price therefore becomes a positive deposit in the business owner's personal bank, then `biz.Zatratq` decreases and a huge order is registered (`:207-219`). `Bank.Change` accepts positive credits and marks personal-bank balances dirty for credits of at least $10,000 (`MoneySystem/Bank.cs:79-99`).
- Concrete fixture arithmetic: type-0 product `Сумка` has base price 7,500 and max count 200 (`database/mainconfig.sql:2460`); the bundled business row includes `Lefts=50` (`database/main.sql:419`). With `value=2,147,483,598` (`2^31 - 50`), unchecked `Lefts + value` wraps to `int.MinValue`, while `value * 7,500` wraps to `-375,000`. `Bank.Change(ownerBank, -price)` therefore receives `+375,000`; count minimum 10 passes. This fixture row is government-owned in the snapshot, so the attack requires a player-owned type-0 business with that stocked product and an active owner `BizIDs` entry; availability on a live server is not established.
- This is a direct owner-bank credit path requiring the caller to own the selected business, not evidence of arbitrary cross-player account access. The resulting enormous order also poisons stock/settlement arithmetic if later delivered or canceled. Because this method also does not dirty-save the business (`MONEY-022`), the bank credit may persist while the malformed order disappears after restart if no unrelated mutation saves it. No RAGE execution or live DB check performed.

**Remediation (not implemented):** reject counts outside the actual remaining capacity using non-overflowing arithmetic (`value <= MaxCount - Lefts`); compute cost in checked `long`, enforce positive configured unit price and bounded positive total, convert only after range checks, and mutate balance/order/inventory only after every validation succeeds.

**Regression:** direct remote calls with `value = int.MinValue`, `int.MaxValue`, `2,147,483,598` and values immediately around the remaining-capacity boundary against a stocked type-0 business. Assert rejected requests leave bank balance, `Zatratq`, `Products`, `Orders`, global `BusinessManager.Orders`, dirty flags and GameLog unchanged. Test safe bulk ordering, cancellation and delivery afterward; perform on a disposable DB/RAGE server.

## Boundaries

Each examined order endpoint checks membership in the caller's server-side `BizIDs`; no other-player business ownership bypass was found in the inspected order methods. Full taxes, delivery-vehicle authorization and stock-sale fulfillment still need tracing. Phone sale and Trucker reservation/pickup are separately reviewed in `BUSINESS_SALE_REVIEW.md` and `BUSINESS_DELIVERY_REVIEW.md`; this overflow finding only covers `addOrder`.
