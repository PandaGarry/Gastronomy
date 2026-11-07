# Phone SIM lifecycle, gallery and animation — static review

Обновлено: 2026-11-07. Traced SIM insert/remove from inventory and settings remotes into the live SIM map and DB/inventory persistence; reviewed gallery limits, camera upload path and phone animation bridge. Static-only; no RAGE runtime, DB failure injection or client animation test was run.

## PHONE-005 — SIM ownership/mapping and inventory mutation are not atomic

**Приоритет: средний; source order confirmed, duplicate-card and failure outcomes are conditional/not reproduced.**

- `Settings.Repository.OnAddSim` accepts the number from an inventory SIM item, sets `characterData.Sim`, then assigns `Main.SimCards[newSim] = characterData.UUID` without checking whether that number is already mapped to another UUID. If a duplicated/invalid SIM item exists, this assignment overwrites the current route for that phone number; other callers' SMS/calls follow the new map even though the previous character may still retain the same `Sim` value (`Players/Phone/Settings/Repository.cs:18-63`). The normal item generators consult `Players.Phone.Sim.Repository`, but the insertion boundary itself does not enforce unique ownership.
- Install/replacement changes the in-memory character/map first, schedules the `characters.Sim` DB update asynchronously, and the caller separately changes the inventory item data. These writes are not one transaction. `OnRemoveSim` removes the map and sets `Sim=-1` before calling `AddNewItem`, and ignores its `-1` failure return (`:66-105`). A slot race, item-insert exception or DB failure can therefore leave the character without its number/card, or leave DB/inventory/mapping out of sync. Inventory changes are themselves saved by a separate queue (see `INV-004`).
- The precise duplication/interception or loss requires a duplicated SIM item or a failure between independent writes; neither was generated in runtime testing.

**Remediation work:** use a single server-authoritative SIM ownership operation with uniqueness/owner recheck and transactional or journaled changes to character row, inventory row and mapping; do not publish the new mapping before commit; check all insertion results and compensate/retry. Reconcile `Main.SimCards` at load and reject duplicate installed numbers. Regression-test install, replacement and removal under item-slot races, duplicate cards, DB failure at each write, reconnect and restart.

## PHONE-006 — `server.phone.anim` can spoof selfie animation to nearby clients

**Приоритет: низкий/cosmetic; whether server intent is required is policy-dependent.**

- The remote handler accepts any client integer `id` and only checks character data indirectly (`Players/Phone/Events.cs:22-24`, `Phone/Repository.cs:22-27`). It broadcasts the caller's player ID and that value to players within 50m without checking camera-open state or rate (`Trigger.ClientEventInRange`).
- Client `phoneAnim.js` interprets `type === 1` as a selfie animation on that player (`src_client/phone/phoneAnim.js:69-82`). A caller can directly invoke the event while not using the phone camera and make nearby clients render that pose. No server state change, other-player targeting or gameplay effect is shown; animation may be interrupted by normal replication.

**Remediation work:** if only camera actions should cause this, track server-side camera intent/phone state and allow only valid start/stop transitions with throttling; otherwise document as intentionally cosmetic. Test direct calls with ids 0/1/invalid values outside camera use and observe nearby clients.

## Reviewed, no standalone issue asserted

- `Gallery.AddGallery` enforces a 25-entry count but accepts unbounded URL strings. Gallery belongs to the caller; its image load is an owner-side resource request. This remains subject to the field-size/URL allowlist work in `PHONE-003` and the cross-recipient SMS image risk in `SEC-010`; no separate cross-player gallery issue found.
- Camera capture requires the client camera flow and uploads the user's chosen screenshot to Imgur through `src_cef/src/api/imgSave.js`; no server-side photo upload remote is exposed in this path. External-service ownership/retention is not validated here; see `EXTERNAL_INTEGRATIONS.md`.
- Phone open/close only toggles the caller's `PhoneData.IsOpen` and scenario animation in the reviewed handlers. No separate authorization issue asserted; item/SIM requirement is a product policy question.

## Remaining phone scope

News/Forbes and call/Tinder/SMS have separate partial reviews. Continue remaining phone property/car/mechanic/taxi remote boundaries, open/close and animation lifecycle, news moderation ACL/edit/delete, gallery URL policy, SIM item issuance/trading, and phone-wide rate limits. Phone/social coverage is not complete.
