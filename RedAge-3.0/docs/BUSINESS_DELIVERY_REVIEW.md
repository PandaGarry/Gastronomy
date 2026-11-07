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
