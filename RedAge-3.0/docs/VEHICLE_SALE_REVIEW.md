# Government vehicle sale — static callback/persistence review

Обновлено: 2026-11-07. Reviewed `server.vehicle.action("sell")` → generic `dialogCallback("CAR_SELL_TOGOV", true)` → `VehicleManager.Remove`. Source-only; no code changes, build, database fault injection or RAGE staging.

## VEH-006 — government-sale confirmation does not revalidate current vehicle ownership

**Приоритет: средний; stale-intent authorization gap, ownership-change sequence not runtime-reproduced.**

- `Houses/HouseManager.cs:2287-2320` checks `vehicleData.Holder == sessionData.Name` and no ticket when the player begins a sale, then stores only the plate in `sessionData.CarSellGov` and opens the dialog.
- `Main.cs:2701-2755` later handles `CAR_SELL_TOGOV` if that session field is non-null. It copies and clears the field, resolves the vehicle, and checks that the vehicle still exists and is not ticketed, but does **not** re-check `vehicleData.Holder == sessionData.Name` before crediting the current caller and deleting the vehicle.
- Therefore the initial ownership check is only at offer creation. If ownership changes before confirmation while the seller's pending `CarSellGov` remains set (for example, via another valid sale/transfer path or an intervening administrative change), confirmation can sell the now-foreign vehicle and credit the old holder. The client-supplied callback name alone is not sufficient: a pending `CarSellGov` value is required, and the handler clears it before completing the operation, so ordinary same-session callback replay is consumed. The stale ownership transition is the concern.

**Remediation (not implemented):** at confirmation, consume a short-lived one-shot intent and revalidate current holder, ticket, vehicle identity and sale eligibility immediately before settlement. Bind the intent to `SqlId` plus owner/version rather than plate alone; invalidate it on any ownership transfer. Reject stale/expired intents without money or asset mutation.

**Regression:** forged confirmation with no pending intent; valid owner sale; transfer to another player after the pending offer but before yes; ticket added during pending offer; repeated/concurrent confirmations; reconnect/expiry. On any stale owner mismatch, both players' balances and the vehicle must remain unchanged. Test legitimate sale payout and vehicle removal once.

## MONEY-013 — sale payout is applied before vehicle deletion is durable

**Приоритет: средний; conditional DB failure/restart replay risk, not runtime-confirmed.**

- In the confirmation branch (`Main.cs:2737-2741`), `Wallet.Change(player, price)` is called before `VehicleManager.Remove(number)`; the wallet result is ignored. No shared transaction or durable sale receipt links the payout to the vehicle deletion.
- `Core/Vehicle.cs:807-850` removes the vehicle from in-memory dictionaries and then schedules a separate async `db.Vehicles.DeleteAsync()`. Its catch only logs the error; it does not restore a durable pending delete or roll back/compensate the payout. `Wallet.Change` for large amounts queues a separate character-money update (`MoneySystem/Wallet.cs:20-37`, `Database/Models/Money.cs:89-119`), whose worker snapshots/clears its in-memory queue before the database writes; these are independent effects.
- If the payout is durably saved while the asynchronous vehicle-row deletion fails, restart can reload the still-existing vehicle with its old holder and allow a later sale attempt. The exact ordering, eligible prices, persistence timing, and repeat payout have not been reproduced; do not claim a confirmed mint or duplicate payout without DB fault-injection evidence.
- The callback clears `CarSellGov` before removal, preventing an immediate same-session replay, but that does not make the separated payout and persistent delete atomic across failures/restarts.

**Remediation (not implemented):** make sale settlement a durable transaction: conditional delete/ownership transition and exactly-once payout receipt in one DB transaction, or a sale ledger/outbox with idempotent recovery. Only report success after durable commit; reconcile cache afterward. Check and handle all wallet and delete results; do not use fire-and-forget delete as the sale receipt.

**Regression:** on disposable DB inject failure before wallet save, after wallet save, during vehicle delete, and after commit-before-notify; restart after each point. For each run, reconcile character balance, vehicle row, holder, garage slots and receipt; at most one payout and one deletion are allowed. Test concurrent/double confirmation and worker outage/retry. Requires MySQL fault injection and RAGE staging.

## Boundaries

This is static evidence for conditional stale-intent and cross-write failure paths, not proof of production exploitability or actual repeated sale. Vehicle sale/trade review remains incomplete; see `VEHICLE_ACTION_REVIEW.md`, `GARAGE_REVIEW.md` and `VEHICLE_REPAIR_REVIEW.md`.

## 2026-11-08 — bounded government vehicle sale confirmation guard

A narrow patch was applied in `Main.cs` for `CAR_SELL_TOGOV`:

- Revalidate `vehicleData.Holder == sessionData.Name` at confirmation, not only when the dialog is opened.
- Reject a nonpositive/unknown vehicle sale price before payout or removal.
- Require `Wallet.Change(player, price)` to succeed before money logs, bank message and vehicle removal.

This closes the stale-owner confirmation path and prevents vehicle deletion when wallet credit rejects. It does not close the crash/DB window after successful payout: `VehicleManager.Remove` still removes from memory and schedules a separate asynchronous DB delete without a durable sale receipt/retry. A DB delete failure/restart can still leave a previously paid vehicle row. No C# build, RAGE staging or MySQL fault injection was run.
