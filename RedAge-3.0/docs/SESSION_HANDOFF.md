# Передача работы RedAge 3.0 в новый чат

Актуально на 2026-11-07. Эта заметка нужна для продолжения аудита из нового чата; актуальный исходник изменений — файлы проекта в этой папке.

## Рабочая папка и Git

- Каноническая RedAge-копия для продолжения: `/home/user/Gastronomy/RedAge-3.0` — отдельный верхнеуровневый каталог внутри рабочей ветки репозитория Gastronomy. Все RedAge-файлы из прежней отдельной папки скопированы сюда; прежняя рабочая папка сохранена.
- Upstream: `https://github.com/ragemp-pro/redage_v3`, snapshot commit `23730b8cd464f86c47eaae6f80d182cd651092b2`; подробности/границы snapshot: `SOURCE_SNAPSHOT.md`.
- У RedAge-подкаталога нет собственного `.git`; изменения отслеживаются родительским Git-репозиторием Gastronomy в `arena/fab5bf55-gastronomy`. Предполагаемое PR содержит только новые пути под `RedAge-3.0/`; корневые файлы и `Recipes/` не заменяются. Любые дальнейшие RedAge-изменения держать внутри этого каталога.
- Из исходной копии не переносился `settings/mainDB.json`; вложенный `.gitignore` продолжает исключать этот путь. Не добавлять реальные секреты.
- Не заменять и не удалять существующие Gastronomy файлы ради RedAge; перед каждым коммитом проверять, что diff содержит только `RedAge-3.0/`.

## Текущий фокус и последние изменения

Продолжается систематический статический аудит RedAge 3.0; feature work отложен.

Последние проходы — две roulette системы:

1. Donate/case remote handlers в `dotnet/resources/NeptuneEvo/Chars/Repository.cs` (`ROULETTE_REVIEW.md`):

- `MONEY-006`: отрицательное количество в `RouletteBuyCase` могло привести к начислению RedBucks; unchecked `Price * count` мог переполниться. Локально добавлены проверки case ID, count `1..100` (CEF selector поддерживает максимум 100), positive case price, `checked` multiplication и запрет отрицательной суммы в `RouletteGetWallet`.
- `INV-007`: отрицательное количество в `RouletteOpenCase` проходило проверку владения, пустой цикл `RouletteCreate` сопровождался вычитанием отрицательного count в `RemoveIndex`, увеличивая stack кейсов. Локально добавлены guards в `RouletteOpenCase`, `RouletteCreate` и общий `RemoveIndex`; нижняя граница case ID проверяется.
- Подробная data-flow и test matrix: `docs/ROULETTE_REVIEW.md`; записи также отражены в `ISSUES.md`, `INVENTORY_REVIEW.md`, `ECONOMY_REVIEW.md`, `TEST_PLAN.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md` и `CHANGELOG.md`.
- В `Chars/Repository.cs` также сохранены предыдущие локальные inventory mitigations для negative/same-slot stack move и read-only чужих палаток, описанные в `INVENTORY_REVIEW.md` (`INV-001..002`). Их runtime-проверка не выполнена.
- `NoteCreate` ownership/edit-intent/duplicate path (`INV-006`) выявлен, исправление не внесено.
- Solo-mode/NPC только отложен в `FUTURE_FEATURES.md`; не реализовывать до завершения аудита.

2. NewCasino Roulette (`CASINO_REVIEW.md`): `CAS-001` server-side phase guard внесён в `Roullete.cs`, не собран/runtime-tested. `CAS-002`: CEF содержит min/max ставок, но сервер допускает только нижнюю общую границу `20`; потенциальное payout overflow описано, intended limits требуют подтверждения. `MONEY-007`: сервер отправляет outcome в `START_GAME` и сохраняет пятисекундный disconnect refund grace; finding зарегистрирован, исправление не внесено, пока не согласована компенсация аварийного disconnect и exactly-once settlement.

## Выполненные проверки и ограничения

- Tree-sitter разобрал выбранные C# member snippets, включая roulette, inventory и NewCasino `OnDestroyLastBet`; это не компиляция. `node --check src_client/casino/roulette.js`, static phase-guard assertion, Markdown link/whitespace check прошли.
- Статические assertions guards и проверка Markdown links/whitespace прошли.
- Полный C# build и RAGE:MP staging smoke tests **не выполнялись**: в среде нет .NET SDK/MSBuild, MySQL test DB и RAGE runtime.
- CEF production build ранее ограничен отсутствующими assets/памятью; см. `TEST_PLAN.md`/`BUILD_LOG.md`.
- Ни один inventory/roulette/NewCasino patch не считать закрытым до compile и staging regression tests. Не менять баланс/донат/прогрессию без согласования; только test DB/test accounts.

## Следующие шаги

1. В новом чате восстановить/подтвердить рабочую папку RedAge и прочитать `INDEX.md`, `AUDIT_COVERAGE.md`, `ISSUES.md`, `TEST_PLAN.md`, `CASINO_REVIEW.md` и эту заметку.
2. PR создаётся из `arena/fab5bf55-gastronomy` в `main` репозитория Gastronomy и должен содержать только добавление изолированного каталога `RedAge-3.0/`. Не пушить изменения в upstream RedAge без отдельного checkout/ветки и разрешения владельца.
3. Продолжить статический review очередных remote event/command boundaries и подсистем; не заявлять полное покрытие без прохождения матрицы `AUDIT_COVERAGE.md`.
4. Подготовить поддерживаемый build-agent, staging/test DB и RAGE runtime; проверить roulette и inventory guards, в особенности положительные/валидные `RemoveIndex` call sites, zero-state при отвергнутых payloads, DB/cache convergence и failure/restart scenarios.
5. Позже исследовать остальные казино/gambling paths и consistency case grant (сбой `AddNewItem`/warehouse после списания) в `ROULETTE_REVIEW.md`.

## Нельзя забыть

- Не заменять и не удалять существующие файлы Gastronomy: изменения RedAge должны оставаться только под `RedAge-3.0/`.
- Не пушить upstream snapshot без отдельного целевого репозитория/ветки и проверки credential cleanup.
- Не включать реальные DB/payment/API credentials в файлы или сообщения.
- NPC/solo-mode остаётся отложенным; синхронизированный ped не является `ExtPlayer`, а поддерживаемые RAGE API/capacity не подтверждены.
