# Phone contacts and SMS — static review

Обновлено: 2026-11-07. Traced contact add/update, direct SMS remote, online delivery, history loading and periodic DB flush. Static-only: no RAGE/CEF execution, MySQL failure injection or live account test.

## SEC-007 — untrusted SMS text reaches executable CEF JavaScript and raw HTML

**Приоритет: высокий; source-to-sink path confirmed, client runtime impact not reproduced.**

- `server.phone.sendMsg` accepts client-supplied `text` and `type` (`Players/Phone/Messages/Events.cs:22-24`). `Repository.SendMessage` does not validate/encode text server-side; for an online recipient it passes the text to `client.phone.msgAdd` and queues it for history (`Players/Phone/Messages/Repository.cs:323-401`). The front-end `format("stringify", ...)` at `message.svelte:127-140` is client-only and is bypassable by calling the server remote directly.
- On live delivery, `src_client/phone/message.js:278-296` interpolates `text` inside a single-quoted string passed to `mp.gui.emmit`; the helper calls `main_browser.execute(execute)` (`src_client/utils/cef.js:37-49`). On history load, `:192-210` embeds the JSON message array the same way. JSON stringification does not escape apostrophes for this surrounding single-quoted JavaScript string. A remote SMS containing quote/statement delimiters can therefore break out of the emitted call and execute script in the target's CEF page when the message is delivered or its chat is opened.
- Separately, the message view renders `{@html formatMessage(message.Text)}` (`src_cef/src/views/player/hudevo/phonenew/components/messages/message.svelte:382-394`). `formatMessage` decodes the client escape markers and then replaces only recognized emoji shortcodes; arbitrary raw HTML sent directly to the remote remains available to this raw HTML sink (`components/messages/data.js:115-135`). This is a second stored/reflected injection path.
- `type` is also client-controlled and not allowlisted by the server. For image type, the same `Text` is passed to `loadImage`, which only checks whether the string contains `jpg`/`jpeg`/`png` before setting `new Image().src` (`src_cef/src/api/functions.js:36-54`; message view `:392-394`). A direct remote can therefore make a recipient's CEF request an attacker-controlled image URL when the chat is open or history is viewed. This is a separate resource-loading/privacy path, not server-side SSRF; URL fetch behavior and exposure were not reproduced.
- `Main.GetPlayerByUUID` returns `null` for an offline player, and the `GetCharacterData` extension is null-safe; `SendMessage` still queues the row after skipping the live-delivery branch. Thus a persisted-history path can target an offline recipient as well; direct live delivery additionally requires an online recipient. The exact CEF bridge capabilities reachable after injection are not established here; no claim of native process or account compromise. No RAGE/CEF reproduction was run.

**Remediation (not implemented):** never concatenate user text or JSON into executable JavaScript. Pass data through a structured bridge or a correctly encoded JSON literal, and render user text as text (`{@html}` only for a strict allowlist of trusted emoji markup after escaping). Validate message type/length server-side and keep formatting canonical across direct remote and CEF UI paths.

**Regression:** on a disposable server, direct-call `sendMsg` with apostrophe/quote/closing-parenthesis sequences and harmless HTML markup, first while the target chat is open and then as a persisted message opened later. Verify no script/DOM sentinel executes, tags render literally, legitimate emoji/map/image flows still work, and storage/rendering use the same safe representation. For `SEC-010`, try controlled untrusted image URLs in `type=img` and verify no request is made outside the approved media host. Test malformed type and oversized text too.

## PROG-009 — contact BattlePass progress is incremented before contact existence/mutation checks

**Приоритет: низкий/средний; statically confirmed active Season4 tasks, not reproduced.**

- `AddContact` calls `BattlePass.Repository.UpdateReward(player, 76)` before checking whether the number is already in `PhoneContacts` (`Players/Phone/Contacts/Repository.cs:20-42`). A direct repeat add of an existing number advances active task 76 despite no contact change.
- `UpdateContact` calls `UpdateReward(player, 78)` before checking `contacts.ContainsKey(number)` (`:46-68`). A direct update for a nonexistent number advances task 78 despite no update.
- Both task IDs are present in the hardwired active Season4 catalog with count 1 (`BattlePass/Season4Models/Repository.cs:73-75`); `UpdateReward` advances active day/week tasks and a selected mission (`BattlePass/Repository.cs:596-660`). These calls can therefore complete the corresponding task without the described contact action. This bypass is bounded by task availability/completion, not an unbounded repeated reward once task state is done.

**Remediation (not implemented):** validate number/name/avatar and determine whether add/update actually changed state before recording progress; award progress only once after successful mutation.

**Regression:** with tasks 76 and 78 active, repeat-add an existing contact and update a missing number via direct remotes; progress must remain unchanged. Valid new contact and valid edit should advance exactly once; replay after task completion must not grant extra progress.

## PHONE-001 — SMS/history batches are cleared before persistence and have no retry

**Приоритет: средний; conditional concurrency/DB-failure loss, not reproduced.**

- Message and read-status queues are ordinary `List<T>` values (`Players/Phone/Messages/Repository.cs:109-158`). The background phone worker invokes their flush every 30 seconds (`Database/Models/Phone.cs:19-43`) while remote event handlers append to the same lists.
- `InsertMessages` snapshots the list and clears the shared list before issuing per-message DB inserts; exceptions are logged without re-queue/compensation (`Repository.cs:111-127`). A DB failure part-way through flush can discard the remaining entries. A producer append between snapshot and `Clear()` can also be erased; no lock/concurrent queue is used. `UpdateMessages` uses the same snapshot-then-clear shape for read receipts (`:130-158`).
- Online SMS delivery and client status are sent before the history insert is durably acknowledged (`:376-400`). Thus a failed/overlapped batch can leave users seeing a message that is absent from history after reconnect. Timing and actual DB-failure impact remain conditional.

**Remediation (not implemented):** use an atomic thread-safe outbox/queue with durable acknowledgment, retry failed batches and isolate poison rows; do not clear messages until each row is committed or safely retained for retry.

**Regression:** append messages during a worker snapshot/clear, fail the first/middle/last insert, restart and compare sender/recipient history; verify all messages either commit once or remain retryable. Repeat for read-status updates and stress concurrent producers/flushes.

## Boundaries

## Deferred system-message remote checks

`server.phone.sendSystemMsg` (`Messages/Events.cs`) checks character data but the handler does not enforce phone/SIM ownership, active phone state or a message-type allowlist; its SIM guard in `SendSystemMessage` is commented out. Police/EMS requests still pass through server active-call/member-availability/cooldown checks (seven minutes for ordinary callers), but the reviewed handlers do not require a phone/SIM. Whether that is an intended emergency-call policy is unconfirmed, so this is **not** logged as a vulnerability. The RedAge bonus/promo route also accepts client text through this remote and needs a separate policy, brute-force and rate-limit review. Track this in the remaining phone work rather than treating `SEC-007` as the only phone finding.

## Boundaries

This is a narrow contacts/SMS slice. Call/settings/Tinder are separately and partially reviewed in `PHONE_CALL_TINDER_REVIEW.md`; News/Forbes are separately reviewed in `PHONE_NEWS_REVIEW.md`; SIM/gallery/animation is partially reviewed in `PHONE_SIM_REVIEW.md`; recents behavior, bonus-code/promo policy, phone-wide throttling and other remotes remain open. No general CEF-XSS conclusion outside the traced SMS sinks is claimed.
