# RedAge 3.0 — единый мастер-план аудита, исправлений, тестирования и развития

**Обновлено:** 2026-11-08  
**Рабочая ветка:** `redage/audit-continuation`  
**Рабочий PR:** [#4](https://github.com/PandaGarry/Gastronomy/pull/4) (Draft; не сливать автоматически)  
**Область изменений:** только каталог `RedAge-3.0/`  
**Исходный upstream snapshot:** `23730b8cd464f86c47eaae6f80d182cd651092b2`

> Этот документ — единый источник истины для согласованного плана и текущего статуса работ RedAge 3.0. При расхождении кратких планов и заметок приоритет имеют этот документ и детальные evidence/review-файлы, на которые он ссылается. Фактические результаты сборок и тестов фиксируются в `BUILD_LOG.md` и `TEST_PLAN.md`; findings и их статусы — в `ISSUES.md`; охват аудита — в `AUDIT_COVERAGE.md`.

---

## 1. Цель проекта

Довести RedAge 3.0 до высокого, измеримого уровня качества по направлениям:

1. **Стабильность:** отсутствие необработанных падений, зависаний, утечек ресурсов и деградации при длительной работе.
2. **Корректность:** деньги, предметы, транспорт, собственность, прогресс и другие игровые данные не теряются, не дублируются и не расходятся между памятью и БД.
3. **Безопасность:** сервер является источником истины; клиентские данные, события и повторные запросы проверяются на каждом критическом переходе.
4. **Работоспособность:** игровые системы и их интеграции корректно работают в реальной среде RAGE:MP.
5. **Производительность:** измеряемые CPU/tick latency, RAM/GC, SQL, сеть и CEF; оптимизация без нарушения поведения.
6. **Масштабируемость:** предсказуемая работа при одновременных действиях игроков и росте онлайна.
7. **Сопровождаемость:** воспроизводимые сборки, тесты, диагностика, документация, rollback и понятный процесс релизов.

GTA5RP — целевой ориентир качества, а не источник недоступных нам внутренних цифр. Не заявлять равенство по онлайну, производительности или стабильности без сопоставимых измерений.

## 2. Обязательные принципы работы

- Работать только в `RedAge-3.0/` и в согласованной рабочей ветке. Не менять `main` напрямую и не отправлять изменения в upstream `ragemp-pro/redage_v3`.
- Перед патчем изучить полный data flow: входные события, валидацию, права, состояние, side effects, сохранение, фоновые worker'ы и потребителей результата.
- Не удалять, не отключать и не переписывать функциональность только потому, что она выглядит старой или подозрительной. Сначала определить назначение, зависимости и реальное использование.
- Не считать отсутствие найденного дефекта доказательством безопасности. Частичный просмотр всегда помечать как частичный.
- Не выдавать статический анализ, syntax check или локальную сборку за runtime-подтверждение.
- Для денежных и имущественных операций проектировать атомарность, идемпотентность, защиту от replay, восстановление после crash/restart и reconciliation частичных результатов.
- Не использовать production DB, production credentials, реальные платежи или публичный игровой сервер для тестов.
- Не придумывать результаты тестов, метрики производительности, максимальные значения или gameplay policy. Неизвестные решения помечать как вопросы владельцу.
- Для каждого изменения сохранять evidence: файл/метод/условие, причина, тест, команда, результат, ограничения.
- Любое новое решение или направление, утверждённое владельцем проекта в обсуждении, заносить сюда до продолжения соответствующей работы.
- Изменение считается завершённым только по Definition of Done (раздел 9), а не по факту коммита.

## 3. Как вести findings и приоритеты

Каждому finding присваивается стабильный ID (например, `MONEY-051`, `INV-019`, `PERF-002`) и фиксируются:

- severity и потенциальный ущерб;
- точный источник: файл, метод/handler, условие и путь данных;
- воспроизводимость и confidence (подтверждён статически / воспроизведён в тесте / подтверждён staging);
- предпосылки эксплуатации и границы доказанного;
- безопасное исправление и возможные побочные эффекты;
- позитивные, негативные, граничные, повторные, конкурентные и failure/restart тесты;
- текущий статус, блокер и доказательство закрытия.

Приоритет:
- **P0:** потеря/создание денег или активов, удалённое выполнение/компрометация, массовая порча данных, критический обход доступа.
- **P1:** серьёзная эксплуатация, неатомарные settlement-процессы, критические сбои сохранения/доступности.
- **P2:** существенная функциональная ошибка, ограниченный обход или деградация.
- **P3:** низкий риск, устойчивость/качество, техдолг.
- Performance-задачи получают отдельный PERF-ID и приоритет по измеренному влиянию.

Severity в `ISSUES.md` сохраняется в принятой там шкале; P0–P3 — рабочая очередность, а не замена severity. Не повышать серьёзность только на основании гипотезы. False positives и policy questions явно отделять от подтверждённых дефектов.

## 4. План аудита и развития — этапы

### Этап 0. Контроль исходников и безопасной работы

**Статус: в основном выполнен; остаются проверки прав и согласование истории веток.**

- [x] Изолированная рабочая ветка и каталог `RedAge-3.0/`.
- [x] Зафиксирован upstream snapshot и границы включённых/исключённых файлов (`SOURCE_SNAPSHOT.md`).
- [x] Локально удалены обнаруженные credential-bearing значения; секреты не должны попадать в Git.
- [x] Созданы Draft PR и рабочие audit-документы.
- [ ] Подтвердить права/разрешение на модификацию, использование UI и игровых ассетов, публикацию и хостинг.
- [ ] Сверить уникальные коммиты `main` и исходной ветки `arena/fab5bf55-gastronomy`; не менять PR base и не сливать до безопасного reconciliation.
- [ ] Повторить secret scan перед релизом; если найденные ранее значения были действующими — владелец выполняет ротацию у соответствующего провайдера.

### Этап 1. Архитектура, карта запуска и покрытие исходников

**Статус: частично выполнен.**

- [x] Составлена предварительная карта C# server, JS client, Svelte/CEF, SQL и конфигураций (`ARCHITECTURE.md`).
- [x] Проведена первичная инвентаризация RemoteEvent/ServerEvent/Command и отдельных progression call sites.
- [x] Создана матрица областей (`AUDIT_COVERAGE.md`).
- [ ] Завершить карту startup dependencies, DB tables/procedures, integrations и runtime lifecycle.
- [ ] Пофайлово завершить аудит всех remote handlers, commands и delegated callbacks: authentication, ownership, types/ranges, distance/dimension, rate limits, replay, exception paths.
- [ ] Завершить области экономики, платежей, inventory/containers, vehicles, property, jobs, factions, casino, quests/progression, auth/session, database, external integrations и background workers.
- [ ] Перепроверить все изменения по мере роста контекста и не дублировать уже закрытые review-проходы.

**Известный объём inventory, не показатель завершённости:** 498 упоминаний `[RemoteEvent]` в 137 файлах, 116 `[ServerEvent]` в 83 файлах, 382 `[Command]` в 38 файлах; это количество упоминаний, а не число проверенных обработчиков. В матрице на 2026-11-07 было 19 областей: 14 частично проверены, 2 проинвентаризированы, 2 не начаты, 1 заблокирована. Эти числа требуют обновления при изменении coverage.

### Этап 2. Воспроизводимые сборки и тестовая инфраструктура

**Статус: базовые проверки частично выполнены; полноценная среда заблокирована отсутствующими инструментами/runtime.**

1. Закрепить совместимые версии .NET SDK/runtime, Node/npm, NuGet/npm dependencies и lockfiles.
2. Поднять CI/build-agent с достаточной RAM и воспроизводимыми зависимостями.
3. Добиться чистой C# сборки, полного CEF production build и корректного release packaging.
4. Подготовить disposable MySQL/MariaDB test DB, импорт, backup/restore и least-privilege credentials.
5. Подготовить изолированный RAGE:MP staging с тестовыми аккаунтами и несколькими клиентами.
6. Добавить автоматические проверки, запускаемые повторно на каждый PR.
7. Создать единый отчёт тестирования: команда, версия инструмента, exit code, артефакт, дата, ограничения.

**Тестовые уровни (все обязательны по применимости):**

- Static analysis: поиск опасных паттернов, nullable/type issues, remote validation, SQL, secrets, dead code.
- Unit tests: чистые функции, расчёты, границы, state transitions, permissions.
- Integration tests: сервисы, repository, wallet/bank, inventory, DB transaction/save.
- Regression tests: конкретный исправленный дефект и соседние сценарии.
- Security/fuzz tests: malformed input, forged IDs, negative/zero/oversized values, unauthorized caller, replay.
- Concurrency tests: duplicate callbacks, simultaneous purchases/transfers, worker overlap, race/lock contention.
- Fault-injection tests: wallet/DB/item grant failures, exception, timeout, disconnect, shutdown, crash между шагами.
- E2E/staging tests: реальные RAGE:MP remotes, CEF bridge/UI, multi-client gameplay.
- Load/soak tests: онлайн-профиль, длительный прогон, spikes, memory/GC, DB saturation.

**Важно:** тестовый harness не должен подменять реальные интеграционные тесты. Mock/fake полезен для unit-тестов, но settlement и persistence должны дополнительно проверяться на настоящей disposable DB и staging.

### Этап 3. Исправление критических дефектов и защита игровых активов

**Статус: аудит продолжается; ряд source patches внесён, runtime validation открыта.**

Приоритетный порядок:
1. Денежные операции, донаты, casino, payouts, bank/business/faction transfers.
2. Инвентарь, контейнеры, предметы, оружие, склады и item grants.
3. Player-to-player trade, tent market, vehicle/house/business sale.
4. Собственность, транспорт, гаражи, бизнесы, фракции и работы.
5. Auth, sessions, Remote Events, commands, delegated callbacks.
6. Quests, BattlePass, rewards, progression.
7. DB lifecycle, queues, workers, external integrations.

Критичные invariants:
- debit не считается успешным без подтверждённого результата;
- item/vehicle/property не выдаётся до подтверждённого settlement или durable reservation;
- частичная операция должна быть атомарно отменена либо оставлена в durable pending state для retry/reconciliation;
- повторный callback не должен повторять payout/grant;
- runtime cache и DB должны сходиться после reconnect/restart;
- все идентификаторы и права проверяются на сервере непосредственно перед side effect;
- клиентская позиция/цена/количество/результат не становятся авторитетными без серверной проверки.

Не делать фиктивную атомарность из двух несвязанных `Wallet.Change` вызовов. Если общий DB transaction/ledger не реализуем без большой архитектурной переделки, сначала спроектировать durable settlement receipt/state machine и recovery worker.

### Этап 4. Производительность и оптимизация

**Статус: подготовительный аудит начат; baseline и профилирование ожидают среды.**

Перед оптимизацией собрать baseline в контролируемых условиях:
- server CPU, tick duration/latency, обработчики с p50/p95/p99;
- RAM, allocation rate, GC pauses, heap growth и длительный soak;
- SQL queries/sec, slow queries, query count per gameplay action, connection pool/waits/locks;
- network event rate и payload sizes;
- CEF JS/CSS bundle size (raw + compressed), startup/load timings, UI frame responsiveness;
- конкретный online/concurrency profile и hardware/software versions.

Затем:
1. Найти подтверждённые hotspots профайлером/метриками.
2. Сформулировать гипотезу и ожидаемый эффект.
3. Внести небольшое изменение.
4. Повторить тот же workload и сравнить baseline.
5. Запустить функциональные/security regression tests.
6. Откатить оптимизацию, если она ухудшает корректность или не даёт измеримого выигрыша.

Проверять отдельно CPU/game ticks, SQL/N+1 и write amplification, allocations/GC, locks/concurrency, timers/worker lifecycle, CEF bundle/runtime. Не выполнять массовый рефакторинг или micro-optimization без измерений.

### Этап 5. Реальная игровая проверка, релиз и сопровождение

- [ ] Smoke test: server start/stop, login, character create/load/save, inventory, movement, базовые gameplay flows.
- [ ] Multi-client сценарии: одновременные покупки, сделки, инвентарь, транспорт, фракции.
- [ ] Restart/disconnect/crash/failure tests на disposable DB.
- [ ] CEF UI/E2E: loading, navigation, forms, bridge events, localization, errors.
- [ ] Security retest и replay/abuse test.
- [ ] Load/soak test и сравнение с baseline.
- [ ] Backup/restore, rollback, incident/recovery drill.
- [ ] Release candidate sign-off по каждому quality gate.
- [ ] Только после отдельного одобрения владельца — merge/deploy.

---

## 5. Тестовая стратегия: конкретные сценарии

Для каждого критического потока тестировать минимум следующие классы случаев:

| Класс | Примеры | Что подтверждаем |
|---|---|---|
| Нормальный путь | валидная покупка/перевод/выдача | ожидаемый успешный результат |
| Отказ/недостаток | недостаток денег, нет прав, нет предмета | нет side effects |
| Границы | 0, отрицательное, максимум, overflow, пустые/null IDs | безопасный отказ/обработанное значение |
| Подмена | чужой ID, чужая сессия, неверная позиция/dimension | серверная авторизация |
| Replay | повтор одного события/receipt/confirm | exactly-once effect |
| Concurrency | два игрока/два callback одновременно | отсутствие double-spend/double-grant |
| Partial failure | отказ второй операции, item grant partial/full slots | rollback или durable pending recovery |
| Disconnect | выход между шагами | согласованное восстановление |
| Restart/crash | падение до/после DB commit | durable state и reconciliation |
| Persistence | save/load/reconnect | память и DB совпадают |
| Observability | exception/timeout/denied action | полезный лог без секретов и ложного success |

### Пример: покупка автомобиля

- Успешная покупка списывает деньги ровно один раз и назначает автомобиль ровно одному владельцу.
- Недостаточный баланс или отказ debit не меняет владельца.
- Отказ seller credit/DB holder update не приводит к ложному success.
- Повторное/параллельное подтверждение не создаёт второй автомобиль и не списывает повторно.
- Disconnect/crash на каждом шаге приводит к завершению либо восстановлению сделки.
- После reconnect/restart wallet, owner, garage и DB согласованы.

### Пример: inventory transfer

- Нельзя переместить предмет из чужого/закрытого/устаревшего контейнера.
- Количество > 0 и не превышает доступный stack.
- Full inventory/partial AddNewItem не приводит к потере исходного предмета.
- Повторный callback не дублирует предмет.
- Parent item/container ownership и access context перепроверяются на каждом mutation.
- DB failure/restart не теряет и не дублирует item SQL ID/count.

---

## 6. Definition of Done — когда finding действительно закрыт

Finding нельзя закрывать только потому, что код изменён.

- [ ] Исходная проблема описана точным source path и affected invariant.
- [ ] Есть тест, который воспроизводит старый дефект или доказывает новое ограничение.
- [ ] Исправление прошло code review: side effects, races, retries, exceptions, partial failures, disconnect/restart.
- [ ] Unit/regression tests проходят.
- [ ] Integration tests с disposable DB проходят, если затронута persistence/transaction.
- [ ] RAGE:MP staging tests проходят, если затронут runtime/remote/UI/gameplay.
- [ ] Build проходит на закреплённом toolchain.
- [ ] Нет новых ошибок/регрессий в соседних системах.
- [ ] Логи/результаты/команды и ограничения сохранены.
- [ ] `ISSUES.md`, subsystem review, `TEST_PLAN.md`, `BUILD_LOG.md`, `CHANGELOG.md`, `ROADMAP.md`, `AUDIT_COVERAGE.md` обновлены по применимости.
- [ ] PR diff проверен; rollback понятен; владелец одобрил закрытие/merge.

Если среда недоступна, статус остаётся «патч внесён — тестирование ожидает», а не «исправлено/проверено».

## 7. Текущий фактический статус

### Уже сделано (по имеющимся журналам и исходникам)

- Изолирован RedAge в `RedAge-3.0/`; зафиксирован upstream snapshot; создана рабочая ветка и Draft PR #4.
- Созданы architecture, audit coverage, issues, test plan, build log, roadmap, master checklist, handoff и специализированные subsystem reviews.
- Baseline: 167/167 JSON файлов валидны; 335/337 JS файлов проходят `node --check`; два неактивных файла требуют отдельного назначения/triage.
- Client webpack build успешно прошёл во временной изолированной копии (не воспроизводим без lockfile).
- Статически рассмотрены многочисленные economy, casino, inventory, vehicle, property, progression, remote и callback paths; полный аудит не завершён.
- Патчи MONEY-049 (Metro ticket), MONEY-050 (Driving School), MONEY-051 (Street Race stake debits) внесены в рабочую ветку; их runtime/build/failure tests ещё ожидают.
- PERF-002: CEF scripts явно задают production mode для build scripts и отключают Svelte hot reload в production; фактический полный build и UI smoke test ещё не прошли.
- Существуют специализированные findings/reviews; актуальные детали — в `ISSUES.md` и соответствующих файлах.

### Проверки, которые не следует считать пройденными

- Полная C# build/test: не выполнена — .NET SDK/MSBuild отсутствовали в предыдущей среде.
- Полная CEF production build: не выполнена — peer dependency конфликт, неполный asset snapshot и OOM в ограниченной среде; PERF-002 не доказывает успешную сборку.
- SQL import/backup/restore: не выполнены — отсутствовал MySQL/MariaDB.
- RAGE:MP runtime, multi-client, CEF in-game smoke: не выполнены — отсутствовала полноценная runtime/staging среда.
- Fault injection, restart/reconnect, нагрузка/soak и performance profiling: не выполнены.
- Статические finding'и не являются доказанными runtime exploit'ами, если reproduction явно не записан.

### Последние патчи — обязательные проверки

| ID | Изменение | Что ещё требуется |
|---|---|---|
| MONEY-049 | Metro: checked long price calculation; success only after successful wallet debit | negative/zero/normal/max input, Wallet false/exception, no log/event/dimension on failure, real ticket flow |
| MONEY-050 | Driving School: all six active license cases stop on failed debit before license/quest/faction/log effects | six success cases, debit false/exception, duplicate callback, shutdown/reconnect/save |
| MONEY-051 | Street Race: both stake debits required before race status/start; compensate first stake if second fails | first/second debit failures, refund failure, duplicate/concurrent accept/finish, payout durability, restart |
| MONEY-002 | Versioned in-process coordinator serializes Wallet.Change, detached worker snapshots and full Character.SaveSql; stale revisions are skipped, in-flight small changes coalesce to latest. Direct DB writers (offline AddMoney, auction refund, referral/tax, admin, merger) remain outside. | Migrate/audit all direct SQL writers; C# build; worker/save/wallet interleaving stress; DB partial-failure/reconnect; restart-loss test; durable outbox/backoff/dead-letter design |
| PERF-002 | CEF production defaults and hotReload disabled for prod | clean install/build for all scripts, output inspection, no source maps/HMR, CEF/RAGE UI smoke, size/time baseline |

**Незакрытые риски Street Race:** MONEY-051 stake compensation durability; MONEY-052 client-supplied waypoint validation; winner payout result and exactly-once durable settlement; `ClearData` abort/death payout result. Ни один из этих finding'ов не закрыт runtime-тестами.

**Известная сложная область:** MONEY-048 player trade/tent market. Не вносить поверхностный patch до проектирования settlement semantics, wallet API contract, item movement and durable recovery.

## 8. Текущие блокеры и необходимые ресурсы

1. Изолированный build-agent с подходящей версией .NET SDK и достаточной RAM. Текущий `NeptuneEvo.csproj` таргетирует `netcoreapp3.1`, а `NeptuneEvo.sln` включает gamemode и SDK projects, но не содержит test project; тестовый harness нужно добавить отдельно и согласовать с legacy target без необоснованного upgrade runtime.
2. Полный разрешённый набор CEF/client assets и закреплённые package lockfiles.
3. Disposable MySQL/MariaDB instance + возможность fault injection/backup/restore.
4. Полноценный RAGE:MP test server, корректные resource binaries/assets и несколько тестовых клиентов.
5. Сбор метрик/профилирование на контролируемом hardware.
6. Подтверждение владельцем прав и gameplay-policy решений, которые нельзя вывести из исходников.

До получения ресурсов продолжать source review, писать изолированные unit/static tests и готовить harness, но явно маркировать границы проверок.

## 9. Единый цикл работы для каждого изменения

1. Выбрать finding из `ISSUES.md` и проверить, не решён ли он уже.
2. Прочитать subsystem review и карту вызовов.
3. Зафиксировать expected invariant и reproducer/test case.
4. Проверить, что тест ловит старое поведение (где возможно).
5. Спроектировать исправление и failure/recovery semantics.
6. Внести минимальный патч в рабочую ветку.
7. Запустить тесты по уровням; сохранить команды и результаты.
8. Выполнить diff review и поиск побочных эффектов.
9. Обновить все применимые документы и этот мастер-план.
10. Обновить PR summary; оставить finding открытым, если обязательные тесты заблокированы.

## 10. Документы проекта и их назначение

- **Этот файл — `REDAGE_MASTER_PLAN.md`:** утверждённые цели, порядок работ, общий статус, правила, блокеры и Definition of Done.
- `MASTER_CHECKLIST.md`: операционный список конкретных задач и отметки выполнения.
- `ISSUES.md`: реестр findings с ID, severity, evidence и remediation.
- `AUDIT_COVERAGE.md`: какие подсистемы/поверхности просмотрены и что ещё не покрыто.
- `TEST_PLAN.md`: тестовые сценарии и статусы проверок.
- `BUILD_LOG.md`: точные toolchain, команды, build output и ограничения.
- `ROADMAP.md`: последовательность развития и зависимые этапы.
- `CHANGELOG.md`: хронология изменений.
- `SESSION_HANDOFF.md`: краткая передача текущего контекста между рабочими сессиями.
- `*_REVIEW.md`: детальные data-flow, findings и regression matrices конкретной подсистемы.

Если краткий документ устарел, исправить его, но не удалять evidence и историю результатов. Не поддерживать разные независимые версии плана: новые утверждённые решения сначала отражать здесь, затем синхронизировать операционные документы.

## 11. Новые решения и дополнения, утверждённые владельцем

### 2026-11-08 — тестирование становится непрерывной частью аудита

Владелец подтвердил:
- не ограничиваться исправлением кода/сборкой; создать отдельную тестовую инфраструктуру и скрипты;
- сочетать static analysis, unit, integration, regression, security/fuzz, concurrency, fault injection, E2E/staging и load/soak tests;
- не считать исправление подтверждённым без соответствующих проверок;
- не допускать некорректного удаления/отключения существующей функциональности;
- измерять производительность до и после оптимизаций;
- использовать GTA5RP как ориентир качества по стабильности, корректности, работоспособности и оптимизации;
- вести единый мастер-документ и добавлять в него новые согласованные планы/решения, чтобы не терять задачи.

Это решение обязательно для последующих этапов и Definition of Done.

---

## 12. Следующие конкретные действия

1. Проверить MONEY-002 source patch: build, concurrency and DB failure/retry tests; отдельно спроектировать durable outbox/recovery, поскольку текущая очередь остаётся in-memory.
2. Проверить MONEY-003 bank transfer patch: legacy-target build, parallel transfer/withdrawal tests, duplicate confirmation, MySQL save failure/retry and restart consistency; затем спроектировать DB transaction + durable idempotency ledger.
3. Продолжить текущий bounded audit без дублирования уже изученных review.
4. Закончить проектирование StreetRace settlement: winner/abort payout, durable receipt/recovery, concurrency; затем покрыть MONEY-051/052 regression tests.
5. Спроектировать безопасное решение MONEY-048 player trade/tent market.
6. Продолжить проверку unchecked Wallet.Change и stock/item settlement callers, затем оставшиеся Remote Events/delegated callbacks.
7. Обследовать реальную структуру .NET/CEF проектов и выбрать совместимые тестовые frameworks без необоснованного upgrade runtime.
8. Добавить первый runnable test harness: pure money arithmetic/validation tests и базовые JS/CEF checks; далее подключить DB integration.
9. Подготовить отдельную staging/test DB и RAGE:MP environment; не подключаться к production.
10. Снять performance baseline до любых существенных оптимизаций.
11. Обновлять этот документ после каждого утверждённого изменения плана и при существенном изменении статуса работ.

### 2026-11-08 — MONEY-003 bank transfer remediation

Applied a bounded source patch to `MoneySystem/Bank.cs`: account balance mutations are synchronized; transfers validate both accounts and both resulting balances before changing either cache; ATM confirmation state is consumed once and source ownership is revalidated; account saves retain dirty state on DB failure or concurrent mutation and reject values outside the current INT schema range. This is an in-memory consistency improvement only. It does not replace a MySQL transaction, durable idempotency key or crash-recovery ledger. Keep MONEY-003 open until legacy-target build, DB fault injection, concurrency and RAGE replay tests pass.

### 2026-11-08 — MONEY-003 follow-up: account creation and reads

Applied a bounded patch: `Bank.GetBalance` uses the shared account synchronization lock; `Bank.Create` rejects invalid holder/type/negative balance and checks conversion to the existing MySQL INT balance column before insertion. The cache is initialized from the validated DB value. Regression cases were added. This does not resolve the mutable `Bank.Data` reference escape hatch, bank deletion queue races, DB transactionality or crash recovery. Static-only; no .NET build, MySQL or RAGE tests.


### 2026-11-08 — MONEY-003 follow-up: direct bank balance mutation encapsulation

Added `Bank.SetBalance` and `Bank.ApplyBalanceAdjustment` so legacy property/business lifecycle paths mutate account balances under `AccountSync`, increment revision and mark persistence dirty. Routed business and house purchase initialization, auction property award initialization, and hourly business/house tax plus repossession reset through these APIs. The tax adjustment intentionally preserves the legacy temporary-negative-balance behavior used to trigger repossession; normal `Bank.Change` still rejects overdrafts. Regression cases are recorded in `BANK_TRANSFER_REVIEW.md` and `TEST_PLAN.md`.

Remaining: audit all mutable `Bank.Data` references/direct writes; verify purchase debit/ownership/bank initialization ordering; durable atomic settlement across property ownership, bank and faction/tax balances; legacy-target build; DB fault injection; concurrent transfer-vs-tax tests; RAGE staging. This is source-only remediation, not runtime-tested or crash-safe.


### 2026-11-08 — property purchase settlement ordering

Hardened direct business and house purchase flows: initialize the property bank balance through the synchronized API, require the buyer `Wallet.Change` debit to succeed, and only then perform ownership/success side effects. On debit rejection, attempt to restore the previous property-account balance and log failed compensation. Added explicit fault-injection cases. This is not a DB transaction; compensation/restart safety and auction award ordering remain open. No build or RAGE/MySQL test has run.


### 2026-11-08 — bank API caller hardening and property settlement ordering

- Every successful `Bank.Change` now marks the account dirty, including small personal-account mutations; dirty IDs are snapshotted under the account lock and the bank deletion worker uses a concurrent retry queue.
- Property/business tax uses synchronized checked bank adjustment; the business Mafia tax share is applied only after successful bank debit.
- House purchase debits before initializing the property bank and ownership; if bank initialization fails it attempts a buyer refund.
- House/business auction awards initialize their bank balances through the synchronized API before assigning ownership/committing auction state; admin bank grants require `Bank.Change` success.
- Targeted current-branch static assertions passed for these call paths. No C# compiler, MySQL/MariaDB or RAGE runtime is installed here, so no build/integration/staging test is claimed. Crash-safe multi-ledger transaction and public `Bank.Accounts` direct-access audit remain open.

### MONEY-039 — business ATM deposit interim patch (2026-11-08)\n\nThe business ATM deposit now checks the business-bank credit after wallet debit; on rejection it attempts a wallet refund, logs compensation failure critically, and returns before success log/message. This is an interim in-memory compensation only. BizIDs ownership/index revalidation, durable receipt/idempotency, crash recovery, C# build and RAGE/MySQL tests remain open. See BUSINESS_BANK_REVIEW.md.\n\n### MONEY-053 — ATM cash settlement (2026-11-08)

Static review found unchecked second legs in regular ATM cash deposit/withdrawal and house deposit. A bounded patch now checks both legs and attempts compensation if the second leg rejects; success effects/logging are delayed until both in-memory changes succeed. Business deposit remains MONEY-039. This is not a durable cross-wallet/bank transaction. Keep MONEY-053 open until C# build, compensation/fault injection, concurrent/replay and restart tests pass. See ATM_REVIEW.md and TEST_PLAN.md.

 
## 2026-11-08 — money settlement follow-up decisions

- **JOB-005:** revalidated all three AutoMechanic settlement paths. No source patch was applied because a local bool guard or call reorder cannot safely coordinate two wallets, business stock/revenue and vehicle repair/fuel state. Require durable one-shot service intent/receipt and restart reconciliation before applying gameplay effects. See MECHANIC_SERVICE_REVIEW.md.
- **StreetRace:** revalidated that both StreetRaceFinished and ClearData ignore winner Wallet.Change results; ClearData removes the only in-memory race context even if payout rejects. Do not add a naive return/retry. Implement one durable race settlement receipt shared by finish/abort, idempotent payout and cleanup only after terminal receipt. See STREET_RACE_REVIEW.md.
- New regression scenarios are in TEST_PLAN.md. These are static source findings; no C# build, RAGE runtime or MySQL failure injection was run.

## 2026-11-08 — MONEY-048 bounded input hardening

- Applied a narrow `Chars/Repository.cs` patch: tent purchases reject negative quantity, normalize the existing zero-to-one convention before stock/slot validation, require positive unit price, calculate total in `long` and reject totals outside the `Wallet.Change` Int32 contract; seller null/character state is checked before use.
- This closes the local negative-quantity/unchecked-multiplication input window only. Buyer debit and seller credit results remain unchecked; item grant/BattlePass/success are not durably coordinated. Player trade still moves items before two unchecked cash legs. Keep MONEY-048 open for durable idempotent settlement and full tests.
- Static assertions only; no C# build, RAGE staging or MySQL fault injection.

## 2026-11-08 — MONEY-037 bounded house-sale correction

- `HouseManager.acceptHouseSell` now validates the seller reference and active session/character before proceeding, rejects nonpositive pending price, and obtains `sellerCharacterData` from the seller rather than the buyer. This corrects money-log attribution and avoids null seller dereferences in the pre-settlement path.
- Buyer debit and seller credit results remain unchecked and house ownership still transfers regardless; no unsafe local compensation was added. MONEY-037 remains high/open pending durable idempotent settlement and build/RAGE/MySQL validation.

## 2026-11-08 — MONEY-035 cash stock result guards

- Applied to both faction and organization `inputStocks`: cash deposits require successful wallet debit before increasing stock; cash withdrawals require successful wallet credit before decreasing stock. Success logs are now after the result guard.
- This is an interim in-memory ordering/result patch only. It does not provide durable atomicity, replay protection, concurrency control or crash recovery. STOCK-001 item cargo transfer paths remain open. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — STOCK-001 exact quantity contract

- Revalidated organization stock withdrawals alongside faction and vehicle cargo. Item grants still ignore AddNewItem result.
- Confirmed AddNewItem may return a successful slot even when requested quantity was only partially inserted; `-1` is not the only failure signal. `Remove` returns void and suppresses exceptions, so the current callers cannot establish exact consumption.
- No unsafe item/cargo patch was applied. Require exact-count inventory APIs or durable intent/receipt with quantity-delta verification and compensation. MONEY-035 cash branches are separately guarded. STOCK-001 remains open; static-only.

## 2026-11-08 — STOCK-002 takeProd bounded hardening

- `Core/Businesses.cs`: `takeProd` now rejects nonpositive quantity and returns false when the requested product name is absent, rather than reporting a successful purchase with no stock match.
- Remaining: stock is still decremented before owner-bank credit; no rollback on bank failure; callers ignore customer debit and item/weapon grant results; business dirty-save remains open under MONEY-022. This is a narrow guard, not a settlement fix. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — MONEY-042 bounded vehicle sale settlement guard

- `Main.cs` BUY_CAR now validates seller reference and positive price, checks seller credit before changing vehicle holder, and attempts buyer refund if seller credit rejects; failed refund is critically logged.
- This is interim in-memory compensation only. Durable sale receipt, buyer debit/credit/holder transaction, asynchronous SaveHolder recovery and restart reconciliation remain open. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — MONEY-044 bounded acceptance preflight

- `acceptBuyBusiness` now rejects missing pending offer/seller, inactive seller character/session, nonpositive price and missing business ID before proceeding.
- Buyer/seller BizIDs and business Owner still mutate before unchecked buyer debit/seller credit. No unsafe local reorder/compensation was applied because owner/BizIDs persistence has no durable commit result. MONEY-044 remains high/open. Static-only.

## 2026-11-08 — MONEY-043 revalidation

- Current branch already contains an interim government business purchase guard: checked Bank.SetBalance, checked buyer Wallet.Change, attempted bank-balance restoration on debit rejection, and owner/stock/orders/BizIDs mutation only after debit success.
- Corrected stale review/issue wording. Durable receipt across bank/wallet/ownership writes and restart reconciliation remain open. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — MONEY-045 quota source correction

- `Core/Businesses.cs` `fillCar`: calculate final monetary cost with `long` after quantity normalization, reject out-of-range cost, remove incorrect comparison of liters against monetary FuelLeft, and reject price above allowance before stock/City Hall/vehicle mutations.
- Durable cross-entity settlement and VEH-009 active fuel-station intent remain open. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — VEH-006 / MONEY-013 government vehicle sale guard

- `Main.cs` `CAR_SELL_TOGOV` now revalidates current holder at confirmation, rejects nonpositive/unknown price and requires wallet payout success before logs/message/removal.
- Async vehicle DB deletion remains separate and not receipt-backed; payout/delete crash consistency, retry and exactly-once recovery remain open. Static-only; no build/RAGE/MySQL tests.

## 2026-11-08 — VEH-001 self-repair payment guard

- `VehicleManager.RepairCar` now returns success/failure; `RepairMyVeh` checks the $500 debit before repair and attempts refund if repair fails, with critical log on failed refund.
- This closes the wallet-rejection/free-repair window only. Server-owned dialog intent, location/mechanic policy and durable refund remain open. Static-only; no build/RAGE tests.


## 2026-11-08 — MONEY-002 worker lifecycle/range hardening

- `Database/Models/Money.cs`: made `Start()` idempotent per process with an `Interlocked` guard; moved the worker to `Task`-based async execution and replaced blocking sleep with `Task.Delay`.
- `AddMoneyUpdate` now rejects invalid UUID, negative balance and values above the existing signed DB INT limit before enqueue, preventing a poison retry batch caused by `Convert.ToInt32(long)` overflow.
- Retained the existing shared queue lock, atomic snapshot/clear, failed-batch requeue and newer-value-wins behavior.
- Remaining: in-memory-only durability, no DB outbox/transaction, retry backoff/dead-letter, and no .NET build, concurrency test or MySQL fault injection. MONEY-002 remains open.


### MONEY-036 — wallet range contract follow-up (2026-11-08)

The persisted cash column and generated model are signed INT while `CharacterData.Money` is long. `Wallet.Change` now uses long arithmetic and rejects values outside `0..Int32.MaxValue`; full `Character.SaveSql` validates the range before any save side effects or narrowing conversion. `Money.AddMoneyUpdate` already rejects invalid snapshots. This is a narrow compatibility patch, not a BIGINT migration. Keep MONEY-036 open for compiler, boundary, UI and DB round-trip tests. Also investigate stale absolute Money worker batches racing full character saves; that ordering issue belongs to MONEY-002 and is not solved by the range guard.


## 2026-11-08 — MONEY-002 detached batch hand-off

Added snapshot-time `ActiveMoneyWrites` markers under `QueueLock`. This closes the specific race where a small wallet mutation after worker detach but before SQL start advanced the version, was not enqueued, and caused the detached snapshot to be skipped without a replacement. The marker is now cleared by normal worker completion or failed-batch requeue. The existing per-UUID semaphore/revision coordinator with `ExecuteCharacterSave` remains partial. Direct DB cash writers outside the coordinator, process-crash loss, retry policy, C# build and MySQL concurrency/fault tests remain open.


## 2026-11-08 — MONEY-002 versioned wallet/save/worker coordination

Expanded the previous detached-batch fix: Wallet.Change now mutates balance and advances revision under a shared striped monitor; Character.Save.Repository.SaveSql captures its money snapshot under that same monitor and serializes its SQL write through a per-stripe semaphore. Worker snapshots carry revisions, are marked in-flight at detach time, and are skipped/retried only while their version remains current. Small wallet changes during pending/detached worker or full-save writes are coalesced as the latest snapshot without making every small mutation an unconditional DB write.

Still open: direct cash SQL writers outside this coordinator (including offline rewards/auction refund/admin/merger paths), durable outbox and process-crash recovery, retry backoff/dead-letter, C# build, multithreaded and MySQL fault-injection tests. See ECONOMY_REVIEW.md and TEST_PLAN.md.


### MONEY-002 — retry hand-off race fix (2026-11-08)

`MoneyUpdate` previously removed `ActiveMoneyWrites` in `finally` even on SQL exception, before `Worker` requeued the failed batch. A small wallet mutation in that interval could miss queue registration. The code now keeps the marker on failed SQL and lets `RequeueMoney` atomically requeue the current version and clear the marker; successful/superseded rows release it after semaphore release. Static verification only; deterministic concurrency/DB fault tests remain mandatory. Direct SQL money writers are still not serialized by the shared protocol and must be migrated only after online/offline semantics are established.

### 2026-11-08 — MONEY-002 offline admin grant acknowledgement

Applied a bounded ordering fix in Core/Admin.cs: OffGiveMoney now awaits the DB update, checks for exactly one affected character row, and only then emits money/admin logs and success notification. A failed or zero-row update no longer produces a false success acknowledgement.

This is not a full money-writer migration. The read-then-absolute-write remains vulnerable to concurrent offline grants and races with online wallet persistence; there is no durable receipt/idempotency or crash recovery. Static source patch only; C# build and DB fault-injection remain pending. Regression cases added to TEST_PLAN.md; see ECONOMY_REVIEW.md.
