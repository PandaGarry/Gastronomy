# Government fleet refuelling and business fuel-stock settlement — static review

Обновлено: 2026-11-08. Traced the petrol remote in Core/Businesses.cs through vehicle fuel capacity, government-fleet eligibility, fraction FuelLeft accounting, business stock/revenue and vehicle fuel mutation. Static-only; no RAGE runtime or DB/failure injection.

## MONEY-045 — government refuelling can proceed after the fraction fuel budget is exhausted

**Приоритет: высокий; missing rejection statically confirmed, exact gameplay exposure and persistence require staging.**

- fillCar computes price = lvl * biz.Products[0].Price before entering the government-fuelling branch (Core/Businesses.cs:2895-2898).
- The government branch verifies the caller's government fraction and that the vehicle belongs to that same fraction, but does not reject a request whose cost exceeds fractionData.FuelLeft (2899-2918).
- It only clamps lvl when lvl > fractionData.FuelLeft, even though FuelLeft is a monetary budget: the old commented guard explicitly compared FuelLeft against lvl * unitPrice (2910-2915). Moreover, price was calculated before this clamp and is not recalculated afterward.
- After stock reservation, the code executes if ((fractionData.FuelLeft - price) >= 0) fractionData.FuelLeft -= price; but has no else return. When the budget is insufficient, the deduction is skipped while the flow continues: it deducts City Hall funds, reports the government refuel path, and finally applies tfuel to the vehicle (2924-2953). The cap therefore does not prevent the fuel delivery once exhausted.
- Daily reset assigns FuelLeft = FuelLimit for the government fractions (Main.cs payday path), and the fraction save worker persists FuelLeft. This supports FuelLeft being the remaining monetary allowance, consistent with the commented legacy comparison. Exact intended accounting semantics should still be confirmed before changing balance policy.
- This finding is separate from MONEY-031: that issue concerns who may edit government fuel limits; this one concerns enforcing the configured limit during a government fuel purchase.

**Remediation (not implemented):** compute a positive checked wide price after all quantity normalization; enforce price <= FuelLeft before stock, city funds or vehicle state changes; reject otherwise. Do not compare liters with currency. Debit the fraction allowance and City Hall ledger consistently with the business stock/fuel grant, using a durable idempotent receipt or compensating state machine. Ensure all values are recalculated after any quantity clamp.

## Regression matrix

- Fuel allowance below, equal to and above total cost; insufficient allowance must leave vehicle fuel, business stock/bank, FuelLeft and City Hall funds unchanged.
- Request amount larger than allowance and unit price greater than one; ensure no units/currency confusion and no stale pre-clamp price.
- Zero/negative/oversized level, full tank, vehicle tank boundary, business stock shortage and price boundaries.
- Duplicate remote, concurrent refuels, disconnect and restart between stock, fraction allowance, City Hall and vehicle-fuel writes.
- Daily reset and admin FuelLimit decrease while FuelLeft is greater than the new limit; verify allowance cannot be exceeded.

## VEH-009 — petrol remote is not bound to an active nearby fuel station

**Приоритет: высокий; missing session/location/type validation statically confirmed; RAGE event reachability requires staging.**

- SessionData.BizID defaults to -1 (Players/Models/SessionData.cs:61). OnBusinessAction sets it to the ID of whichever business interaction was entered, before switching on the business type (Core/Businesses.cs:1035-1054). The inspected source has no corresponding reset on leaving the business; the same stale-context pattern is independently documented for the 24/7 shop callback in CAS-024.
- The petrol remote fillCar only checks that BizID is nonnegative/present and the caller is in a vehicle; it does not require biz.Type == 1, current proximity to the selected station, matching dimension or an active server-issued refuelling session (Core/Businesses.cs:2841-2854).
- It then calls takeProd(biz.ID, lvl, "Бензин", price) and applies fuel to the vehicle (2919-2953). STOCK-002 documents that takeProd returns true when no matching product exists; therefore a BizID left by a non-fuel business can still pass the stock gate despite that business having no petrol product. The unchecked Wallet.Change and stock settlement issues remain covered by STOCK-002; this finding is specifically the missing authorization/context boundary.
- A player who has previously interacted with a business can directly invoke petrol while away from a station; the selected business can even be a non-fuel business. The precise client remote invocation and RAGE position/dimension behavior were not runtime-tested.

**Remediation (not implemented):** create a short-lived server-side refuelling intent only when entering a Type==1 station; bind it to player, business ID, vehicle identity, position/dimension and expiry. Recheck station proximity/type, driver seat, vehicle identity and active intent on every petrol event. Consume the intent or use a bounded refill session, and reset it on exit/disconnect/context change. Independently make takeProd return false when the product is absent.

**Regression:** interact with a non-fuel business, leave and directly call petrol; interact with a fuel station then move far away/change dimension and call petrol; swap vehicle, passenger seat, stale/deleted business and replay the event. Every invalid context must leave fuel, stock, wallet, owner bank, FuelLeft and City Hall balance unchanged. Confirm legitimate in-range refuelling still works.

## Scope boundary

VEH-009 is separate from MONEY-045 (government quota enforcement), STOCK-002 (missing-product success and retail settlement), and CAS-024 (24/7 shop stale BizID).
