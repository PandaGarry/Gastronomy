# Vehicle sync remotes — static review

Обновлено: 2026-11-07. Reviewed `VehStream_RadioChange`, `VehStream_SetVehicleDirt` and `VehStream_SetIndicatorLightsData` in `Core/VehicleSync.cs` with their client callsites. Cosmetic/state-sync slice only; no code changes, build or RAGE reproduction.

## VEH-007 — dirt and indicator remotes trust client-selected vehicle entities

**Приоритет: низкий; static entity-authorization/input-validation gap, runtime reachability and persistence need staging.**

- `VehStream_SetVehicleDirt(ExtPlayer, ExtVehicle, float)` (`VehicleSync.cs:379-391`) only checks that the sender has character data and the supplied vehicle is non-null. It does not require the sender to be the driver, to occupy that vehicle, to have keys, or to be near it; it does not constrain the dirt float.
- The shared `SetVehicleDirt` helper (`:456-477`) copies the client value into both `VehicleLocalStateData.Dirt` and the global `VehicleData.Dirt`, then publishes it as shared data `vDirt`. `VehicleManager.SaveSql` later writes `vehicleData.Dirt` (`Core/Vehicle.cs:871-887`), so a forged value can survive a later save if this tracked vehicle is persisted through that path. This handler does not itself issue an immediate DB save.
- The normal client callsite only sends for the currently driven vehicle and clamps the upper value to 15 (`src_client/vehicle/vehiclesync.js:80-90`), but the server does not enforce either rule. The client data handler applies numeric `vDirt` to streamed vehicles (`:195-209`).
- `VehStream_SetIndicatorLightsData(ExtPlayer, ExtVehicle, bool, bool)` (`VehicleSync.cs:393-439`) checks only character data and that the target has vehicle-state data / engine on. It toggles the target's authoritative left/right indicator state and broadcasts `vIL`; it does not bind `veh` to the caller's current vehicle/driver seat or check keys. Client UI callsites pass `global.localplayer.vehicle` (`src_client/vehicle/control.js:59,78,97`), but direct remotes can attempt other streamed entity handles if RAGE marshalling permits.

**Impact boundary:** A forged dirt call can alter another tracked vehicle's cosmetic state and cached dirt value; indicator calls can toggle another vehicle's lights. Dirt bounds/native behavior, exact durability, cross-player entity marshalling and whether the client can target another player's vehicle are not runtime-confirmed. No engine/ownership/money effect is established. Treat as low-priority state integrity/cosmetic griefing, not vehicle theft.

**Remediation (not implemented):** resolve the target from server-authoritative `player.Vehicle`, require the driver seat if intended, and reject stale/nonexistent vehicle state. Clamp dirt to a documented finite range (including rejecting NaN/infinity); only update persistent vehicle data for authorized personal vehicles. If passengers are allowed to change indicators, explicitly document that policy; otherwise bind to the driver's vehicle. Add rate limits if remotes can be spammed.

**Regression:** direct calls while on foot, passenger, driver, and near a foreign vehicle; current vs forged entity, deleted entity, `NaN`, infinities, negative, 0, max and over-max dirt; assert only authorized current vehicle changes and invalid values do not reach shared data/cache/DB. Test repeated indicator toggles and engine-off vehicles. Restart/save to verify authorized dirt persistence. Requires RAGE staging.

## VEH-008 — radio station shared state is writable by any seated occupant

**Приоритет: низкий; intended driver/passenger policy confirmation required.**

- `VehStream_RadioChange(ExtPlayer, short)` (`VehicleSync.cs:364-377`) checks character state and `player.IsInVehicle`, then writes the supplied `index` to shared vehicle data `vehradio`. It does not require driver seat or validate station index.
- The visible client callsite, `src_client/vehicle/radiosync.js:7-12`, sends the event only when the local player is in the vehicle **and** occupies the driver seat, indicating a likely intended driver-only rule. Server-side direct invocation by a passenger bypasses that client gate and can change synchronized station for everyone in the vehicle. Whether passengers are meant to control it is policy-dependent; out-of-range station behavior is untested.

**Remediation (not implemented):** require `player.Vehicle` to exist and the sender to be its driver if that is intended; validate `index` against an explicit supported station/off allowlist. If passenger control is intentional, document and test it.

**Regression:** driver/passenger/on-foot/invalid station values, repeated toggles and vehicle replacement; verify shared state and all occupants' client radios.

## Boundaries

This checks three synchronization events only. It does not review vehicle engine/lock/door, damage, seat, handling, mod or network ownership flows. See `VEHICLE_ACTION_REVIEW.md`, `GARAGE_REVIEW.md` and `VEHICLE_SALE_REVIEW.md`.
