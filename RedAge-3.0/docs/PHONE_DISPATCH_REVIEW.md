# Phone taxi/mechanic dispatch and read-only remotes — static review

Обновлено: 2026-11-07. Traced phone taxi/mechanic request, cancel and driver-take handlers plus narrow car/property/GPS/recent-list load paths. Static source review only; no RAGE simulation, concurrent remote test, rate-limit measurement or gameplay-owner policy confirmation was available.

## JOB-002 — taxi/mechanic dispatch does not enforce an exclusive active assignment

**Приоритет: средний; missing server-side state checks confirmed statically; hijack/race/timer effects require RAGE staging.**

- `server.phone.taxijob.take` (`Taxi/Orders/Repository.cs:65-105`) looks up an order by caller-supplied character UUID and accepts any matching row with a live caller. It checks the taker's taxi job/vehicle/session ride state, then sets `taxiData.Driver = player`, starts a new periodic position timer, and removes the order from other drivers' UI. It does not require `taxiData.Driver == null`, nor does it reject a second outstanding dispatch for this driver. The list sent to drivers intentionally omits orders with a non-null `Driver` (`:35-60`), so UI hiding does not protect a direct remote call.
- `server.phone.mechjob.take` has the same missing order-claim/per-driver active-order check (`Mechanic/Orders/Repository.cs:113-149`). It writes `mechanicData.Driver = player` and starts a timer without ensuring the request is still unassigned.
- Re-taking an occupied order overwrites its stored driver and `DriverTimer` reference without stopping the previous timer. A driver can also accept multiple different UUIDs because dispatch assignment is not recorded in the driver's trip-state guard. Old callbacks can continue after reassignment; the periodic callbacks do not verify that the driver remains the active owner of that order before notifying or processing proximity. They continue sending the displaced driver's position to the caller through `updatePosOrder`, and a displaced driver is no longer discoverable by `OnCancel` through the order's current `Driver` field. BattlePass `UpdateReward` checks `IsDone`, so duplicate task payout is **not** asserted from this path; the demonstrated concern is dispatch ownership/state and stale location/timer/notification behavior.
- The UI removes accepted orders from the other workers' lists, consistent with an intended claim/assignment transition, but exclusivity policy should still be confirmed. No takeover, duplicate service or notification loop was reproduced.

**Remediation work:** atomically claim only pending orders (`Driver == null`), enforce one dispatch per driver if that is the intended workflow, bind each timer to an assignment token and recheck order/driver identity on every tick; stop timers on reassign/cancel/disconnect/completion. Test direct repeated takes, two drivers racing one UUID, one driver taking multiple UUIDs, cancel and disconnect during each state, and stale callbacks after reassignment.

## JOB-003 — repeatable taxi/mechanic calls can fan out worker notifications without an app-level cooldown

**Приоритет: низкий; unthrottled order/cancel sequence confirmed in these handlers; external event-layer throttling and real-world spam impact unverified.**

- `server.phone.taxi.order` and `server.phone.mech.order` send a caller's name/position to eligible on-duty workers and append a dispatch request when at least one worker is available (`Taxi/Repository.cs:45-101`, `Mechanic/Repository.cs:55-109`). Caller-side `cancel` removes that request (`Taxi/Repository.cs:105-166`, `Mechanic/Repository.cs:111-163`). No per-caller cooldown or request-rate check appears in these handlers.
- A caller who repeatedly direct-invokes order then cancel can create repeated worker fan-out and location notifications. The existing `OrdersList` check blocks concurrent duplicate requests, not a rapid sequence after cancellation. Global RAGE ingress limits were not reviewed, so impact beyond the app path is not claimed.

**Remediation work:** add a server-owned cooldown/rate limit keyed by character and bound dispatch fan-out; apply it before publishing location/notifications. Exercise rapid order/cancel/reconnect and direct event sequences with multiple worker clients; verify legitimate retries and cancellation remain usable.

## Narrow read-only endpoint checks — no separate finding asserted

- `server.phone.cars.load` takes no user/vehicle identifier and requires session, account and character data. It derives personal vehicles from the caller or vehicles associated with the caller's own house/roommates, then filters garage entries/holder before responding (`Cars/Repository.cs:18-74,76-150`). Household occupants can see shared-garage vehicle metadata; this is explicit in the household UI shape but should be confirmed against vehicle privacy policy. No arbitrary account/vehicle lookup from this remote was found.
- `server.phone.loadProperty` derives the house via `HouseManager.GetHouse(player)` and business IDs from the caller's `characterData.BizIDs`; it accepts no target ID (`Property/Repository.cs:10-48`). `server.phone.house.load` similarly derives the caller's house/roommate state and assigns owner-specific menu permissions (`Property/Houses/Repository.cs:14-166`). Related mutation remotes and household ACLs are separate audit scope; no conclusion about them is implied here.
- `gps.pointDefault` handles only the named `house`, `biz`, `frac`, and `org` cases, deriving the destination from the caller's own house/business/faction/organization state; unknown names do not select a client-provided coordinate (`Gps/Repository.cs:379-417`). Client receives only its own waypoint.
- `server.phone.recentsClear` clears the caller's in-memory recents list only (`Recents/Repository.cs:69-76`); persistence is part of the later phone-info save. No target selection or cross-player mutation appears in this handler.

## Boundaries

This slice does not complete taxi fare/mileage, mechanic service/payment, business/property mutation, shared-house policy, phone-wide rate limiting or all phone remotes. Taxi mileage has separate `MONEY-012`/`PROG-007` coverage; see `TAXI_MILEAGE_REVIEW.md`. Static findings remain open for owner policy and RAGE regression tests.
