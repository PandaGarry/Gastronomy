# Organization fleet vehicle remotes — static slice

Обновлено: 2026-11-07. Traced `server.org.main.vehiclesLoad`, `evacuation`, `gps`, `updateVehicleRank`, and `sellCar` through `Organizations/Table/Vehicle/Repository.cs` and `Organizations/Manager.DeleteVehicle`. This is a fleet-vehicle slice, not a full organizations ACL review. No source changes or runtime tests.

## Access checks observed

- `vehiclesLoad` requires organization member data and resolves that member's organization; it returns fleet rows with access flags for the UI (`Repository.cs:24-54`). No client-supplied organization ID selects another organization's data.
- `updateVehicleRank` checks `SetVehicleRank`, requires the target plate in the member's organization vehicle dictionary, and bounds both the old and requested minimum rank by the caller's rank; negative ranks are rejected (`:56-115`). Dynamic rank catalog limits and concurrent change behavior still need review.
- `evacuation` and `gps` resolve the vehicle's local data and require `vehicleLocalData.Fraction == memberOrganizationData.Id` and caller rank >= `MinRank` (`:122-212`). Evac additionally rejects occupants, organization-garage vehicles and ticketed vehicles before replacement.
- `sellCar` delegates to `Manager.DeleteVehicle`, which checks `OrgSellCar`, current organization, and target membership in `organizationData.Vehicles` (`Manager.cs:489-506`). The confirmation path re-enters this method and repeats the access/membership checks. No cross-organization target path was established in this slice.

## MONEY-014 — fleet sale pays before asynchronous organization-vehicle deletion

**Приоритет: средний; conditional database failure/restart path, not reproduced.**

- After an authorized `ORGCAR_SELL_TOGOV` confirmation, `Manager.DeleteVehicle(..., type:true)` credits the player (`:562`), then deletes the local vehicle, removes the fleet entry from memory, and schedules a separate async `Orgvehicles.DeleteAsync()` (`:567-592`). The delete failure is only logged; there is no transaction, durable sale receipt, retry, or compensation.
- Therefore if the payout is durably saved while the organization-vehicle row delete fails, restart may reload the fleet vehicle and allow a second sale. The old row/cache and payout failure ordering has not been fault-injected; do not claim duplicated proceeds as runtime-confirmed.
- If no local vehicle handle is found, the branch still logs an error and continues to remove the organization-data entry and schedule the DB delete after credit; the exact legitimate conditions for a missing handle need staging/owner confirmation.

**Remediation (not implemented):** atomically/ idempotently settle organization fleet sale with a unique receipt and durable delete or outbox. Only notify/credit after committed removal, and reconcile the organization cache/used garage slot on retry/restart. Check affected rows and prevent sale replay.

**Regression:** authorized and unauthorized ranks, normal confirmation, forged callback without intent, repeated/concurrent confirmation, missing local handle, and failures before/after wallet persistence and `Orgvehicles` delete. Restart after each injected failure; reconcile org row, in-memory `Vehicles`/`Used`, local vehicle instance and player balance. Requires disposable DB + RAGE staging.

## MONEY-015 — organization vehicle evacuation can complete before the $20 debit succeeds

**Приоритет: низкий; conditional on server-stop/wallet-failure behavior.**

- `Repository.Evacuation` checks `characterData.Money >= 20`, validates vehicle/rank/occupancy, deletes the current entity, recreates it in the organization garage, and only then calls `Wallet.Change(player, -20)` (`:142-174`). The return value is ignored; the handler logs/notifies success regardless.
- `Wallet.Change` can return false for negative amounts while `Admin.IsServerStoping` (`MoneySystem/Wallet.cs:20-29`), so if the remote is still processed during shutdown, the $20 relocation completes without a successful charge. Other concurrent balance/failure cases also need testing. The low nominal amount and shutdown timing make impact limited; no exploit reproduction exists.

**Remediation (not implemented):** successfully debit before replacing the vehicle or use an atomic receipt/compensating rollback; if the debit fails, leave the original vehicle unchanged and do not report success. Explicitly test shutdown behavior.

## Boundaries

Only organization fleet UI/actions were traced. Organization ranks, member ACL mutation, fleet purchases/creation, all organization vehicle entity controls and other organization assets remain open. This advances the organization area from not-started to partial in `AUDIT_COVERAGE.md`; it does not close it.
