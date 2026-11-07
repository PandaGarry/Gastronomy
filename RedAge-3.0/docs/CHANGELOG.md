# Журнал работ

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
