# Phone business delivery reservation — static review

Обновлено: 2026-11-07. Traced `server.phone.truck.load/take/cancel` through Trucker cargo pickup, business delivery interaction, and disconnect cleanup. Static-only; no RAGE staging.

## JOB-001 — delivery order is reserved before the caller is validated for cargo pickup

**Приоритет: низкий/средний; conditional live denial of one order, not reproduced.**

- `Open` requires the Trucker job ID but does not require `sessionData.WorkData.OnWork`; its on-duty check is commented out (`Players/Phone/Property/Businesses/Orders/Repository.cs:35-60, 88-111`). It lists unclaimed order IDs to any Trucker, including one who is off shift.
- `Take` checks a session exists, the feature is enabled, order slot is empty, caller is within 30m of the loading point, and the current vehicle's local `WorkId` is Trucker (`:114-175`). It does **not** check `WorkID`, `WorkData.OnWork`, a non-null rental, `rentData.Vehicle == player.Vehicle`, or a driver-seat requirement.
- It sets `bizOrder.Taked = true` and `sessionData.OrderData.Order = uid` before calling `Truckers.playerGotProducts` (`:170-174`). That cargo method silently returns if `RentData` is absent, the caller is not in a vehicle, or the rented vehicle is not the current one (`Jobs/Truckers.cs:154-168`). There is no success result/rollback to release the reservation.
- Completion separately requires an active Trucker job/on-duty state and the caller's own rented work vehicle (`Jobs/Truckers.cs:198-235`). Therefore an off-duty Trucker who is a passenger in another Trucker's work truck at the loading point can load an order ID, reserve it via direct `take`, and fail to acquire cargo. The order remains `Taked`, so other drivers cannot claim it; the caller can hold the slot until cancel or disconnect. Disconnect calls `Truckers.CancelOrder` (`Players/Disconnect/Repository.cs:212-215`), which resets `Taked`; this is temporary queue denial, not evidence of permanent order loss or business theft.

**Remediation (not implemented):** require active Trucker job/on-duty and the caller's own current work rental before reservation; require a driver seat if that is the job policy; make pickup return success and only commit `Taked`/session state after cargo state is established, or roll back on failure.

**Regression:** with two Trucker accounts and one valid order, test on-duty owner/driver, off-duty passenger in another worker's truck, non-Trucker passenger, no rental, mismatched rental, on-foot, outside/inside loading radius and cancel/disconnect. Failed pickup attempts must not reserve the order; valid pickup must create one cargo session and only one driver can take it.

## Scope boundary

This covers order reservation and pickup state only; delivery-point policy, driver/passenger reward policy and full product inventory fulfillment need runtime/owner-policy review. No money theft or cross-business access was established in this slice.


## JOB-004 — Trucker delivery consumes the order even when wallet payout fails

**Приоритет: средний; unchecked payout result and subsequent completion mutations statically confirmed; runtime failure path not reproduced.**

- `OnTrucker` validates the delivery session/order and computes the payout, then calls `MoneySystem.Wallet.Change(player, payment)` without checking its boolean result (`Jobs/Truckers.cs:198-235`).
- `Wallet.Change` can return `false` when the character data is unavailable, when the resulting cash balance would be negative (including an overflowed `int` sum), when a debit is rejected during shutdown, or when an exception occurs (`MoneySystem/Wallet.cs:13-34`). For a positive delivery reward, the relevant failure cases are missing/stale character state, overflow/invalid amount behavior, or exception.
- Regardless of the return value, `OnTrucker` writes the money log, updates quest progress, replenishes the business product stock, removes the business order from `biz.Orders` and `BusinessManager.Orders`, clears the driver's order state, and sends the success notification (`Jobs/Truckers.cs:235-292`). The delivery is therefore irreversibly marked complete in memory even when no wallet credit was applied.
- This is not a claim that ordinary successful deliveries fail; it is a settlement-integrity gap when `Wallet.Change` returns false. The current `GetPrice` calculation and the order-quantity overflow path (`MONEY-025`) also warrant separate boundary tests; this finding does not rely on an unproven client-side delivery count.

**Remediation (not implemented):** compute and validate a bounded positive payout before completion; require a successful wallet credit before consuming the order, or use a durable idempotent delivery receipt/state machine that can retry payout without duplicating stock/order completion. Only log and advance quest progress after settlement succeeds. Reconcile wallet, order, stock and receipt after restart.

**Regression:** inject `Wallet.Change` false/exception at delivery completion; verify order remains recoverable and stock is not replenished until payout is settled, or a durable pending-payout receipt is created. Test wallet near numeric boundaries, disconnect/state teardown around the checkpoint, duplicate colshape entry, restart/retry and successful exactly-once delivery.
