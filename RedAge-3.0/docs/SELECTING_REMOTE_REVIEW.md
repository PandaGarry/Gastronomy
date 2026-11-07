# Core selection/player-interaction remotes — static review

Обновлено: 2026-11-07. Reviewed `Core/Selecting.cs` remote surfaces for objects, seatbelt, vehicle interaction, player selection, carry/paired animation, mute, organization interactions and walk style. Cross-checked phone groups for contacts/blacklist/call/recents/GPS/gallery/settings/property-car and business/dispatch routes. Static-only: no RAGE, CEF or MySQL runtime tests; this is a narrow pass and not completion of these subsystems.

## PROG-010 — seatbelt remote can complete BattlePass progress without a belt action

**Приоритет: низкий/средний; direct progress path and active task catalog statically confirmed; remote/task behavior not runtime-reproduced.**

- `beltSelected` accepts a client Boolean, emits an RP chat line, and calls `BattlePass.Repository.UpdateReward(player, 86)` unconditionally (`Core/Selecting.cs:355-368`). There is no server-side check that the player is in a vehicle, the vehicle has seatbelts, the belt state changed, or the Boolean represents fastening rather than unfastening.
- The client normally sends this remote from an in-vehicle UI/key flow (`src_client/player/circle.js:518,969`) after its own vehicle-class check, but direct remote invocation bypasses that client-only policy.
- The active Season 4 task 86 is “Пристегнуть ремень безопасности”, count 1 (`BattlePass/Season4Models/Repository.cs:78`). `UpdateReward` can advance matching active daily/weekly task or mission state; no producer-side success/idempotency condition is present here. The effect is bounded by the task being selected and not already complete; XP/runtime behavior remains untested.

**Remediation (not implemented):** server-check player/vehicle/seat and supported vehicle class; store authoritative belt state and only progress on a false→true transition. If belt state is intentionally client-only, do not award progression from this remote. Test direct calls outside a vehicle, on unsupported vehicle classes, with both Boolean values and repeated calls; valid fastening should progress once, unfastening should not.

## Phone groups cross-checked in this pass

- Contact add/update, blacklist add/delete, gallery add/delete, recents clear, phone open/close, settings toggles and default GPS point were inspected against the phone repositories and client bridge. Their direct-call input/persistence risks are already represented by `PROG-009`, `PHONE-002..003`, `PHONE-006` and existing phone reviews; no duplicate finding was created. The contact BP reward is invoked before checking that the requested add/update mutates a contact (`PHONE_MESSAGES_REVIEW.md`, `PROG-009`).
- Call `take`/`put` use server-held call objects and `acceptPressed` checks request state/expiry for paired interactions; settings sound indices and phone preference URL/size validation are already captured by `PHONE-002..003`. No further independent call-state exploit was established statically.
- Phone property-car listing is read-only and derives vehicles from the caller's house/ownership and garage context in the examined method. Business phone routes are separately tracked in `BUSINESS_ORDER_REVIEW.md`, `BUSINESS_SALE_REVIEW.md` and `BUSINESS_DELIVERY_REVIEW.md`; those findings remain open.

## Core selecting boundaries and remaining work

- `oSelected` resolves a server-created object ID, checks existence and proximity, then the safe/robbery path rechecks the house and lockpick after its delay. It remains necessary to stage-test concurrent house safe jobs, lockpick/inventory mutation and item-save failure; no concurrent duplicate-loot claim is made here.
- `vehicleSelected` checks distance and applies branch-specific vehicle key/faction checks. The full trunk/storage ACL and vehicle remote surface are not reviewed by this note; refer to `GARAGE_REVIEW.md` and `VEHICLE_ACTION_REVIEW.md`.
- `pSelected` has distance checks and delegates most actions to separate fraction/medical/property handlers. Organization-specific selection checks an organization access rank. A full delegated-handler permission audit is still required.
- Carry start includes range/state checks and an accepted-request path; `acceptPressed` validates server-held request state and timeout. Paired animation uses that request state. These spot checks do not close the social/player-interaction surface.
- `unmuteAll` only clears the caller's own muted-player list. `SitWalkSyle` changes only the caller's shared walk-style state. Neither was treated as an authorization issue in this slice.

## Audit limits

No runtime claims are made. Continue reviewing delegated fraction, garage, safe/storage, weapon-shop, damage and all remaining remote/command handlers. Apply all findings as required fixes; do not treat this document as a security sign-off.
