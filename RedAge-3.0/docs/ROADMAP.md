# План изучения и развития RedAge 3.0

Актуально на 2026-11-07. Статусы: `В работе`, `Ожидает`, `Заблокировано`, `Готово`. Пока — только изучение текущего состояния; игровые системы не меняем без отдельного согласования.

## Принципы

1. Сначала фиксируем исходный снимок и воспроизводимость; не меняем gameplay вслепую.
2. Работаем в тестовой копии и тестовой БД, не подключаемся к чужим production-сервисам.
3. Секреты — только в локальной конфигурации/секретах хостинга; в Git остаются шаблоны.
4. Каждое изменение сопровождаем проверкой, записью в `CHANGELOG.md` и обновлением документации.
5. Обновляем зависимости и runtime небольшими совместимыми шагами, а не «всё сразу».

## Этап 0 — Безопасная фиксация базы (`Готово`)

- [x] Выделена отдельная верхнеуровневая папка `RedAge-3.0` внутри изолированной рабочей ветки Gastronomy; файлы корневого проекта и `Recipes/` не изменяются.
- [x] Зафиксирован upstream commit и перечень включённых/исключённых файлов в `SOURCE_SNAPSHOT.md`.
- [x] Заполненные поля подключения БД и закомментированные website DB credentials в локальной копии заменены безопасными заглушками/комментарием; config игнорируется Git.
- [x] Удалены локальные Git-метаданные upstream, чтобы исключить случайный push туда и не хранить исходный credential-bearing blob.
- [x] Подготовлен первоначальный аудит.
- [ ] Владелец подтверждает границы разрешения: исходники, UI/игровые ассеты, правки, публикация/хостинг.

## Этап 1 — Инвентаризация и карта запуска (`В работе`)

- [x] Определены основные части: C# сервер, JS client, Svelte CEF, SQL и конфиги.
- [x] Составлена предварительная карта подсистем и конфигураций; см. `ARCHITECTURE.md`.
- [x] JSON baseline: 167/167 валидны; JS syntax baseline: 335/337, два неиспользуемых entry-point файла требуют разбора.
- [x] Найдена частичная последовательность: RAGE resource `meta.xml` → `NeptuneEvo.Main` constructor/`MySQL.Init()` → module initialization; детали runtime ordering ещё требуют smoke test.
- [x] Снять декларации .NET/NuGet и npm зависимостей; см. `DEPENDENCIES.md` (runtime compatibility и полный resolution ещё открыты).
- [x] Подсчитать SQL structures и перечислить внешние hostname references; см. `EXTERNAL_INTEGRATIONS.md` (call sites и владельцы endpoints ещё надо подтвердить).
- [ ] Составить полную карту SQL-таблиц/процедур, service integrations и startup dependencies.
- [ ] Получить полный авторизованный набор runtime/client assets, необходимых для полноценной сборки.

## Этап 2 — Воспроизводимая сборка и тестовая база (`В работе`)

- [ ] Зафиксировать целевые версии SDK/toolchain и lockfiles из доверенных registry.
- [x] Client JS webpack build прошёл в изолированной временной копии; см. `TEST_PLAN.md` и `BUILD_LOG.md`.
- [ ] Собрать C# backend — заблокировано отсутствием .NET SDK.
- [ ] Повторить CEF UI production build на build-agent с достаточной RAM; сейчас конфликт peer dependencies, audit advisories и OOM.
- [ ] Проверить импорт всех SQL-файлов в изолированную MySQL-совместимую тестовую БД.
- [ ] Поднять тестовый сервер без публичного объявления и без production-секретов.
- [ ] Добавить smoke tests для входа, создания персонажа, сохранения/загрузки, инвентаря и базовых команд.

## Этап 3 — Аудит безопасности и надёжности (`В работе`)

- [x] Начальный credential/config scan: локально убраны обнаруженные credentials; владельцу указана необходимость ротации, если upstream значения были активны.
- [x] Зафиксированы DB transport/logging/startup concerns в `ISSUES.md` (TLS disabled, global max_connections, SQL text logging).
- [x] Сделан первый статический разбор password flow; обнаружены legacy unsalted SHA-256 + ASCII conversion. См. `SECURITY_REVIEW.md`.
- [x] Выявлен shared queue list без синхронизации между remote handlers и background thread; записан в `ISSUES.md`.
- [x] Выполнен первый статический economy/payment review: RedBucks gift, deferred money persistence, bank transfer callback/replay, ATM remote state, DonatePack package grants и external payment receipt processing; findings `MONEY-001..006` и `PAY-001..003`, см. `ECONOMY_REVIEW.md` и `PAYMENTS_REVIEW.md`.
- [x] Создана `AUDIT_COVERAGE.md`: разграничивает просмотренные/непросмотренные подсистемы и критерии завершения полного аудита; большинство gameplay-модулей остаются не начаты.
- [x] Начат inventory remote/persistence review; findings `INV-001..007`, добавлены локальные mitigations для stack count/same slot и foreign-tent read-only paths. Статические snippets распарсились; отдельные roulette count guards также внесены; compile/staging tests заблокированы отсутствующими .NET/RAGE runtime.
- [x] Начат NewCasino Roulette static review: server-side phase guard для `DESTROY_LAST_BET` добавлен (`CAS-001`); обнаружены client-only bet min/max (`CAS-002`) и outcome-dependent пятисекундная disconnect refund policy (`MONEY-007`), код не менялся до согласования gameplay semantics. См. `CASINO_REVIEW.md`; build/staging ещё недоступны.
- [x] Начат Blackjack remote/state review: bounds/duplicate-seat и duplicate-bet guards внесены (`CAS-003`, `CAS-006`); arbitrary-coordinate teleport, illegal split/double/state moves и client-only bet max зарегистрированы (`CAS-004/005/007`). Денежные/gameplay policy issues оставлены без patch до согласования; см. `BLACKJACK_REVIEW.md`.
- [x] Начаты NewCasino Spin/Horses static reviews: `CAS-008..016` покрывают post-reveal refund windows, client-authoritative slot coordinates/bet limits, 54/53 slot cardinality mismatch, odds/RTP, horse session/authorization и scheduler settlement failure; вычислены Spin RTP ≈42.0199% и Horses gross return 50%, policies требуют подтверждения. См. `SPIN_REVIEW.md`, `HORSES_REVIEW.md`; build/staging tests не запускались.
- [x] Начат NewCasino LuckyWheel static review: зарегистрированы `CAS-017..019` по отсутствию server-side location claim, призовым grant failures/partial costume and garage branch, и недоказанной durable consume-once state; рассчитаны 20-slot reward odds и ожидаемый fixed cash/RB component. См. `LUCKYWHEEL_REVIEW.md`; runtime/DB tests не проводились.
- [ ] Завершить inventory trade/storage/weapon/clothes/shop permissions, исправить NoteCreate ownership/dedup, подтвердить mitigations полной сборкой и regression tests.
- [ ] Продолжить review удалённых событий/команд: авторизация, проверка аргументов, rate limits, доверие клиенту.
- [ ] Проверить SQL: параметризация, транзакции, пул соединений, таймауты, ошибки и повторные попытки.
- [ ] Завершить аудит прав админов/фракций, экономических операций, донат/платежей и журналов аудита.
- [ ] Проверить CORS/HTTP endpoints, TLS, файлы логов/дампов и безопасную конфигурацию на всём проекте.
- [ ] Составить полный список рисков с уровнями, ссылками на код и проверяемыми исправлениями.

## Этап 4 — Технический долг и совместимость (`Ожидает`)

- [ ] Измерить базовые latency, загрузку CPU/RAM, частоту/длительность DB-запросов и ошибки.
- [ ] Проверить поддержку .NET Core 3.1, сопоставить с RAGE:MP и выбрать безопасную целевую версию.
- [ ] Проверить npm/NuGet зависимости и построить план обновления с контрольными сборками.
- [ ] Разделить production/dev конфиги; сделать миграции БД версионируемыми и тестируемыми.
- [ ] Устранить подтверждённые проблемы производительности по измерениям, не по предположениям.

## Этап 5 — Игровые улучшения (`Ожидает завершения аудита`)

- [ ] После полного аудита согласовать приоритеты и критерии готовности для каждой системы.
- [ ] Отложенный backlog: solo-mode с живым городом/NPC-фракциями/экономической симуляцией — `FUTURE_FEATURES.md`; до завершения аудита не реализовывать.
- [ ] Реализовывать небольшими изолированными изменениями: тест → review → staging → выпуск.
- [ ] Не менять баланс, донат, прогрессию и правила сервера без отдельного решения владельца.

## Этап 6 — Staging и production (`Ожидает`)

- [ ] Выбрать хостинг, который поддерживает долгоживущий RAGE:MP процесс и нужные TCP/UDP-порты.
- [ ] Настроить отдельного системного пользователя, firewall, TLS где применимо, секреты и резервное копирование.
- [ ] Подготовить мониторинг, лог-ротацию, health checks, план отката и тест восстановления БД.
- [ ] Сначала staging, затем короткое окно релиза; production-ключи и реальные данные не передавать в чат.

## Блокеры

- Нет `dotnet` SDK в текущей рабочей среде: C# сборка пока не проверена.
- В текущем снимке намеренно отсутствуют серверные бинарники/runtime, собранные client packages и часть тяжёлых UI/game assets.
- Нет подтверждённой полной схемы запуска и сведений о предполагаемом production-хостинге.
