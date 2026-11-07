# Матрица полного аудита RedAge 3.0

Обновлено: 2026-11-07. Матрица разделяет предварительную инвентаризацию и завершённый аудит: `Частично` не означает, что подсистема безопасна. Runtime проверки не проводились. Источник анализа — snapshot commit `23730b8cd464f86c47eaae6f80d182cd651092b2`.

## Состояние покрытия

| Область | Статус | Что проверено / зарегистрировано | Что остаётся до закрытия |
|---|---|---|---|
| Исходный снимок, секреты, разрешение | Частично | Отдельная рабочая папка; локальные конфиги очищены; исходник без LICENSE, scope разрешения отмечен. | Сохранить подтверждение прав на исходники, UI и ассеты, модификации, хостинг/публикацию; повторять secret scan после правок. |
| Build/dependencies/release | Частично | Dependency inventory, client build, часть JS/JSON checks; фиксированы CEF peer конфликт/OOM, Debug DLL path, отсутствие lockfiles. | Доверенный reproducible build, C# compile, полный CEF build, SBOM/advisory triage, правильный Release package/meta.xml. |
| DB/bootstrap/configuration | Частично | MySQL helper/config, отключённый TLS, global `max_connections`, SQL logging, boot path; SQL objects подсчитаны. | Полная schema/procedure review; TLS/least privilege; error/timeout/retry/transactions; чистый import/restore; runtime startup order. |
| Auth/accounts/sessions/passwords | Частично | Legacy unsalted SHA-256 + ASCII conversion; registration/login helpers и часть session flow. | Полный auth/2FA/session lifecycle, throttling, account recovery, privilege boundaries, migration tests. |
| Queue/concurrency | Частично | `Players.Queue.Repository` shared `List`/worker race. | Все cross-thread collections, lock ordering, disconnect/reconnect/load testing. |
| Server remote events/commands | Инвентаризация | Считано около 498 `[RemoteEvent]` в 137 файлах, 116 `[ServerEvent]` в 83 файлах; изучены отдельные ATM/dialog/payment paths. | Пофайлово проверить каждый event/command: auth, ownership, type/range, distance/dimension, rate limit, replay/idempotency, exception/logging. |
| Economy/RedBucks/bank/ATM | Частично | `MONEY-001..007`: gift debit/credit, deferred save queue, bank transfer replay, ATM state, DonatePack partial purchase, roulette case purchase input exploit and NewCasino outcome-dependent disconnect refund; narrow guards remain unverified and MONEY-007 requires gameplay-policy agreement. | Исправить после безопасного transactional design; staging tests, balances/ledger reconciliation, concurrent/replay tests. См. `ECONOMY_REVIEW.md`. |
| Внешние донаты/платёжные receipts/DonatePack | Частично | `PAY-001..003`: no exactly-once receipt, timer/thread affinity, unsafe/volatile pack intent. | Provider contract/signature, durable unique ledger, outage/crash/multi-instance tests, config/secrets review. См. `PAYMENTS_REVIEW.md`. |
| Inventory/items/shops/weapons/clothes | Частично | Reviewed remote move/stack/use/drop/notes paths, roulette case consumption, CEF slot rules, tent read-only path и item persistence queue. Findings `INV-001..007`; roulette negative-count duplication is locally guarded but unverified; локально добавлены unverified guards для count/same-slot и read-only чужой палатки на проверенных mutation paths. | Продолжить trade/storage/weapon/clothing/shop paths; проверить все container ownership/type policies, caps, note edit authorization, queue recovery; собрать и прогнать regression tests до закрытия патчей. |
| Characters/progression/quests/battle pass | Частично | BattlePass `take`/`takeAll`/mission reward and persistence paths reviewed statically; CAS-027..028 cover crash replay of claim receipts and failed/partial grants consumed as claimed. Другие progression call sites ранее упоминались только точечно. | Проверить все `UpdateReward` producers, season/reset/migration, daily/weekly task scheduling, quest/achievement endpoints; выполнить C# build и DB/RAGE failure/replay tests; проверить full character lifecycle and auth. См. `BATTLEPASS_REVIEW.md`. |
| Vehicles/garages/vehicle trade | Не начато | Инвентаризация архитектуры; детальный security review отсутствует. | Ownership/keys/locks/spawn/store/garage/trade/number plate, race/duplication, world cleanup. |
| Houses/businesses/properties | Не начато | Только ATM deposit limits call sites частично просмотрены. | Ownership/tenant/permissions, storage, balances, taxes, auctions/transfers, offline behavior. |
| Factions/organizations/admin/moderation | Не начато | Нет полного ACL review. | Permission matrix, rank changes, invite/kick, money/assets, command authorization/audit logs. |
| Jobs/world events/casinos/gambling | Частично | NewCasino Roulette/Blackjack/Spin/Horses/LuckyWheel и legacy `/dice`/Lottery имеют частичные статические reviews: guards CAS-001/003/006 внесены, не runtime-tested; CAS-008..026 открыты либо требуют policy confirmation; CAS-011 RTP calculation требует согласования; MONEY-007 roulette outcome-refund открыт. См. `CASINO_REVIEW.md`, `BLACKJACK_REVIEW.md`, `SPIN_REVIEW.md`, `HORSES_REVIEW.md`, `LUCKYWHEEL_REVIEW.md`, `DICE_REVIEW.md`, `LOTTERY_REVIEW.md`. | Скомпилировать/staging test всех patches; решить settlement/refund/limits/RTP/prize policies; проверить остальные casino/gambling remote paths, shop session authorization, RNG/concurrency/DB failure и оставшийся gambling scope. |
| Phone/social/communications | Не начато | Нет полного review. | Contact privacy, messages, calls, GPS/phone payments, user text injection, throttles. |
| Client JS / CEF UI | Частично | Syntax baseline, client bundle build, dependency audit summary. | Event trust boundaries, HTML/CEF injection, browser storage, bridge/API permissions, UI consistency with server validation. |
| External services/integrations | Инвентаризация | Hostnames/API/CDN/payment/radio references перечислены. | Активные endpoints, ownership, TLS/auth/signatures, data flows, outage/timeout behavior, replacements. |
| Performance/optimization | Не начато | Подтверждённые измерения не выполнялись. | Staging baseline CPU/RAM/tick latency/DB query profiles; optimize only measured bottlenecks with regression checks. |
| Deployment/operations/recovery | Заблокировано | Requirements for persistent process/ports and environment recorded. | RAGE runtime and host chosen; firewall, backups/restore, monitoring, log rotation, incident/rollback drills. |

## Порядок выполнения

1. Продолжать статический review в областях высокой ценности/риска; каждое наблюдение получает ID, severity, code reference, confidence, remediation and tests in `ISSUES.md`.
2. Для критичных economy/auth/payment issues согласовать семантику и разработать transactional/idempotent design до изменений, а не накладывать локальные checks поверх race-prone flow.
3. Подготовить test harness/build-agent и одноразовую DB; внедрять маленькие патчи, тестировать regression/failure/concurrency scenarios, обновлять issues до `Закрыто` только после доказательной проверки.
4. Проверить каждый reachable remote event/command и затем UI/client bridges, чтобы сервер не доверял клиенту.
5. Только после функциональной/безопасностной базы — измерить staging performance и оптимизировать по профилю; затем подготовить deployment/recovery drills.

## Критерии завершения аудита

- Весь список reachable remote/server events, commands, webhooks и integration entry points проверен, а каждый finding либо исправлен и протестирован, либо принят как documented design decision.
- Денежные и платежные операции имеют server authority, transaction/idempotency strategy, durable audit trail и tests на retry, restart, race, DB failure.
- Все subsystems из таблицы имеют завершённые review notes; security-sensitive client input проверяется server-side.
- Есть воспроизводимая сборка и staging smoke/integration suite с покрытием основных gameplay flows и failure paths.
- Perf-изменения подкреплены baseline/profiling, а не предположениями; release/recovery process проверен.

Даже при выполнении критериев нельзя математически гарантировать отсутствие всех багов; цель — систематическое покрытие исходника, тестируемые инварианты и контролируемый release, а не недоказуемое обещание «ошибок больше нет».
