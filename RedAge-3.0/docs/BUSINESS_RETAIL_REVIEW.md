# Business retail purchase and stock settlement — static review

Обновлено: 2026-11-08. Traced the shared BusinessManager.takeProd helper and representative 24/7, weapon-shop, ammo, component, clothing and service purchase callers. Static-only; no source patch, build, RAGE runtime or DB fault injection.

## STOCK-002 — retail stock/revenue is mutated before customer settlement and grant confirmation

**Приоритет: высокий; static control-flow confirmed, runtime failure paths not reproduced.**

- Shared helper BusinessManager.takeProd checks business existence and rejects negative addMoney, then finds the product and immediately decrements p.Lefts (Core/Businesses.cs:1920-1945).
- For a privately owned business it then resolves the owner's bank account and calls Bank.Change(bData.ID, addMoney, false). If the account lookup is missing/null or the bank credit fails, the helper returns false after stock has already been decremented; there is no rollback. A caller that handles false exits, so the customer is not charged/granted an item but stock remains consumed.
- If no matching product is found, the loop ends and the helper returns true anyway. Callers can then continue their purchase path despite no stock reservation/decrement. Current callers often derive names from product lists, so this is primarily a config/state-integrity edge, not proof of a direct client-controlled arbitrary product name.
- Representative 24/7 flow: Event_ShopCallback invokes takeProd, then calls AddNewItem without checking its result, and finally calls Wallet.Change(player, -prod.Price) without checking its result (Core/Businesses.cs:3450-3675). A failed customer debit can therefore still leave the item granted and business revenue credited; a failed item grant can still leave customer debit, stock decrement and owner revenue.
- Weapon-shop component/ammo paths similarly call takeProd, ignore the wallet debit result, and ignore AddNewItem result (Core/Businesses.cs:3730-3840). Weapon purchase calls takeProd, ignores wallet debit result, then invokes WeaponRepository.GiveWeapon without a settlement receipt (Core/Businesses.cs:3845-3895). Other shop/service callsites use the same helper and unchecked wallet calls (pet shop, carwash, clothing, barber and petrol). LS Customs personal tuning also calls takeProd for parts before SetCustomization; if its internal CanIChange check fails, the already-reserved stock/owner credit is not compensated, and if Wallet.Change fails after preflight the vehicle customization is still applied (Core/Businesses.cs:1620-1730).
- The helper and Business.BuyItemBusiness do not set biz.IsSave=true; BuyItemBusiness only inserts history and increments in-memory Pribil (Core/Businesses.cs:4157-4162). The business worker saves only dirty businesses (Database/Models/Business.cs:20-46), and Business.Save serializes Products. This extends existing MONEY-022: retail stock reductions can be absent from the next business save unless another mutation dirties the row, while customer/owner bank writes are persisted independently.

**Remediation (not implemented):** replace takeProd + caller-side wallet/grant sequence with one server-side purchase settlement service. Validate business/product/quantity/price/owner bank and customer balance first; reserve exact stock; debit customer and credit business atomically or through a durable idempotent receipt/state machine; grant exact item/weapon/service; commit stock and mark business dirty only after settlement, with compensation/reconciliation for partial failures. Return false when the product is absent; reject nonpositive quantities and bound all arithmetic. Do not emit success, history, BattlePass/quest progress or money logs until the purchase is committed.

**Regression matrix:**
- Missing owner bank account / Bank.Change=false after stock validation: no stock loss, customer debit, item grant or false success.
- Customer Wallet.Change=false after stock reservation / business credit: no free item or business revenue; reservation rolled back or durable pending receipt.
- AddNewItem returns failure/partial result; weapon grant fails; disconnect/crash between debit, credit, grant and stock commit.
- Product name absent from biz.Products: helper must reject, never return success.
- Quantity 0/negative/large, price boundaries and checked arithmetic; duplicate/replay/concurrent same-product purchases.
- Successful purchase followed by restart with no unrelated business mutation: stock remains decremented and owner proceeds remain consistent.
- Cover 24/7 items/SIM/lottery, weapon/components/ammo, clothes/masks, barber/tattoo, pet food, carwash and petrol; verify quest/BattlePass/history side effects occur exactly once.

## Scope and confidence

The ordering and ignored return values are visible in source. Whether each failure can be induced in production, exact AddNewItem partial-insert semantics, weapon grant semantics and crash windows require disposable MySQL + RAGE staging. This review does not claim live exploitation or successful runtime reproduction.

## 2026-11-08 — bounded takeProd input/missing-product hardening

Applied a narrow patch to `Core/Businesses.cs`:

- Reject `amount <= 0` before product lookup or stock arithmetic.
- Use the direct comparison `p.Lefts < amount` after positive-quantity validation.
- Track whether a matching product was found; return `false` if no product matches instead of reporting success.

This closes the helper's missing-product false-success path and invalid/nonpositive quantity input. It does **not** fix stock decrement before owner-bank credit, missing rollback on bank failure, unchecked customer Wallet.Change, unchecked/partial item or weapon grants, or missing business dirty-save marking. Those remain open under STOCK-002/MONEY-022. No C# build, RAGE staging or MySQL fault injection was run.
