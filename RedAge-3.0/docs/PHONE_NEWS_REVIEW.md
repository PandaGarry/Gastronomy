# Phone News/Forbes — static review

Обновлено: 2026-11-07. Traced phone advertisement submission through bank debit, LS News moderation/payout/persistence, published phone-news rendering and Forbes privacy display. Static-only; no RAGE/CSP/CSS or database failure test was run.

## MONEY-027 — phone-news charge is not coupled to durable advert creation

**Приоритет: средний; debit-before-async persistence confirmed, failure/refund path not reproduced.**

- `server.phone.addNews` reaches `Players/Phone/News/Repository.Add`. After client text length, cooldown, queue and SIM checks, it computes a server-side price and debits with `Bank.Change(..., -price, false)` (`News/Repository.cs:23-68`).
- Only after the debit does it send `successNews` and schedule `LsNewsSystem.AddAdvert` asynchronously (`:70-75`). `AddAdvert` can return early if session/character data is no longer available; it also catches insert/DB exceptions after logging. Neither path refunds the debit or records a retryable receipt (`Fractions/LSNews/LsNewsSystem.cs:379-430`). The BattlePass reward and success notification also precede the advertised-row insert.
- Therefore disconnect/session expiry or DB/constraint failure after successful debit can leave the payer charged without a queued ad, and may award progress without a saved ad. This depends on the relevant timing/DB mode and is not runtime-reproduced. `link` is client-supplied and lacks an app-level length check despite SQL `advertised.Link VARCHAR(150)`, which is one concrete constraint-failure case under strict SQL mode.

**Remediation work:** model advert creation/payment as a durable idempotent transaction/outbox; validate all fields against schema before debit; confirm insert before reporting success/progression, or reliably compensate/retry on failure. Test DB outage/constraint failure/disconnect after debit and concurrent duplicate submissions.

## MONEY-028 — News moderation payout/publication can replay if advert completion is not durably recorded

**Приоритет: средний; failure/restart replay conditional, not reproduced.**

- `LsNewsSystem.UpdateAnswer` credits the reviewing editor with `Bank.Change(..., moneyad, false)`, enqueues a completed-ad record, publishes the ad into `News.Repository.NewsList`, awards table score, and notifies the author before scheduling the DB update that sets `advertised.Status=true` (`Fractions/LSNews/LsNewsSystem.cs:466-507`). The return from `Bank.Change` is ignored.
- `AdvertList` is removed in memory before the DB write. Startup reloads every row whose DB `Status` is still false (`LsNewsSystem.cs:195-220`). If a crash/DB error occurs after the commission or publication side effect but before the status update commits, the row can be reloaded and reviewed again; an editor could receive duplicate commission/publication/progression. Exact bank durability and restart ordering depend on separate save-worker timing; no fault-injection test was run.
- `AdvertSend` verifies LS News access and pending status but does not check that the caller is the editor currently assigned in `AdvertData.Editor` (`LsNewsSystem.cs:340-353`/`UpdateAnswer`). Whether `take` is intended to be an exclusive lock is a workflow policy question; not logged separately without owner confirmation.

**Remediation work:** make completion status, editor commission, progress and public publication one idempotent settlement keyed by advert ID (or use a durable completion receipt/outbox); validate/ack the bank operation; expose the ad as pending again only if no completion receipt exists. Test crash/failure after each side effect, repeated send, competing editors and restart.

## SEC-009 — published News image link enters inline CSS without URL validation

**Приоритет: средний кандидат; compiled-CEF/CSP resource request requires staging proof. No script-execution claim.**

- Phone `addNews` accepts a client `link` with no URL scheme/host/length validation in `News.Repository.Add` (`:23-75`). The LS News insert stores it as an advertisement; authorized editor `UpdateAnswer` publishes the accepted advert through `News.Repository.AddList` (`Fractions/LSNews/LsNewsSystem.cs:433-478`). The link is then included in the public phone `NewsListJson` (`News/Repository.cs:79-93`).
- The phone News list checks whether the link contains `jpg`, `jpeg` or `png`, then interpolates it inside `style="background-image: url({item.link})"` (`src_cef/.../components/news/list/index.svelte:100-103`). A crafted link that passes the extension substring check may break out of the CSS `url()` value and trigger a resource request when viewers open News. Moderator approval is a precondition; CEF CSS parsing, CSP and actual network request were not tested.

**Remediation work:** enforce a bounded HTTPS URL on the trusted media host (or store server-generated image IDs); never use an untrusted URL as a raw CSS declaration value. Test rejected schemes/hosts and CSS delimiters with a controlled staging request logger after moderation.

## Forbes privacy control — reviewed, no finding asserted

`Forbes.Repository.GetData` continues to include a hidden user in ranking and exposes the user's aggregate cash/bank `Money`, `SumMoney`, level and rank. The toggle is described in UI as privacy for asset/property details, and the repository clears the per-asset `List` when `IsShowForbes` is false; the CEF item view hides those details and displays the configured privacy notice. This is consistent with a narrower asset-detail opt-out, not proof of a privacy bypass. Product owners should confirm whether aggregate wealth/rank is intentionally still public; if not, change both server ranking payload and UI together.

## Boundaries

News add/publish/review settlement has narrow static coverage (`MONEY-027..028`, `SEC-009`); moderation role semantics, deletion/edit replay, all advertised UI entry points and phone-wide rate limits remain unreviewed. Forbes aggregate wealth visibility remains a policy question. No general security conclusion for other phone modules is claimed.
