## 2026-11-08 — LinqToDB 3.3.0 transaction API reconnaissance

- Verified against the pinned `linq2db.MySql` 3.3.0 source that `ServerBD` inherits `DataConnection` and exposes async begin/commit/rollback transaction methods. The 3.3.0 `BeginTransactionAsync` behavior disposes/rolls back an already attached transaction before starting another; coordinator must own one transaction per context.
- This is API-level confirmation only. MariaDB InnoDB engine, schema constraints, commit durability, affected-row semantics and runtime rollback still require disposable-DB validation. No source code or DB schema changed.

## 2026-11-08 — MONEY-002 durability boundary and offline-writer test plan

- Reconciled `MONEY-002` against the current source and issue register: queue synchronization/retry, revision-aware worker/full-save coordination and hand-off interleaving fixes are already present; build, concurrency and MySQL fault-injection validation remain pending.
- Documented why a background outbox written after the in-memory `Wallet.Change` cannot guarantee crash durability; the transaction boundary must move to the original logical cash mutation and all legacy writers must be migrated together.
- Expanded `TEST_PLAN.md` with offline direct-writer races, login/full-save overlap, receipt idempotency, InnoDB/rollback checks and mixed-version migration tests.
- No source code changed in this step; no build or runtime result is claimed. See `ECONOMY_REVIEW.md` and `TEST_PLAN.md`.

## 2026-11-08 — Phone auction settlement hardening (source patch)

- Patched `Players/Phone/Auction/Repository.cs`: reject nonpositive and expired/ended bids; use `long` fee arithmetic to prevent `int.MaxValue` wraparound from turning a debit into a credit.
- Serialize `OnBet` and `End` per auction object; `End` rechecks the ended flag under the same lock.
- Skip the no-bid UUID-zero refund sentinel; make `ReturnMoney` null-safe so the existing offline DB fallback can execute.
- Updated MONEY-023/024/038 status, review, checklist and regression plan. These are source patches only: no .NET build, RAGE runtime, MySQL fault injection or concurrency test has been run. Offline payout idempotency and maximum-bid policy remain open.

## 2026-11-08 — INV-019 weapon/key-ring parent ownership

- Traced weapon and CarKey subcontainer open paths, session location storage, generic inventory move/stack/use remotes and SetItemData cleanup.
- Registered INV-019: the mutable `other` location is not rebound to current parent item existence/ownership; former-holder access after parent transfer/removal is a staging hypothesis, not a reproduced theft.
- Added WEAPON_KEYRING_SUBCONTAINER_REVIEW.md and regression matrix; updated issue register, inventory review, master checklist, test plan, coverage, index, roadmap and handoff.
- Static-only; no gameplay patch, build, RAGE/MySQL runtime or exploit reproduction.

# Журнал работ

## 2026-11-08 — Аудит продажи автомобиля между игроками

- Внесён `MONEY-042`: BUY_CAR проверяет списание покупателя, но игнорирует результат начисления продавцу; после этого меняет владельца автомобиля и сообщает успех. `Vehicle.SaveHolder` выполняет async DB update без подтверждения/receipt/retry. Добавлены failure/restart/replay tests. Статический анализ; runtime не запускался. См. `VEHICLE_PLAYER_SALE_REVIEW.md`.

## 2026-11-08 — Аудит налога и изъятия бизнеса

- Внесены `MONEY-040/041`: обычное hourly tax списание с бизнес-счёта не помечает bank account dirty; repossession игнорирует online Wallet.Change result, а offline payout запускается асинхронно без подтверждения перед очисткой владельца. Добавлены persistence/fault-injection тесты. Статический анализ; runtime не запускался. См. `BUSINESS_TAX_REVIEW.md`.

## 2026-11-08 — Аудит депозитов на бизнес-счёт через ATM

- Внесён `MONEY-039`: `atmVal` для бизнес-счёта сначала списывает деньги игрока, затем игнорирует результат `Bank.Change` и всё равно логирует/сообщает успех. Добавлены требования к атомарному transfer, refund/receipt и replay tests. Статический анализ; runtime fault injection не выполнялся. См. `BUSINESS_BANK_REVIEW.md`.

## 2026-11-08 — Аудит розничных покупок в бизнесах

- Прослежен `BusinessManager.takeProd` и основные 24/7/weapon-shop/service callers. Внесён `STOCK-002`: stock уменьшается до подтверждения owner-bank credit, отсутствующий product может вернуть success, а callers игнорируют customer Wallet.Change и item/weapon grant results. `MONEY-022` расширен на отсутствие dirty-save для retail stock changes. Только static; build/RAGE/DB fault injection не выполнялись. См. `BUSINESS_RETAIL_REVIEW.md`.

## 2026-11-08 — Расширение аудита продажи бизнеса

- Расширен `MONEY-026`: `OnSellConfirm` не проверяет результат `Wallet.Change` и очищает владельца бизнеса даже при неуспешном начислении продавцу. Добавлены fault-injection/regression требования. Статический анализ; runtime не запускался.


## 2026-11-07 — Старт изучения и baseline тестов

- Изолирован RedAge 3.0 snapshot из `ragemp-pro/redage_v3`, commit `23730b8cd464f86c47eaae6f80d182cd651092b2`.
- Подготовлены план работ, карта архитектуры, первоначальный аудит, список наблюдений, план тестов и журнал сборок в `docs/`.
- JSON static check: 167/167 успешно.
- JS syntax check: 335/337; две ошибки в файлах, которые не подключаются известными entry points; не менял без выяснения назначения.
- Client webpack production build прошёл в изолированной временной копии с Node 22 и legacy OpenSSL provider.
- CEF install выявил peer conflict webpack 5/cache-loader 4; временный dependency audit сообщил 49 advisories (5 critical, 21 high, 22 moderate, 1 low) без upstream lockfile.
- CEF production build на полном временном asset tree завершился OOM/exit 137 из-за лимита памяти среды; исходный snapshot не менялся.
- SQL import, C# build и RAGE:MP smoke test заблокированы отсутствием соответствующих runtime/DB/SDK.
- Заполненные поля БД в локальном `settings/mainDB.json` заменены заглушками; также очищена закомментированная строка с website DB credentials из `Main.cs`. Владелец должен сменить upstream credentials, если они ещё действуют.
- Добавлен `meta.xml` и зафиксирован частичный startup path от RAGE:MP resource до C# Main/DB/module initialization; TLS настроек БД требует проверки.
- Зафиксированы риски: DB TLS отключён в connection strings, startup пробует менять global `max_connections`, SQL command text может попадать в debug/error logs.
- Дополнена карта зависимостей и внешних API/CDN/payment/radio endpoints. Обнаружен Debug-only DLL path в `meta.xml` и SQLite package version mismatch между связанными проектами.
- Проведён первый auth review: unsalted SHA-256 по ASCII bytes, неполностью подтверждённые rate/length limits; queue использует обычный `List` между server handlers и background thread. Добавлен осторожный migration/testing plan, код не менялся.
- Созданы `DEPENDENCIES.md`, `EXTERNAL_INTEGRATIONS.md`, `SECURITY_REVIEW.md` и `INDEX.md`; в roadmap/test plan зафиксированы следующие приоритеты.
- Первый статический economy/payment review: `GiftDonate` списывает до безопасного зачисления; deferred money dictionaries имеют гонку и теряют failed batches; generic bank confirmation callback повторно применим к неочищенному session state; ATM handlers не проверяют server-side proximity/active-ATM state; `BuySet` способен частично выдавать набор без списания или завершиться после debit без полного grant; payment polling не идемпотентен и использует volatile/thread-shared DonatePack intents. Занесены `MONEY-001..005` и `PAY-001..003`, созданы `ECONOMY_REVIEW.md`/`PAYMENTS_REVIEW.md`, добавлены targeted staging tests. Создана `AUDIT_COVERAGE.md`, чтобы отслеживать полный охват подсистем и не выдавать частичный review за завершённый. Production logic не менялась.
- На этапе исходного baseline production gameplay/code изменений не делалось.

## 2026-11-07 — Продолжение: inventory remote/persistence review

- Проверены inventory move/stack/use/drop/note client→server paths, client-only `isMove` policies, foreign-tent read-only path и `Database.Models.Items` worker.
- Подтверждены stack duplication через отрицательный count, обход read-only чужой палатки прямыми remote calls и неавторизованный `NoteCreate` item-ID path.
- В `Chars/Repository.cs` внесены локальные server-side guards для count<=0, count>source, empty source, same-slot и чужой палатки в проверенных move/use/drop/editor/stack paths; full stack move очищает source SQL row. Paid tent purchase flow сохранён. Mitigations не закрыты: .NET SDK/RAGE runtime отсутствуют, build/staging regression tests ещё не выполнены.
- Создан `INVENTORY_REVIEW.md`, заведены `INV-001..006`; матрица `AUDIT_COVERAGE.md` обновлена. Остальные inventory trade/storage/weapon/clothes/shop paths остаются частично или не проверены.
- Установлен Tree-sitter C# во временный cache venv без изменений dependency manifests. Полный syntax tree parse дал 5 error flags; отдельно проверенные snippets распарсились без syntax-tree errors. Tree-sitter не является C# compiler; findings flags требуют compiler triage.
- По просьбе владельца записана, но отложена до окончания аудита идея solo-mode с NPC-фракциями/симуляцией. В `FUTURE_FEATURES.md` отмечено, что синхронизированный ped не равен `ExtPlayer`, а API/runtime и capacity ещё надо подтвердить; fake online/accounts не планируются.


## 2026-11-07 — Roulette/case remote audit

- Прослежен data-flow `server.roullete.buy/open` через `RouletteGetWallet`, `RouletteUpdateWallet`, `Donate.GetPrice/UpdatePrice`, `RouletteCreate` и `RemoveIndex`; подтверждены negative-count RedBucks credit (`MONEY-006`) и case stack duplication plus BattlePass reward (`INV-007`), включая риск `int` overflow в покупке.
- Внесены локальные guards: buy count `1..100` (соответствует пределу selector UI), valid case IDs, positive price, checked total, negative wallet-amount rejection; open/create reject nonpositive counts; `RemoveIndex` ignores nonpositive quantity.
- Создан `ROULETTE_REVIEW.md`, обновлены issue register, test plan и coverage. Исправления не скомпилированы и не runtime-tested; staging verification остаётся обязательной. Другие casino/gambling paths не покрыты этим review.


## 2026-11-07 — Подготовка передачи в новый чат

- Добавлен `docs/SESSION_HANDOFF.md` с путём рабочей папки, upstream snapshot, состоянием последних inventory/roulette mitigations, тестовыми блокерами и безопасным порядком продолжения.
- Зафиксировано, что локальная RedAge-копия не содержит `.git`, а текущая Arena-ветка относится к Gastronomy; PR для RedAge требует отдельного checkout/сессии. Никакие изменения RedAge не переносились в Gastronomy.


## 2026-11-07 — Изолированное размещение в рабочей ветке

- Снимок RedAge перенесён из прежней отдельной рабочей папки в верхнеуровневый `RedAge-3.0/` внутри ветки `arena/fab5bf55-gastronomy`, чтобы его можно было сохранить через PR. Существующие файлы Gastronomy не заменялись; source `settings/mainDB.json` намеренно не копировался и остаётся исключён nested `.gitignore`.
- Для продолжения обновлён `SESSION_HANDOFF.md`; работа по RedAge впредь ведётся только внутри `RedAge-3.0/`.


## 2026-11-07 — NewCasino Roulette remote audit

- Прослежены seat/bet/cancel/clear remote events, `ContinueGame`, payout и общий disconnect path; создан `CASINO_REVIEW.md`.
- Подтверждён server-side race window логики отмены ставки после `table.Process=true`; добавлена phase guard (`CAS-001`), сохраняющая легальную отмену до старта. Статический snippet требует compile/RAGE staging tests.
- Подтверждён отдельный пятисекундный disconnect refund path после того, как сервер отправляет исход roulette в client event (`MONEY-007`). Код не менялся: policy может затрагивать компенсацию аварийного разрыва; необходимы согласование и staging design для exactly-once settlement.
- Зафиксирован client-only bet min/max path и потенциальный settlement overflow (`CAS-002`); серверную policy не менял до подтверждения intended limits.
- Покрытие обновлено; другие казино, включая Blackjack/Spin/Horses, остаются неаудированными.


## 2026-11-07 — Blackjack remote/state audit

- Проверены Blackjack join/bet/move/leave events, client/CEF controls, table state machine, payout and disconnect paths; создан `BLACKJACK_REVIEW.md`.
- Подтверждён unbounded table-index allocation before casino eligibility and duplicate seating window; добавлены table/seat bounds, finite-coordinate guards, global one-seat guard (`CAS-003`). Координаты всё ещё client-provided; arbitrary teleport зарегистрирован отдельно (`CAS-004`).
- Подтверждён repeat `setBet` debit + `Rate` overwrite; добавлены duplicate-bet guard и обязательная проверка `Wallet.Change` result (`CAS-006`).
- Задокументированы authoritative-move/rules bypass для split/double (`CAS-005`) и CEF-only table maximum/payout overflow (`CAS-007`); не менялись без подтверждения gameplay limits. Build/RAGE tests не выполнены.


## 2026-11-07 — Spin and Horses static review

- Созданы `SPIN_REVIEW.md`/`HORSES_REVIEW.md`; добавлены `CAS-008..016` в `ISSUES.md`.
- Зафиксированы Spin refund-after-reveal через remote leave, client-supplied slot teleport, mismatch 54 client slots/53 server states, zero/unbounded stake/debit/payout guards, off-by-one weight bucket и exact payout math: gross RTP 42.01992698%.
- Зафиксированы Horses winning horse в публичном race payload до 3-second disconnect refund deadline, remote betting без server-side session/location, zero/unbounded stake, unchecked wallet operations, generic casino marker teardown и scheduler/dictionary concurrency failure path. При равномерной лошади gross return = 50%.
- Gambling policy/RTP/refund and stake-limit issues не переписаны без подтверждения; build/RAGE/staging tests не запускались.


## 2026-11-07 — Lucky Wheel static review

- Создан `LUCKYWHEEL_REVIEW.md`; `CAS-017..019` внесены в `ISSUES.md`.
- Зафиксированы forged remote daily spin без server-side casino proximity и global 21-second lock; возможные prize-grant failures (partial costume, garage-cap vehicle return, unchecked wallet/item/weapon results) и непроверенный durable consume-once/recovery path.
- Рассчитаны nominal 20-slot shares: 20% clothes, 20% cash, 5% vehicle, 25% mystic, 20% weapon, 5% costume, 5% RedBucks; ожидаемая фиксированная часть — $6,452.10 и 3.725 RB per spin при текущих random ranges. Build/RAGE/DB tests не запускались.


## 2026-11-07 — Legacy dice and lottery static review

- Прослежен `/dice` от `CMD_dice`/`callDice` через `dialogCallback(DICE_PLAY)` к `AcceptDice` и `Wallet.Change`; создан `DICE_REVIEW.md`, добавлены CAS-020..023. Подтверждены split wallet settlement с игнорированием bool, acceptance-time validation gaps, self-target без opponent и tie recursion; self-play progression отмечен как policy-dependent, не как повторный reward exploit.
- Прослежен Lottery 24/7 shop callback, in-memory ticket/jackpot state, async `LotteryPlayers` insert и payday winner payout; создан `LOTTERY_REVIEW.md`, добавлены CAS-024..026. Зафиксированы stale `BizID` purchase boundary, non-atomic debit/ticket persistence и payout/reset без durable acknowledgment.
- Обновлены index, casino scope, coverage matrix, test plan, roadmap и session handoff. Изменялись только документы под `RedAge-3.0/docs`; исходники не менялись. C# build, MySQL failure-injection и RAGE runtime tests отсутствуют.


## 2026-11-07 — BattlePass claim and persistence review

- Прослежены `server.battlepass.take`, `takeAll`, mission reward flow, `GiveBonus`, `AddNewItemWarehouse`, BattlePass save/load и character save call sites.
- Добавлены CAS-027..028: claim marker живёт в памяти и сохраняется через character-save/disconnect, отдельно от prize grant; после persist grant до аварии/restart возможен replay claim. `GiveBonus` swallowing exceptions/no grant acknowledgements приводит к consumed claim при failed/partial reward.
- Создан `BATTLEPASS_REVIEW.md`; обновлены `ISSUES.md`, `AUDIT_COVERAGE.md`, index, test plan, roadmap и handoff. Исходники не менялись; C# build, DB fault injection, crash/reconnect и RAGE tests не выполнялись.


## 2026-11-07 — BattlePass producer trace and Sapper remote review

- Инвентаризированы `UpdateReward` calls: 209 non-comment source invocation lines; 72 call sites указывают на 55 IDs отсутствующих в зафиксированном Season4 catalog и потому no-op в текущем `UpdateReward`. Нужна policy/legacy confirmation; все 209 producers ещё не reviewed end-to-end.
- В Sapper прослежены remote stake/end flow и CEF RNG: отрицательная ставка приводит к RB credit (`MONEY-008`), а forged client outcome позволяет выбрать payout/refund (`MONEY-009`); оба critical. `SappeEnd` также начисляет task 3 до проверки active game (`PROG-001`). Создан `SAPPER_REVIEW.md` и расширены issue/coverage/test docs.
- Static source assertions for signed stake, client-controlled multiplier, progress-before-state-guard and `UpdateReward` catalog counts passed; `node --check` passed for the Sapper bridge and extracted CEF script; Markdown relative links and `git diff --check` passed. Исходники не менялись. Эксплойт, DB effects, C# compilation и RAGE runtime не запускались.


## 2026-11-07 — Quest remotes and objective progression review

- Частично прослежены generic `qMain` remotes, Granny Bear pickup, Defender Day Dada/Edward objectives and admin SkipQuest command. Добавлены `PROG-002..004` (task 97 direct-clear, client-forgeable Dada/Edward objective flags, wrong SkipQuest receiver), `BUG-001` (Valentine/Defender legacy handlers отсутствуют в generic dispatch; NPC runtime activation не подтверждена) и `INV-008` (server quest-item grant без server pickup/state checks).
- Создан `QUESTS_REVIEW.md`; обновлены issue register, coverage, index, test plan, roadmap и handoff. Никакие игровые исходники не менялись.
- Static source assertions, `node --check` для проверенного client script и docs link/whitespace checks выполнены после изменений. Live remotes, quest rewards/trade value, DB persistence, C# build и RAGE runtime не тестировались; все findings остаются открыты.


## 2026-11-07 — Wedding divorce settlement and quest call-graph follow-up

- Расширен static call-graph: generic qMain `perform/take` does not dispatch Valentine/Defender legacy actor transitions; their NPC spawn setup appears commented in this snapshot, so active runtime scope is marked for owner confirmation. PROG-003 was narrowed to client-forgeable completion booleans only; no downstream rewards/transitions are claimed.
- Создан `WEDDING_REVIEW.md`; `MONEY-010` documents spouse-disconnect after one-sided divorce prompt (debit precedes a null dereference/unlink); `WEDDING-001` tracks invalid target input exception path without claiming server crash/DoS. Coverage, `ECONOMY_REVIEW.md`, issue register, index, test plan, roadmap and handoff updated.
- Static quest/wedding source assertions, `node --check` for `npc_dialogs.js`, `main.js` and `wedding.js`, `git diff --check` and Markdown relative links passed; no source patches, DB/RAGE runtime or C# build performed.


## 2026-11-07 — Time rewards, TimeInfo persistence and achievement-array audit

- Traced minute reward thresholds against hourly `SaveServer`, disconnect/admin character saves, `TimeInfo` load/save and independent RB/warehouse writes. Added `MONEY-011` for the unprotected reward/checkpoint crash-consistency gap; exact replay requires fault-injection, and no remotely-triggered crash is claimed.
- Rechecked all active `Achievements[index]` sites. A valid short `Achiev` JSON list is not normalized on load despite create/fallback using 401 flags (`PROG-005`). DDL also allows nullable `characters.time`; JSON `null` bypasses deserialize catch and interrupts the outer minute pass (`PROG-006`). Both findings are conditional on row contents; production rows were not queried.
- Created `ONLINE_REWARDS_REVIEW.md`; updated issue register, economy/coverage/index/test plan. No source code changed.
- Static source assertions, relative Markdown-link validation (29 docs) and `git diff --check` passed. C# build, DB fault-injection and RAGE runtime tests were unavailable/not performed. Both findings remain open.


## 2026-11-07 — Taxi mileage remote and progression producer trace

- Traced client `MileageClass` → `server.vehicle.updateMileage` → taxi billing → BattlePass calls. Added `MONEY-012` for client-supplied unvalidated mileage reaching passenger-to-driver fare transfer, and `PROG-007` because the same request advances miles-based driver/passenger task counters before unchecked wallet mutations.
- Created `TAXI_MILEAGE_REVIEW.md`; linked findings into issue/coverage/economy/index/roadmap/test plan and handoff. No game source changed.
- Static review only; forged remote, fare settlement, C# build and RAGE/DB tests not run. Findings remain open pending test-ride reproduction and owner policy confirmation.


## 2026-11-07 — Audit stage snapshot and passport progression request

- Added a transparent coverage snapshot to `AUDIT_COVERAGE.md`: 19 domains (11 partial, 2 inventory-only, 5 not started, 1 blocked), plus raw remote/server-event/command inventories. Explicitly distinguished discovered handlers from fully checked handlers; no percent claimed.
- Traced passport `target` remote through request, timeout, accept and `UpdateReward(101)`. `target == player` is not rejected, so self-show can satisfy the active “show passport” task if RAGE entity marshalling behaves as normal; added conditional `PROG-008` and `DOCUMENTS_REVIEW.md`.
- Findings and staging scenarios added to issue, index, roadmap, test plan and handoff. No source code changed; remote reproduction/build/runtime tests remain unrun.


## 2026-11-07 — Vehicle self-repair callback and matrix update

- Traced `dialogCallback("RepairMyVeh", true)`: callback branch is active, the apparent repair-point opener is commented out, there is no server-owned pending intent/location recheck, and repair is performed before unchecked `$500` Wallet debit. Added policy-dependent `VEH-001` and `VEHICLE_REPAIR_REVIEW.md`; no free-repair claim under ordinary wallet success.
- One narrow vehicle-flow pass changes matrix status to 12 partial, 2 inventory-only, 4 not started, 1 blocked. Broader vehicle/garage scope remains unreviewed.
- Updated issue register, coverage, index, roadmap, test plan, BattlePass producer notes and handoff. Static source-order/catalog assertions, Node syntax, 40 relative Markdown links and `git diff --check` passed; no C# build, MySQL failure injection or RAGE reproduction.


## 2026-11-08 — GitHub write access, Draft PR and Main.cs settlement audit

- Confirmed GitHub write access through successful creation of `redage/audit-continuation` and documentation commits. Created Draft PR #4 to `main`; it must remain draft until the divergent `main`/arena history and included documentation delta are reconciled.
- Added `MASTER_CHECKLIST.md` with repository safety, audit, build/staging, remediation, test and release gates.
- Continued delegated `Main.cs`/fraction callback review. Added `MONEY-032`: mayor treasury withdrawal ignores failed personal-bank credit before debiting City Hall treasury. Added `MONEY-033`: ticket confirmation can continue payout after both debit paths fail and the ticket intent is not consumed from session state, allowing replay.
- Updated `MAIN_REMOTE_REVIEW.md`, `ISSUES.md`, `INDEX.md`, `AUDIT_COVERAGE.md`, `TEST_PLAN.md`, `ROADMAP.md` and `SESSION_HANDOFF.md` as applicable.
- Static source review only. No C# build, RAGE:MP runtime, disposable MySQL or exploit reproduction was performed; findings remain open.


## 2026-11-08 — inputCallback case inventory and delegated helper review

- Enumerated all 38 `case` occurrences (32 unique callback names) in `Main.ClientEvent_inputCallback` and traced selected delegated paths.
- Confirmed `player_medkit` and `player_heal` helpers repeat role/on-duty/price/proximity/trade checks; confirmed `mayor_put` aborts on failed bank debit; traced ticket issue-side policy checks while retaining MONEY-033 for confirmation settlement.
- Recorded remaining delegated callback paths and explicit review gaps in `MAIN_REMOTE_REVIEW.md`. No additional independent finding was asserted without sufficient source evidence. No source code changed; no C# build or RAGE/MySQL runtime tests performed.


## 2026-11-08 — MONEY-034 gang drug purchase arithmetic

- Traced `buy_drugs` from generic input callback into `Gangs.BuyDrugs`, configured default price and `Chars.Repository.AddNewItem` stack behavior.
- Registered MONEY-034: unchecked `int` multiplication can turn `int.MaxValue * 30` into `-30`, causing faction balance increase; unchecked capacity addition can also wrap for partially loaded vehicles. Exact item/DB corruption remains unverified.
- Updated issue register, remote review, index, coverage, master checklist, roadmap, test plan and handoff. Documentation-only change; no source patch/build/staging test.


## 2026-11-08 — Fraction stock/cargo remote audit

- Прослежены `inputCallback` → `Stocks.inputStocks` / `Stocks.fracgarage` для character↔fraction и vehicle↔fraction transfers. Внесён `STOCK-001`: faction stock totals меняются вокруг `Remove`, `AddNewItem` и `Wallet.Change` без проверки точного результата/компенсации; точная runtime failure/exploitability не заявляется.
- Создан `FRACTION_STOCK_REVIEW.md`; `ISSUES.md`, `MASTER_CHECKLIST.md`, `INDEX.md`, `AUDIT_COVERAGE.md` и `ROADMAP.md` обновлены. Нет source patch, C# build или RAGE/MySQL runtime tests.


## 2026-11-08 — faction stock settlement review

- Registered MONEY-035: faction cash stock is debited before Wallet.Change and its bool result is ignored; source confirms false-return paths.
- Registered STOCK-001: faction/vehicle stock is debited despite ignored AddNewItem result; AddNewItem can fail or partially insert, and vehicle medkit slot precheck is commented out.
- Verified generic inputCallback rejects put_stock/take_stock quantities below 1; negative-quantity exploit not asserted for this entry point.
- Updated issue register, remote review, master checklist, test plan, index, coverage, roadmap and handoff. Documentation only; no source changes or runtime tests.

- Follow-up parity check: `Organizations.Manager.inputStocks` repeats unchecked wallet and inventory settlement ordering; included under MONEY-035/STOCK-001 rather than duplicated as new IDs.


## 2026-11-08 — MONEY-036 shared wallet integer truncation

- Compared CharacterData.Money (long) with Wallet.Change arithmetic (int cast/add/store); registered MONEY-036 as a systemic economy defect. Out-of-Int32 balances can be rejected or overwritten with unrelated 32-bit values.
- Added long-boundary, persistence and call-site regression matrix; linked with MONEY-035 stock settlement ordering.
- No source code patch or runtime/build test; documentation only.


## 2026-11-08 — MONEY-037 player-to-player house sale

- Added `HOUSE_SALE_REVIEW.md`; registered MONEY-037 for unchecked buyer debit/seller credit followed by ownership transfer, plus incorrect seller UUID in money log.
- Updated master checklist, index, coverage, roadmap and test plan. Static source review only; no source patch, build or runtime tests.


## 2026-11-08 — MONEY-038 phone auction bid overflow

- Extended `AUCTION_REVIEW.md` with the client-controlled `int` bid-fee overflow path: `int.MaxValue` can wrap the calculated fee total negative and reverse the subsequent bank debit into a credit.
- Registered MONEY-038 in `ISSUES.md`, `MASTER_CHECKLIST.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md`, `INDEX.md` and `TEST_PLAN.md`; added numeric-boundary staging cases.
- Static finding only. No gameplay source patch, C# build, RAGE reproduction or DB fault-injection test was performed.


## 2026-11-08 — INV-011 Other-item auction settlement

- Extended `AUCTION_REVIEW.md`: `AuctionType.Other` moves an item into the auction location, but auction end has no Other-item award or return branch.
- Registered INV-011 in `ISSUES.md`, `MASTER_CHECKLIST.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md`, `INDEX.md` and `TEST_PLAN.md`; added item ownership, offline and restart regression cases.
- Static finding only. UI workflow, DB persistence and runtime recovery remain to be verified; no gameplay source patch or build was performed.


## 2026-11-08 — JOB-004 Trucker payout settlement

- Extended `BUSINESS_DELIVERY_REVIEW.md`: Trucker delivery ignores the boolean result of `Wallet.Change`, then removes the order, replenishes business stock and reports success. Registered JOB-004 and added wallet-failure/retry tests.
- Expanded `BUSINESS_ORDER_REVIEW.md` / MONEY-022: cancellation removes the order before confirming `Bank.Change` refund; a failed credit has no pending-refund retry path in the method.
- Updated `ISSUES.md`, `MASTER_CHECKLIST.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md`, `INDEX.md` and `TEST_PLAN.md`. Static-only; no runtime injection or source patch performed.

## 2026-11-08 — business ownership settlement review

- Добавлен `BUSINESS_OWNERSHIP_REVIEW.md`: `MONEY-043` — покупка государственного бизнеса продолжает смену владельца и сброс склада/заказов без проверки результата списания; `MONEY-044` — передача бизнеса между игроками меняет Owner/BizIDs до двух непроверенных wallet operations.
- Обновлены issue register, master checklist, test plan, coverage, roadmap, index и session handoff. Только статический анализ; C# build, RAGE runtime и MySQL fault injection не запускались. Исходники игры не менялись.

## 2026-11-08 — government fleet fuel quota review

- Добавлен `MONEY-045`: `fillCar` не отклоняет государственную заправку при недостаточном `FuelLeft`; условие только пропускает списание лимита, но заправка продолжается. Дополнительно quantity/currency сравниваются некорректно, а price рассчитывается до clamp. Создан `BUSINESS_FUEL_REVIEW.md`. Static-only; требуется подтвердить бюджетную семантику и выполнить RAGE/DB tests.

- Дополнен `BUSINESS_FUEL_REVIEW.md`: `VEH-009` — petrol remote не проверяет Type==1, расстояние, dimension и активную сессию заправки; BizID устанавливается при входе в любой бизнес и не сбрасывается в проверенном flow, поэтому возможен stale/non-fuel context. Связанные `STOCK-002` и `MONEY-045` не дублировались. Static-only; RAGE staging required.

## 2026-11-08 — AutoMechanic service settlement review

- Добавлен `JOB-005`: AutoMechanic repair/fuel acceptance игнорирует результаты списания клиента и начисления механику, но выполняет repair/fuel transfer, success logs и quest progress. `buyFuel` также увеличивает топливный резерв после непроверенного списания. Создан `MECHANIC_SERVICE_REVIEW.md` с failure/replay/restart matrix. Static-only; build/RAGE/DB tests не выполнялись.

- Расширен `BUSINESS_OWNERSHIP_REVIEW.md`: `BUG-002` — admin delete удаляет DB row до null-unsafe owner lookup, из-за чего offline/government owner может оставить runtime BizList/world ghost; `MONEY-047` — результат online owner refund игнорируется перед удалением бизнеса. Добавлены failure/restart tests. Static-only.


## 2026-11-08 — PET-001 pet-shop remote authorization

- Traced the pet-shop client event and server petshopBuy handler. It trusts any existing TempBizID, does not validate Type==14, active location/session or pet name, teleports before house eligibility checks and leaves the intent reusable after success.
- Added PET-001 and PETSHOP_REMOTE_REVIEW.md; expanded MONEY-045 with stale pre-clamp tfuel (stock quantity, price and applied fuel can diverge). Updated issue register, test plan, checklist, coverage, roadmap, index and handoff.
- Static-only. No source patch, build, RAGE/CEF runtime or DB fault injection was performed.


## 2026-11-08 — VEH-010 LS Customs tuning session

- Traced personal and organization tuning entry/exit. Organization exit eventType=1 does not reset CharacterData.TuningShop; the personal server.custom.buy remote trusts that value without active Type==12/location/dimension intent checks. Character position resolution also reads non--1 TuningShop.
- Registered VEH-010, created TUNING_REMOTE_REVIEW.md and expanded BUSINESS_RETAIL_REVIEW.md / STOCK-002 scope to include LS Customs stock reservation and customization settlement ordering.
- Updated issue register, checklist, test plan, coverage, roadmap, index and handoff. Static-only; no source patch/build/RAGE/DB tests.


## 2026-11-08 — VEH-011 signed mileage wrap

- Continued the taxi mileage trace. server.vehicle.updateMileage casts client-supplied signed int centimeters to uint without a positive/range check; negative values wrap into huge transient VehicleLocalData.Centimeters increments. Client meter also appears to accumulate centimeters/second on a 200ms callback without elapsed-time scaling (runtime cadence needs measurement).
- Registered VEH-011 separately from MONEY-012/PROG-007; expanded TAXI_MILEAGE_REVIEW, issue register, checklist, regression plan, coverage, index, roadmap and handoff. No source code changed; no runtime/build/DB test.


## 2026-11-08 — MONEY-051 Street race stake settlement

- `StreetRace.Accept` previously marked a race active and started it without checking either participant's wallet debit result. Patched it to require both stake debits; if the second fails, the first is refunded and the race is cancelled. Compensation failure is logged for reconciliation.
- Added MONEY-051 and a failure/concurrency regression matrix. Winner payout result, durable refund receipt and duplicate/concurrent finish semantics remain open; no build or RAGE tests have been run.

## 2026-11-08 — MONEY-052 Street race finish authorization

- `server.streetrace.finished` previously trusted a client-triggered finish event without checking that the race had started or that the caller was near the server-side finish position. Added active-race and 10m server-position checks to prevent pre-start payout and remote finish claims.
- Added MONEY-052 and regression scenarios. Finite/minimum-distance waypoint validation is now applied; map-boundary policy, payout result/durability, abort payout and concurrency remain open; no build or RAGE staging tests have been run.

## 2026-11-08 — PERF-002 CEF production build defaults

- CEF build scripts now explicitly set production mode through the already-installed `cross-env`; the dev script explicitly selects development.
- All three Svelte loaders now enable hot reload only outside production. This prevents clean-shell build invocations from silently defaulting to development mode/source maps/HMR.
- Added `CEF_BUILD_REVIEW.md` and PERF-002. No CEF build, bundle-size measurement or RAGE:MP smoke test has yet been run; CSS optimization and measured performance remain open.

## 2026-11-08 — MONEY-050 Driving school license settlement

- `Core.DrivingSchool.startDrivingCourse` previously granted each active license before the debit and ignored `Wallet.Change` results. Case 1 advanced quest state before payment; cases 3–5 credited the faction balance after an unchecked debit.
- Patched all six active license cases to abort when the wallet debit fails and defer license/quest/faction/log/success effects until after successful payment. Added `MONEY-050`, review and regression matrix. Static patch only; C# build and RAGE/MySQL failure tests pending.

## 2026-11-08 — MONEY-049 Metro ticket settlement

- `Events.Metro.OnBuyTicket` previously multiplied the client-supplied `Increase` by ticket price in `int`, then ignored `Wallet.Change` and proceeded to log success and move the player into the metro dimension.
- Patched calculation to widen to `long`, reject values outside positive `int` range, and abort all subsequent effects unless the wallet debit succeeds. Added MONEY-049 and boundary/failure regression cases. Static verification only; C# build and RAGE staging remain pending.

## 2026-11-08 — INV-012 vehicle trunk inventory context

- Traced vehicleSelected branch 3 → LoadOtherItemsData → generic inventory move/stack/use remotes. Initial 5m/trunk-open gate is not revalidated on each item mutation; the generic item methods rely on InventoryOtherLocationName and do not bind it to current vehicle/access/range/dimension/door state.
- Registered INV-012 with an explicit policy caveat: whether any nearby player may loot a physically open trunk requires gameplay-owner confirmation; stale session and missing per-operation range/context checks remain the concern. Created VEHICLE_TRUNK_ACCESS_REVIEW.md and updated inventory/issue/test/checklist/coverage/index/roadmap/handoff docs.
- Static-only; no source patch, C# build, RAGE runtime or DB fault injection.


## 2026-11-08 — VEH-012 vehicle trunk reservation cleanup

- Traced CEF closeOther → client bridge → inventory.otherclose → Repository.OtherClose. The server clears InventoryOtherLocationName but leaves SelectedVeh and BagInUse; only full ItemsClose and disconnect currently release the reservation.
- Registered VEH-012 and created VEHICLE_TRUNK_LIFECYCLE_REVIEW.md; linked it to INV-012 while keeping authorization and cleanup findings separate.
- Static-only; no source changes, C# build, RAGE runtime or DB tests.


## 2026-11-08 — INV-013/014 event loot remotes

- AirDrop: team membership check is not a spatial check; start-hack lacks player/crate position binding, lock completion trusts client health and open-inventory lacks caller proximity/dimension validation.
- MatWar: start/progress/open remotes lack active-war and proximity/session checks, share a generic IsAirDropHacking flag with AirDrop, and endWar leaves matwar_100 inventory/lock state until next startWar.
- Registered INV-013 and INV-014; created AIRDROP_REMOTE_REVIEW.md and MATWAR_REMOTE_REVIEW.md. Expanded INVENTORY_REVIEW with the LoadOtherItemsData container entry-point map.
- Static-only; no source changes, build, RAGE exploit reproduction or DB tests.


## 2026-11-08 — INV-015 faction stock session authorization

- Traced OnFracStock assignments across FIB, Sheriff, Army, City Hall and Police. No reset was found. The openWeaponStock remote checks only current faction ID and rank, not duty, stock-open state, location, dimension or session freshness.
- Registered INV-015 and created FRACTION_STOCK_SESSION_REVIEW.md; added staging matrix and linked the finding to the inventory container map.
- Static-only; no source changes, build, RAGE exploit reproduction or DB tests.

## 2026-11-08 — INV-016 organization stock exit lifecycle

- Traced OpenWeaponStock → LoadOtherItemsData → RemovePlayer. Exit clears InsideOrganizationID and moves the player outside but does not close/revoke the other inventory context; generic item remotes do not recheck organization interior state.
- Registered INV-016 and created ORGANIZATION_STOCK_SESSION_REVIEW.md; expanded inventory container map and staging matrix.
- Static-only; no source changes, build, RAGE exploit reproduction or DB tests.

## 2026-11-08 — INV-017 furniture safe stale context

- Traced objectSelected furniture-safe access and HouseManager.RemovePlayer. The exit path clears InsideHouseID and moves the player outside without closing/revoking the opened furniture inventory; generic item remotes do not revalidate the house/object/access context.
- Registered INV-017 and created FURNITURE_SAFE_SESSION_REVIEW.md; added regression matrix and inventory map reference.
- Static-only; no source changes, build, RAGE exploit reproduction or DB tests.

## 2026-11-08 — INV-018 HeliCrash key-clamp bypass

- Traced KeyClamp.SetKeyClamp → keyClamp.end → HeliCrash End. KeyClampData is installed before ArmyLockpick validation; the end remote trusts client value, and HeliCrash End can roll an unlock at zero without verifying a successful keydown reservation. Failed rolls leave a reusable session.
- Registered INV-018 and created HELICRASH_KEYCLAMP_REVIEW.md with direct-remote and concurrency regression matrix.
- Static-only; no source changes, build, RAGE exploit reproduction or DB tests.

- 2026-11-08: documented MONEY-048 — unchecked wallet settlement and item-before-payment ordering in player trades and tent-market purchases. Documentation only; no gameplay patch or runtime validation.


## 2026-11-08 — MONEY-002 money queue synchronization and retry (source patch)

- Added a shared lock for queue producers and worker snapshot/clear; switched per-key replacement to dictionary indexer.
- Failed absolute-value DB batches are requeued; retry preserves a newer value enqueued during the previous flush.
- The batch remains in-memory and is not crash-durable; there is no transaction/outbox, bounded backoff or dead-letter policy.
- Updated MONEY-002 evidence and regression plan. Static review only; no C# build, concurrency test or MySQL fault injection has run.


## 2026-11-08 — MONEY-003 bank transfer hardening (source patch)

- ATM transfer confirmation tuple is consumed before processing and source account is revalidated against the current character.
- Bank.Change now serializes balance mutation and checks overflow; notification failures are isolated from the applied mutation.
- Bank.Transfer validates positive amount/account identity/existence/funds/overflow and applies both in-memory balance legs under one lock; both accounts are marked dirty.
- Bank.Save snapshots revision and balance, retains dirty state on DB errors/concurrent mutation, and rejects out-of-range DB INT balances without clearing pending save.
- Updated bank transfer review, issue registry, master checklist and regression matrix. Static only; no .NET build, MySQL or RAGE tests.

## 2026-11-08 — MONEY-003 bank creation/read hardening (source patch)

- `Bank.GetBalance` now reads mutable account balance under the shared account lock.
- `Bank.Create` validates holder, signed TINYINT type range and non-negative balance; checked conversion prevents truncation beyond the current DB INT balance schema.
- Cache initialization uses the exact validated database balance.
- Regression cases added for boundary values, invalid input and concurrent reads/mutations.
- Static source checks only; no build, DB or RAGE runtime tests have run.

- Follow-up: synchronized GetBalance, holder lookup, account cache insert/removal and holder rename with the shared account lock. Retained checked account-creation validation against current TINYINT/INT schema. Bank.Get(int)/Get(string) now return snapshots under the account lock; direct public Bank.Accounts consumers still need audit.

- Follow-up: every Bank.Change balance mutation now marks the account dirty; dirty account IDs are snapshotted under AccountSync. Bank persistence worker uses ConcurrentQueue for account deletions and requeues failed delete batches after DB errors. Crash durability and write-volume profiling remain pending.


- MONEY-003: added synchronized `Bank.SetBalance` and `Bank.ApplyBalanceAdjustment`; routed business/house purchase initialization, auction property balance initialization, and hourly business/house tax/repossess balance changes through the shared account lock and dirty revision tracking. Static-only; build and runtime/fault-injection tests pending.

- Follow-up caller migration: hourly house/business tax uses synchronized ApplyBalanceAdjustment; house purchase debits before bank initialization and ownership; house/business auction awards initialize bank balances before ownership/state commit; admin bank grant requires Change success. Targeted current-branch scan found no active direct Balance writes in the reviewed caller files.

- MONEY-053 interim ATM settlement hardening: regular cash deposit/withdrawal and house deposit now check the second balance leg, attempt compensation on rejection, and defer success side effects/logs until both in-memory changes succeed. Durable transaction and runtime validation remain open.
\n## 2026-11-08 — MONEY-039 interim business ATM settlement patch\n\n- `MoneySystem/Bank.cs`: business ATM deposit now checks `Bank.Change` after the wallet debit; on rejection it attempts wallet compensation, critically logs a failed refund, notifies failure and returns before success log/message/UI refresh.\n- Updated `ISSUES.md`, `BUSINESS_BANK_REVIEW.md`, `ATM_REVIEW.md`, `TEST_PLAN.md`, master plan and checklist.\n- Static assertions passed for second-leg check, compensation call and success-log ordering. No C# build, MySQL fault injection or RAGE runtime test was available; durable settlement, replay and stale BizIDs validation remain open.\n
 
## 2026-11-08 — JOB-005 / StreetRace settlement revalidation

- Re-fetched current branch AutoMechanic and StreetRace sources. Confirmed JOB-005's three unchecked settlement paths remain; intentionally made no unsafe partial patch pending a durable multi-entity settlement API.
- Confirmed StreetRace normal finish and death/vehicle-exit abort ignore winner payout results; documented receipt/idempotency requirements and cleanup ordering.
- Updated mechanic and street-race reviews, master plan, checklist, test plan and handoff. Static-only; no build or runtime tests.

## 2026-11-08 — MONEY-048 tent input hardening

- `Chars/Repository.cs`: reject negative tent purchase quantity; normalize zero to one before stock/slot validation; require positive unit price; calculate total using `long` and reject values outside the `Wallet.Change` Int32 range; validate seller reference before dereference.
- Static assertions passed. This does not fix unchecked buyer/seller wallet results or the non-atomic item/cash settlement; `ConfirmTrade` remains unchanged. No C# build, RAGE or MySQL tests.

## 2026-11-08 — MONEY-037 house-sale preflight and audit attribution

- `HouseManager.cs`: validate seller reference/session/character and positive pending price before settlement; correct `sellerCharacterData` to read from seller, fixing buyer UUID duplication in money logs.
- Static assertions passed. Buyer debit/seller credit results remain unchecked and ownership transfer is still non-atomic. No C# build, RAGE or MySQL tests.

## 2026-11-08 — MONEY-035 faction/organization cash stock guards

- `Fractions/Manager.cs` and `Organizations/Manager.cs`: check `Wallet.Change` before cash stock mutation for both `put_stock` and `take_stock`; success logs follow the guard.
- Static assertions passed for all four cash paths. Durable transaction/receipt, replay/concurrency/restart behavior and STOCK-001 item paths remain open. No C# build, RAGE or MySQL tests.

## 2026-11-08 — STOCK-001 organization and partial-grant revalidation

- Expanded stock audit to `Organizations.Manager.inputStocks` and traced `AddNewItem`/`Remove` contracts. AddNewItem can return a slot after partial insertion; Remove returns void and catches failures internally. Existing item/cargo callers cannot verify exact quantity transfer.
- No source patch applied to item/cargo paths pending exact-count API and rollback/reconciliation design. MONEY-035 cash branch guards remain separate. No C# build or runtime tests.

## 2026-11-08 — STOCK-002 takeProd validation patch

- `Core/Businesses.cs`: reject `amount <= 0`, use bounded stock comparison after positive validation, and return false when no matching product is found.
- Owner-bank failure rollback, unchecked customer wallet debit, exact item/weapon grant, dirty-save and durable idempotent settlement remain open. Static assertions only; no C# build, RAGE or MySQL tests.

## 2026-11-08 — MONEY-042 BUY_CAR settlement guard

- `Main.cs`: validate seller/price; check seller wallet credit before vehicle holder mutation; attempt buyer refund on seller-credit rejection and critically log failed compensation.
- Static assertions passed. Durable idempotent receipt, async holder DB retry/reconciliation and all RAGE/MySQL tests remain pending.

## 2026-11-08 — MONEY-044 acceptance preflight guard

- `Core/Businesses.cs`: validate pending offer, seller reference/character/session, positive price and current business ID before transfer logic.
- Core settlement remains unsafe: owner/BizIDs mutate before unchecked buyer debit and seller credit. Durable transaction/receipt required. Static assertions only; no build/RAGE/MySQL tests.

## 2026-11-08 — MONEY-043 current-branch audit correction

- Revalidated `buyBusinessCommand`: checked bank initialization and buyer debit are already present; bank balance compensation is attempted on debit rejection; ownership effects follow successful debit.
- Updated stale MONEY-043 documentation. Durable cross-entity receipt and restart recovery remain open. No C# build, RAGE or MySQL tests.

## 2026-11-08 — MONEY-045 government fuel quota guard

- `Core/Businesses.cs`: normalize final refuel quantity, calculate bounded price in `long`, remove liters-vs-currency clamp and reject monetary cost above FuelLeft before stock/city/vehicle effects.
- Static assertions passed. Durable cross-entity receipt and VEH-009 station authorization remain open. No C# build, RAGE or MySQL tests.

## 2026-11-08 — VEH-006 / MONEY-013 government vehicle sale guard

- `Main.cs`: revalidate holder at confirmation; reject nonpositive sale price; check wallet payout before logging/reporting/removing the vehicle.
- Static assertions passed. Async DB delete/restart exactly-once settlement remains open; no C# build, RAGE or MySQL tests.

## 2026-11-08 — VEH-001 self-repair guard

- `Core/Vehicle.cs`: RepairCar now returns bool for successful repair vs invalid/missing state/exception.
- `Main.cs`: require successful $500 wallet debit before repair; attempt refund on repair failure and critically log failed compensation. Dialog-intent/location policy remains open. No C# build/RAGE tests.


## 2026-11-08 — MONEY-002 persistence worker follow-up

- `Database/Models/Money.cs`: prevent duplicate worker startup; use async task loop/nonblocking delay; reject invalid UUID and balances outside the current DB signed-INT range before enqueue.
- Existing lock/retry/newer-value-wins logic retained. Static source checks only; no C# build, concurrency or MySQL fault-injection tests. Durable queue/restart recovery remains open.


## 2026-11-08 — MONEY-036 wallet Int32 range guard

- Patched `Wallet.Change` to calculate the new balance in `long` and reject values outside the existing signed DB INT range before mutating character state.
- Patched `Character.Save.Repository.SaveSql` to reject invalid cash balance before related save side effects and `Convert.ToInt32`.
- Confirmed `CharacterData.Money` is `long`; generated `characters.money` model is `int?` (`int(11)`). No schema migration performed.
- Added boundary, UI, round-trip and concurrent worker/full-save tests. Static review only; no C# build, MySQL or RAGE tests.


- 2026-11-08: MONEY-036 follow-up in `Players/Phone/Auction/Repository.cs`: offline auction refund fallback now widens balance addition to `long`, rejects null/negative/out-of-range DB INT balances and narrows only after validation. This prevents overflow in that direct SQL write but does not fix async refund acknowledgement/idempotency. Static only; build/DB/RAGE tests pending.


- 2026-11-08: MONEY-002 worker hand-off hardening: mark detached UUID snapshots as in-flight at the same locked snapshot/clear boundary, so small wallet changes during the gap before SQL setup enqueue a newer revision rather than being lost when the old snapshot is skipped. Failed context/batch retry clears the marker and restores only a still-current version. Static only; direct SQL writers and durable outbox remain open.


## 2026-11-08 — MONEY-002 versioned writer ordering patch

- Added fixed 64-stripe async write gates and sync balance monitors to coordinate Wallet.Change, detached Database.Models.Money worker snapshots and full Character.Save.Repository.SaveSql writes.
- Added per-UUID revision counters; the worker checks detached revision immediately before SQL, skips stale snapshots, and retries only revisions that remain current.
- SaveSql captures the cash balance under the shared monitor, invalidates older queued snapshots, serializes its SQL update and restores the snapshot after failure unless a newer Wallet mutation replaced it.
- Wallet.Change advances revision on every mutation. Small changes are coalesced into the queue only when a batch/save is pending or in-flight, preserving the existing eager-write threshold otherwise.
- Detached batches are marked in-flight at snapshot time to close the gap before worker SQL setup.
- Remaining direct DB cash writers and durable outbox/restart recovery are not yet covered. Static checks only; no compiler, concurrency or DB tests.


## 2026-11-08 — MONEY-002 failed-write retry hand-off

- Fixed a race in `Database/Models/Money.MoneyUpdate`: on SQL failure, a detached row now retains its `ActiveMoneyWrites` marker until `Worker` registers the failed batch for retry. Successful and superseded rows still release the marker after the UUID semaphore is released.
- This prevents a small wallet mutation in the failure-to-requeue interval from being omitted from the queue. Added deterministic interleaving and multi-row failure test cases.
- Static source review only; no compiler, DB fault injection or concurrency stress test has run. Direct SQL money writers remain open.

## 2026-11-08 — MONEY-002 offline admin grant acknowledgement

- Core/Admin.OffGiveMoney now awaits the character cash UPDATE and requires exactly one affected row before writing money/admin logs or showing success.
- Failed/zero-row persistence is logged and reported to the administrator without success side effects.
- This does not remove the read-modify-write race, coordinate with the online money worker, or provide durable idempotency/restart recovery. Static patch only; no C# build or DB test.

- 2026-11-08: Повторно проверены `Wallet.Change`, `Character.Save.Repository.AddMoney`, referral cash reward и payday lottery payout. Зафиксированы lost-update/read-modify-write и online/offline cache handoff constraints; InnoDB для `characters` не подтверждён. Обновлён `ECONOMY_REVIEW.md`; source code/build/runtime tests не менялись/не запускались.


## 2026-11-08 — MONEY-002 direct cash writer inventory expansion

- Traced offline auction refund, offline referral-owner reward and admin offline grant paths in addition to AddMoney and lottery payout. Recorded read-modify-absolute-write lost-update risks and login/full-save handoff races; account merger is tracked as a separate migration/import writer.
- Expanded MONEY-002 regression cases for concurrent offline credits, login races, reward partial failures, retry/idempotency and merger interruption. No source code changed; storage engine for `characters` remains unverified.


## 2026-11-08 — MONEY-002 schema and referral settlement evidence

- Read the checked-in `database/main.sql`: `characters`, `money`, `accounts`, and `refferals` are declared InnoDB; `characters.money` is nullable signed INT; dump header says MariaDB 10.10.2. This is repository DDL evidence only, not confirmation of deployed schema.
- Traced referral settlement ordering: online reward legs and success marker are separate; offline branch writes success marker, account RB/VIP, and cash in separate operations. Added fault-injection/replay cases.
- No source code changed; no C# build, DB integration/fault-injection, concurrency, or RAGE staging test ran.
