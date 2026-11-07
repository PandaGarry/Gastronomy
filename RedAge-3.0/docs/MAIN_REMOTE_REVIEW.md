# Generic Main.cs input/dialog remotes — static review

Обновлено: 2026-11-07. Reviewed `inputCallback`, the mayor/fuel-control menu route, `syncWaypoint`, and selected generic `dialogCallback`/vehicle sync callsites in `Main.cs`. Static-only: no RAGE, CEF or MySQL runtime test. Findings below are mandatory remediation work, not accepted risks or confirmed runtime exploitation.

## MONEY-030 — festive-coin exchange can credit RedBucks without consuming coins

**Приоритет: высокий; count/remove location mismatch and RB credit order confirmed statically; direct-move→exchange chain requires RAGE proof.**

- `inputCallback` accepts the callback name and text from the client (`Main.cs:1503-1535`). In `sell_festive` (`:1891-1921`), it validates `3..500` coins and divisibility by three, then counts EventCoins across all character inventory sub-locations via `getCountItem(..., bagsToggled:false)`.
- It then calls `Chars.Repository.Remove(..., "inventory", EventCoins, limit)` without verifying that the requested amount was removed and immediately credits `limit / 3` RedBucks through `UpdateData.RedBucks`.
- `Remove` only examines the named `inventory` location (`Chars/Repository.cs:3410-3444`). If the event coins reside in `fastSlots` or another counted sub-location, the count check can pass while removal finds no coins; the RB credit still executes. Existing `INV-003` records that direct inventory-move remotes do not enforce all CEF slot restrictions. A direct move→`inputCallback("sell_festive", "3")` could therefore repeatedly exchange the same three coins for one RedBuck if the RAGE path permits the move. No reproduction or actual exploit is claimed.

**Remediation (not implemented):** validate and consume the exact quantity atomically from a single explicitly permitted location before credit; abort unless the consumed count equals the request. Prefer a transactional/idempotent exchange receipt and server-owned callback intent. Do not count from broader locations than the debit can consume.

**Regression:** on a disposable account, place event coins separately in inventory, fast slots and other character locations; direct-call the callback with 3, 498, 500, non-multiples, repeated calls and insufficient balances. Compare exact item/RedBuck balances and persistence after reconnect. Invalid or repeated exchange must not credit; valid exchange consumes exact coins exactly once. Static exploit chain depends on `INV-003` and requires RAGE staging.

## MONEY-031 — generic input callback bypasses mayor authorization for government fuel limits

**Приоритет: средний/высокий; missing authorization and persistent global state mutation statically confirmed; financial/gameplay impact requires staging.**

- `server.mayormenu.open` and `OpenFuelcontrolMenu` require the City Hall fraction leader (`Main.cs:5070-5075, 5120-5124`), and the normal UI callback is reachable through those gated menus.
- However, `inputCallback` accepts `fuelcontrol_city`, `fuelcontrol_police`, `fuelcontrol_ems`, `fuelcontrol_fib`, `fuelcontrol_army` and `fuelcontrol_news` without rechecking the sender's fraction or rank (`Main.cs:1544-1625`). Any authenticated character who passes the common session/account/character and non-Demorgan checks can submit a positive integer; there is no upper bound. The callback mutates `FractionData.FuelLimit` and may also clamp `FuelLeft`.
- `Fractions.Manager.SaveFractions` persists these fields; the daily reset copies `FuelLimit` into `FuelLeft` (`Main.cs:4800-4835`). Government refueling uses `FuelLeft` and debits the City Hall fraction balance (`Core/Businesses.cs:2908-2945`). An unauthorized large limit can therefore alter public fuel allocation, potentially across multiple government factions. Actual financial effect, worker ordering and balance policy were not exercised.

**Remediation (not implemented):** move authorization into the server-side setter; require City Hall leader/explicit authorized rank for the whole operation, use a server-owned target fraction and a documented maximum, and audit fuel-limit changes. Test ordinary leader/nonleader direct calls, every target fraction, over-limit integers, persistence/reconnect and daily reset/refuel accounting.

## Waypoint relay — reviewed, no standalone issue asserted

`syncWaypoint` requires the sender to be a passenger in a vehicle with another character as driver, then relays client-provided X/Y and awards task 126. The relay itself performs the described passenger-to-driver waypoint transfer, so this static pass does not classify the client-supplied coordinates as a task bypass. Finite/world-bound validation and rate limiting still need staging/policy review; no coordinates were executed or tested.

## Other paths spot-checked / remaining scope

- `dialogCallback` has prior transaction findings documented separately (`VEH-001`, `VEH-006`, house/business/economy reviews); those paths remain open and are not repeated here.
- `syncSirenSound` contains server-side driver/faction checks. `VehStream_updateSirenStatus` is a separate client-supplied vehicle-entity sync path and needs a focused review; its normal client poll is currently commented out, so no runtime reachability claim is made here.
- `inputCallback` has many delegated callbacks (faction stock, transfers, tickets, leases, pet/tent and sale flows). Only listed branches were traced in this pass; authorization, numeric bounds, one-shot intent and persistence for all delegated handlers remain incomplete.
- No RAGE/DB assertions were executed. Continue the Main.cs and remote-event audit; do not treat this review as complete.
