# Phone calls, preferences and Tinder — static review

Обновлено: 2026-11-07. Traced call state transitions, settings remotes and Tinder profile/action remotes through CEF rendering and phone-data persistence. Static-only: RAGE/CEF, MySQL fault injection and client CSS behavior were not run. Findings below remain remediation work; none is considered accepted or fixed by documentation.

## PHONE-002 — unchecked sound indexes can break incoming-call/SMS processing

**Приоритет: низкий/средний; invalid-index exception and source ordering statically confirmed, runtime not reproduced.**

- `server.phone.settings.bellId` and `server.phone.settings.smsId` accept any client `int`; `OnUpdateBellId`/`OnUpdateSmsId` assign it directly (`Players/Phone/Settings/Events.cs:28-35`, `Settings/Repository.cs:196-211`). The CEF selectors choose legitimate indices, but the server remote is independently callable.
- `PlayCall` indexes `SoundsCall[Settings.BellId]` and `PlayNotify` indexes `SoundsNotify[Settings.SmsId]` with no bounds check (`Settings/Repository.cs:327-369`). A negative or too-large ID throws before the sound API is called.
- On an incoming call, `Call.Repository.OnCall` first assigns the recipient's `PhoneData.Call`, then calls `PlayCall(target)`, and only afterwards assigns the caller's `PhoneData.Call` (`Call/Repository.cs:64-99`). An invalid recipient bell ID can therefore interrupt the handler after reserving the recipient's line but before completing caller state. For a non-selected chat, an invalid SMS ID can throw after live `msgAdd` but before sender status/history queue steps (`Messages/Repository.cs:376-401`). Exact recovery behavior depends on RAGE exception handling and disconnect cleanup.

**Remediation work:** clamp/allowlist both indices server-side (or normalize invalid persisted values to defaults) and make call/message state transitions exception-safe. Regression-test all legal boundary IDs and negative/oversized direct-remote values, including invalid stored state after reconnect.

## PHONE-003 — unbounded phone preferences/contact/gallery input can poison phone-info saves

**Приоритет: низкий; schema/write and URL sink paths confirmed statically; practical request-size, DB-mode and CEF network effects not runtime-tested.**

- `addContact`/`updateContact` accept arbitrary `name`/`avatar` strings and there is no contact-count cap; `addBlackList` accepts any integer and has no count cap (`Contacts/Repository.cs`, `BlackList/Repository.cs`). Gallery has a 25-entry cap but no per-link length, scheme or host validation (`Gallery/Repository.cs:12-36`); `settings.wallpaper` likewise accepts an arbitrary string (`Settings/Repository.cs:128-134`).
- `server.phone.addGallery` writes the caller-supplied link into that caller's `phoneData.Gallery`. On gallery open, the CEF `loadImage` helper only checks for the substrings `jpg|jpeg|png`, then assigns the value to `new Image().src`; the helper is used by gallery tiles and the selected-image view (`src_client/phone/gallery.js:16-18`, `src_cef/src/api/functions.js:36-53`, `components/gallery/index.svelte:12-15,47-49,67`). This is an owner-side resource request path; no cross-player gallery write/read path was found, and no script-execution claim is made. Actual CEF network behavior is unverified.
- `phoneinfo.contacts`, `blackList`, and `gallery` are `TEXT`, while `phoneinfo.settings` is `VARCHAR(500)` (`database/main.sql`, `phoneinfo` schema). `SaveSettings` serializes the values and writes all these columns in one update (`Players/Phone/Repository.cs:130-151`), called from character save (`Character/Save/Repository.cs:45`). An unbounded gallery URL or repeated contact/blacklist data can exceed the available column/row value limits; depending on MySQL SQL mode the update may fail or truncate, preventing the other phone-info fields in that statement from saving. Practical remote payload limits and this failure mode were not tested.
- The reviewed remotes mutate only the caller's own phone data; a broader cross-account impact is not established.

**Remediation work:** enforce per-field byte/character limits, allowed URL scheme/host and per-player contact/blacklist limits server-side; preferably persist media IDs or serve media through a trusted proxy rather than loading raw user URLs. Reject before in-memory mutation, size DB fields consistently and isolate/handle failed saves. Test near-column boundaries, large direct gallery URLs, many unique entries, a controlled CEF request log, failed save, reconnect and preservation of unrelated preferences.

## PHONE-004 — replayable Tinder likes can resend match notifications/messages

**Приоритет: средний; duplicate effect statically confirmed, abuse rate and persistence not reproduced.**

- `server.phone.tinder.action` takes arbitrary `uuid` and `isLove` (`Tinder/Events.cs:12-14`). For a valid profile, `OnAction` appends to `Likes` or `NoLikes` without checking for an existing action and without server cooldown/idempotency (`Tinder/Repository.cs:199-238`).
- If the target has already liked the caller, every repeated `isLove=true` call passes `List[uuid].Likes.Contains(callerUuid)` and sends a match payload plus system messages to both participants (`:219-230`). `AddSystemMessage` queues a phone history row; the action therefore permits repeated notifications and message-row creation for an already-established match.
- `GetListRandom` uses `IsVisible` and profile-type filters, but `OnAction` only checks that UUIDs exist in the global profile dictionary. Whether direct likes against an undiscoverable profile should be rejected is a product-privacy rule that still needs confirmation; do not treat that part as a confirmed privacy violation until policy is established.

**Remediation work:** validate target eligibility/visibility and allowed type against server-generated candidates; make each pair/action idempotent, prevent self-targets, and rate-limit actions/match notification delivery. Test direct hidden/ineligible UUIDs, repeated positive/negative actions, already-mutual matches and reconnect persistence.

## SEC-008 — Tinder avatar is interpolated into a CSS `url()` value without server URL validation

**Приоритет: средний кандидат; CSS/request impact requires compiled-CEF reproduction. No script-execution claim.**

- `server.phone.tinder.save` checks profile text length but stores the client-supplied `avatar` without scheme/host/length validation (`Tinder/Repository.cs:261-294`; SQL column `phonetinder.avatar` is `VARCHAR(250)`). The profile is sent to other eligible users by `GetListRandom` (`:175-190`).
- Tinder list/matches render that profile field inside inline CSS `background-image: url(...)` (`src_cef/.../tinder/list.svelte:57-63`, `matches.svelte:20-26`; profile view also uses this pattern). A crafted value may terminate the `url()` value and introduce another CSS URL, potentially causing clients browsing the profile to request an attacker-controlled resource. This is a CSS/resource-loading risk only; CEF CSS parser/CSP behavior and actual victim request were not tested.

**Remediation work:** accept only bounded HTTPS URLs from the trusted image host (or convert upload IDs to server-generated URLs); avoid constructing CSS declarations from unconstrained strings. Verify with a controlled staging endpoint and confirm disallowed schemes/hosts never trigger requests.

## Additional reviewed boundaries (no issue asserted here)

- Call handlers require character data and the caller's active SIM, reject same-SIM/blacklist/airplane/busy targets and bind answer/voice state to the server-created call objects. No arbitrary target-player parameter is accepted by `take`/`put`. Invalid sound indexes remain tracked above.
- `gps.pointDefault` accepts only fixed `house`, `biz`, `frac`, `org` names and resolves positions from the caller's own context; it does not accept client-supplied coordinates.
- `recentsClear` clears the caller's own recents; phone settings airplane mode has a server-side five-minute cooldown.

News/Forbes are separately and partially reviewed in `PHONE_NEWS_REVIEW.md`; SIM/gallery/animation lifecycle is in `PHONE_SIM_REVIEW.md`. Still out of scope: complete gallery upload/URL lifecycle, SIM issuance/trading and all direct remote throttling. See `AUDIT_COVERAGE.md` before treating Phone/social as complete.
