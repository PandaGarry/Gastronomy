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

Последние проходы — casino remote flows:

1. Donate/case remote handlers в `dotnet/resources/NeptuneEvo/Chars/Repository.cs` (`ROULETTE_REVIEW.md`):

- `MONEY-006`: отрицательное количество в `RouletteBuyCase` могло привести к начислению RedBucks; unchecked `Price * count` мог переполниться. Локально добавлены проверки case ID, count `1..100` (CEF selector поддерживает максимум 100), positive case price, `checked` multiplication и запрет отрицательной суммы в `RouletteGetWallet`.
- `INV-007`: отрицательное количество в `RouletteOpenCase` проходило проверку владения, пустой цикл `RouletteCreate` сопровождался вычитанием отрицательного count в `RemoveIndex`, увеличивая stack кейсов. Локально добавлены guards в `RouletteOpenCase`, `RouletteCreate` и общий `RemoveIndex`; нижняя граница case ID проверяется.
- Подробная data-flow и test matrix: `docs/ROULETTE_REVIEW.md`; записи также отражены в `ISSUES.md`, `INVENTORY_REVIEW.md`, `ECONOMY_REVIEW.md`, `TEST_PLAN.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md` и `CHANGELOG.md`.
- В `Chars/Repository.cs` также сохранены предыдущие локальные inventory mitigations для negative/same-slot stack move и read-only чужих палаток, описанные в `INVENTORY_REVIEW.md` (`INV-001..002`). Их runtime-проверка не выполнена.
- `NoteCreate` ownership/edit-intent/duplicate path (`INV-006`) выявлен, исправление не внесено.
- Solo-mode/NPC только отложен в `FUTURE_FEATURES.md`; не реализовывать до завершения аудита.

2. NewCasino Roulette (`CASINO_REVIEW.md`): `CAS-001` server-side phase guard внесён в `Roullete.cs`, не собран/runtime-tested. `CAS-002`: CEF содержит min/max ставок, но сервер допускает только нижнюю общую границу `20`; потенциальное payout overflow описано, intended limits требуют подтверждения. `MONEY-007`: сервер отправляет outcome в `START_GAME` и сохраняет пятисекундный disconnect refund grace; finding зарегистрирован, исправление не внесено, пока не согласована компенсация аварийного disconnect и exactly-once settlement.
3. Blackjack (`BLACKJACK_REVIEW.md`): `CAS-003` table/seat and duplicate-join guards, `CAS-006` duplicate-bet/debit guard внесены, но не собраны/runtime-tested. Открыты arbitrary-coordinate teleport (`CAS-004`), move/split/double server validation (`CAS-005`) и CEF-only bet maximum/payout overflow (`CAS-007`).
4. Spin (`SPIN_REVIEW.md`): `CAS-008` outcome revealed at ~600 ms while `LEAVE_SLOT` refunds for 2 seconds; `CAS-009` client coordinate teleport and 53/54 slot-count mismatch; `CAS-010` stake/debit/payout validation; `CAS-011` computed gross RTP ≈42.0199% and selection bucket bias. Нет patch/build/runtime test.
5. Horses (`HORSES_REVIEW.md`): `CAS-012` winner disclosed before 3-second disconnect refund deadline; `CAS-013..016` remote betting/session/stake, generic casino marker, integer payout and scheduler/concurrency findings. Static calculation gives 50% gross return if six horses equiprobable; runtime/policy confirmation needed.
6. LuckyWheel (`LUCKYWHEEL_REVIEW.md`): `CAS-017..019` cover remote daily prize/no server-side location, global cooldown, partial/failed prize grant and durable claim/recovery. Nominal 20-slot mapping yields fixed expected cash `$6,452.10` and `3.725 RB` per spin; total EV needs item/vehicle value policy. No build/runtime verification.
7. Legacy `/dice` (`DICE_REVIEW.md`): `CAS-020..023` cover ignored wallet-transfer results/non-atomic settlement, offer-time-only eligibility checks, self-target (policy-dependent progression), and unbounded recursive tie reroll. Static-only; no source changes.
8. Legacy Lottery (`LOTTERY_REVIEW.md`): `CAS-024..026` cover stale `BizID` shop callback without location/session validation, in-memory ticket/debit vs async persistence ordering, and payday payout/reset without durable acknowledgment. Static-only; no source changes.
9. BattlePass progression (`BATTLEPASS_REVIEW.md`): `CAS-027..028` cover separate prize grant/claim persistence crash window and marking rewards claimed despite swallowed/partial grant failure. Full quests/achievements/progression audit is not complete.
10. BattlePass producer trace / Sapper (`SAPPER_REVIEW.md`): 209 non-comment `UpdateReward` invocation lines counted; 72 refer to 55 IDs absent from the hardwired Season4 task catalog and are no-ops in `UpdateReward`. Not all producers traced end-to-end. Sapper has critical `MONEY-008..009` (negative stake RB credit, client-selected payout/refund) and `PROG-001` (task progress before active-game check); no source changes.
11. Partial quest remote review (`QUESTS_REVIEW.md`): added `PROG-002` direct quest-clear task bypass, `INV-008` Granny Bear injection, `PROG-003` client-forgeable Dada/Edward completion flags, `BUG-001` disconnected Valentine/Defender legacy actor dispatch (runtime enabled-state unconfirmed), and `PROG-004` admin SkipQuest wrong receiver. Source-only evidence, no source patches/build/runtime tests. Actor handlers remain partly unreviewed; achievement indexes were separately traced in `ONLINE_REWARDS_REVIEW.md`.
12. Wedding settlement review (`WEDDING_REVIEW.md`): `MONEY-010` debit-before-spouse-null failure can consume up to $300,000 during out-of-range divorce disconnect race; `WEDDING-001` invalid/stale target null dereference is low robustness. Static-only; no source changes.
13. Time reward and achievement persistence (`ONLINE_REWARDS_REVIEW.md`): `MONEY-011` documents possible reward replay/loss across stale hourly character checkpoints and independent account/warehouse writes; practical replay remains conditional on crash/partial-write ordering, not runtime-confirmed. `PROG-005` documents valid short `Achiev` JSON accepted without padding; `PROG-006` documents nullable `characters.time`/JSON-null loading that can terminate the shared minute pass. Production-row prevalence unknown. Static-only, no source changes or runtime tests.
14. Taxi mileage producer (`TAXI_MILEAGE_REVIEW.md`): client-calculated centimeters are accepted by `server.vehicle.updateMileage`, bounded only to 3 miles per call, then `TaxiPay` transfers fare and progresses BattlePass IDs 2/59/159/95 before wallet results. Added `MONEY-012`/`PROG-007`; active ride required, forged payload and settlement not reproduced on RAGE staging.
15. Stage snapshot + passport task flow (`DOCUMENTS_REVIEW.md`): current matrix has 19 areas (11 partial, 2 inventory-only, 5 not started, 1 blocked); raw scan inventory is 498 RemoteEvent, 116 ServerEvent, 382 Command declarations. These are not checked counts; no defensible per-handler coverage percentage exists. Traced passport request→accept: a self-target request is not forbidden and can call `UpdateReward(101)` if RAGE maps local entity args normally; added conditional `PROG-008`, staging marshalling test still required.

## Выполненные проверки и ограничения

- Tree-sitter разобрал выбранные C# member snippets для roulette/inventory/Blackjack и целиком синтаксические деревья `Spin.cs`, `Horses.cs`, `LuckyWheel.cs`; это не компиляция. Для legacy `/dice`/Lottery/BattlePass/Sapper flows выполнен статический data-flow review; для BattlePass/Sapper, текущих quest remotes и wedding flows проверены static invariants/source order и client JS syntax, но compile/runtime/DB failure tests не выполнялись. `node --check` выполнен для Roulette/Blackjack/Spin/Horses/LuckyWheel, `npc_dialogs.js`, `src_client/main.js` и `wedding.js`; static guard/data-flow assertions и Markdown link/whitespace checks выполнены.
- Статические assertions guards и проверка Markdown links/whitespace прошли.
- В текущем time-reward/achievement pass проверены все три call sites `Character.Save.Repository.SaveSql`, hourly `SaveServer` / minute loop timing, `TimeInfo` load/save, RB/warehouse grant ordering и все активные achievement indexes/catch scopes. Custom source assertions, relative Markdown links и `git diff --check` прошли; для `MONEY-011`/`PROG-005`/`PROG-006` нет C# build, test DB, fault-injection или RAGE runtime evidence.
- Taxi mileage pass traced `src_client/vehicle/mileage.js` → server remote → fare → `UpdateReward`; custom assertions подтвердили порядок вызовов и catalog IDs; Node syntax + Markdown/diff checks passed. No taxi remote, DB settlement or RAGE staging test performed; `MONEY-012`/`PROG-007` remain open.
- Inventory counts re-run: 498 RemoteEvent mentions / 137 files, 116 ServerEvent / 83 files, 382 Command / 38 files; matrix tallies to 19 areas (11 partial, 2 inventory-only, 5 not started, 1 blocked). Passport chain confirms active request/expiry/rechecks but lacks self-target rejection; static assertions and links passed, entity marshalling not runtime-tested.
- Полный C# build и RAGE:MP staging smoke tests **не выполнялись**: в среде нет .NET SDK/MSBuild, MySQL test DB и RAGE runtime.
- CEF production build ранее ограничен отсутствующими assets/памятью; см. `TEST_PLAN.md`/`BUILD_LOG.md`.
- Ни один inventory/roulette/NewCasino patch не считать закрытым до compile и staging regression tests. Не менять баланс/донат/прогрессию без согласования; только test DB/test accounts.

## Следующие шаги

1. В новом чате восстановить/подтвердить рабочую папку RedAge и прочитать `INDEX.md`, `AUDIT_COVERAGE.md`, `ISSUES.md`, `TEST_PLAN.md`, `CASINO_REVIEW.md`, `BLACKJACK_REVIEW.md`, `SPIN_REVIEW.md`, `HORSES_REVIEW.md`, `LUCKYWHEEL_REVIEW.md`, `DICE_REVIEW.md`, `LOTTERY_REVIEW.md`, `BATTLEPASS_REVIEW.md`, `SAPPER_REVIEW.md`, `QUESTS_REVIEW.md`, `WEDDING_REVIEW.md`, `ONLINE_REWARDS_REVIEW.md`, `TAXI_MILEAGE_REVIEW.md`, `DOCUMENTS_REVIEW.md` и эту заметку.
2. PR [#2](https://github.com/PandaGarry/Gastronomy/pull/2) открыт из `arena/fab5bf55-gastronomy` в `main`; продолжать добавлять только новые/изменённые файлы внутри `RedAge-3.0/`. Не менять/удалять root Gastronomy files и не пушить в upstream RedAge без отдельного checkout/ветки и разрешения владельца.
3. Продолжить статический review очередных remote event/command boundaries и подсистем; не заявлять полное покрытие без прохождения матрицы `AUDIT_COVERAGE.md`.
4. Подготовить поддерживаемый build-agent, staging/test DB и RAGE runtime; проверить inventory/roulette/Blackjack guards, Spin/Horses bet/refund fixes after implementation, положительные `RemoveIndex` call sites, rejected-payload no-op, DB/cache convergence, duplicate joins/bets и round settlement failure/restart.
5. Продолжить casino/gambling review: подтвердить dice acceptance/self-target and wager bounds policy; проверить legacy lottery shop session, ticket persistence and winner payout exactly-once; решить NewCasino blackjack coordinate/action/bet limits and Roulette/Spin/Horses disconnect settlement; test all wheel/horses/slot prize flows; также изучить roulette case grant fail-after-debit в `ROULETTE_REVIEW.md`.
6. Проверить CAS-020..028 на disposable DB/RAGE staging с fault injection, crash/reconnect и replay tests; для BattlePass reward claims обеспечить exactly-once grant/receipt. Не маркировать findings закрытыми без воспроизводимых regression tests и владельческой policy confirmation.
7. Продолжить progression review: end-to-end trace remaining `UpdateReward` producers (209 invocation lines; 72 stale IDs require confirmation), review remaining actor-specific quest handlers/resets, and run `MONEY-011` crash/partial-write fault injection plus `PROG-005` short-JSON and `PROG-006` null-Time load/tick/save tests, plus `MONEY-012`/`PROG-007` forged taxi-mileage test ride and `PROG-008` self-target entity-marshalling test when disposable MySQL/RAGE staging exists. Check `ONLINE_REWARDS_REVIEW.md`, `TAXI_MILEAGE_REVIEW.md` and `DOCUMENTS_REVIEW.md`; do not assert crash replay as runtime-proven or claim malformed DB rows exist without evidence. Continue tracing remaining `UpdateReward` producers, then proceed to the next uncovered subsystem.

## Нельзя забыть

- Не заменять и не удалять существующие файлы Gastronomy: изменения RedAge должны оставаться только под `RedAge-3.0/`.
- Не пушить upstream snapshot без отдельного целевого репозитория/ветки и проверки credential cleanup.
- Не включать реальные DB/payment/API credentials в файлы или сообщения.
- NPC/solo-mode остаётся отложенным; синхронизированный ped не является `ExtPlayer`, а поддерживаемые RAGE API/capacity не подтверждены.
