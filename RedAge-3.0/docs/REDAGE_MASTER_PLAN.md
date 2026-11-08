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
| MONEY-052 | StreetRace finish remote now requires active race and server-side 10m proximity to stored finish | pending-offer replay, outside-radius call, finite/min-distance waypoint validation, map bounds, concurrent finish, payout/recovery tests |\n| MONEY-002 | Money save queue now synchronizes producers/snapshot and retries failed absolute-value batches without overwriting newer queued values | C# build; concurrent producer tests; DB partial-failure/reconnect; restart-loss test; design durable outbox/backoff/dead-letter |
| PERF-002 | CEF production defaults and hotReload disabled for prod | clean install/build for all scripts, output inspection, no source maps/HMR, CEF/RAGE UI smoke, size/time baseline |

**Незакрытые риски Street Race:** MONEY-051 stake compensation durability; MONEY-052 client-supplied waypoint validation; winner payout result and exactly-once durable settlement; `ClearData` abort/death payout result. Ни один из этих finding'ов не закрыт runtime-тестами.

**Известная сложная область:** MONEY-048 player trade/tent market. Не вносить поверхностный patch до проектирования settlement semantics, wallet API contract, item movement and durable recovery.

## 8. Текущие блокеры и необходимые ресурсы

1. Изолированный build-agent с подходящей версией .NET SDK и достаточной RAM.
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

1. Проверить MONEY-002 source patch: build, concurrency and DB failure/retry tests; отдельно спроектировать durable outbox/recovery, поскольку текущая очередь остаётся in-memory.\n2. Продолжить текущий bounded audit без дублирования уже изученных review.
2. Закончить проектирование StreetRace settlement: winner/abort payout, durable receipt/recovery, concurrency; затем покрыть MONEY-051/052 regression tests.
3. Спроектировать безопасное решение MONEY-048 player trade/tent market.
4. Продолжить проверку unchecked `Wallet.Change` и stock/item settlement callers, затем оставшиеся Remote Events/delegated callbacks.
5. Обследовать реальную структуру .NET/CEF проектов и выбрать совместимые тестовые frameworks без необоснованного upgrade runtime.
6. Добавить первый runnable test harness: pure money arithmetic/validation tests и базовые JS/CEF checks; далее подключить DB integration.
7. Подготовить отдельную staging/test DB и RAGE:MP environment; не подключаться к production.
8. Снять performance baseline до любых существенных оптимизаций.
9. Обновлять этот документ после каждого утверждённого изменения плана и при существенном изменении статуса работ.
