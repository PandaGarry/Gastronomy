# Player-to-player vehicle sale — static review

Обновлено: 2026-11-08. Traced seller offer input, BUY_CAR confirmation, buyer debit, seller credit, vehicle holder mutation, garage updates and async holder persistence. Static-only; no RAGE/DB fault injection.

## MONEY-042 — vehicle sale transfers ownership without confirmed seller proceeds or durable holder commit

**Приоритет: высокий; unchecked credit and asynchronous persistence paths statically confirmed, runtime failure not reproduced.**

- Seller's sellcar input path validates requested price (1..100,000,000), buyer proximity, buyer garage capacity, buyer's current balance, vehicle existence and seller ownership; then stores the offer in both sessions (Main.cs:1784-1875).
- On BUY_CAR confirmation, server checks seller session/character, buyer-seller distance, vehicle existence and that vehicleData.Holder still equals seller.Name. It checks buyer Wallet.Change(player, -price) and aborts if that debit fails. After a successful debit it immediately changes vehicleData.Holder to buyer.Name, but ignores the boolean result of Wallet.Change(seller, price) (Main.cs:2548-2595).
- Wallet.Change can return false for missing/stale character state, a negative result after its long-to-int balance conversion, shutdown rejection for debit operations, or exception (`MoneySystem/Wallet.cs:13-34`). For this positive seller credit, missing/stale state, int-range overflow and exceptions remain relevant. The vehicle is nevertheless transferred and both parties receive success messages.
- Vehicle holder persistence is launched asynchronously only after the in-memory ownership change, logs and success notifications. Vehicle.SaveHolder performs a DB update inside Trigger.SetTask and catches/logs exceptions without returning success or retaining a pending retry receipt (`Core/Vehicle.cs:917-940`). A failed/late DB update can leave the DB holder as the seller while the buyer already has the vehicle in memory and paid; restart can restore stale ownership.
- The sale has no durable unique sale ID or state machine tying buyer debit, seller credit, vehicle holder DB update and garage placement together. The buyer debit is checked, but seller credit and durable asset transfer are not confirmed before the method reports success.

**Remediation (not implemented):** use a durable idempotent vehicle-sale settlement keyed by a unique sale ID. Validate both characters, price, current holder, buyer capacity and vehicle state; reserve buyer funds, confirm seller proceeds and persist holder change transactionally or via a durable outbox/receipt; only then update garage/runtime state and notify. On partial failure, compensate or reconcile without a second debit/credit. Make SaveHolder return/record durable completion and retry safely.

**Regression:** inject seller Wallet.Change=false/exception and seller balance above Int32 range; buyer debit must be compensated or sale must remain pending without ownership transfer. Inject DB update failure/delay in SaveHolder after buyer debit and seller credit; restart and reconcile holder, wallet, garage and sale receipt. Replay BUY_CAR before/after each boundary; test disconnects, duplicate callbacks, stale holder, missing vehicle, full garage and concurrent sale offers.

## Scope and confidence

Static ordering and API return contracts are visible. No live exploitation, runtime reproduction or DB failure test is claimed.

## 2026-11-08 — bounded BUY_CAR settlement guard

A narrow patch was applied in `Main.cs` for `BUY_CAR`:

- Reject a null/non-character seller before reading seller session/character state; reject a nonpositive pending sale price.
- Buyer debit remains checked as before.
- Seller credit is now checked. If seller credit rejects, the code attempts to refund the buyer; a failed refund emits a critical log with buyer/seller UUIDs, vehicle plate and amount.
- Vehicle holder mutation now occurs only after seller credit succeeds. Success log, garage changes and success notifications remain after that point.

This closes the specific path where seller credit rejects but vehicle ownership was already transferred and the method still reported success. It remains an in-memory compensating sequence, not a durable sale transaction: buyer debit/refund and seller credit are not tied to a durable receipt, compensation can fail, and `VehicleManager.SaveHolder` remains asynchronous without durable retry/reconciliation. No C# build, RAGE staging or MySQL fault injection was run.
