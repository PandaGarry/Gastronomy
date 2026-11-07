# House resident permission remotes — static review

Обновлено: 2026-11-07. Reviewed `server.house.resident.access`, `server.house.resident.dell`, the house invite acceptance write, and permission consumers. This is a resident/ACL slice, not a full property review. No code changes, build, DB or RAGE tests.

## PROP-001 — a roommate can change resident ACLs and evict other roommates

**Приоритет: высокий; статически подтверждённая role/authorization failure, runtime reproduction pending.**

- Both remotes call `GetHouse(player)` (`HouseManager.cs:2063-2072`, `2098-2107`). `GetHouse` returns a house when the player is the owner **or** when the name appears in `Roommates` (`:927-943`); these handlers do not use owner-only `GetHouse(player, true)` and contain no owner/delegated-admin check.
- `server.house.resident.access` accepts a target roommate name and toggles `isFurniture` or `isPark` (`:2074-2090`). It does not restrict the target to the caller or verify the caller is the owner. Consequently a roommate can toggle their own permissions or another roommate's.
- These flags are authorization inputs, not merely UI preferences: `Players/Phone/Property/Houses/Repository.cs:66-82,132-136` grants the `inGarage` and `furniture` menu accesses from `isPark`/`isFurniture`; `Core/Selecting.cs:120-125,252` treats `isFurniture` as authorized furniture/safe access and directly opens the `furniture_<houseId>` container. Thus self-toggling `isFurniture` lets the roommate skip the lockpick/hijack branch and reach the safe-container open path; `isPark` grants garage UI access. Whether every later item mutation enforces an additional server-side check was not traced in this slice.
- `server.house.resident.dell` removes any requested key in the same `Roommates` dictionary and calls `garage.DeleteCarToName(name)` (`:2109-2116`). A roommate can therefore evict a different roommate and remove their garage slot associations. The owner itself is not in `Roommates`, so this handler cannot remove the owner through this particular branch.

**Impact boundary:** The server accepts the role/permission mutation from an ordinary roommate by static control flow. The resulting furniture/safe or garage asset impact, client UI response, and whether any subsequent subsystem blocks it are not reproduced. Do not claim actual item theft or permanent vehicle loss without staging.

**Remediation (not implemented):** require the actual owner (or a separately defined server-side delegated permission) before changing or deleting roommate records. A roommate may leave themselves through a distinct action, but cannot grant/revoke another resident's permissions. Validate action allowlist and target against current membership; use explicit desired permission values rather than toggle commands to avoid replay ambiguity.

**Regression:** owner vs roommate calls for `isFurniture`, `isPark`, and eviction; direct self/other/owner/nonexistent names and repeated calls. Non-owner calls must not change ACL or garage state. On staging, confirm furniture/safe and parking access stay denied to unauthorized residents and ordinary roommate self-leave remains possible.

## PROP-002 — roommate membership/permission writes are not marked dirty for the house save worker

**Приоритет: средний; static persistence gap; exact save/restart behavior needs DB test.**

- The persistence worker only selects houses where `House.IsSave` is true (`Database/Models/Houses.cs:26-50`) and writes the serialized `Roommates` dictionary via `House.Save` (`HouseManager.cs:425-445`).
- `OnResidentAccess` changes resident flags and `OnResidentDell` removes membership, but neither sets `house.IsSave = true` (`HouseManager.cs:2063-2116`). The accepted invite path adds `house.Roommates.Add(player.Name, ...)` at `:2692` and likewise does not mark the house dirty. No direct DB update for these mutations is present in the traced handlers.
- For a parking permission revoke or eviction, `garage.DeleteCarToName` marks the *garage* dirty and its slot data may be saved, but that does not save `house.Roommates`. Unless a separate house mutation has already marked the house dirty, a restart can reload stale resident membership/flags from the database. This can resurrect a removed roommate or lose a valid invite/permission change; exact behavior depends on worker timing and other dirty house writes.

**Remediation (not implemented):** mark the house dirty on every membership/permission change, or persist the mutation directly with checked DB result and cache convergence. Couple resident removal with garage-slot cleanup and decide an explicit crash-consistent ordering.

**Regression:** invite/accept, permission toggles, eviction, self-leave, server restart with and without unrelated house mutations; compare DB `Roommates`, runtime dictionary, garage slots, property accesses, and notifications. Inject DB save failure and ensure retry/reconciliation.

## Boundaries

House ownership transfer, furniture purchase/use transaction paths, bank/tax/auction/storage ACL and other property remotes remain unreviewed. This starts a partial houses/properties review only; it does not close that coverage area.
