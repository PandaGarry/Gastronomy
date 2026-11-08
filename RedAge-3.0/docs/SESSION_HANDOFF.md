# Передача работы RedAge 3.0 в новый чат

> **Сначала прочитать:** [`REDAGE_MASTER_PLAN.md`](REDAGE_MASTER_PLAN.md) — главный источник истины по целям, утверждённым решениям, плану, тестовой стратегии, фактическому статусу и блокерам. Остальные документы — специализированные журналы и чек-листы.

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
15. Stage snapshot + passport task flow (`DOCUMENTS_REVIEW.md`): raw scan inventory is 498 RemoteEvent, 116 ServerEvent, 382 Command declarations. These are not checked counts; no defensible per-handler coverage percentage exists. Traced passport request→accept: a self-target request is not forbidden and can call `UpdateReward(101)` if RAGE maps local entity args normally; added conditional `PROG-008`, staging marshalling test still required.
16. Vehicle repair callback slice (`VEHICLE_REPAIR_REVIEW.md`): generic `dialogCallback("RepairMyVeh", true)` has no pending server intent; apparent physical opener is commented and debit result is unchecked. `VEH-001` remains policy-dependent and not runtime-reproduced.
17. House garage remote slice (`GARAGE_REVIEW.md`): `server.garage.parking` checks caller house/garage but resolves `autoId` globally without household-holder authorization (`VEH-002`); source establishes an unauthorized garage-slot/vehicle recreation path, but theft/duplication/permanent loss and ID enumeration are unproven. An unused negative slot index below -1 can persist and fail spawn (`VEH-003`); positive overflow is normalized, so no general capacity bypass.
18. Vehicle action remotes (`VEHICLE_ACTION_REVIEW.md`): `server.vehicle.action` skips owner/household checks for several aircraft actions (`VEH-004`); registered `server.vehicle.tuning(ExtVehicle)` does not bind the passed entity to the caller's current vehicle (`VEH-005`), but its visible callsite is commented and RAGE marshalling/reachability remain untested.
19. Government sale confirmation (`VEHICLE_SALE_REVIEW.md`): `VEH-006` callback does not revalidate current holder after a pending sale offer; `MONEY-013` payout precedes a separate asynchronous vehicle DB delete, so duplicate payout is conditional on persistence failure/restart and unproven.
20. Vehicle sync remotes (`VEHICLE_SYNC_REVIEW.md`): `VEH-007` dirt/indicator setters accept client-selected `ExtVehicle` without current-driver/access validation; dirt is unbounded and reaches cached state. `VEH-008` radio remote accepts passengers although visible client sends only from driver. Low/cosmetic or policy-dependent; marshalling/runtime untested.
21. Organization fleet slice (`ORG_VEHICLE_REVIEW.md`): access checks on load/rank/GPS/evac/sale appear scoped to member organization and permissions; `MONEY-014` is a conditional async sale-delete replay window and `MONEY-015` a low-value $20 evacuation-before-debit failure window. Static-only; organization-wide ACL remains open.
22. House resident ACL/persistence (`HOUSE_RESIDENT_REVIEW.md`): `PROP-001` roommate caller can toggle resident permissions or evict another roommate because the remote uses owner-or-roommate `GetHouse`; `PROP-002` invite/access/dell writes do not set `house.IsSave`, so restart can lose changes/resurrect a resident unless another dirty save occurs.
23. House sale (`PROPERTY_SALE_REVIEW.md`): `MONEY-016` payout and dirty owner-row save are separate; house save polls every 30 seconds and clears dirty state before update, so duplicate resale is conditional on crash/DB failure and remains untested. House acceptance still rechecks current ownership; no non-owner sale path found.
24. House purchase (`PROPERTY_PURCHASE_REVIEW.md`): `MONEY-017` ownership is set before debit, while wallet debit can reject during shutdown and its return is ignored. Conditional timing path; no free purchase reproduced.
25. Player-to-player house transfer (`PROPERTY_TRANSFER_REVIEW.md`): `MONEY-018` ignores buyer debit rejection, then credits seller and transfers title; conditional shutdown-only money creation, not reproduced.
26. House tax (`PROPERTY_TAX_REVIEW.md`): `MONEY-019` direct hourly debits do not dirty the bank account; `PROP-003` tax repossession clears owner without dirtying the house row. Both can roll back/resurrect state on restart if no other mutation saves it; static-only.
27. ATM cash withdrawals (`ATM_REVIEW.md`): `MONEY-004` direct `atmCB`/`atmVal` sequence bypasses ATM range and `OnAtm` wanted/demorgan checks, but only withdraws caller-owned funds. Policy-dependent, not runtime-tested.
28. Bank transfer confirmation (`BANK_TRANSFER_REVIEW.md`, detail for `MONEY-003`): pending source/destination/amount stay set after acceptance; replaying generic `AcceptBankTransfer` repeats the caller-authorized transfer and bypasses the request cooldown, without cross-player source debit. Static, RAGE test required.
29. Business phone orders (`BUSINESS_ORDER_REVIEW.md`): `MONEY-022` add/bulk/cancel/price mutations do not set `biz.IsSave`, while the business worker persists only dirty rows. A saved bank debit/refund can diverge from order state on restart; conditional, not reproduced.
30. Phone auctions (`AUCTION_REVIEW.md`): `MONEY-023` fresh-auction first bid debits before refunding `LastBetUUID=0`, which can throw; `MONEY-024` accepts bids after expiry/end while the record remains cached; `PROP-004` detaches a house/business before async listing insert; `PROP-005` offline business winner may lack `BizIDs`. Static-only, no runtime/DB tests.
31. Business order overflow (`BUSINESS_ORDER_REVIEW.md`): `MONEY-025` demonstrates a concrete unchecked-int count/cost wrap on `server.phone.business.addOrder` that can credit +$375,000 in the bundled stocked-product fixture if a caller owns a stocked type-0 business. High-priority static finding; not run on RAGE/MySQL.
32. Business sale (`BUSINESS_SALE_REVIEW.md`): `MONEY-026` additionally confirms `Wallet.Change` result is ignored before business ownership release; sale can both release ownership without confirmed proceeds and replay after hard crash if business+wallet writes persist before character `BizIDs`. Stale list reloads without owner reconciliation; generic `BIZ_SELL_TOGOV` confirmation lacks an owner check. No fault-injection/crash reproduction.
34. Business retail purchases (`BUSINESS_RETAIL_REVIEW.md`): `STOCK-002` confirms takeProd decrements stock before owner-bank credit and callers ignore customer debit/item grant results; `MONEY-022` expanded to retail stock dirty-save omission. Static-only; no runtime failure injection.
35. ATM business account (`BUSINESS_BANK_REVIEW.md`): `MONEY-039` confirms the ATM path debits the player wallet before an unchecked business-bank credit and reports success regardless of the second-leg result. Static-only; no fault injection.
36. Business hourly tax/repossession (`BUSINESS_TAX_REVIEW.md`): `MONEY-040` confirms ordinary tax debit is not marked dirty for bank persistence; `MONEY-041` confirms online payout result is ignored and offline compensation is asynchronous/unconfirmed before ownership release. Static-only; no DB/RAGE fault injection.
37. Player-to-player vehicle sale (`VEHICLE_PLAYER_SALE_REVIEW.md`): `MONEY-042` confirms seller credit is unchecked after buyer debit and vehicle holder persistence is asynchronous without durable receipt/retry. Static-only; no runtime/DB failure injection.
33. Trucker business delivery (`BUSINESS_DELIVERY_REVIEW.md`): `JOB-001` `Take` marks public order Taked before cargo acquisition; off-duty passenger / missing rental can reserve and temporarily block it until cancel/disconnect. Static-only.
34. Phone contacts/SMS (`PHONE_MESSAGES_REVIEW.md`): `PROG-009` contact add/update progresses active BP tasks before mutation validation; `SEC-007` untrusted SMS reaches CEF executable-JS/raw-HTML sinks; `SEC-010` message image type loads arbitrary recipient-side URLs; `PHONE-001` async message/status lists clear before DB confirmation and can lose batches under race/failure. Static-only; no RAGE/CEF/MySQL tests.
35. Call/settings/Tinder slice (`PHONE_CALL_TINDER_REVIEW.md`): `PHONE-002` unchecked sound IDs can interrupt call/message paths; `PHONE-003` unbounded preference/contact/gallery URL input can break phone-info saves; gallery URLs also reach owner-side CEF `Image.src` after a weak substring check; `PHONE-004` replayed Tinder likes can resend match messages; `SEC-008` Tinder avatar CSS/resource loading is a candidate pending CEF proof. No runtime reproduction.
36. Phone News/Forbes (`PHONE_NEWS_REVIEW.md`): `MONEY-027` bank debit and success precede async advert DB insert without compensation; `MONEY-028` editor payout/publication/progress precede durable completion, allowing conditional replay; `SEC-009` moderator-approved advert link reaches public inline CSS `url()` rendering and may cause resource requests. Both static-only; no DB/CSP runtime tests. Forbes opt-out appears to hide individual assets while retaining aggregate cash/bank and ranking; product policy still needs owner confirmation, so no finding is asserted.
37. SIM/gallery/animation (`PHONE_SIM_REVIEW.md`): `PHONE-005` SIM install/remove/map/inventory writes are non-atomic and no insert-time unique-owner check protects `Main.SimCards`; duplicate-card interception and write-failure outcomes are conditional. `PHONE-006` allows direct nearby selfie-animation broadcasts without camera-state validation; cosmetic/policy-dependent. Gallery has a caller-owned 25-item cap but unbounded URLs (`PHONE-003`); its CEF image load is owner-side only and still needs a controlled request test. Camera screenshot goes to Imgur by the client path. Static-only. Continue phone property/car/mechanic/taxi remotes, News moderation ACL/edit/delete and rate limits; matrix remains 19 areas: 14 partial / 2 inventory-only / 2 not started / 1 blocked.

38. Phone dispatch/read endpoints (`PHONE_DISPATCH_REVIEW.md`): `JOB-002` taxi/mechanic take remotes can overwrite assigned orders and leave stale position timers; `JOB-003` repeat order/cancel can fan out worker/location notifications without an app-level cooldown. Static-only; takeover, scheduler and global RAGE rate limiting remain untested. Narrow `cars.load`/house/property/GPS/recent read paths were traced with no standalone arbitrary-target finding; household vehicle metadata visibility remains a policy question. Continue taxi/mechanic service lifecycle, fare/mileage and phone business/property mutations.


39. House furniture crafting (`HOUSE_FURNITURE_REVIEW.md`): `INV-009` counts recipe materials across all character sub-locations but removes only from `inventory`; the direct move→craft path depends on `INV-003` slot-policy bypass and still requires RAGE proof. The phone house UI reaches the previously logged `PROP-001` resident ACL handlers. No furniture craft or DB recovery was runtime-tested.


## Выполненные проверки и ограничения

- Tree-sitter разобрал выбранные C# member snippets для roulette/inventory/Blackjack и целиком синтаксические деревья `Spin.cs`, `Horses.cs`, `LuckyWheel.cs`; это не компиляция. Для legacy `/dice`/Lottery/BattlePass/Sapper flows выполнен статический data-flow review; для BattlePass/Sapper, текущих quest remotes и wedding flows проверены static invariants/source order и client JS syntax, но compile/runtime/DB failure tests не выполнялись. `node --check` выполнен для Roulette/Blackjack/Spin/Horses/LuckyWheel, `npc_dialogs.js`, `src_client/main.js` и `wedding.js`; static guard/data-flow assertions и Markdown link/whitespace checks выполнены.
- Статические assertions guards и проверка Markdown links/whitespace прошли.
- В текущем time-reward/achievement pass проверены все три call sites `Character.Save.Repository.SaveSql`, hourly `SaveServer` / minute loop timing, `TimeInfo` load/save, RB/warehouse grant ordering и все активные achievement indexes/catch scopes. Custom source assertions, relative Markdown links и `git diff --check` прошли; для `MONEY-011`/`PROG-005`/`PROG-006` нет C# build, test DB, fault-injection или RAGE runtime evidence.
- Taxi mileage pass traced `src_client/vehicle/mileage.js` → server remote → fare → `UpdateReward`; custom assertions подтвердили порядок вызовов и catalog IDs; Node syntax + Markdown/diff checks passed. No taxi remote, DB settlement or RAGE staging test performed; `MONEY-012`/`PROG-007` remain open.
- Inventory counts re-run: 498 RemoteEvent mentions / 137 files, 116 ServerEvent / 83 files, 382 Command / 38 files; matrix now 19 areas (14 partial, 2 inventory-only, 2 not started, 1 blocked). Passport chain confirms active request/expiry/rechecks but lacks self-target rejection; static assertions and links passed, entity marshalling not runtime-tested. Vehicle reviews now include `VEH-001..008` and `MONEY-013..015`: repair, garage global-ID/negative-index, aircraft action/entity, sale/payout-delete, dirt/indicator, passenger radio and one organization fleet slice. Source assertions and modified-doc links passed; no C# build, MySQL fault injection or RAGE test.
- Полный C# build и RAGE:MP staging smoke tests **не выполнялись**: в среде нет .NET SDK/MSBuild, MySQL test DB и RAGE runtime.
- CEF production build ранее ограничен отсутствующими assets/памятью; см. `TEST_PLAN.md`/`BUILD_LOG.md`.
- Ни один inventory/roulette/NewCasino patch не считать закрытым до compile и staging regression tests. Не менять баланс/донат/прогрессию без согласования; только test DB/test accounts.

## Следующие шаги

1. В новом чате восстановить/подтвердить рабочую папку RedAge и прочитать `INDEX.md`, `AUDIT_COVERAGE.md`, `ISSUES.md`, `TEST_PLAN.md`, `CASINO_REVIEW.md`, `BLACKJACK_REVIEW.md`, `SPIN_REVIEW.md`, `HORSES_REVIEW.md`, `LUCKYWHEEL_REVIEW.md`, `DICE_REVIEW.md`, `LOTTERY_REVIEW.md`, `BATTLEPASS_REVIEW.md`, `SAPPER_REVIEW.md`, `QUESTS_REVIEW.md`, `WEDDING_REVIEW.md`, `ONLINE_REWARDS_REVIEW.md`, `TAXI_MILEAGE_REVIEW.md`, `DOCUMENTS_REVIEW.md`, `VEHICLE_REPAIR_REVIEW.md`, `GARAGE_REVIEW.md`, `VEHICLE_ACTION_REVIEW.md`, `VEHICLE_SALE_REVIEW.md`, `VEHICLE_SYNC_REVIEW.md`, `ORG_VEHICLE_REVIEW.md`, `HOUSE_RESIDENT_REVIEW.md`, `PROPERTY_SALE_REVIEW.md`, `PROPERTY_PURCHASE_REVIEW.md`, `PROPERTY_TRANSFER_REVIEW.md`, `PROPERTY_TAX_REVIEW.md`, `ATM_REVIEW.md`, `BANK_TRANSFER_REVIEW.md`, `PHONE_MESSAGES_REVIEW.md`, `PHONE_CALL_TINDER_REVIEW.md`, `PHONE_NEWS_REVIEW.md`, `PHONE_SIM_REVIEW.md`, `PHONE_DISPATCH_REVIEW.md`, `HOUSE_FURNITURE_REVIEW.md`, `WEAPON_REMOTE_REVIEW.md`, `SELECTING_REMOTE_REVIEW.md`, `CARROOM_REVIEW.md` и эту заметку.
2. PR [#2](https://github.com/PandaGarry/Gastronomy/pull/2) открыт из `arena/fab5bf55-gastronomy` в `main`; продолжать добавлять только новые/изменённые файлы внутри `RedAge-3.0/`. Не менять/удалять root Gastronomy files и не пушить в upstream RedAge без отдельного checkout/ветки и разрешения владельца.
3. Продолжить статический review очередных remote event/command boundaries и подсистем; не заявлять полное покрытие без прохождения матрицы `AUDIT_COVERAGE.md`.
4. Подготовить поддерживаемый build-agent, staging/test DB и RAGE runtime; проверить inventory/roulette/Blackjack guards, Spin/Horses bet/refund fixes after implementation, положительные `RemoveIndex` call sites, rejected-payload no-op, DB/cache convergence, duplicate joins/bets и round settlement failure/restart.
5. Продолжить casino/gambling review: подтвердить dice acceptance/self-target and wager bounds policy; проверить legacy lottery shop session, ticket persistence and winner payout exactly-once; решить NewCasino blackjack coordinate/action/bet limits and Roulette/Spin/Horses disconnect settlement; test all wheel/horses/slot prize flows; также изучить roulette case grant fail-after-debit в `ROULETTE_REVIEW.md`.
6. Проверить CAS-020..028 на disposable DB/RAGE staging с fault injection, crash/reconnect и replay tests; для BattlePass reward claims обеспечить exactly-once grant/receipt. Не маркировать findings закрытыми без воспроизводимых regression tests и владельческой policy confirmation.
7. Continue progression review: trace the remaining `UpdateReward` producers (209 invocation lines; 72 stale IDs require confirmation), review remaining actor-specific quest handlers/resets, and run `MONEY-011` crash/partial-write fault injection, `PROG-005` short-JSON, `PROG-006` null-Time load/tick/save, `MONEY-012`/`PROG-007` forged taxi-mileage, and `PROG-008` self-target marshalling tests. When disposable MySQL/RAGE staging exists, test `VEH-001` repair policy; `VEH-002` foreign vehicle ID authorization/recovery; `VEH-003` negative slot/corrupt-load; `VEH-004` foreign-aircraft actions; `VEH-005` entity marshalling; `VEH-006` stale sale ownership; `VEH-007..008` sync entity/radio behavior; `MONEY-013..014` sale-delete failure/restart, `MONEY-015` evacuation debit failure and organization ACL/rank boundaries; `PROP-001..002` roommate privilege/eviction and restart persistence tests from `HOUSE_RESIDENT_REVIEW.md`, plus `MONEY-016` house sale crash/restart tests from `PROPERTY_SALE_REVIEW.md` and `MONEY-017` shutdown debit failure tests from `PROPERTY_PURCHASE_REVIEW.md`, and `MONEY-018` player-transfer debit/payout tests from `PROPERTY_TRANSFER_REVIEW.md`, `MONEY-019` tax-account restart tests and `PROP-003` repossession restart tests from `PROPERTY_TAX_REVIEW.md`, plus `MONEY-004` direct ATM remote/range/eligibility tests from `ATM_REVIEW.md`, plus `MONEY-003` transfer-confirmation replay tests from `BANK_TRANSFER_REVIEW.md` and `MONEY-022`/`MONEY-025` business order/save and arithmetic-overflow tests from `BUSINESS_ORDER_REVIEW.md`, `STOCK-002` retail purchase settlement tests from `BUSINESS_RETAIL_REVIEW.md`, `MONEY-039` ATM business deposit tests from `BUSINESS_BANK_REVIEW.md`, `MONEY-040/041` business tax/repo tests from `BUSINESS_TAX_REVIEW.md`, `MONEY-042` player vehicle sale settlement tests from `VEHICLE_PLAYER_SALE_REVIEW.md`, `MONEY-026` crash/restart replay tests from `BUSINESS_SALE_REVIEW.md`, `JOB-001` reservation/cargo tests from `BUSINESS_DELIVERY_REVIEW.md`, `SEC-007`/`SEC-010`/`PROG-009` and `PHONE-001` cases from `PHONE_MESSAGES_REVIEW.md`, `SEC-008` and `PHONE-002..004` cases from `PHONE_CALL_TINDER_REVIEW.md`, `SEC-009`/`MONEY-027..028` cases from `PHONE_NEWS_REVIEW.md`, `PHONE-005..006` cases from `PHONE_SIM_REVIEW.md`, `JOB-002..003` taxi/mechanic dispatcher takeover/flood cases from `PHONE_DISPATCH_REVIEW.md`, `INV-009` furniture recipe/location mismatch from `HOUSE_FURNITURE_REVIEW.md`, plus `MONEY-023..024` and `PROP-004..005` auction failure/restart tests from `AUCTION_REVIEW.md`. Continue auditing remaining vehicle/garage remotes. Check `ONLINE_REWARDS_REVIEW.md`, `TAXI_MILEAGE_REVIEW.md`, `DOCUMENTS_REVIEW.md`, `VEHICLE_REPAIR_REVIEW.md`, `GARAGE_REVIEW.md`, `VEHICLE_ACTION_REVIEW.md`, `VEHICLE_SALE_REVIEW.md`, `VEHICLE_SYNC_REVIEW.md`, `ORG_VEHICLE_REVIEW.md`, `HOUSE_RESIDENT_REVIEW.md`, `PROPERTY_SALE_REVIEW.md`, `PROPERTY_PURCHASE_REVIEW.md`, `PROPERTY_TRANSFER_REVIEW.md`, `PROPERTY_TAX_REVIEW.md`, `ATM_REVIEW.md`, `BANK_TRANSFER_REVIEW.md`, `BUSINESS_ORDER_REVIEW.md`, `BUSINESS_SALE_REVIEW.md`, `BUSINESS_DELIVERY_REVIEW.md`, `PHONE_MESSAGES_REVIEW.md`, `PHONE_CALL_TINDER_REVIEW.md`, `PHONE_NEWS_REVIEW.md`, `PHONE_SIM_REVIEW.md`, `PHONE_DISPATCH_REVIEW.md`, `HOUSE_FURNITURE_REVIEW.md` and `AUCTION_REVIEW.md`; do not assert crash replay as runtime-proven or claim malformed DB rows exist without evidence. Continue remaining `UpdateReward` producers, then proceed to the next uncovered subsystem.

- Последующее продолжение в том же проходе: `Core/Carroom.cs` добавил статический `MONEY-029` — invalid client color после debit может оставить оплату без транспорта; testDrive дополнительно требует проверки model allowlist и гарантированного cleanup. См. `CARROOM_REVIEW.md`, test 46. Runtime-эффект не проверялся.

## Нельзя забыть

- Не заменять и не удалять существующие файлы Gastronomy: изменения RedAge должны оставаться только под `RedAge-3.0/`.
- Не пушить upstream snapshot без отдельного целевого репозитория/ветки и проверки credential cleanup.
- Не включать реальные DB/payment/API credentials в файлы или сообщения.
- NPC/solo-mode остаётся отложенным; синхронизированный ped не является `ExtPlayer`, а поддерживаемые RAGE API/capacity не подтверждены.


## Последний проход (2026-11-07)

- Продолжен широкий remote review: phone contacts/blacklist/call/recents/GPS/gallery/settings/open-close/property-car и business/dispatch cross-check; не добавляли дубликаты ранее описанных `PROG-009`, `PHONE-002..003`, `PHONE-006` и бизнес-findingов. Полнота phone audit не достигнута.
- Проверен `Core/Selecting.cs`: `beltSelected` безусловно вызывает BattlePass task 86; зарегистрирован `PROG-010`.
- Проверен `Core/WeaponRepository.cs`: ammo-return remote использует client count для inventory-capacity вычисления до clip clamp и допускает unchecked drop; зарегистрирован `INV-010`. Статический вывод; RAGE behavior не проверен.
- Добавлены tests 44–45 и новые review files. Ближайшее продолжение: проверить `INV-010`/`PROG-010` на disposable RAGE staging, затем покрывать непроверенные weapon damage/shop/vehicle and remaining remote groups; аудит не завершать преждевременно.


## Продолжение после merge PR #2 (2026-11-07)

- PR #2 слит в `main`; продолжать только на фиксированной ветке `arena/fab5bf55-gastronomy`. Новые audit-doc изменения после merge следует отправлять отдельным PR из этой ветки; не пытаться повторно изменять уже слитый PR #2.
- Очередной `Main.cs` pass зарегистрировал `MONEY-030` (условный EventCoins→RedBuck credit без точного снятия при различии локаций) и `MONEY-031` (generic input callback без проверки City Hall leader для фракционных fuel caps). См. `MAIN_REMOTE_REVIEW.md`; это статический анализ, не runtime-подтверждение. `syncWaypoint` cross-check не объявлялся отдельным finding: эвент непосредственно выполняет описанный waypoint relay.
- Проверить new test cases 47–48 на disposable RAGE/MySQL staging; продолжить оставшиеся delegated `inputCallback`/`dialogCallback` and remote handlers.


## Продолжение (2026-11-08)

- GitHub write access теперь подтверждён реальной операцией: создана ветка `redage/audit-continuation` от `arena/fab5bf55-gastronomy`; `main` не изменялась.
- Создан Draft PR #4: https://github.com/PandaGarry/Gastronomy/pull/4. Не сливать: `main` и arena branch diverged (по одному уникальному коммиту на каждой стороне до продолжения); PR содержит существующую документационную разницу и новые audit updates. Сначала reconcile history/diff.
- Создан `MASTER_CHECKLIST.md`; PR body обновлён по мере добавления findings.
- Продолжен `Main.cs` delegated callback review. MONEY-032: `mayor_take` игнорирует false от `Bank.Change` и всё равно списывает казначейские средства. MONEY-033: `ticketConfirm` продолжает выплату при неудаче обоих debit paths и не очищает `targetSessionData.TicketsData`, поэтому settlement replayable. См. `MAIN_REMOTE_REVIEW.md`, `ISSUES.md`, `TEST_PLAN.md`.
- Только статический анализ; C# build, RAGE:MP, MySQL fault injection и runtime reproduction не выполнялись. Оба finding остаются открытыми.
- Продолжить аудит оставшихся delegated `inputCallback`/ `dialogCallback` paths, затем остальные неохваченные remote groups; не считать audit завершённым.


## Продолжение аудита (2026-11-08, pass 2)

- Перечислены 38 `case` occurrences (32 уникальных callback names) в `Main.ClientEvent_inputCallback`. Это inventory labels, а не завершённое покрытие всех delegated handlers.
- Проверены `sellMedKitToTarget` и `healTarget`: повторные проверки доступа/дежурства/цены/дистанции присутствуют. Проверен `mayor_put`: результат bank debit проверяется до пополнения казны. В issue register не добавлялись findings без отдельного доказанного дефекта.
- Открытые для следующего прохода delegated paths: club price, house sale offer, drugs, faction stock/garage, street race, vehicle sale acceptance/settlement, hotel rent extension, tent rename/sell, pet rename, legacy weaptransfer, generic argument/rate-limit handling.
- MONEY-030..033 остаются открытыми. Статический анализ only; C# build, RAGE runtime и MySQL failure tests не выполнялись.


## Аудит продолжен — MONEY-034 (2026-11-08)

- Проверен `buy_drugs`: `Main.ClientEvent_inputCallback` допускает любое положительное значение int; `Gangs.BuyDrugs` использует unchecked `amount * Main.DrugsPrice` (default 30) и `count + amount`. Для int.MaxValue стоимость становится -30, проверка средств проходит, а вычитание увеличивает деньги фракции на 30. При частично заполненном транспорте capacity sum тоже может переполниться. AddNewItem result игнорируется; DB/item effect требует staging.
- Зарегистрирован MONEY-034 и добавлены тесты границ int, вместимости, partial insertion, replay и restart в TEST_PLAN.
- HOUSE sale MONEY-018 уже был в PROPERTY_TRANSFER_REVIEW/ISSUES; не дублировал его.
- MONEY-030..034 открыты. Новых игровых исходников не менял. Runtime/build/DB tests не запускались.
- Чек-лист обновлён: 38 case occurrences / 32 unique names — это инвентаризация, не завершение review всех handlers. Следующий шаг — детально закрывать остальные delegated callbacks и remote groups.


## Продолжение — фракционные склады (2026-11-08)

- Проверен Fractions.Manager.inputStocks и Chars.Repository.AddNewItem. Входной Main.ClientEvent_inputCallback для put_stock/take_stock отвергает amount < 1; отрицательный amount не записан как подтверждённый exploit через этот путь.
- MONEY-035: при take_stock money сначала уменьшается fractionData.Money, затем игнорируется bool от Wallet.Change. Wallet.Change имеет false-return paths; при отказе баланс фракции уже уменьшен.
- STOCK-001: AddNewItem возвращает -1 при неудаче и может сообщить последний слот при частичной вставке; склад/запасы уменьшаются на полное requested amount. Для medkits vehicle free-slot check закомментирован; aggregate count не гарантирует свободные slots.
- Обновлены ISSUES, MAIN_REMOTE_REVIEW, MASTER_CHECKLIST, TEST_PLAN, INDEX, AUDIT_COVERAGE, ROADMAP, CHANGELOG и SESSION_HANDOFF. Runtime/staging не выполнялись; source code не менялся.
- Следующий проход: сравнить Organizations.Manager.inputStocks с теми же invariants, затем прочие faction stock callback actions и ownership/rank checks.

- Organization parity checked: `Organizations.Manager.inputStocks` repeats the unchecked wallet credit/debit and AddNewItem/Remove settlement ordering. Covered by MONEY-035/STOCK-001, not duplicated. Test deposit as well as withdrawal paths.


## Дополнение — MONEY-036 (2026-11-08)

- Первоначальная оценка MONEY-036 была чрезмерно высокой. Дополнительная проверка установила, что generated DB model хранит `characters.money` как `int(11)`, а создание, character save и money worker также приводят значение к `int`. В текущем persistence contract путь к балансу > Int32.MaxValue не найден; математический пример с 4,294,967,296 не подтверждён как достижимый.
- MONEY-036 оставлен как низкоприоритетная несогласованность типов/контракта. Требуется выбрать явный Int32 cap либо end-to-end BIGINT migration. Риск отказа начисления на верхней границе остаётся важен для callers, игнорирующих `Wallet.Change=false` (например, MONEY-035/CAS-020), но самостоятельная порча валидного DB-range баланса не доказана.
- Исходники не менялись; runtime/build/DB tests не выполнялись.


## 2026-11-08 continuation — MONEY-037

- Audited player-to-player house sale confirmation (`HouseManager.acceptHouseSell`). Buyer and seller `Wallet.Change` return values are ignored; house ownership changes regardless. Found sellerCharacterData assigned from buyer, causing wrong seller UUID in money log. Added `HOUSE_SALE_REVIEW.md`, MONEY-037, checklist and regression cases. Static only; no runtime/build validation.


## 2026-11-08 continuation — MONEY-038

- Continued phone auction audit in `Players/Phone/Auction/Events.cs`, `Repository.cs` and `MoneySystem/Bank.cs`.
- Registered MONEY-038: client-supplied `int price` is used in unchecked `int` fee arithmetic. `int.MaxValue` wraps `price + price/100` to `-2,126,008,813`; negating that value sends a positive credit to `Bank.Change` rather than a debit. `Bank.Change` accepts positive amounts as credits. Evidence is static; RAGE runtime, C# build and DB fault injection remain unavailable.
- Updated `AUCTION_REVIEW.md`, `ISSUES.md`, `MASTER_CHECKLIST.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md`, `INDEX.md`, `TEST_PLAN.md` and `CHANGELOG.md`. No gameplay source changes. PR remains draft and must not be merged until branch histories/diff are reconciled.


## 2026-11-08 continuation — INV-011

- Extended phone auction lifecycle review to AuctionType.Other. OnCreate removes the item from the character inventory and queues its SQL record into location `auction`; End handles only House/Biz/Vehicle and has no Other-item winner grant or seller-return branch. The ended row is later removed from active auction cache. Registered INV-011; exact DB recovery behavior and intended UI exposure still require staging confirmation.
- Updated `AUCTION_REVIEW.md`, `ISSUES.md`, `MASTER_CHECKLIST.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md`, `INDEX.md` and `TEST_PLAN.md`. No source patch/build/runtime test. PR remains draft; do not merge until branch histories and diff are reconciled.


## 2026-11-08 continuation — business order/delivery settlement

- Expanded MONEY-022 evidence: `CancelOrder` clears order/product state before `Bank.Change` refund and ignores a false return. The account API can return false for a missing account or exception; no pending refund is retained in the cancellation method. Static only.
- Registered JOB-004: `Jobs/Truckers.cs` ignores `Wallet.Change` result and proceeds to money log, stock replenishment, order removal, session cleanup and success notification. If the wallet credit fails, delivery is consumed without guaranteed payment. Added `BUSINESS_DELIVERY_REVIEW.md` and regression cases.
- Updated `ISSUES.md`, `MASTER_CHECKLIST.md`, `TEST_PLAN.md`, `INDEX.md`, `AUDIT_COVERAGE.md`, `ROADMAP.md` and `CHANGELOG.md`. No gameplay source patch, C# build, RAGE runtime or DB fault injection performed.


## 2026-11-08 continuation — MONEY-043/044 business ownership

- Продолжен широкий business lifecycle review. `buyBusinessCommand` ignores the buyer `Wallet.Change` result, then clears stock/orders, changes owner, adds BizID and saves; registered `MONEY-043`.
- `acceptBuyBusiness` saves buyer/seller BizIDs and changes `biz.Owner` before two unchecked wallet operations; registered `MONEY-044`. Buyer may receive the business without paying or seller may not receive proceeds after buyer debit.
- Added `BUSINESS_OWNERSHIP_REVIEW.md`, regression matrix and references in issue register/checklist/test plan/coverage/roadmap/index/changelog. Static-only; no gameplay source patch, C# build, RAGE runtime or DB fault injection.
- Continue the remaining business purchase/ownership/admin deletion and stock/order lifecycle paths without duplicating `STOCK-002`, `MONEY-022/025/026`, `MONEY-039..041`, or `JOB-004`.


## 2026-11-08 continuation — MONEY-045 government fuel quota

- Traced the petrol remote through vehicle/fraction/business state. Government branch does not reject when the computed cost exceeds FuelLeft; it merely skips the FuelLeft decrement and continues to charge City Hall/apply fuel. It also compares liters to a monetary allowance and computes price before quantity clamp. Registered MONEY-045 in BUSINESS_FUEL_REVIEW.md with policy caveat and regression matrix.
- Updated ISSUES, MASTER_CHECKLIST, TEST_PLAN, AUDIT_COVERAGE, INDEX, ROADMAP, CHANGELOG and this handoff. Static-only; no code patch, build, RAGE runtime or DB fault injection.
- Next: continue business/vehicle fuel and ownership lifecycle, checking all related remote paths and avoiding duplication with STOCK-002, MONEY-031, MONEY-043/044.


## 2026-11-08 continuation — VEH-009 petrol remote context

- Found `OnBusinessAction` assigns SessionData.BizID for every business interaction, with no exit reset found; `petrol` only checks BizID exists and player is in a vehicle, not fuel-station type/proximity/dimension/active intent. `takeProd` returns true when no matching product exists (STOCK-002), so stale/non-fuel context can pass. Registered VEH-009 in BUSINESS_FUEL_REVIEW.md.
- Updated issue register, checklist, test plan, coverage, index, roadmap, changelog and handoff. Static-only; runtime event reachability remains to be tested.


## 2026-11-08 continuation — JOB-005 AutoMechanic settlement

- Traced mechanic repair/fuel offer and acceptance plus mechanic gas-station fuel purchase. `mechanicPay` and `mechanicPayFuel` ignore both buyer debit and mechanic credit results while applying service effects and reporting success; `buyFuel` ignores buyer debit before increasing work-vehicle fuel reserve. Registered JOB-005 in MECHANIC_SERVICE_REVIEW.md.
- Updated issue register, master checklist, test plan, coverage, index, roadmap, changelog and handoff. Static-only; no gameplay source patch, C# build, RAGE runtime or DB failure injection.


## 2026-11-08 continuation — business admin deletion

- Audited deleteBusinessCommand: DB row is deleted before a null-unsafe owner lookup; offline/government owner can throw before BizList/world cleanup and intended offline BizIDs branch. Registered BUG-002. Online owner branch ignores Wallet.Change refund result before business removal; registered MONEY-047.
- Extended BUSINESS_OWNERSHIP_REVIEW.md and updated issue register, checklist, test plan, coverage, index, roadmap, changelog and handoff. Static-only; RAGE/admin/DB failure tests not performed.


## 2026-11-08 continuation — PET-001 pet-shop remote

- Found petshopBuy accepts any existing TempBizID without requiring a Type==14 business, nearby active session or one-shot intent; it teleports before checking house eligibility, does not clear TempBizID after success and persists unvalidated petName. Registered PET-001 and created PETSHOP_REMOTE_REVIEW.md.
- Expanded MONEY-045: tfuel and price are computed before the government quota clamp; stock reservation receives clamped liters while the vehicle receives stale pre-clamp fuel amount. Added regression assertions.
- Updated ISSUES, MASTER_CHECKLIST, TEST_PLAN, AUDIT_COVERAGE, INDEX, ROADMAP, CHANGELOG and SESSION_HANDOFF. Static-only; no source patch/build/RAGE/CEF/DB tests.
- Next: continue business stock/service callers and inventory/remote authorization; avoid duplicating STOCK-002, MONEY-045, VEH-009 and PET-001.


## 2026-11-08 continuation — VEH-010 LS Customs tuning

- Organization tuning entry stores the business ID in CharacterData.TuningShop. Client exit sends eventType=1; server case 1 does not clear the field. The personal server.custom.buy remote trusts this stale value and lacks active session, Type==12, proximity and dimension checks. Character.Repository also uses TuningShop for CurPosition resolution.
- Registered VEH-010 and created TUNING_REMOTE_REVIEW.md. Expanded STOCK-002 retail/service review to include LS Customs reservation-before-SetCustomization and unchecked wallet debit.
- Updated ISSUES, MASTER_CHECKLIST, TEST_PLAN, AUDIT_COVERAGE, INDEX, ROADMAP, CHANGELOG and SESSION_HANDOFF. Static-only; no source patch/build/RAGE/DB tests.
- Next: continue remote authorization review around vehicle/business and phone flows; avoid duplication with VEH-010, VEH-009, PET-001 and STOCK-002.


## 2026-11-08 continuation — VEH-011 mileage counter wrap

- Found unchecked (uint)centimeters in server.vehicle.updateMileage; negative client values wrap to large unsigned increments in transient VehicleLocalData.Centimeters. No persistent DB corruption is claimed. Existing MONEY-012/PROG-007 still cover unverified taxi fare and BattlePass progression.
- Client mileage calc runs on a 200ms render event but adds a per-second centimeter value without elapsed-time scaling; likely ~5x at exact cadence, pending runtime measurement. Added as a client-side observation, not a separate issue.
- Registered VEH-011; updated TAXI_MILEAGE_REVIEW, ISSUES, MASTER_CHECKLIST, TEST_PLAN, AUDIT_COVERAGE, INDEX, ROADMAP, CHANGELOG and SESSION_HANDOFF. Static-only, no source changes/build/RAGE/DB tests.
- Next: continue uncovered vehicle sync/control and garage/storage lifecycle; avoid duplicating MONEY-012, PROG-007, VEH-007..010.


## 2026-11-08 continuation — INV-012 vehicle trunk inventory

- Found vehicleSelected branch 3 opens a vehicle container after one-time 5m/trunk-open check, then generic inventory move/stack/use handlers mutate `other` without rechecking vehicle ACL, proximity, dimension, door state or selected vehicle. ItemsUse can transfer an `other` item to character inventory.
- Registered INV-012 and created VEHICLE_TRUNK_ACCESS_REVIEW.md. Open-trunk public access remains policy-dependent; no successful theft is claimed. Updated INVENTORY_REVIEW, ISSUES, TEST_PLAN, MASTER_CHECKLIST, AUDIT_COVERAGE, INDEX, ROADMAP, CHANGELOG and SESSION_HANDOFF.
- Static-only; no source changes/build/RAGE/DB tests. Next: trace vehicle trunk close/session invalidation, storage ownership, and all other `LoadOtherItemsData` endpoints; avoid duplicating INV-003/INV-012.


## 2026-11-08 continuation — VEH-012 vehicle trunk reservation cleanup

- CEF `closeOther` clears the other pane and calls `client.inventory.OtherClose`; the client bridge invokes `server.gamemenu.inventory.otherclose`. `Repository.OtherClose` clears InventoryOtherLocationName but not SelectedVeh/BagInUse. Full ItemsClose and disconnect do release BagInUse, so the stale reservation can block another player until one of those paths runs.
- Registered VEH-012 and created VEHICLE_TRUNK_LIFECYCLE_REVIEW.md. Separate from INV-012 (per-operation authorization); no source patch/build/runtime/DB test.
- Next: trace all remaining LoadOtherItemsData endpoints and their container-specific open/close ACLs; then continue vehicle control/garage/storage lifecycle. Do not duplicate INV-003/INV-012/VEH-012.


## 2026-11-08 continuation — INV-013/014 event loot remotes

- Mapped LoadOtherItemsData targets: vehicle, furniture safes, faction stocks, organization stock, personal warehouse, tent, AirDrop, MatWar, HeliCrash, weapon components and key ring. INVENTORY_REVIEW now records entry paths and the shared mutation-boundary caveat.
- AirDrop: IsPlayerToEvents is a TeamsInfo membership check, not proximity/dimension; StartedHack sets a generic session Boolean without binding the player to a DropId; AirdropChangeLockStatus trusts client health; OpenInventory opens unlocked loot without proximity/dimension checks. Added INV-013 / AIRDROP_REMOTE_REVIEW.md.
- MatWar: start-hack lacks active-war/proximity/faction checks; completion trusts client health and shares IsAirDropHacking; open checks only character + ShapeId; endWar leaves matwar_100 and lock state until next startWar. Added INV-014 / MATWAR_REMOTE_REVIEW.md.
- Static-only; no source patches, build, RAGE exploit reproduction or DB tests. Next: continue remaining container entry points (furniture, warehouse, faction/org stocks, HeliCrash) and close lifecycle/ACL traces; then vehicle control/garage/storage. Avoid duplicates with INV-003, INV-012..014 and VEH-012.


## 2026-11-08 continuation — INV-015 faction stock stale session

- Faction interaction handlers set OnFracStock but no reset was found. openWeaponStock remote only checks current fraction ID and IsFractionAccess rank; no duty, IsOpenGunStock, proximity, dimension or expiring intent. A member with retained rank can attempt remote reopen after prior legitimate access.
- Registered INV-015; created FRACTION_STOCK_SESSION_REVIEW.md and expanded INVENTORY_REVIEW / TEST_PLAN / checklist / coverage / index / roadmap / changelog.
- Static-only; no source patch/build/RAGE/DB tests. Continue with furniture, warehouse, organization and HeliCrash container ACL/lifecycle; avoid duplicates with INV-003 and INV-012..015.

## 2026-11-08 continuation — INV-016 organization stock stale context

- OpenWeaponStock validates InsideOrganizationID only at open. RemovePlayer clears it and exits the HQ without calling ItemsClose/OtherClose; generic inventory mutation remotes continue to rely on InventoryOtherLocationName. Added INV-016 and ORGANIZATION_STOCK_SESSION_REVIEW.md.
- Static-only; no source patch/build/RAGE/DB test. Continue remaining furniture, warehouse and HeliCrash lifecycle checks; avoid duplicates with INV-003, INV-012..016 and VEH-012.

## 2026-11-08 continuation — INV-017 furniture safe stale context

- objectSelected validates safe object, 5m range, InsideHouseID and owner/roommate/burglary access before LoadOtherItemsData. HouseManager.RemovePlayer clears InsideHouseID and exits without ItemsClose/OtherClose; generic item remotes do not revalidate the house/object ACL. Added INV-017 / FURNITURE_SAFE_SESSION_REVIEW.md.
- Static-only; no source patch/build/RAGE/DB test. Continue warehouse and HeliCrash lifecycle, then remaining vehicle/garage storage; avoid duplicates with INV-003, INV-012..017 and VEH-012.

## Remaining inventory container TODOs

- Warehouse: own UUID storage; WarehouseExit does not close the other pane and Stock.Perform lacks IsInPostalStock, but qMain requires active npc_stock quest. Determine whether location persistence is intended; do not call it cross-player theft.
- HeliCrash: server colshape/key-clamp open path; OpenHeliCrash and later item operations lack explicit current box/range binding. Confirm interaction framework and event lifecycle.
- weapon_<SqlId> / CarKey_<SqlId>: LoadOtherItemsData stores location only, not a server-side parent-item intent. Trace parent transfer/drop/delete and revoke semantics before registering a finding.

## 2026-11-08 continuation — INV-018 HeliCrash key clamp

- InHeliCrash installs KeyClampData before GetHealth checks ArmyLockpick. Generic KeyClamp.OnEnd accepts client value and invokes callback without requiring successful keyDown; HeliCrash End sets health from value and can roll unlock at 0 without verifying IsHack owner/lockpick. Failure leaves reusable KeyClampData. Added INV-018 / HELICRASH_KEYCLAMP_REVIEW.md.
- Static-only; no source patch/build/RAGE/DB test. Continue remaining warehouse and parent-item subcontainer traces; avoid duplicates with INV-003, INV-012..018 and VEH-012.


## 2026-11-08 continuation — INV-019 weapon/key-ring parent binding

- Traced ItemsUse → LoadOtherItemsData for `weapon_<SqlId>` and `CarKey_<SqlId>`; LoadOtherItemsData stores only InventoryOtherLocationName. GetLocationName/GetItemData/SetItemData and generic move/stack/use remotes do not revalidate that the parent still exists and remains owned by the caller. SetItemData does not revoke the other pane when parent state changes.
- Registered INV-019 with a conservative medium priority and explicit runtime boundary; created WEAPON_KEYRING_SUBCONTAINER_REVIEW.md and former/new-owner replay tests. No successful cross-owner extraction is claimed.
- Reviewed adjacent delegated callbacks: hotel rent rejects negative price through CanIChange (so the apparent overflow path is not a confirmed free-credit issue); pet rename rechecks OwnerUUID; street-race zero stake remains a policy/abuse question, not a confirmed payout exploit in this pass. Warehouse remains personal-UUID storage with location-policy question; HeliCrash opening/range still needs staging confirmation.
- Static-only; no source patch, C# build, RAGE runtime or MySQL fault injection. Next phase should prioritize source-backed critical money/inventory findings for patch design, while staging/build blockers remain explicit.

43. Street race settlement (`STREET_RACE_REVIEW.md`): added MONEY-051; race now starts only after both stake debits succeed; second-leg failure attempts refund of the first stake and cancels the race. Refund durability, winner payout acknowledgment and duplicate/concurrent callback tests remain open.
42. CEF build/performance (`CEF_BUILD_REVIEW.md`): added PERF-002; production scripts now explicitly set `NODE_ENV=production`, dev explicitly selects development, and Svelte hot reload is disabled only in production. Static config verification only; clean builds, bundle measurements and RAGE UI smoke tests remain pending.
41. Driving school license settlement (`DRIVING_SCHOOL_REVIEW.md`): added `MONEY-050`; all six active license cases now require `Wallet.Change` success before license grant, quest progression, faction credit, logging or success notification. Static source patch; build/RAGE/shutdown tests pending.
40. Metro ticket settlement (`METRO_REVIEW.md`): added `MONEY-049`; widened client-supplied ticket-count arithmetic and require a successful wallet debit before log/success/dimension transition. Source patch is on branch; no build or RAGE failure test yet.
38. Player cash/item trade and tent market (`PLAYER_TRADE_REVIEW.md`): added `MONEY-048`. `ConfirmTrade` moves items before both cash `Wallet.Change` results are checked (they are ignored); `ItemBuy` ignores buyer debit/seller credit and uses unchecked `Item.Price * Value` before item transfer/BattlePass progress. Source-level ordering confirmed; failure/race/overflow impact requires RAGE/MySQL staging. No source patch/build/runtime tests.
37. Phone auction source patch (`AUCTION_REVIEW.md`): `Players/Phone/Auction/Repository.cs` now rejects nonpositive and expired/ended bids, uses widened `long` fee arithmetic, serializes `OnBet` / `End` on the auction object, skips the UUID-zero no-bid refund, and uses a null-safe player lookup so offline DB fallback can run. MONEY-023/024/038 remain open pending C# build, RAGE/DB boundary, failure, concurrency and restart tests; offline refund/payout still lacks a durable idempotent receipt. No runtime test claimed.
