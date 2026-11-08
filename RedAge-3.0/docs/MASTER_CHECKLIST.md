# RedAge 3.0 — Master Checklist

Обновлено: 2026-11-08
Рабочая ветка: `redage/audit-continuation`
База рабочей ветки: `arena/fab5bf55-gastronomy`
Целевая ветка релиза: `main` (не изменять напрямую).

## Правила безопасной работы

- [ ] Перед каждым изменением проверить актуальные refs, diff и полный data flow.
- [ ] Все изменения RedAge держать только внутри `RedAge-3.0/`; не менять корневые файлы Gastronomy.
- [ ] Не отправлять изменения в upstream `ragemp-pro/redage_v3`.
- [ ] Каждый finding получает ID, severity, точные code references, confidence, remediation и regression tests.
- [ ] Не считать статический finding runtime-подтверждённым.
- [ ] Не закрывать finding до C# build и релевантных RAGE:MP/MySQL regression tests.
- [ ] Денежные операции проектировать атомарно и идемпотентно; не доверять клиентскому результату.
- [ ] Не использовать production DB, реальные платёжные данные или реальные credentials для тестов.
- [ ] Каждый патч сопровождается обновлением ISSUES, соответствующего review, TEST_PLAN, BUILD_LOG, CHANGELOG, ROADMAP и AUDIT_COVERAGE по применимости.
- [ ] Перед merge проверять PR diff, тесты, конфликты и возможность rollback.

## Этап A — Репозиторий и контроль изменений

- [x] GitHub read access подтверждён.
- [x] GitHub write access проверен реальной операцией создания ветки.
- [x] Создана рабочая ветка `redage/audit-continuation` от `arena/fab5bf55-gastronomy`.
- [ ] Сверить уникальные коммиты `main` и `arena/fab5bf55-gastronomy`; не объединять ветки вслепую.
- [ ] Подтвердить лицензионные права на исходники, UI и игровые ассеты.
- [ ] Проверить видимость репозитория и секреты; ротировать любые действовавшие credentials, если это требуется.
- [ ] Согласовать базу и target для первого Draft PR.

## Этап B — Воспроизводимая сборка и стенд

- [ ] Закрепить совместимую версию .NET SDK/runtime для `netcoreapp3.1` и RAGE:MP.
- [ ] Закрепить NuGet/npm зависимости и создать проверенные lockfiles.
- [ ] Повторить C# build на изолированном агенте.
- [ ] Завершить CEF production build на агенте с достаточной RAM.
- [ ] Поднять одноразовую MySQL test DB и проверить импорт/restore.
- [ ] Поднять RAGE:MP staging с тестовыми аккаунтами.
- [ ] Подготовить fault-injection, replay, concurrency и restart test harness.

## Этап C — Критичные деньги, платежи и игровые активы

- [ ] MONEY-008/009, PROG-001 — Sapper: серверная state machine, RNG, ход, cashout, exactly-once settlement.
- [ ] STOCK-001 — faction/organization/vehicle stock and cargo transfers: exact Remove/AddNewItem/Wallet.Change result, atomicity, authorization, idempotency and restart recovery; include partial grants and all stock containers. See `FRACTION_STOCK_REVIEW.md` and `ISSUES.md`.\n- [ ] STOCK-002 — business retail stock and customer settlement: takeProd rollback, owner-bank credit, customer Wallet.Change, exact item/weapon grant, missing product rejection, dirty-save and exactly-once behavior. See BUSINESS_RETAIL_REVIEW.md.
- [ ] MONEY-030 — EventCoins: точное списание из разрешённого контейнера до начисления RB.
- [ ] MONEY-031 — Fuel Control: server-side role/fraction authorization и input bounds.
- [ ] MONEY-032 — Mayor treasury withdrawal: confirm bank credit before treasury debit; transactional/restart-safe settlement.
- [ ] MONEY-033 — Ticket settlement: successful debit required, server-side one-shot intent and durable idempotent payout.
- [ ] MONEY-034 — Gang drug purchase: quantity cap, checked/long cost+capacity math, exact item-grant result before faction debit.
- [ ] MONEY-035 — Faction/organization money withdrawal: check wallet credit result; atomic stock/player balance transfer.
- [ ] MONEY-037 — Player-to-player house sale: buyer debit and seller credit must both succeed before ownership transfer; correct seller UUID in money log; idempotent offer settlement and crash/replay tests; see `HOUSE_SALE_REVIEW.md`.
- [ ] MONEY-038 — Phone auction bid: reject nonpositive/out-of-policy bids; use checked `long` fee arithmetic so client `int` overflow can never turn a debit into a credit; test numeric boundaries, bank failures and replay/concurrency; see `AUCTION_REVIEW.md`.
- [ ] MONEY-036 — Shared Wallet.Change: preserve long balance; remove int truncation and test every caller at numeric boundaries.
- [ ] Review organization stock implementation against the same money/item settlement invariants.
- [ ] MONEY-022/025/026 — business order dirty-save, unchecked cancel-refund result, quantity overflow, government-sale unchecked payout/ownership release and stale-BizID replay; include `JOB-004` Trucker payout settlement.
- [ ] MONEY-003/004 — bank transfer replay и ATM policy/location.
- [ ] MONEY-005, PAY-001..003 — payment receipts, durable idempotency и compensation.
- [ ] MONEY-001/002/011/012 — money queue, online reward checkpoint, taxi mileage/fare.
- [ ] MONEY-013..019, 022..024, 027..029 — property, vehicle, business and phone settlement/persistence.
- [ ] INV-001..011 — inventory/container ownership, counts, ammo, crafting and item lifecycle; include Other-item auction escrow award/return (`INV-011`, `AUCTION_REVIEW.md`).
- [ ] CAS-001..028 — casino state machines, RNG, wager limits, disconnect settlement and prize grants.
- [ ] PROP-001..005, VEH-001..008 — ownership/ACL, persistence, vehicle actions and recovery.

## Этап D — Auth, remotes и инфраструктура

- [ ] Versioned password-KDF migration with backward-compatible legacy verification.
- [ ] Review all 498 RemoteEvent mentions, 116 ServerEvent mentions and 382 Command mentions; inventory counts are not completion evidence.
- [x] Enumerate 38 `Main.ClientEvent_inputCallback` case occurrences (32 unique callback names); selected delegated helpers checked, remaining paths explicitly listed in `MAIN_REMOTE_REVIEW.md`.
- [ ] Finish every delegated `inputCallback` handler review, including stock, house/drug sale, street race, vehicle trade, hotel, tent and pet flows.
- [ ] Server-side ownership, permission, type/range, distance/dimension, rate-limit and replay checks.
- [ ] Audit shared collections, worker threads, lock ordering and RAGE thread affinity.
- [ ] DB TLS, least-privilege accounts, parameterized SQL, safe logs, timeout/retry/transaction behavior.
- [ ] External integration signatures, nonce/timestamp, idempotency, timeout/retry and secret rotation.

## Этап E — Качество, производительность и релиз

- [ ] Automated static checks and CI.
- [ ] C# unit/integration and RAGE staging regression suite.
- [ ] Profile CPU, RAM, tick latency and DB queries before optimization.
- [ ] Review CEF bridge, HTML/resource loading, accessibility and UX.
- [ ] Release checklist, backup/restore, rollback and incident drills.
- [ ] Consider solo-mode/NPC simulation only after security baseline and API/capacity validation.

## Definition of Done для каждого finding

- [ ] Reproducible source path and affected invariant documented.
- [ ] Fix reviewed for races, retries, exceptions, partial DB failures and disconnect/restart.
- [ ] Regression tests cover valid, invalid, boundary, duplicate/replay and concurrent inputs.
- [ ] Build and relevant staging tests pass; logs/results recorded.
- [ ] Docs, issue status and changelog updated.
- [ ] PR reviewed; merge only after owner approval.

## Текущие подтверждённые ограничения

- C# build, full CEF production build, disposable MySQL DB and RAGE:MP runtime are not yet available in this work context.
- MONEY-030/031 and Sapper issues are statically confirmed; no live exploitation or runtime test is claimed.
- `main` and `arena/fab5bf55-gastronomy` diverge by one unique commit on each side. Preserve both histories until the diff is reconciled.
- GitHub repository API currently reports visibility as public; verify and change in GitHub settings only if that is not intended.
