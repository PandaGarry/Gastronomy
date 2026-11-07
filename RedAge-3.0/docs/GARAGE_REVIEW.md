# House garage remote `server.garage.parking` — статический review

Обновлено: 2026-11-07. Это один garage mutation remote, не полный аудит vehicle/garage subsystem. Код не менялся; C# build, game-event marshalling, MySQL и RAGE staging tests недоступны в текущем окружении.

## VEH-002 — garage parking accepts a globally resolved vehicle ID without household ownership validation

**Приоритет: средний; статически подтверждённая authorization gap, практический ущерб/достижимость ID требуют staging.**

- `Houses/GarageManager.cs:1221-1260` obtains the caller's owner-or-roommate house (`HouseManager.GetHouse(player)`), requires that the house's garage exists and matches `characterData.InsideGarageID`, and validates the garage type. These checks bind the caller to a garage, but do not bind the supplied `autoId` to that household.
- Both mutation branches resolve the client-supplied integer through `VehicleManager.GetVehicleToAutoId(autoId)` (`:1274`, `:1327`). `Core/Vehicle.cs:150-175` loads every database vehicle into the global `Vehicles` map and `VehiclesSqlIdToNumber` map; `GetVehicleToAutoId` (`:984-988`) resolves from that global map. No `vehicleData.Holder == house.Owner || house.Roommates.ContainsKey(vehicleData.Holder)` check appears in this remote.
- The checks at `:1307` and `:1342` only constrain the live local vehicle's access mode when such a local vehicle exists. An absent local vehicle passes these conditions; neither check verifies holder/household ownership. The home-phone list filtering (`Players/Phone/Cars/Repository.cs:GetCarToHouse`) limits normal UI output but is not server authorization for a forged direct remote.
- The handler writes the resolved foreign `SqlId` into this garage's `CarSlots`, destroys any current local instance by plate, and invokes `SpawnCar` (`:1317-1323`, `:1349-1354`). `SpawnCar` creates a locked `VehicleAccess.Garage` instance in the target garage dimension (`GarageManager.cs:335-359`) and is not passed household context. The normal `SpawnCars(..., house)` loading path later removes slots whose vehicle is not among household vehicle numbers / whose holder is neither owner nor roommate (`:370-392`); this delayed cleanup does not protect the direct remote mutation.

**Impact boundary:** Source establishes that an authenticated house owner/roommate standing in that house's garage can request a slot mutation for any globally indexed `autoId`, without an explicit household ownership check; direct execution can mutate that garage's slot mapping and attempt to destroy/recreate the associated vehicle in that garage. The numeric-ID enumeration/guessability, exact RAGE runtime behavior, whether a victim can recover/use the vehicle, and any permanent loss/theft/duplication are **not established**. Do not describe this as proven theft or duplication absent staging reproduction.

**Remediation (not implemented):** before any mutation, require the vehicle's `Holder` to be the house owner or a current roommate (and verify any intended shared-vehicle policy). Also validate the occupant being displaced under the same rule. Keep the UI list filter as presentation only. Prefer a single ownership-aware service used by remote, load, and persistence paths; make slot updates transactional/atomic with spawn/delete outcomes, and prevent stale `CarSlots` associations across garages.

**Regression:** use two disposable characters/houses, owner and roommate cases, and foreign vehicles in active, garaged, and unspawned states. Invoke the remote directly with valid own, roommate, foreign, nonexistent, and changed-roommate IDs; assert foreign requests do not change either garage's serialized `CarSlots`, vehicle local access/dimension/existence, position, or owner-visible list. Test occupant swaps, full garages, concurrent requests, restart/load cleanup, and owner recovery. Confirm normal household parking remains valid. Requires test DB and RAGE staging.

## VEH-003 — crafted negative slot index can persist an invalid garage slot and prevent spawn

**Приоритет: низкий/средний; статически подтверждаемая data-integrity/availability issue.**

- `server.garage.parking` receives `index` as an unrestricted `int` (`:1222`). The non-occupied branch writes `garage.CarSlots[index] = vehicleData.SqlId` and sets `garage.IsSave = true` (`:1325-1361`); there is no `0 <= index < GarageTypes[garage.Type].MaxCars` validation.
- For an unused key below `-1` (for example `-2`), `Garage.UpdateCarSlot` (`:125-165`) treats the id as already slotted and only rejects keys `>= MaxCars`; it returns the negative key unchanged. `SpawnCar` then indexes `VehiclesPositions[index]` / `VehiclesRotations[index]` (`:347-356`), which throws and is caught (`:361-364`). The slot remains in `CarSlots`; the handler marks the garage for save, and `Garage.Save` serializes the dictionary (`:276-286`).
- A later house-aware `SpawnCars` pass filters ownership associations but does not validate the slot-key range (`:370-402`); `SpawnCarToPos` reaches the same invalid-index path. Thus the affected vehicle can fail to spawn through this slot until repaired/removed. Exact restart behavior depends on database save scheduling and was not run.
- Out-of-range positive keys behave differently: `UpdateCarSlot` removes keys at/above `MaxCars` and attempts to allocate a valid free slot. Do not report arbitrary positive indices as a capacity bypass based on this trace. The demonstrated case is an unused negative key below `-1`.

**Remediation (not implemented):** reject all indices outside `0..MaxCars-1` before any dictionary mutation; also validate loaded `CarSlots` records during garage initialization and before save/spawn, removing/quarantining invalid entries and logging garage/vehicle identifiers. Do not rely on `UpdateCarSlot` to sanitize a key supplied by the caller.

**Regression:** direct-call with `-2`, `int.MinValue`, `-1`, `0`, `MaxCars-1`, `MaxCars`, and `int.MaxValue`; verify invalid values are no-ops and do not set dirty/save state, alter `CarSlots`, destroy/recreate a vehicle, or stop other garage spawns. Test corrupted serialized keys on load and clean recovery. Requires C# build, disposable DB and RAGE staging.

## Boundaries and next work

This is source-only evidence, not a live exploit reproduction. The garage remote is now partially reviewed; remaining work includes all other vehicle storage/impound/recovery/trade/keys/locks/spawn paths, remote boundary inventory, and runtime validation. The prior `VEH-001` self-repair callback remains policy-dependent; see `VEHICLE_REPAIR_REVIEW.md`.
