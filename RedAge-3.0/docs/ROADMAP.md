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

- [ ] MONEY-032: исправить mayor treasury withdrawal — проверять результат bank credit до списания казначейства; транзакционная/идемпотентная модель и failure tests.
- [ ] MONEY-033: исправить ticket settlement — consume-once ticket intent, подтверждённое списание до выплат, durable idempotency и replay/concurrency/failure tests.

- [ ] MONEY-034: gang drug purchase integer overflow — bounded quantity, checked/long arithmetic, exact grant-before-debit and overflow regression tests.

- [ ] STOCK-001: fraction stock and vehicle cargo transfers — exact item/cash result, atomic/idempotent settlement, authorization and failure/restart tests; see `FRACTION_STOCK_REVIEW.md`.

- [ ] MONEY-035: make faction/organization cash withdrawals atomic; verify wallet credit before stock commit.
- [ ] MONEY-036: decide and enforce one money-width contract (Int32 cap or end-to-end BIGINT); update wallet arithmetic, generated DB model and all save workers consistently.
- [ ] STOCK-001: make faction/vehicle stock item grants exact and atomic; handle partial/full-slot failures.
- [ ] STOCK-002: replace business takeProd/customer debit/item grant sequence with idempotent atomic retail settlement; test owner-bank, wallet, item grant, missing-product and restart failures. See BUSINESS_RETAIL_REVIEW.md.
- [ ] MONEY-039: make ATM business-account deposit an atomic/idempotent player-debit/business-credit transfer with checked result, refund/retry and stale BizID/index protection. See BUSINESS_BANK_REVIEW.md.
- [ ] MONEY-040/041: persist hourly business tax debits and make online/offline repossession compensation durable/idempotent before ownership release. See BUSINESS_TAX_REVIEW.md.
- [ ] MONEY-042: make player-to-player vehicle sale debit/credit and holder persistence durable/idempotent; test failed seller credit and SaveHolder DB failure/restart. See VEHICLE_PLAYER_SALE_REVIEW.md.

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
- [x] Продолжен legacy gambling review: `/dice` и Lottery purchase/draw; добавлены `CAS-020..026` по неатомарному dice settlement, offer-time-only eligibility, self-target policy, recursive tie reroll, stale 24/7 `BizID`, async lottery ticket persistence и payout acknowledgment. См. `DICE_REVIEW.md` и `LOTTERY_REVIEW.md`; изменения исходников не вносились, C#/RAGE/DB tests не запускались.
- [x] Начат BattlePass static progression review; `CAS-027..028` фиксируют crash/replay gap между prize grant и persistence claimed IDs, а также consumed claim при fail/partial prize. Trace `UpdateReward` насчитал 209 non-comment source-вызовов; 72 относятся к 55 IDs вне Season4 catalog и потому не продвигают задачу. Найден `PROG-001` в Sapper завершении до проверки active game; обновлены producer/failure tests. Вся progression область остаётся частичной, без patch/build/runtime verification. См. `BATTLEPASS_REVIEW.md`, `SAPPER_REVIEW.md`.
- [x] Sapper minigame review выявил critical `MONEY-008..009`: signed negative stake создаёт RedBucks, client-side RNG/outcome выбирает server payout/refund; серверный result validation отсутствует. Никаких патчей не вносил; только disposable-account regression после design server-authoritative round/ledger. См. `SAPPER_REVIEW.md`.
- [x] Частично проверены generic quest remotes, Granny pickup и Dada/Edward objectives: `PROG-002..004`, `BUG-001` и `INV-008`. Dada/Edward objective flags client-forgeable; generic dialogue dispatcher не вызывает Valentine/Defender legacy `Perform/Take` methods (runtime activation не подтверждена); `SkipQuest` использует неверный receiver. Wedding review зарегистрировал `MONEY-010` divorce disconnect/debit gap и `WEDDING-001` null-target path. Только документы; actor handlers, build and runtime/failure tests остаются.
- [x] Прослежены minute/hour `TimeInfo` persistence and online reward writes, плюс все активные фиксированные `Achievements[index]` sites. Добавлены `MONEY-011` (условный crash/partial-save replay/loss gap), `PROG-005` (short valid JSON list не нормализуется) и `PROG-006` (nullable `TimeInfo` может прервать shared minute pass). См. `ONLINE_REWARDS_REVIEW.md`; prevalence и runtime effects ещё не подтверждены.
- [x] Частично прослежен taxi mileage remote до passenger billing и BattlePass IDs 2/59/159/95: `MONEY-012` (client-supplied distance может начислить fare за неподтверждённый пробег) и `PROG-007` (те же requests продвигают driver/passenger miles tasks до wallet result). Только static review; C#/RAGE/DB failure tests остаются. См. `TAXI_MILEAGE_REVIEW.md`. Дополнительно зарегистрирован `VEH-011`: отрицательный signed mileage delta unchecked-преобразованием превращается в огромный uint increment; persistent DB effect не подтверждён.
- [x] Проверен generic passport request→accept путь для task 101. `target==player` не запрещён и то же лицо может принять own request, вызывая progress; `PROG-008` открыт с оговоркой о проверке entity marshalling на staging. См. `DOCUMENTS_REVIEW.md`.
- [x] Vehicle/garage remote slices: `VEH-001` self-repair callback lacks pending intent (policy-dependent); `VEH-002` house parking accepts global vehicle IDs without household-holder authorization; `VEH-003` negative slot key can persist and fail spawn; `VEH-004..005` record aircraft action and entity-argument authorization gaps; `VEH-006`/`MONEY-013` record stale government-sale ownership and conditional payout/delete failure; `VEH-007..008` record vehicle-sync entity authorization and passenger radio policy gaps; one organization fleet slice is now partially reviewed (`MONEY-014..015`), with conditional sale-persistence and evacuation-debit findings; house resident ACL/save, purchase and sale slices are partially reviewed (`PROP-001..005`, `MONEY-016..019`, `MONEY-022..026`), with roommate privilege escalation, dirty-save, conditional purchase/transfer debit failures, furniture crafting ingredient-location mismatch (`INV-009`), sale payout replay, tax balance rollback, house repossession resurrection, policy-dependent ATM location/eligibility bypass (`MONEY-004`), replayable bank transfer confirmation (`MONEY-003`), business order dirty-save (`MONEY-022`), quantity-overflow bank credit (`MONEY-025`), unchecked government-sale payout and stale-BizID replay (`MONEY-026`), Trucker order reservation (`JOB-001`) and unchecked delivery payout settlement (`JOB-004`), SMS CEF injection and image URL sink (`SEC-007`, `SEC-010`), contact BattlePass bypass (`PROG-009`), conditional message-history flush loss (`PHONE-001`), phone preference/call validation and Tinder replay (`PHONE-002..004`), Tinder avatar CSS/resource candidate (`SEC-008`), News link CSS candidate (`SEC-009`), conditional News charge-without-ad/moderation replay (`MONEY-027..028`), non-atomic SIM ownership lifecycle (`PHONE-005`) and camera animation spoof (`PHONE-006`), auction first-bid and stale-end settlement (`MONEY-023..024`), property auction listing/offline-award persistence (`PROP-004..005`), and phone taxi/mechanic dispatch takeover/repeat-call issues (`JOB-002..003`) gaps. Static-only; exact impact needs RAGE marshalling and DB fault-injection. Broader vehicle/garage/organization/property audit remains open; see `VEHICLE_REPAIR_REVIEW.md`, `GARAGE_REVIEW.md`, `VEHICLE_ACTION_REVIEW.md`, `VEHICLE_SALE_REVIEW.md`, `VEHICLE_SYNC_REVIEW.md`, `ORG_VEHICLE_REVIEW.md`, `HOUSE_RESIDENT_REVIEW.md`, `PROPERTY_PURCHASE_REVIEW.md`, `PROPERTY_SALE_REVIEW.md`, `PROPERTY_TRANSFER_REVIEW.md`, `PROPERTY_TAX_REVIEW.md`, `ATM_REVIEW.md`, `BANK_TRANSFER_REVIEW.md`, `BUSINESS_ORDER_REVIEW.md`, `BUSINESS_SALE_REVIEW.md`, `BUSINESS_DELIVERY_REVIEW.md`, `PHONE_MESSAGES_REVIEW.md`, `PHONE_CALL_TINDER_REVIEW.md`, `PHONE_NEWS_REVIEW.md`, `PHONE_SIM_REVIEW.md`, `PHONE_DISPATCH_REVIEW.md`, `HOUSE_FURNITURE_REVIEW.md`, `AUCTION_REVIEW.md`.
- [ ] Завершить inventory trade/storage/weapon/clothes/shop permissions, исправить NoteCreate ownership/dedup, подтвердить mitigations полной сборкой и regression tests.
- [ ] Продолжить review удалённых событий/команд: авторизация, проверка аргументов, rate limits, доверие клиенту.
- [x] Следующий широкий проход `Main.cs`: задокументированы `MONEY-030` (условный EventCoins→RedBuck count/remove mismatch) и `MONEY-031` (прямое изменение government fuel caps без leader ACL). Статически; runtime требует RAGE/DB staging. `syncWaypoint` отдельно рассмотрен без утверждения о task bypass. См. `MAIN_REMOTE_REVIEW.md`.
- [x] Ещё один крупный remote pass: phone contacts/blacklist/call/recents/GPS/gallery/settings/property-car и часть business/dispatch routes cross-checked; в `Core/Selecting.cs` найден `PROG-010` (belt task progress без server transition), в `Core/WeaponRepository.cs` — `INV-010` (ammo return quantity до clip-cap). Оба статически обоснованы, runtime не подтверждён; далее RAGE staging. См. `SELECTING_REMOTE_REVIEW.md` и `WEAPON_REMOTE_REVIEW.md`.
- [x] Прослежен `Core/Carroom.cs`: `MONEY-029` — malformed client color can fail after purchase/test-drive charge and skip cleanup; test-drive model/showroom policy remains open. Только статический source trace; см. `CARROOM_REVIEW.md`.
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


- [ ] MONEY-037: player-to-player house sale settlement — checked buyer debit/seller credit, atomic ownership handoff, offer idempotency and correct audit identities; see `HOUSE_SALE_REVIEW.md`.
- [ ] MONEY-038: source patch now rejects nonpositive bids and uses widened `long` fee arithmetic; still needs C# build/RAGE boundary and bank-failure tests, plus owner decision on maximum bid; see `AUCTION_REVIEW.md`.
- [ ] INV-011: Other-item auction lifecycle — either disable unsupported listing type or implement durable winner grant/no-bid return with offline/restart recovery; see `AUCTION_REVIEW.md`.

- [ ] MONEY-043: make government business purchase debit and ownership/stock/order reset one durable idempotent operation; reject ownership commit on failed debit.
- [ ] MONEY-044: make player-to-player business transfer settle buyer debit, seller credit, Owner and both BizIDs atomically/idempotently; support compensation/reconciliation and offline/restart recovery. See `BUSINESS_OWNERSHIP_REVIEW.md`.

- [ ] MONEY-045: enforce government fleet fuel budget against checked monetary cost after quantity normalization; reject before any stock/funds/fuel mutation and reconcile fraction, City Hall and business ledgers. See BUSINESS_FUEL_REVIEW.md.

- [ ] VEH-009: require a short-lived server-side refuelling intent bound to a nearby Type==1 station and vehicle; revalidate and consume on every petrol remote. See BUSINESS_FUEL_REVIEW.md.

- [ ] PET-001: require Type==14 pet-shop intent, location/dimension and allowlisted pet model; prevent stale TempBizID teleport and replay. See PETSHOP_REMOTE_REVIEW.md.

- [ ] VEH-010: clear organization tuning context on exit and require an active Type==12 one-shot tuning intent for every personal purchase remote. See TUNING_REMOTE_REVIEW.md.

- [ ] JOB-005: make mechanic repair/fuel acceptance and mechanic fuel-reserve purchases exactly-once; confirm both wallet legs before repair/fuel mutation and add stale-offer/replay/restart tests. See MECHANIC_SERVICE_REVIEW.md.

- [ ] BUG-002/MONEY-047: make admin business deletion null-safe and idempotent across DB row, online/offline owner BizIDs/refund, runtime cache and world cleanup; test failures/restart. See BUSINESS_OWNERSHIP_REVIEW.md.

- [ ] INV-012: bind vehicle trunk inventory to exact vehicle/access session and revalidate distance, dimension, door, ownership/key and faction/org rank on every mutation; test stale context and replay. See VEHICLE_TRUNK_ACCESS_REVIEW.md.

- [ ] VEH-012: make vehicle trunk reservation release idempotent and session-owner-bound; clear BagInUse/SelectedVeh on OtherClose, context replacement, full close, disconnect and vehicle deletion; test competing openers and stale close. See VEHICLE_TRUNK_LIFECYCLE_REVIEW.md.

- [ ] INV-013: make AirDrop hacking and loot access server-authoritative and bind every remote to exact drop, active event, player, dimension and proximity; test client progress tampering, replay and cross-event calls. See AIRDROP_REMOTE_REVIEW.md.
- [ ] INV-014: require active MatWar generation and exact nearby crate for status/hack/open; server-time lock progress; remove/revoke stale matwar_100 loot on endWar. See MATWAR_REMOTE_REVIEW.md.

- [ ] INV-015: bind faction weapon-stock access to a short-lived player/fraction/stock intent; recheck duty, rank, stock-open state, position and dimension on open and every mutation; clear stale OnFracStock. See FRACTION_STOCK_SESSION_REVIEW.md.

- [ ] INV-016: revoke Organization inventory session on interior exit and revalidate current organization/dimension/stock state on every mutation; test stale and concurrent remotes. See ORGANIZATION_STOCK_SESSION_REVIEW.md.

- [ ] INV-017: revoke furniture safe inventory on house exit and bind it to exact house/object/access mode; revalidate range, dimension and ACL on every mutation. See FURNITURE_SAFE_SESSION_REVIEW.md.

- [ ] INV-018: make HeliCrash key-clamp progress server-authoritative; require exact active player/box reservation and lockpick; clear/revoke state on success, failure, exit and disconnect. See HELICRASH_KEYCLAMP_REVIEW.md.

- [ ] INV-019: bind weapon/key-ring subcontainer access to exact parent SqlId/type/current owner and revoke on parent transfer/drop/delete/replacement; validate every move/stack/use operation. See WEAPON_KEYRING_SUBCONTAINER_REVIEW.md.

- [ ] MONEY-050 — driving-school license grants: source patch applied; verify all six license types, failed wallet debit, quest/faction side effects, shutdown and persistence. See `DRIVING_SCHOOL_REVIEW.md`.
- [ ] MONEY-049 — Metro ticket price overflow and unchecked debit; source patch added, boundary/failure staging required. See `METRO_REVIEW.md`.
- [ ] MONEY-048 — player cash/item trade and tent-market purchase settlement; checked pricing, exact debit/credit, durable idempotency and compensation. See `PLAYER_TRADE_REVIEW.md`.
