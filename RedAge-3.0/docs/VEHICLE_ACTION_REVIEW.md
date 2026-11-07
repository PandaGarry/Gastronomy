# Vehicle action remotes — статический review

Обновлено: 2026-11-07. Проверены `server.vehicle.action` and `server.vehicle.tuning` in `Houses/HouseManager.cs`. Это два call paths, не полный vehicle review. No source code changed. RAGE event marshalling, C# build and staging were not available.

## VEH-004 — `server.vehicle.action` omits owner/key authorization for aircraft tune, repair, evacuation and GPS actions

**Приоритет: средний; статически подтверждённый authorization gap, target reachability and practical impact require staging.**

- `Houses/HouseManager.cs:2165-2203` accepts a client-supplied `number` and resolves it through the global `VehicleManager.GetVehicleToNumber`. For ground vehicles the handler requires that the selected car is in the caller's household garage slot (except `sell`/`gps`); **aircraft bypass this household check entirely** (`isAir` skips the block at `:2194-2203`).
- The switch enforces `vehicleData.Holder == sessionData.Name` for `spawn`, `sell`, `key` and `changekey` (`:2260-2265`, `:2287-2292`, `:2527-2533`, `:2541-2546`), but does not impose that check in `tune`, `repair`, `evac`, or `gps` (`:2204-2259`, `:2322-2441`, `:2487-2526`). The normal air-vehicle list is owner-filtered, but the event's `number` remains client-controlled and the lookup itself is global.
- For `tune`, a caller within 5m of the air-vehicle NPC can request any known aircraft whose active local vehicle is at the configured spawn area; the code unlocks it if needed, asks the client to put the player in it, then moves that vehicle into a private tuning dimension and opens the tuning UI (`:2206-2258`). The later `server.custom.buy` requires `VehicleManager.canAccessByNumber` (`Core/Businesses.cs:1620-1633`), so this review does not assert unauthorized purchases/customization. The preceding vehicle move/unlock/forced-entry side effects are still performed before that check.
- For `repair`, an aircraft within the NPC range may be repaired after charging the caller; this affects a globally resolved aircraft without a holder check (`:2322-2356`). This is primarily unauthorized use/asset manipulation; repairs cost the invoker under the normal successful wallet path.
- For `evac`, a non-occupied aircraft can be deleted and recreated at the aircraft spawn position (`:2357-2425`) without checking that the caller owns it. `Wallet.Change(player, -Main.EvacCar)` occurs after the relocation and its result is ignored (`:2438`); the earlier balance comparison does not make the two effects atomic. Permanent loss is not established, but another player can request an unowned aircraft's relocation if its plate is known and the caller is near the required NPC.
- For `gps`, aircraft are exempt from household garage checks and the handler sends a waypoint for the globally selected active aircraft's current position (or the general aircraft NPC position if it is not locally spawned) (`:2487-2524`). This is a potential location-disclosure path when a foreign plate is known.

**Impact boundary:** Source supports a missing per-action owner/authorized-key check for aircraft. The relocation/forced-entry/GPS operations are concrete server-side branches; whether an attacker can successfully supply a foreign plate, trigger the client-side enter/exit sequence, and observe/use the result is not reproduced. The `canAccessByNumber` check limits downstream tuning purchases, not the earlier action branch. Do not claim theft or permanent loss.

**Remediation (not implemented):** use a common authoritative access policy before dispatch: owner or explicitly permitted key-holder/household member as gameplay policy allows, plus action-specific location, active-vehicle and occupancy checks. Do not use UI list filtering as access control. For evacuation, validate debit success before moving the vehicle (or use an atomic receipt); bind the request to the server-verified vehicle and action intent.

**Regression:** from two test accounts, invoke each action directly with own, key-shared, foreign and nonexistent aircraft plates; test near/far from NPC, active/stored, locked/unlocked, occupied/unoccupied and ticketed states. Foreign requests must not move/dimension-change/unlock/repair/recreate a vehicle or disclose its position; valid owner/key-holder flows should remain. Inject insufficient funds, server-stop and wallet failure into evac and verify no free relocation or false success. Test normal ground-vehicle household rules separately. Requires RAGE staging and disposable DB.

## VEH-005 — `server.vehicle.tuning` can mutate a client-selected vehicle entity without binding it to the caller's vehicle or access

**Приоритет: средний; conditional on RAGE entity argument marshalling.**

- `Houses/HouseManager.cs:2124-2162` is an active `[RemoteEvent("server.vehicle.tuning")]` with an `ExtVehicle vehicle` argument. It checks the caller has session/account/character and is in *a* vehicle (`player.IsInVehicle`), then reads the passed entity's local data and resolves its plate globally. It does not check `vehicle == player.Vehicle`, `VehicleManager.canAccessByNumber`, ownership, proximity, or a server-created tuning intent.
- It then changes the passed vehicle's dimension and position to the tuning interior before opening the custom UI (`:2154-2162`). The only visible callsite in the examined source, `HouseManager.cs:2234`, is commented out; the active `VehicleAction("tune")` path uses a different client event and does not call this remote. A missing legitimate callsite does not by itself disable the registered remote.
- As with `VEH-004`, the later `server.custom.buy` checks `canAccessByNumber`, but that later guard does not undo the earlier entity relocation. `server.custom.exit` event type 2 can move the current vehicle back to the aircraft spawn (`Core/Businesses.cs:1506-1537`); actual event marshalling and end-to-end reachability are untested.

**Impact boundary:** If a modified client can marshal an arbitrary network `ExtVehicle` into this remote while satisfying `player.IsInVehicle`, the handler attempts to move that vehicle to the caller's private tuning dimension without proving ownership/access or that it is the player's current vehicle. This is a static conditional finding, not a reproduced exploit; unknown/invalid entity serialization may prevent the path.

**Remediation (not implemented):** remove the stale remote if unused, or replace the entity argument with a short-lived server-side tuning intent bound to the actual occupied vehicle, caller, authorized key state and allowed location. Revalidate those facts at entry, each purchase and exit; do not accept a client entity handle as authority.

**Regression:** on RAGE staging test event dispatch with the current vehicle, another player's aircraft/ground vehicle, invalid/deleted entity, and no vehicle; confirm marshalling. If unused, direct event must be disabled. If intended, reject any entity not equal to the server-verified occupied vehicle and any unauthorized owner/key-holder. Assert vehicle dimension/position/access, customization, player seat, wallet and persistence before/after.

## Boundaries and next work

Static source evidence only. Continue tracing other `server.vehicle.*`, impound, storage, garage, key/lock and sale callbacks; this does not close the vehicle/garage subsystem. See `GARAGE_REVIEW.md` and `VEHICLE_REPAIR_REVIEW.md`.
