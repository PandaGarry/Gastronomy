# Проверки и результаты

> **Стратегия и обязательные quality gates:** [`REDAGE_MASTER_PLAN.md`](REDAGE_MASTER_PLAN.md). Этот файл хранит конкретные тестовые сценарии и фактические результаты запусков; не помечать тест как пройденный без команды, результата и среды.

Последнее обновление: 2026-11-07. Это baseline текущего исходного снимка; production-тесты не выполнялись.

## Среда

- Node.js: `v22.22.3`
- npm: `10.9.8`
- .NET SDK/MSBuild/Mono: отсутствуют
- MySQL/MariaDB client/server: отсутствуют
- Доступная RAM в sandbox: около 3.8 GiB; большие webpack jobs завершаются OOM/exit 137
- Полный RAGE:MP runtime/server binaries: не включены в рабочий snapshot

## Baseline

| Проверка | Статус | Результат / ограничение |
|---|---|---|
| JSON синтаксис | Пройдено | Проверены 167 JSON-файлов: 167 валидны. Значения секретов не печатались; DB-конфиг локально редактирован. |
| JavaScript syntax | Частично пройдено | Из 337 `.js`: 335 проходят `node --check`. 2 ошибки в файлах, не подключённых из текущих entry points: `src_client/synchronization/sit1asdas.js` (повторное объявление `sitData`) и `src_cef/src/views/player/hudevo/phonenew/map.js` (лишняя запятая перед `;`). Активный `src_client/index.js` и `synchronization/sit.js` проходят. Не исправлял до выяснения назначения старых файлов. |
| Client webpack build | Пройдено в изолированной копии | Временная копия `src_client`; npm install с отключёнными lifecycle scripts; `NODE_OPTIONS=--openssl-legacy-provider`; production bundle собран успешно (webpack 5.112.2). Артефакт не переносился в исходник. Нет upstream lockfile, поэтому это не воспроизводимый pin. |
| CEF npm dependency resolution | Требует исправления | Обычный `npm install` остановлен `ERESOLVE`: `cache-loader@4.1.0` требует peer webpack 4, а manifest фиксирует webpack 5. Установка прошла только с `--legacy-peer-deps`. |
| CEF dependency audit | Высокий риск / требует triage | Временная свежая установка из manifest (не upstream lock) получила 49 npm audit advisories: 5 critical, 21 high, 22 moderate, 1 low. Среди прямых пакетов отмечены `request`, `webpack`, iconfont-related plugins. Это не автоматически означает runtime-эксплуатацию; нужно разобрать, какие пакеты реально используются при сборке/в игре, и составить обновление. |
| CEF/Svelte build | Заблокировано окружением/неполнотой снимка | С неполным snapshot build проходит компиляцию модулей, затем сообщает ошибки из-за намеренно исключённых image/font/media assets (1256 ошибок; также Svelte a11y/deprecation warnings). Для проверки полностью получены assets только во временную папку; production webpack завершился OOM/exit 137 при лимите памяти sandbox. Исходные файлы не менялись. Нужен CI/host с большей RAM и проверка чистого полного набора. |
| C# build | Заблокировано | В среде отсутствуют .NET SDK/MSBuild; проект target `netcoreapp3.1`. Npm/PyPI install не дал доступного SDK. Нужен контролируемый build-agent и проверка совместимости RAGE:MP. |
| C# static syntax parse | Частичный эксперимент | Tree-sitter C# разобрал 558 файлов; полный parse дал error flag для 5 крупных файлов (`Main.cs`, `Chars/Repository.cs`, `Core/Commands.cs`, `Fractions/Manager.cs`, `Jobs/Miner.cs`), но без полноценного compiler/parser triage нельзя отличить грамматические ограничения от реальных errors. Изменённые `IsReadOnlyOpenedTent`/`ItemsMoveStack` и `ItemsMove` snippets отдельно распарсились без syntax-tree errors; это не заменяет compile. |
| SQL import | Заблокировано | Нет MySQL/MariaDB. Файлы имеют MySQL-specific `DELIMITER` stored procedures; generic parser не заменяет настоящий импорт. В test DB ещё не загружались. |
| DB transport/config review | Статический риск | Connection strings отключают TLS (`SslMode=None`), startup выполняет `SET GLOBAL max_connections=500`; оба пункта заведены в `ISSUES.md`, тестовый DB-профиль ещё не выбран. |
| RAGE:MP smoke test | Заблокировано | Не включены runtime/server binaries, полный `client_packages` и тестовый игровой сервер. Не запускал неизвестные бинарники. |
| Нагрузочный тест | Ожидает | Нужны стабильно собираемый staging и согласованный профиль нагрузки/метрики. |

## Правила выполнения

- Не запускать production binaries и не подключать production DB из этого sandbox.
- Сначала статические проверки; SQL — только на одноразовой тестовой БД.
- Любой credential считать скомпрометированным, если он попал в публичный upstream; сменить его у владельца.
- Сохранять версии toolchain, команды, exit status и ограничения; dependency audit проводить на зафиксированном lockfile.
- Build, успешный только с временными флагами/неполными зависимостями, помечать experimental, не выдавать за воспроизводимый release build.

## Следующие наборы тестов после подготовки staging

1. **Auth/passwords:** legacy hash verify, безопасный KDF rehash/reset, Unicode, неверный пароль, повторные/параллельные попытки, отсутствие секретов в логах.
2. **Queue/concurrency:** много одновременных auth/connect/disconnect событий при заполненных слотах; нет duplicate entry, lost player, race exception или обхода rate limit.
3. **Economy/payments:** только sandbox endpoints; сценарии `ECONOMY_REVIEW.md` + `PAYMENTS_REVIEW.md` + `ROULETTE_REVIEW.md` + `CASINO_REVIEW.md` + `BLACKJACK_REVIEW.md` + `SPIN_REVIEW.md` + `HORSES_REVIEW.md` + `LUCKYWHEEL_REVIEW.md`: offline/online RedBucks receiver, DB failure/rollback, replay transfer callback, concurrent money-worker producers, receipt duplicate/crash-before-ack, multi-worker overlap, promo dedupe, DonatePack invalid ID/restart/delayed payment, malformed ATM args и overflow; roulette buy/open negative/zero/over-limit counts, checked price overflow, discount and item/wallet consistency; NewCasino Roulette forged last-bet cancel around `table.Process`, exposed outcome payload, disconnect/death/timeout within and outside the five-second refund grace, exactly-once round settlement; Blackjack invalid table/seat and forged-coordinate joins, repeated setBet, out-of-turn/invalid split/double, server max-bet and payout overflow cases; Spin loss/win leave within two-second reveal refund window, slot forged coordinates, zero/over-limit bets and calculated RTP; Horses disconnect/death after `START_RACING` reveal before 3-second refund deadline, forged remote bet/session, zero/over-limit/invalid horse, payout overflow and scheduler race/exception recovery; LuckyWheel forged remote claim outside casino, global cooldown/parallel replay, inventory/garage grant failure and async-save/reconnect exactly-once cases. Проверять exactly-once ledger, affected rows, cache consistency и отсутствие ложных success notifications; в `BuySet` искусственно заполнять inventory перед каждым шагом выдачи и сверять debit/full reward/compensation; legacy `/dice`: acceptance after movement/cuff/death/config changes, self-target policy, deterministic repeated ties, winner credit/debit failure near int bounds and exactly-once wager ledger; lottery: forged shop callback after leaving/changing dimension, wallet debit/ticket insert failure and restart, online/offline winner payout failure, stale round-ID write, repeated payday callback and exactly-once draw/payout reconciliation; BattlePass ordinary/premium `take`/`takeAll`, fail each item/money/RedBucks/VIP grant, crash after grant before marker persistence, retry/reconnect and verify exactly-once reward/receipt; `buyLvl` invalid indexes/bounds/cost and mission reward/skip failure cases per `BATTLEPASS_REVIEW.md`; Sapper direct negative/zero/over-limit bet, fake win index, repeat/early exit and `SappeEnd` without active round as detailed in `SAPPER_REVIEW.md`.
4. **Inventory:** direct remote fuzz для отрицательных/нулевых/over-source counts и same-slot; все transfer/use/drop из чужих tent/read-only containers; stack/carry caps/full-source move; tampered/duplicate NoteCreate IDs; roulette negative case-open count and `RemoveIndex` no-op for nonpositive count; reconnect; затем DB outage/restart и сверка каждого item SQL ID/count. Подробно: `INVENTORY_REVIEW.md`.
5. **DB lifecycle:** чистый импорт, повторный импорт только если заявлен idempotent, backup→restore, least-privilege DB user, TLS.
6. **Quest/progression remotes:** `server.quest.clear` without/with/replayed interaction and verify task 97 daily/week/mission progress; `server.take_quest_item` wrong/no Granny stage, forged index, wrong location/dimension, sequential/parallel calls, movement/disconnect during callback, full inventory and DB insert failure; Defender Day Dada/Edward forged update remotes and verify false `Complete`; exercise UI `perform`/`take` dispatch and confirm expected Dada→Edward→Zak route (currently generic dispatch appears disconnected), wrong line/location, repeat and objective/reward state; admin `SkipQuest` with equal/different quest rows on admin/target plus invalid/disconnected target; Valentine/Defender NPC deployment and generic dispatch; wedding one-sided divorce prompt then spouse disconnect before confirm, invalid/stale target IDs, duplicate callbacks, wallet debit failure and marriage DB/memory convergence. Granny Bear quantity 2-vs-5 and active quest/NPC scope require gameplay-owner confirmation. Matrices: `QUESTS_REVIEW.md`, `WEDDING_REVIEW.md`.
7. **Release packaging:** повторяемые clean builds, `meta.xml` указывает на фактический Release artifact, правильные client bundles/assets, rollback artefacts.
8. **Time rewards/achievement state:** на disposable DB проверить дневные пороги 120/180/240/300/480 минут и месячный 18,000-minute reward. Вводить crash/DB failure после RB queue flush, warehouse insert и до/во время `Characters.Time` save; reconnect/replay должен дать ровно один durable reward per threshold/period, без потери. Одновременные tick/save и repeated login покрыть race. Для `Achiev` прогнать null/invalid/empty/short/canonical JSON lengths, сохранить прежние true flags, проверить индексы 16/17/18/21/22/23/24/27 и что malformed character не прерывает обработку других игроков; проверить `Time` SQL NULL, JSON `null`, malformed/empty values и valid legacy JSON, load→tick→save→reload; null-time character не должен блокировать minute tick/rewards остальных игроков. Проверить save→reload. Подробно: `ONLINE_REWARDS_REVIEW.md`. Нужны MySQL fault injection и RAGE staging; в текущем sandbox эти тесты недоступны.
9. **Taxi mileage billing/progression:** в test ride проверить spoofed `server.vehicle.updateMileage` при текущем taxi vehicle ID с `0`, `-1`, `int.MinValue`, boundary, `100000`, `300000`, `int.MaxValue`; assert negative values are rejected before `(uint)` conversion and cannot wrap `Centimeters`, повтором быстрее client 10s interval, passenger funds/exits and concurrent callbacks. При активных daily/weekly entries/mission IDs 2/59/159/95 без подтверждённого server-side distance delta fare и progression не должны изменяться; verify atomic debit/credit, progress after successful receipt, mileage cache/persistence and restart. Подробно: `TAXI_MILEAGE_REVIEW.md`; нужен RAGE staging/disposable accounts.
10. **Passport/BattlePass task 101:** вызвать `passport(self)` напрямую и `acceptPressed`; self request должен быть отклонён/не начислять ID101, а reset/expiry/duplicate request — безопасны. Контроль: другой target, тот же dimension, within/outside 2m, moved/different dimension before accept; проверить request cleanup и именно один progress per valid distinct show. Подтвердить entity argument marshalling на RAGE staging. Подробно: `DOCUMENTS_REVIEW.md`.
11. **Vehicle repair intent:** direct `dialogCallback("RepairMyVeh", true)` вне repair site, с/без active mechanic, no pending intent, while in eligible/ineligible vehicles, insufficient/exact funds, server-stop and injected wallet failure. Для valid configured site контроль one charge/one repair; вне scope/disabled feature должен быть no-op; проверять health, balance, GameLog, notification. Сверить фактическую repair policy/active deployment. Подробно: `VEHICLE_REPAIR_REVIEW.md`; нужен RAGE staging.
12. **Vehicle garage remote (`VEH-002..003`):** on disposable RAGE staging with two test houses and distinct owners/roommates, directly invoke `server.garage.parking` using own, roommate, foreign, nonexistent, and revoked-roommate `autoId` values for active, garage-access, and unspawned vehicles. Verify foreign attempts cannot mutate either garage `CarSlots`, vehicle spawn/local access/dimension/position, or owner recovery; test full/occupied-slot swap, concurrent requests, save/restart/load cleanup and normal household flow. Fuzz indices `int.MinValue`, `-2`, `-1`, `0`, `MaxCars-1`, `MaxCars`, `int.MaxValue`; invalid values must be no-ops, and corrupted serialized keys must be sanitized without aborting unrelated garage spawns. Record whether IDs can be enumerated and exact victim impact; do not infer theft/duplication from source alone. Static review: `GARAGE_REVIEW.md`; C# build, MySQL test DB and RAGE runtime are prerequisites.
13. **Vehicle action/entity remotes (`VEH-004..005`):** from two disposable accounts, invoke `server.vehicle.action` with own/shared/foreign aircraft plates for `tune`, `repair`, `evac`, `gps`, `spawn`, `sell`, `key`, `changekey`; test NPC distance, active/stored, locked, occupied and ticketed states. Foreign targets must not be moved/unlocked/repaired/recreated or have location disclosed unless policy explicitly permits key-holder actions. Inject evac wallet failure/server stop and verify no unpaid relocation. For `server.vehicle.tuning`, determine whether an arbitrary network vehicle entity can be marshalled; try current, other-player, stale/deleted and invalid entities while caller is/is not in a vehicle. Disable if unused; otherwise only the verified occupied authorized vehicle may enter tuning. Verify dimensions, positions, seats, access, customization, balances and persistence across exit/restart. Static review: `VEHICLE_ACTION_REVIEW.md`; requires RAGE staging and disposable accounts.
14. **Government vehicle sale (`VEH-006`, `MONEY-013`):** create a pending government sale as the owner, transfer/change the vehicle holder before confirmation, then invoke yes/no/repeated callbacks; stale owner must not receive money or delete the new owner's car. Test forged callback without intent, ticket added during intent, concurrent confirmation and normal sale once. With disposable DB fault injection, fail the async vehicle-row delete after wallet update succeeds, restart, and verify no stale vehicle or second payout; also fail wallet persistence and verify sale retry/receipt recovery. Reconcile in-memory vehicle map, DB row, holder, garage slots and character balance. Static review: `VEHICLE_SALE_REVIEW.md`; requires MySQL fault injection and RAGE staging.
15. **Vehicle synchronization (`VEH-007..008`):** on RAGE staging, call `VehStream_SetVehicleDirt` and `VehStream_SetIndicatorLightsData` from on-foot, passenger and driver contexts with current, foreign, stale/deleted entity args; test dirt `NaN`, infinities, negative, zero, 15 and over-max. Unauthorized/invalid payloads must not alter another vehicle's shared/local/cache/DB state; verify save/restart behavior. Call `VehStream_RadioChange` as driver/passenger/on-foot with valid/off/out-of-range station indexes; enforce the confirmed passenger policy and verify shared station/client consistency. Static review: `VEHICLE_SYNC_REVIEW.md`.
16. **Organization fleet vehicle remotes (`MONEY-014..015`):** use test organizations and ranks to exercise fleet list, rank update, GPS, evacuation and sale with authorized/unauthorized members, own/foreign organization plates, stale/missing entities, occupied/ticketed/garage states and min-rank boundaries. Inject wallet-save and `Orgvehicles.DeleteAsync` failures around a confirmed sale, then restart and reconcile sale receipt, balance, DB row, org cache/Used garage slot and vehicle entity; no double payout. For evacuation, force `Wallet.Change` to reject (including server-stopping state) after all prior validation; vehicle must not be moved without a committed $20 debit. Static review: `ORG_VEHICLE_REVIEW.md`; requires disposable DB and RAGE staging.
17. **House resident ACL/persistence (`PROP-001..002`):** owner and roommate accounts directly invoke `server.house.resident.access` for self, another roommate, owner and missing names with `isFurniture`/`isPark`; invoke `.dell` against another roommate and owner. Only owner/delegated ACL may change resident permissions or evict; test downstream furniture/safe and garage access plus garage slot cleanup. Exercise invite accept, toggles, eviction and self-leave, restart with/without an unrelated dirty house mutation, and DB save failures; verify runtime `Roommates`, serialized DB, garage slots and access converge with no stale roommate resurrection. Static review: `HOUSE_RESIDENT_REVIEW.md`; requires RAGE staging and disposable DB.
18. **House sale persistence (`MONEY-016`):** owner direct sale callback with/without an opened prompt, stale owner change, inside-garage rejection, repeated/concurrent confirmation; then inject restart/DB failure between wallet persistence and dirty-house save (including the 30-second worker interval and `House.Save` failure). Verify one committed sale/payout only, no resurrected owner/roommates, and consistent garage/bank state. Static review: `PROPERTY_SALE_REVIEW.md`; requires MySQL fault injection and RAGE staging.
19. **House purchase (`MONEY-017`):** buy only through current server-side `HouseID`; forged remote without the entry colshape, unavailable/auction/zero-price/max-house limit, competing buyers; inject `Wallet.Change=false` during server stopping and DB failure between debit and owner save. Verify no owner is committed without exactly one successful debit; reconcile cash, house balance, garage, notifications and restart state. Static review: `PROPERTY_PURCHASE_REVIEW.md`; requires RAGE staging and disposable DB fault injection.
20. **Player house transfer (`MONEY-018`):** accept/reject a valid offer, forged callback without server-side offer, seller ownership change and buyer acquiring another house before acceptance; repeat/concurrent accept; simulate buyer `Wallet.Change(-price)` rejection during shutdown and failure after buyer debit/seller credit/owner save. Verify no seller payout or title change without successful debit, exactly-once balances/title, and consistent house/garage state after restart. Static review: `PROPERTY_TRANSFER_REVIEW.md`; requires RAGE staging and disposable DB fault injection.
21. **House tax/repossessions (`MONEY-019`, `PROP-003`):** deposit house tax, allow successful bank save, then run hourly tax without other account/house mutation and restart; confirm tax debits persist. Force negative house balance for online owner, restart before unrelated house save; confirm owner/roommates remain cleared and bank is zero. Also test offline owner, DB failures, worker ordering, dirty flags and city tax ledger. Static review: `PROPERTY_TAX_REVIEW.md`; requires disposable MySQL and RAGE staging.
22. **ATM remote intent/location (`MONEY-004`):** normal ATM cash deposit/withdrawal; direct `atmCB(type=1,index=1)` then `atmVal` at a remote location; leave range after opening; wanted/demorgan and no-account states; repeat/close/stale intent and server stopping. Verify unauthorized withdrawals are rejected without balance changes and normal ATM access remains functional. Static review: `ATM_REVIEW.md`; requires RAGE staging and confirmation of intended policy.
23. **Bank transfer confirmation replay (`MONEY-003`):** transfer once, replay `dialogCallback("AcceptBankTransfer", true)`, cancel/stale intent replay, no pending tuple, insufficient balance, cooldown and destination deletion. Verify exactly one debit/credit, clear pending state on all outcomes, and cooldown applies at settlement. Static review: `BANK_TRANSFER_REVIEW.md`; requires RAGE staging and policy confirmation.
24. **Business phone orders (`MONEY-022`, `MONEY-025`):** create single/bulk order, persist caller bank state while `biz.IsSave` is false, restart and verify order/debit convergence; cancel persisted order and verify refund/order removal remain paired. Inject missing bank account/exception during cancel refund: order must remain recoverable and no success notification/log may be committed until credit succeeds. Change price and restart; inject separate bank/business save failures. Directly invoke `server.phone.business.addOrder` with `int.MinValue`, `int.MaxValue`, `2,147,483,598` and safe remaining-capacity boundaries against a stocked type-0 product; rejected over-limit values must not change bank, `Zatratq`, product, order or logs. Static review: `BUSINESS_ORDER_REVIEW.md`; requires disposable DB/RAGE staging.
25. **Phone auction first bid/settlement (`MONEY-023..024`, `MONEY-038`; source patch pending validation):** first bid with `LastBetUUID=0` for each auction type must not call refund; overbid while previous bidder is offline; auction end while seller is offline for house/business/vehicle; verify offline DB fallback and exactly-once asset handoff. Inject exception after debit, failed online/offline refund and DB update failure. Attempt stale/expired bid before end tick and after `End` but before the 30-second save worker removes the lot; run concurrent bid/end and assert shared lock prevents post-end settlement. Directly invoke bid remote with `int.MaxValue`, `int.MaxValue-1`, zero, negative and `int.MinValue`; verify fee is calculated in positive `long` and `Bank.Change` receives a debit, never a credit; rejected inputs must not mutate balance/state/logs. Agree a policy max bid before enforcing a cap. Static review/patch: `AUCTION_REVIEW.md`; requires C# build, RAGE and disposable DB staging.
26. **Property auction lifecycle (`PROP-004..005`):** fail the async auction-row insert after listing a house/business; restart and verify owner/asset/listing consistency. Let an offline character win a business auction; verify owner and `BizIDs` persist and phone ACL works after reconnect. Static review: `AUCTION_REVIEW.md`; requires DB fault injection and RAGE staging.
27. **Other-item auction lifecycle (`INV-011`):** direct-call `server.phone.auction.add` for Other with valid, foreign, nonexistent and stale SQL item IDs; end auctions with and without bids; test online/offline seller and winner, DB failure during item move/grant/return, and restart before/after end. Verify the item is transferred exactly once to the winner or returned to the seller, never stranded in auction storage. If the feature is not supported, the server must reject Other before changing inventory. Static review: `AUCTION_REVIEW.md`; requires disposable DB and RAGE staging.

## Business subsystem regression additions

- **Business retail purchases (`STOCK-002`, `MONEY-022`):** inject missing owner bank / Bank.Change=false after takeProd decrements stock; assert exact rollback and no customer charge/grant. Inject Wallet.Change=false and AddNewItem failure/partial result in 24/7, weapon/ammo/component, clothes, barber, pet, carwash and petrol flows; assert no free item, lost payment or unbalanced owner revenue. Test missing product name, nonpositive/overflow quantities, replay/concurrency and restart without unrelated business dirtying. Static review: BUSINESS_RETAIL_REVIEW.md; requires disposable MySQL/RAGE staging.
- **Business government sale (`MONEY-026`):** test direct/replayed dialogCallback("BIZ_SELL_TOGOV", true) with current/stale/non-owner BizIDs. Inject Wallet.Change=false/exception and assert no owner release, BizIDs removal, success log or notification without confirmed proceeds. Inject hard crash after wallet+business owner writes but before character Biz list save; reconnect, load via stale ID, invoke callback, and verify owner check/receipt prevents repeat payout or management access. Fail each wallet/business/character write and compare DB Owner, characters.Biz, wallet and receipt. Static review: BUSINESS_SALE_REVIEW.md; requires disposable MySQL/RAGE staging.
- **Business bank deposit (`MONEY-039`):** select a business account at ATM, inject Bank.Change=false/exception after successful Wallet.Change and assert wallet compensation is attempted exactly once, compensation failure is critically logged, and no success log/message/UI refresh occurs. Then test durable receipt/restart recovery (not implemented), replay, stale BizIDs, invalid index and amount boundaries. Test stale BizIDs, invalid index, zero/negative/int boundary values and direct remote away from ATM. Static review: BUSINESS_BANK_REVIEW.md; requires disposable MySQL/RAGE staging.
- **Business tax/repossessions (`MONEY-040`, `MONEY-041`):** run payday with a solvent business and verify tax debit survives bank-worker flush/restart; inject bank DB failure. For insolvent business inject online Wallet.Change=false/exception and offline character DB update failure/crash; assert owner compensation is durable/exactly once before ownership release and bank reset. Static review: BUSINESS_TAX_REVIEW.md; requires disposable MySQL/RAGE staging.
- **Player-to-player vehicle sale (`MONEY-042`):** inject seller Wallet.Change=false/exception and seller balance at/near Int32.MaxValue where a credit may be rejected; assert no ownership transfer/success without confirmed seller proceeds. Inject SaveHolder DB failure/delay after buyer debit and seller credit, restart and reconcile holder, wallet, garage and receipt. Replay BUY_CAR before/after every settlement boundary; test disconnect, stale holder, missing vehicle, full garage and concurrent offers. Static review: VEHICLE_PLAYER_SALE_REVIEW.md; requires disposable MySQL/RAGE staging.
- **Trucker order lifecycle (`JOB-001`, `JOB-004`):** two Trucker characters, one valid order; test on-duty owner driver, off-duty passenger in another Trucker work vehicle, non-Trucker passenger, no/mismatched rental, on-foot, pickup radius, cancel/disconnect. Invalid cargo pickup must not set Order.Taked or retain OrderData.Order. At delivery inject Wallet.Change=false and exception; order/stock must remain recoverable or a durable pending-payout receipt must be written, with no false success log/notification. Test duplicate checkpoint entry, wallet boundary, restart/retry and exactly-once payout/order completion. Static review: BUSINESS_DELIVERY_REVIEW.md; requires RAGE staging.

29. **Contact BattlePass tasks (`PROG-009`):** activate tasks 76/78, direct-repeat-add an existing contact and update a nonexistent number; neither may advance progress. A valid create/edit should advance only after one successful mutation; repeat/replay must not overcount. Static review: `PHONE_MESSAGES_REVIEW.md`; requires RAGE staging.
30. **SMS CEF input/history (`SEC-007`, `PHONE-001`):** direct-call `server.phone.sendMsg` with inert quote/statement delimiters, raw HTML, malformed `type` and max-sized text to a test recipient with chat open and later from stored history. Verify no CEF script or HTML executes and text renders literally. Concurrently append during worker snapshot/clear and inject DB failures after each insert; verify every message/read receipt is durably committed once or retryable after restart. Static review: `PHONE_MESSAGES_REVIEW.md`; requires disposable RAGE/CEF and MySQL staging.
31. **Phone sound setting bounds (`PHONE-002`):** direct-call bell/sms setting remotes with `-1`, exact array bounds and very large integers; then trigger incoming call, non-selected incoming SMS, selected-chat SMS and teardown/reconnect. No array exception, orphaned call state or lost queued history; valid selectors remain functional. Static review: `PHONE_CALL_TINDER_REVIEW.md`; requires RAGE staging.
32. **Phone-info value bounds and gallery URL (`PHONE-003`):** direct-call wallpaper/contact/blacklist/gallery remotes with near-limit and oversized strings/counts, including a URL over the `TEXT` value boundary. Verify rejection before mutation and valid persistence; force a DB save failure and reconnect to confirm unrelated phone fields remain intact. Open gallery with controlled allowed/blocked URLs and observe CEF requests; verify scheme/host allowlist and no unexpected requests. Static review: `PHONE_CALL_TINDER_REVIEW.md`; requires disposable MySQL/RAGE/CEF staging.
33. **Tinder action idempotency/privacy (`PHONE-004`):** create two test profiles with mutual likes, then replay direct positive/negative actions and count each participant’s match events, SMS rows and like entries. Probe self-target, invisible profile and type mismatch; enforce confirmed product policy. Static review: `PHONE_CALL_TINDER_REVIEW.md`; requires RAGE staging.
34. **Tinder avatar URL/CSS (`SEC-008`):** save only on disposable accounts and render in list, profile and matches against a controlled request logger. Verify unsupported schemes/hosts, CSS delimiters and oversized values are rejected; confirm no request reaches a disallowed host and no HTML/script executes. Static candidate: `PHONE_CALL_TINDER_REVIEW.md`; compiled CEF/CSP staging required.
35. **Phone News payment/persistence (`MONEY-027`):** charge a valid advert on disposable accounts; inject SQL constraint/connect failures and disconnect after debit but before insert; verify exactly one durable advert+receipt or exact compensation, no success/progress without commit, and replay cannot debit twice. Include max-length/overlong `link` boundaries and concurrent direct submissions. Static review: `PHONE_NEWS_REVIEW.md`; requires MySQL/RAGE fault injection.
36. **Published News image URL (`SEC-009`):** submit controlled links containing valid image suffix and CSS delimiters, have a test LS News moderator approve on staging, then open feed from separate clients with request logging. Verify only trusted HTTPS media URLs load; no disallowed host, CSS declaration injection or script execution. Static candidate: `PHONE_NEWS_REVIEW.md`; compiled CEF/CSP/RAGE staging required.
37. **SMS image resource allowlist (`SEC-010`):** direct-call `sendMsg` with `type=img`, an image-like trusted URL, arbitrary HTTPS host, local/private address, invalid schemes and malformed types. Observe network requests in test CEF for active chat and stored history; only approved media origin should load. Static review: `PHONE_MESSAGES_REVIEW.md`; requires isolated CEF/RAGE staging and a request logger, not production hosts.
38. **SIM ownership/persistence (`PHONE-005`):** on disposable characters, use/reassign/remove distinct SIMs and a controlled duplicate SIM; inject failure/crash between character.Sim write, inventory item write and map update. Verify one number maps to one UUID, item/card and installed state reconcile after reconnect/restart, failed removal preserves either the SIM or its card, and legitimate replacement remains exactly-once. Static review: `PHONE_SIM_REVIEW.md`, linked to `INV-004`; requires MySQL/RAGE fault injection.
39. **Phone animation intent (`PHONE-006`):** invoke `server.phone.anim` directly with 0, 1 and invalid IDs while camera/phone is closed; observe only intended nearby clients and interruption/cleanup. Confirm whether cosmetic spoof is allowed; if not, test server-owned camera intent and rate limits. Static review: `PHONE_SIM_REVIEW.md`; requires RAGE staging.
40. **LS News moderation settlement (`MONEY-028`):** approve a queued advert, inject failure/crash after commission, completion queue, public NewsList, progress and before/after `advertised.Status` update. Restart and replay moderation; verify commission, publication and progress occur exactly once or recover consistently. Test failed `Bank.Change`, two editors and stale pending rows. Static review: `PHONE_NEWS_REVIEW.md`; requires disposable MySQL/RAGE fault injection.
41. **Phone taxi/mechanic dispatch claim (`JOB-002`):** direct-call `taxijob.take`/`mechjob.take` with already-claimed UUIDs and several outstanding orders per worker; race two workers on one order. Verify one atomic owner, no overwritten timer references, old timers stop and cannot notify/progress after cancel/reassign/disconnect. Check BP reward IsDone behavior and customer order restoration. Static review: `PHONE_DISPATCH_REVIEW.md`; requires multi-client RAGE staging.
42. **Phone dispatch flood (`JOB-003`):** repeatedly direct-call order/cancel for taxi and mechanic with multiple worker clients; record fan-out, caller coordinates and event rate. Verify cooldown/rate limit is enforced server-side and legitimate retry/reconnect works; separately measure any framework-level throttling. Static review: `PHONE_DISPATCH_REVIEW.md`; requires RAGE staging.
43. **House furniture recipe consumption (`INV-009`):** on disposable owner account, direct-call `server.gamemenu.inventory.move` to put each recipe material in `fastSlots`/other character sub-locations, then call `server.furniture.buy(name, type=1)`. Verify all required materials are consumed exactly once or request is rejected, and furniture is never created after failed removal; test partial stacks, repeated calls, cancellation and restart/worker failures. Re-test ordinary UI inventory restrictions and recipes in `HouseFurniture.NameModels`. Static review: `HOUSE_FURNITURE_REVIEW.md`; requires RAGE/MySQL staging.

44. **Ammo return remote (`INV-010`):** on disposable RAGE accounts, direct-call `server.weapon.ammoin` with no active weapon, mismatched valid hash, 0, -1, exact clip maximum, clip maximum + 1, 1,000 and `int.MaxValue`. Repeat with empty/partial/full inventory; audit all ammo stacks and world drops. Only a server-authorized removed clip may be returned once; compare regular holster, weapon switch, death and retry paths. Static review: `WEAPON_REMOTE_REVIEW.md`; RAGE/inventory staging required.
45. **Seatbelt BattlePass progress (`PROG-010`):** activate task 86, invoke `beltSelected` directly on foot, on supported/unsupported vehicle classes, and with both Boolean values/replays. Invalid contexts and unfastening must not progress; a legitimate server-validated false→true transition should progress exactly once. Static review: `SELECTING_REMOTE_REVIEW.md`; requires RAGE staging.

46. **Car showroom payment and test-drive cleanup (`MONEY-029`):** on disposable RAGE/DB accounts, direct-call `carroomBuy` with a valid showroom/product but invalid/empty color for personal and organization purchase; compare wallet, dealership stock, organization fleet, dimension and selection state. Exercise `testDrive` with invalid color/model and entity-create failure; assert no untracked vehicle or player stranded in dimension and that any debit is compensated. Test all valid colors/models as controls and retry behavior. Static review: `CARROOM_REVIEW.md`; runtime/fault injection required.

47. **Festive coin→RedBuck exchange (`MONEY-030`):** on disposable RAGE accounts, place EventCoins in `inventory`, `fastSlots` and other character locations; direct-call `inputCallback("sell_festive", "3")` and test 498, 500, nonmultiples, insufficient totals and repeated replay. Verify exact debit equals the exchange amount before any RedBuck credit; replay/no-removal must not credit. Also verify ordinary UI/valid exchange. Static review: `MAIN_REMOTE_REVIEW.md`, dependent slot route `INV-003`; requires RAGE/inventory staging.
48. **Government fuel-limit authorization (`MONEY-031`):** direct-call each `fuelcontrol_*` callback as nonleader, wrong faction rank and City Hall leader with zero, negative, configured max and `int.MaxValue`; inspect all faction `FuelLimit/FuelLeft` values, DB persistence and next-day reset/refueling. Unauthorized/over-cap requests must be no-ops. Static review: `MAIN_REMOTE_REVIEW.md`; requires disposable RAGE/MySQL staging.


## MONEY-033 — ticket settlement regression matrix (pending staging)

- [ ] Cash-only debit succeeds; exactly one City Hall/officer payout.
- [ ] Bank-only debit succeeds; exactly one City Hall/officer payout.
- [ ] Both cash and bank debits fail: no recipient credit and no fraction balance change.
- [ ] Duplicate and concurrent `TICKET` confirmation: exactly one settlement.
- [ ] Invalid/stale issuer, target disconnect and reconnect: no stale or cross-player settlement.
- [ ] Inject crash after debit, after fraction credit and after officer credit; restart reconciliation must produce exactly one complete settlement.
- [ ] Verify the actual `targetSessionData.TicketsData` is consumed/cleared after accept or decline.

No runtime tests have been run; execute only on disposable RAGE:MP/MySQL staging accounts.


## MONEY-034 — gang drug purchase overflow regression (pending staging)

- [ ] Empty vehicle rejects amounts above configured capacity; no balance or inventory mutation.
- [ ] Partially filled vehicle rejects `int.MaxValue` and all addition-overflow boundaries.
- [ ] Price multiplication boundary values and `int.MaxValue` never produce negative/zero price or increase faction funds.
- [ ] Valid minimum/maximum quantities debit exactly `amount * configuredPrice` and grant exactly the same quantity.
- [ ] Insufficient faction funds, full slots, partial AddNewItem result and injected persistence failure do not create an unbalanced transaction.
- [ ] Concurrent/replayed direct callbacks settle once; restart reconciliation preserves exact balance and item count.
- [ ] Inventory item counts remain positive, within stack limits, and within vehicle capacity in memory and SQL.

No runtime exploit reproduction or DB test has been performed; use disposable RAGE:MP/MySQL staging only.


## MONEY-035 — faction money withdrawal settlement (pending staging)

- [ ] Wallet credit succeeds: faction stock decreases by exactly the amount and player wallet increases by exactly the amount.
- [ ] Wallet credit returns false/throws: faction stock remains unchanged; no misleading success notification/log.
- [ ] Test wallet balance near integer limits and missing/disconnecting character state.
- [ ] Concurrent and replayed withdrawals settle exactly once; restart reconciliation preserves both balances.

## STOCK-001 — faction and vehicle inventory grant consistency (pending staging)

- [ ] Zero free slots: AddNewItem failure does not debit faction/organization stock.
- [ ] Mixed vehicle inventory with fewer free slots than requested: partial insertion is detected and stock is debited only by actual inserted quantity, or the whole operation rolls back.
- [ ] Fragmented stacks and exact stack boundaries preserve item count and stack limits.
- [ ] SQL insert/update failure, disconnect and restart do not produce stock/item mismatch.
- [ ] Concurrent requests cannot overspend stock or duplicate items.
- [ ] Repeat for materials, drugs and medkits; verify the commented-out medkit free-slot path is replaced by authoritative insertion result.


## Organization stock parity — MONEY-035 / STOCK-001 (pending staging)

- [ ] Organization money withdrawal: Wallet.Change false/exception must not debit organization money.
- [ ] Organization money deposit: failed wallet debit must not credit organization money.
- [ ] Organization item withdrawal: failed/partial AddNewItem must not debit organization stock.
- [ ] Organization item deposit: failed/partial Remove must not credit organization stock.
- [ ] Test simultaneous stock requests and organization membership/status changes; verify exactly-once balance/item deltas.


## MONEY-036 — wallet / database money-width contract (pending decision and tests)

- [ ] Confirm canonical maximum: current generated `characters.money` is `int(11)` while `CharacterData.Money` is `long`.
- [ ] At Int32.MaxValue-1 and Int32.MaxValue, test positive credits that cross the cap; reject without wrap and require caller compensation/no false success.
- [ ] Test negative debits at 0, 1 and Int32.MaxValue; no negative balance or integer wrap.
- [ ] Verify create, normal character save and MoneyUpdate worker round-trip at the selected maximum. If migrating to BIGINT, include >Int32 values through every persistence path.
- [ ] Test every Wallet.Change call-site category (bank/ATM, faction/org stock, jobs/rewards, player trades, vehicles/business/casino) for ignored false return and side-effect ordering.
- [ ] Save/restart preserves exact 64-bit balance; DB column and serialization width are verified.


## MONEY-037 — player-to-player house sale (pending staging)

- [ ] Normal sale: buyer debit, seller credit and ownership transfer settle exactly once.
- [ ] Inject buyer Wallet.Change false/exception: seller receives nothing; house ownership and pending offer remain recoverable/unchanged.
- [ ] Inject seller Wallet.Change false/exception after buyer debit: buyer is refunded or settlement resumes durably; ownership does not silently transfer without seller payment.
- [ ] Duplicate/concurrent accept, offer replay, cancellation, disconnect and stale seller ownership are idempotent.
- [ ] Crash/restart after each settlement step reconciles money and ownership exactly once.
- [ ] Money log contains distinct buyer/seller UUIDs and settlement correlation ID.
- [ ] Repeat at MONEY-036 selected maximum and DB round-trip boundaries.

- **Business government acquisition (`MONEY-043`):** inject `Wallet.Change=false`/exception after `CanIChange` preflight (concurrent balance change, shutdown gate, controlled failure). Assert owner, buyer BizIDs, stock, orders and business bank remain unchanged; no success log/message. Test already-owned/stale business, duplicate/concurrent command, restart after each write boundary.
- **Player-to-player business transfer (`MONEY-044`):** independently fail buyer debit, seller credit, buyer BizIDs save, seller BizIDs save and business owner save. Assert all-or-nothing settlement or durable pending receipt with exactly-once retry; never report success with partial payment. Replay confirmation, concurrent confirmations, offer replacement/expiry, changed owner, disconnect/restart and buyer business-limit boundaries. Static review: `BUSINESS_OWNERSHIP_REVIEW.md`; requires disposable MySQL/RAGE staging.

- **Government fleet fuel allowance (`MONEY-045`):** with FuelLeft below/equal/above total cost, assert insufficient allowance rejects before stock, fraction, City Hall or vehicle fuel mutation. Test unit price > 1, request quantity clamp, recalculated total, zero/negative/oversized level, tank/stock limits, duplicate/concurrent remote, daily reset and restart between settlement writes. Specifically assert that the clamped quantity drives both stock reservation and final vehicleLocalData.Petrol; current code computes tfuel and price before clamp. Static review: `BUSINESS_FUEL_REVIEW.md`; requires disposable RAGE/MySQL staging.

- **Petrol remote context (`VEH-009`):** interact with a non-fuel business, leave, then call petrol directly; interact with a fuel station then move away/change dimension/swap vehicle and replay. All invalid contexts must leave vehicle fuel, stock, wallet, owner bank, fraction FuelLeft and City Hall balance unchanged. Confirm valid in-range station flow. Static review: `BUSINESS_FUEL_REVIEW.md`; requires RAGE staging.

- **AutoMechanic service settlement (`JOB-005`):** independently inject buyer debit and mechanic credit false/exception for repair and fuel delivery; assert no free service, unpaid mechanic, false success or quest progress. For buyFuel, fail wallet debit after takeProd and assert no increase in mechanic fuel reserve. Test stale/replaced offers, wrong buyer, movement, vehicle swap, work-duty changes, duplicate callback, disconnect and restart at each settlement boundary. Static review: `MECHANIC_SERVICE_REVIEW.md`; requires disposable RAGE/MySQL staging.

- **Admin business deletion (`BUG-002`, `MONEY-047`):** delete government-owned and privately owned businesses with online/offline owners. Inject null player lookup, missing character, Wallet.Change=false/exception, SQL delete/update failure and crash between writes. Assert DB row, BizList/world objects, owner BizIDs, wallet and compensation receipt converge after restart; no success notice before committed deletion.


## PET-001 — pet-shop remote context and one-shot purchase (pending staging)

- [ ] Direct/replayed petshopBuy without active pet-shop intent; stale TempBizID from every non-pet business type must not authorize the action or teleport the player.
- [ ] Require Type==14, proximity, dimension, current session and one-shot intent; test moving away, changing dimension, disconnect and context replacement.
- [ ] Test all nine server-allowed pet names and arbitrary/empty/oversized values; invalid model strings must not be persisted or passed to client mp.peds.new.
- [ ] No house, unsupported house type and no PetPosition must reject before teleport/payment.
- [ ] Missing food product, zero/negative price, stock shortage, owner-bank failure and customer Wallet.Change=false/exception must leave house, character, stock and balances unchanged.
- [ ] Duplicate/concurrent confirmation and replay after success must result in at most one charge and one pet-state mutation; restart after each settlement boundary must reconcile exactly once. Static review: PETSHOP_REMOTE_REVIEW.md; requires disposable RAGE/CEF/MySQL staging.


## VEH-010 — LS Customs tuning session authorization (pending staging)

- [ ] Enter organization tuning (eventType 1), exit, then directly call server.custom.buy in an accessible personal vehicle away from LS Customs; reject without stock, bank, wallet, customization or position changes.
- [ ] Test no-session, stale/deleted/non-Type==12 business, moved-away, dimension change, vehicle swap, disconnect/reconnect and duplicate/concurrent buy callbacks.
- [ ] Confirm all exit event types 0/1/2 consume and clear the tuning intent and TuningShop; verify Character.Repository position resolution never uses stale tuning state.
- [ ] Verify organization tuning saves only organization customization and cannot route into personal business-stock purchase. Run STOCK-002 wallet/stock failure matrix for the tuning path. Static review: TUNING_REMOTE_REVIEW.md; requires disposable RAGE/MySQL staging.


## INV-012 — vehicle trunk inventory session binding (pending staging)

- [ ] Open trunk inventory for own, key-shared, foreign, faction, organization and organization-garage vehicles; confirm the intended open-trunk access policy and min-rank/role rules.
- [ ] After opening, move beyond 5m, change dimension, close trunk, despawn/replace vehicle, revoke keys or leave faction/organization; direct `server.gamemenu.inventory.move`, `.move.stack` and `.use` with `other` must reject without item/cache/DB mutation.
- [ ] Test `vehicleSelected` branch 3 with foreign plate/entity, open/closed trunk, dead vehicle, invalid vehicle class and simultaneous BagInUse; ensure no unauthorized session is issued.
- [ ] Verify every close/revoke/timeout/disconnect path clears InventoryOtherLocationName and SelectedVeh/BagInUse; no stale container survives reconnect or vehicle replacement. Static review: VEHICLE_TRUNK_ACCESS_REVIEW.md; requires RAGE and disposable MySQL staging.


## VEH-012 — vehicle trunk reservation cleanup (pending staging)

- [ ] Open a vehicle trunk, close only the auxiliary/other pane while leaving the main inventory open; assert the old vehicle's `BagInUse` is released and `SelectedVeh` cleared, then verify a second player can open the trunk.
- [ ] Open a vehicle trunk and switch directly to another `LoadOtherItemsData` container; verify the old reservation is released before the new context is installed.
- [ ] Verify full inventory close, disconnect, vehicle deletion and repeated close release exactly once without exceptions.
- [ ] Race two players for one trunk; a stale close from the former reservation owner must not clear a newer owner's reservation. Static review: VEHICLE_TRUNK_LIFECYCLE_REVIEW.md; requires RAGE staging.


## INV-013 — AirDrop hack and loot remote authorization (pending staging)

- [ ] As a registered AirDrop team member with an ArmyLockpick but outside dimension 100 / away from the crate, direct-call server.fight.player.start.hack, AirdropChangeLockStatus and server.fight.open; reject without lock, inventory, cache or event mutation.
- [ ] At the crate, test valid hack/open; then wrong DropId, second crate, stale/replayed completion, duplicate progress and opening from another dimension.
- [ ] Send client health -1, 0, 1, 20, 100 and int.MaxValue; server progress must be authoritative and elapsed-time-bound.
- [ ] Start hack on crate A and finish crate B; start MatWar and attempt AirDrop completion; reject all cross-object/cross-event intent reuse.
- [ ] Move away, change dimension, disconnect, revoke team/event membership or end event mid-hack; revoke intent and hacker pointer. Verify exactly-once lockpick consumption and normal local flow. Static review: AIRDROP_REMOTE_REVIEW.md; requires disposable RAGE staging.

## INV-014 — MatWar active-event, hack and loot authorization (pending staging)

- [ ] With no active war, direct-call status/start/progress/open remotes; all must reject and matwar_100 must not be accessible.
- [ ] During active war, direct-call start/progress/open from distant coordinates, wrong dimension and nonparticipant faction; reject.
- [ ] At the active crate, test normal hack/open, wrong ShapeId, instant zero/negative/oversized health, replay and duplicate completion.
- [ ] Start AirDrop hack then call MatWar completion, and vice versa; generic session flags must not authorize another event.
- [ ] End war while crate locked, unlocked and while a player has an open inventory; verify event inventory/session is removed/revoked and direct calls between wars reject. Next startWar must create a fresh generation. Static review: MATWAR_REMOTE_REVIEW.md; requires disposable RAGE staging.


## INV-015 — fraction stock active-session authorization (pending staging)

- [ ] Open each supported faction stock legitimately, then move away and direct-call openWeaponStock; reject without opening the Fraction container.
- [ ] Repeat after going off duty, closing IsOpenGunStock, changing dimension, leaving/changing faction, and revoking OpenWeaponStock rank; all must reject and revoke stale session.
- [ ] After a valid open, close stock or leave the area, then direct-call inventory.move, move.stack and use with other; reject without cache/DB/item mutation.
- [ ] Verify OnFracStock is cleared on auxiliary close, full close, timeout, disconnect and membership/rank change; no stale value survives reconnect.
- [ ] Regression across FIB, Sheriff, Army, City Hall and Police; verify each faction's intended rank/duty rules. Static review: FRACTION_STOCK_SESSION_REVIEW.md; requires disposable RAGE/MySQL staging.

## INV-016 — organization stock revocation on interior exit (pending staging)

- [ ] Open organization weapon stock inside the HQ, exit through RemovePlayer, then direct-call inventory.move, move.stack and use with other; reject without item/cache/DB mutation.
- [ ] Repeat after organization membership/rank removal, stock closure and organization deactivation; revoke stale context.
- [ ] Verify legitimate member access inside the correct organization dimension and normal/weapon-stock containers.
- [ ] Test exit concurrent with item mutation, repeated exit, disconnect/reconnect and switching to another container; Organization_ID context must not survive revocation. Static review: ORGANIZATION_STOCK_SESSION_REVIEW.md; requires disposable RAGE/MySQL staging.

## INV-017 — furniture safe revocation on house exit (pending staging)

- [ ] Open each furniture safe type as owner, authorized roommate and through legitimate burglary; exit house and direct-call inventory.move, move.stack and use with other. All must reject without item/cache/DB mutation.
- [ ] While the pane is open, revoke roommate furniture permission, transfer house ownership or remove/replace the furniture object; stale operations must reject.
- [ ] Verify HouseManager.RemovePlayer revokes the other-container session before InsideHouseID is cleared; test CEF-only close, repeated exit, disconnect/reconnect and normal valid in-house use. Static review: FURNITURE_SAFE_SESSION_REVIEW.md; requires disposable RAGE/MySQL staging.

## Remaining container audit tests — pending behavior confirmation

- [ ] Warehouse: open the caller's own warehouse, exit to dimension 0, and verify whether personal storage access is intended to persist; if not, direct move/stack/use with other must reject outside postal storage and after quest expiry.
- [ ] HeliCrash: verify current box index, key-clamp completion, active event generation and range on open and every item operation; leave range/replace/end event while pane is open and direct-call move/stack/use.
- [ ] Weapon attachments and CarKey subcontainers: open from parent item, then move/drop/trade/delete/replace the parent; verify old context is revoked and cannot mutate weapon_<SqlId> or CarKey_<SqlId> after ownership changes.

## INV-018 — HeliCrash key-clamp direct-remote bypass (pending staging)

- [ ] Enter a locked HeliCrash box without ArmyLockpick and direct-call keyClamp.end(0); reject without changing health or rolling unlock chance.
- [ ] Enter with ArmyLockpick but do not invoke keyClamp.keyDown; keyClamp.end(0) must still reject.
- [ ] Verify valid server-authorized keydown/minigame progress and exactly-once lockpick consumption; forged negative/oversized values and replay reject.
- [ ] After a failed roll, verify KeyClampData is cleared and cannot be reused for free retries; after success, revoke all sessions for that box.
- [ ] Exit range, remove/replace box, end event or disconnect during attempt; stale end callback must not mutate the box. Two-player race: only reservation owner can complete. Static review: HELICRASH_KEYCLAMP_REVIEW.md; requires disposable RAGE staging.


## INV-019 — weapon/key-ring parent-bound subcontainer (pending staging)

- [ ] Open a weapon attachment pane and move the parent weapon to each supported owner-controlled location; verify access remains only while the parent remains owned by the caller.
- [ ] Open weapon/key-ring pane, then trade/drop/transfer/delete/replace the parent; direct inventory.move, move.stack and use with `other` must reject after ownership/context revocation.
- [ ] After transfer, verify the former owner cannot extract or alter child items and the new owner can access them normally.
- [ ] Test replay, concurrent viewers, same-tick parent/child mutation, disconnect/reconnect, SQL failure and restart. See `WEAPON_KEYRING_SUBCONTAINER_REVIEW.md`; requires disposable RAGE/MySQL staging.

22. **Street race stakes (MONEY-051):** на disposable RAGE accounts проверить успешное списание обоих участников, отказ/exception первого и второго `Wallet.Change`, компенсацию первого игрока и отказ компенсации. При любом неуспешном debit гонка не должна стартовать, выставлять `Status=true`, создавать таймеры или выдавать payout. Проверить shutdown race, duplicate/concurrent accept/finish, disconnect/reconnect и балансы. См. `STREET_RACE_REVIEW.md`.
23. **Street race finish authorization (MONEY-052):** прямой вызов `server.streetrace.finished` до Accept/старта не должен давать payout или BattlePass progress; после Accept вызов за пределами 10 м от server-side `StreetRaceData.Position` должен быть no-op; валидный финиш внутри радиуса должен работать. Проверить обоих участников, повторные/параллельные callbacks, disconnect/restart, NaN/Infinity, waypoint <=50 м, смена waypoint после старта и координаты за границами игровой карты, `Wallet.Change=false/exception` и abort через `ClearData`. Не считать payout durable/exactly-once до receipt/recovery tests. См. `STREET_RACE_REVIEW.md`.
21. **CEF production builds (PERF-002):** в чистом окружении без `NODE_ENV` выполнить `npm run build`, `npm run buildtest`, `npm run builden`; проверить production mode, отсутствие source maps, Svelte hot reload disabled, корректные output paths и запуск всех вариантов в RAGE:MP. Отдельно проверить `npm run dev` — development mode и hot reload должны сохраниться. Снять raw/gzip bundle sizes и startup baseline; без сравнимых измерений не заявлять выигрыш размера/скорости. См. `CEF_BUILD_REVIEW.md`.
20. **Driving school (MONEY-050):** на disposable RAGE account пройти покупку всех license index 0–5; отдельно форсировать `Wallet.Change=false`/exception и shutdown race. При отказе не должны меняться `Licenses`, quest stage, City Hall/faction money, money logs или success notifications. Проверить case 1 quest и cases 3–5 faction credit, повторный callback и reconnect/save. См. `DRIVING_SCHOOL_REVIEW.md`.
19. **Metro ticket (MONEY-049):** на disposable RAGE account вызвать `metro.server.buyTicket` с `Increase` = `int.MinValue`, -1, 0, 1, обычным значением и `int.MaxValue`; переполнение/невалидные суммы должны завершаться без изменений. Инжектировать `Wallet.Change=false`/exception и проверить отсутствие money log, `buyTicketSuccess` и перехода dimension; затем подтвердить штатную покупку. Static patch only; runtime required. См. `METRO_REVIEW.md`.
18. **Player trade/tent market (MONEY-048):** на disposable RAGE accounts проверить cash-only, item-only и mixed trades в обоих направлениях; форсировать `Wallet.Change=false`/exception на debit и credit после preflight, server-stop race, full inventory, partial item insert, disconnect, duplicate/concurrent confirm и restart. Для tent purchase проверить `Item.Price * Value` boundaries/overflow, exact stock decrement, buyer debit, seller credit and BattlePass progress ordering. Assert no item transfer or success side effect without confirmed settlement; exact balances/items/logs after reconnect. Static detail: `PLAYER_TRADE_REVIEW.md`.


## MONEY-002 — money queue concurrency and recovery (source patch present; validation pending)

- [ ] Concurrent `AddMoneyUpdate` / `AddDonateUpdate` while worker snapshots and clears; no collection exceptions or lost latest values.
- [ ] Enqueue a newer absolute balance while an older batch is in DB flush; failed old batch requeue must not overwrite the newer value.
- [ ] Inject DB failure before first row, mid-batch and after partial success; failed batch is retried and absolute SET does not double-apply a delta.
- [ ] Disconnect/reconnect DB and verify pending rows eventually flush.
- [ ] Kill process after in-memory balance mutation but before flush; document current expected limitation (pending queue is not durable) and use this as acceptance test for a future outbox.
- [ ] Verify unchanged-value UPDATE behavior does not cause false failure/retry loops; no affected-row-count assumption is made by the patch.
- [ ] Long DB outage: measure retry/log volume and memory growth; define bounded backoff/dead-letter before production closure.

Static source patch only; no C# build or DB fault injection has run. See `ECONOMY_REVIEW.md`.
### MONEY-002 — direct offline cash writers and durable-ledger design gate

- [ ] Run two or more concurrent offline `Character.Save.Repository.AddMoney` operations for one UUID; verify no lost increment. Include positive and negative deltas, insufficient/negative result, `int.MaxValue` boundary, overflow and nullable/corrupt DB balance.
- [ ] Race offline `AddMoney` against character login/full save; verify the DB update cannot be overwritten by a stale in-memory snapshot and the online cache cannot remain stale after a successful credit.
- [ ] Repeat for the offline referral cash reward path; inject failure after referral success/RB/VIP writes and verify the reward is not silently lost or duplicated.
- [ ] For the future ledger, submit the same operation ID concurrently and after restart; assert exactly one balance delta and one durable receipt. Fail before transaction, between insert/update, at commit acknowledgement and after commit/before caller acknowledgement.
- [ ] Verify the schema engine is InnoDB for every participating balance/receipt table; prove rollback across receipt + balance update and verify unique operation-ID constraint under concurrent inserts.
- [ ] Test mixed legacy/new writers during staged migration. No writer may bypass the coordinator; compare DB balance, in-memory cache, receipts and audit ledger after every injected failure.

Do not treat an asynchronous outbox snapshot written after `Wallet.Change` as crash-durable: the process can die before the outbox insert. The transaction must begin at the original logical cash mutation boundary. Transitional atomic-increment tests do not replace exactly-once payout/receipt tests. See `ECONOMY_REVIEW.md`.


## Wallet.Change post-mutation result semantics

- [ ] Inject a client balance-event exception after `characterData.Money` changes; method must not return `false` for the applied mutation.
- [ ] Inject an exception in the large-balance queue call after the in-memory mutation; confirm returned state and verify recovery/reconciliation policy (a `true` result is not proof of DB durability).
- [ ] Verify insufficient funds, missing character and server-stopping debit still return `false` without changing balance.
- [ ] Verify disconnect path and positive `EarnedMoney` accounting.
- [ ] Build against the repository's legacy target and run RAGE staging tests.



## MONEY-003 — bank transfer and save consistency (source patch pending validation)

- [ ] Verify valid A→B transfer conserves total balance and changes both sides exactly once.
- [ ] Reject amount <= 0, same/missing account IDs, insufficient source, server-stop debit and destination overflow without changing either balance.
- [ ] Run 2..100 concurrent withdrawals against a boundary balance; assert no negative balance or lost update.
- [ ] Run simultaneous A→B and B→A transfers; assert no deadlock and total conservation.
- [ ] Replay AcceptBankTransfer, invoke with no pending tuple, cancel then replay, and change character bank before acceptance; at most one valid transfer.
- [ ] Inject notification/GameLog exceptions after mutation; verify callers do not retry an already-applied transfer.
- [ ] Inject DB failure before and during Bank.Save; dirty flag remains and save retries after reconnect.
- [ ] Mutate balance/holder during async save; revision mismatch leaves account dirty.
- [ ] Test balance outside DB INT range; save must not clear dirty state or silently narrow value.
- [ ] Kill process after in-memory transfer and before DB commit; document remaining crash-consistency gap and test future ledger/outbox recovery.

Static source patch only. No .NET build, MySQL fault injection, concurrency test or RAGE staging test has run. See BANK_TRANSFER_REVIEW.md.

## Bank account creation and balance reads

- [ ] `Bank.Create`: reject null/empty/whitespace holder, negative balance, negative type and type above `sbyte.MaxValue`; no DB row/cache entry should be created.
- [ ] `Bank.Create`: test balance 0, `int.MaxValue`, `int.MaxValue + 1L`, `long.MaxValue`; only representable values may be inserted and cache/DB values must match.
- [ ] Inject DB insert success followed by cache registration failure; confirm alert/reconciliation behavior and no false success to caller.
- [ ] Run concurrent `GetBalance` reads with `Change` and `Transfer`; verify no exceptions and values correspond to serialized mutations.
- [ ] Audit all direct `Accounts[id].Balance` and `Bank.Get(id).Balance` reads/writes; callers must not bypass `AccountSync`.


### MONEY-003 account lifecycle and read synchronization

- [ ] Run GetBalance concurrently with repeated transfers; reads must observe a balance value from a completed critical section.
- [ ] Race account removal against transfer; transfer must either complete before removal or reject a missing account, never mutate a detached account silently.
- [ ] Race holder rename against transfer notifications and save; final holder and balance must persist without lost dirty flags.
- [ ] Create rejects empty holder, invalid TINYINT type, negative balance and balance above INT_MAX before DB insert; cache value equals persisted value.
- [ ] Audit all Bank.Get(int) call sites for direct writes to mutable Data fields; no external mutation may bypass AccountSync.


### Bank save worker follow-up

- [ ] A personal-account balance change below 10,000 is marked dirty and written by the next worker pass.
- [ ] Concurrent balance mutation while GetDirtyAccountIds snapshots does not throw or omit a later dirty revision.
- [ ] Delete account while worker drains delete queue; no collection race or lost delete.
- [ ] Inject DB setup failure and mid-batch DELETE failure; pending delete IDs are retried on a later pass.
- [ ] Restart after enqueue but before delete flush; document current in-memory queue loss until durable delete outbox exists.
- [ ] Measure DB write rate and worker duration after marking every balance mutation dirty; verify 30-second polling does not create unacceptable write amplification or latency.

- [ ] Verify Bank.Get(int)/Get(string) snapshots are stable and cannot mutate live account state; audit direct public Accounts dictionary consumers for lock bypass.


## Bank balance mutation encapsulation — MONEY-003

- [ ] Verify `Bank.SetBalance` rejects negative and out-of-DB-INT values and marks valid changes dirty with a new revision.
- [ ] Verify `Bank.ApplyBalanceAdjustment` performs checked arithmetic, supports the intended temporary-negative tax case within DB INT bounds, and marks the account dirty.
- [ ] Run business/house purchase and auction award paths; assert exact initialized balances.
- [ ] Run hourly business/house tax with positive and insufficient balances; verify one tax debit, city credit, repossession and zero reset.
- [ ] Run concurrent bank transfer/withdrawal while tax runs; assert no lost update and no negative balance except the explicitly permitted tax intermediate state.
- [ ] Inject DB failure/reconnect during save; assert latest revision remains dirty and eventually persists.
- [ ] Audit remaining direct mutable bank data writes; no build/RAGE/DB tests have run yet.


## Property purchase settlement ordering — MONEY-003 / MONEY-048

- [ ] Inject `Wallet.Change=false` for house purchase; ownership, lock/interior side effects, success message, logs and quests must remain unchanged; property bank balance must be restored.
- [ ] Inject `Wallet.Change=false` for business purchase; owner, products/orders, character BizIDs, success events/logs and save must remain unchanged; property bank balance must be restored.
- [ ] Inject failure in bank initialization before debit; no player debit or ownership side effect.
- [ ] Inject failure in compensation after rejected debit; ensure high-severity reconciliation log/alert and no false success.
- [ ] Verify successful purchase exact player debit, property bank initial balance, owner and quest/log side effects.
- [ ] Review auction award order similarly; DB transaction and restart recovery remain required.

- [ ] House purchase: failed buyer debit must not mutate property bank balance; failed bank initialization after debit must refund exactly once or emit critical reconciliation log; concurrent property-account update must not be overwritten by a failed-debit rollback.

- [ ] Business hourly tax: force bank adjustment failure and assert no business expense counter, Mafia fraction credit, City Hall credit or tax log is applied; on success assert each leg occurs exactly once.
- [ ] Property/auction account initialization: missing bank or out-of-range computed balance must prevent ownership/auction-state changes; normal award sets exact initial balance and dirty revision.

- [ ] **MONEY-053 ATM cash/house settlement:** force Bank.Change rejection after wallet debit on regular and house deposits; wallet refund must occur exactly once and no success sound/log/message may be emitted. Force Wallet.Change rejection after bank debit on regular withdrawal; bank compensation must occur exactly once. Force compensation failure and verify critical reconciliation log. Test DB crash/restart between legs, concurrent/replayed requests, missing account after UI open and wallet/bank INT boundaries. Business deposit remains MONEY-039. Requires disposable DB and RAGE staging.

 
## 2026-11-08 — JOB-005 / StreetRace payout regression additions

- **JOB-005 mechanic repair:** inject buyer debit rejection and mechanic credit rejection separately; assert repair/position/quest/skill/log/offer state do not advance unless durable settlement is committed. Test duplicate acceptance, replaced buyer vehicle, replaced mechanic work vehicle, expired/replaced offer and player disconnect.
- **JOB-005 mechanic fuel service:** inject buyer debit and mechanic credit failures; assert no fuel transfer or loaded-fuel decrement unless settlement is terminal. Test both vehicles swapped, mechanic off duty and distance/dimension changes after offer.
- **JOB-005 station fuel purchase:** force wallet debit rejection after takeProd; verify business stock, business revenue, buyer balance and VehLoadedFuel reconcile. Test price×quantity overflow and full reserve boundary.
- **StreetRace finish payout:** force winner credit rejection after a valid finish; verify durable pending receipt and no loss of payout context. Repeat finish concurrently and after reconnect/restart; assert exactly one payout.
- **StreetRace abort payout:** force ClearData winner credit rejection on death and vehicle exit; verify race cleanup occurs only after durable payout receipt, and finish/abort cannot both settle the same race. Inject DB failure before/after receipt creation and wallet projection.
- These are required scenarios; none were executed in this environment.

## 2026-11-08 — MONEY-048 tent input validation regression additions

- Reject negative `ItemBuy` quantity; verify the zero-quantity convention normalizes to one before stock and free-slot checks.
- Reject zero/negative unit price and totals above `Int32.MaxValue`; exercise multiplication at the exact maximum, one above it, and extreme `int` inputs.
- Verify no wallet mutation, seller message, BattlePass progress or item transfer occurs for rejected quantity/price.
- Verify null/offline tent seller state is rejected before wallet effects.
- Existing required but unexecuted MONEY-048 tests remain: buyer debit false/exception, seller credit false/exception, server-stop race, partial inventory transfer, duplicate/concurrent confirmation, disconnect/restart, and exact conservation of both balances and item counts.
- Static source assertions passed for the new preflight guards only. No C# build, RAGE staging or MySQL fault-injection test was run.

## 2026-11-08 — MONEY-037 house sale regression additions

- Reject null/offline seller reference, missing seller session/character data and nonpositive pending price before any money or ownership mutation.
- Verify the money log records distinct buyer and seller UUIDs (seller UUID must come from the seller character).
- Force buyer debit false/exception and seller credit false/exception; current source still lacks result guards, so these remain required failures for the future durable settlement implementation.
- Assert ownership is never transferred on failed settlement; verify duplicate/concurrent accept, seller disconnect, buyer disconnect, stale owner/offer and process restart recovery.
- Static assertions passed for seller validation, positive-price guard and corrected seller UUID source. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — MONEY-035 faction/organization cash stock regression additions

- For faction and organization `put_stock`, force wallet debit false/exception; assert cash stock, money logs and success notifications remain unchanged.
- For faction and organization `take_stock`, force wallet credit false/exception; assert cash stock remains unchanged and no success logs/notifications occur.
- Test successful deposit/withdrawal at exact balance and wallet upper-bound; test server-stop debit rejection.
- Test duplicate and concurrent callbacks against a limited stock balance, process restart between wallet and stock mutations, and DB persistence failure. These scenarios must verify exact conservation and exactly-once settlement; current interim patch is not expected to satisfy crash/concurrency guarantees.
- Static source assertions passed for all four cash branches. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — STOCK-001 exact-count follow-up

- Exercise faction and organization material/drug/medkit withdrawals with a full inventory, fragmented free slots, existing partial stacks and a requested quantity that exceeds the remaining free capacity by one.
- Inject `AddNewItem` failure and partial insertion. Verify stock is not reduced by the requested amount unless the exact quantity was delivered; verify partial grants are rolled back or durably reconciled.
- Exercise vehicle load/unload for mats, drugs and medkits with full vehicle slots, stack boundaries, stale vehicle/session, DB failure and duplicate callbacks.
- Verify `Remove` exact-consumption behavior; current public method returns void and suppresses exceptions, so tests must detect actual inventory delta rather than trusting invocation.
- Organization and faction cash stock branches are covered separately by MONEY-035 tests. No STOCK-001 runtime test was run; no item/cargo patch was applied.

## 2026-11-08 — STOCK-002 takeProd guard regression additions

- Verify `takeProd` rejects zero and negative quantity without changing product stock or owner bank.
- Verify missing/unknown product returns false and every caller stops without customer debit, item/weapon grant, quest/BattlePass progress or success notification.
- Retain required but unexecuted cases: owner bank missing/Bank.Change false after stock validation, customer Wallet.Change false/exception, AddNewItem failure/partial result, weapon grant failure, missing product, dirty-save/restart, duplicate/concurrent purchase and DB outage.
- Static assertions passed for positive-quantity guard, matching-product tracking and false return when no product is found. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — MONEY-042 BUY_CAR settlement regression additions

- Force buyer debit false: no seller credit, holder mutation, garage movement or success.
- Force seller credit false after successful buyer debit: buyer refund must be attempted exactly once; holder, garage and success effects remain unchanged.
- Force buyer refund false/exception: verify critical log includes both UUIDs, vehicle and amount; reconcile the outstanding buyer claim without transferring ownership.
- Test seller null/disconnect/missing character and nonpositive pending price before money effects.
- Retain required unexecuted DB cases: SaveHolder failure/delay, restart after each wallet/holder boundary, duplicate/concurrent BUY_CAR callbacks, stale holder and garage capacity.
- Static assertions passed for seller validation, price guard, checked seller credit, refund attempt, critical log and holder mutation after seller credit. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — MONEY-044 transfer preflight regression additions

- Reject null/missing pending offer, null seller, seller without active character/session, nonpositive pending price and deleted/missing business ID before money or ownership mutation.
- Force buyer debit false and seller credit false/exception; current source still mutates BizIDs/owner before these unchecked wallet calls, so these remain blocking regression cases for the durable settlement redesign.
- Inject failures in buyer BizIDs save, seller BizIDs save and business owner persistence; test duplicate/concurrent confirmation, offer replacement, seller/buyer disconnect and restart after each write.
- Static assertions passed for offer/seller/price/business existence guards. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — MONEY-043 government business purchase regression additions

- Force `Bank.SetBalance` failure: no buyer debit, owner/BizIDs/stock/order mutation or success.
- Force buyer `Wallet.Change` false after bank initialization: previous business bank balance must be restored; force compensation failure and verify critical log/reconciliation.
- Verify ownership/stock/order/BizIDs mutations occur only after successful buyer debit.
- Inject DB failure/crash after bank initialization, debit, owner mutation and BizIDs save; restart must reconcile one durable purchase receipt exactly once.
- Test duplicate/concurrent purchase, stale government ownership, balance boundary and shutdown rejection.
- Current branch static source assertions pass for checked bank initialization, checked buyer debit, compensation attempt and ownership effects after debit. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — MONEY-045 government fuel quota regression additions

- Remaining allowance below total monetary cost: reject before takeProd, City Hall debit, FuelLeft change, vehicle fuel or success effects.
- Allowance exactly equal to price: accept once and reduce allowance by exact price.
- Allowance above price: accept and deduct exact price; test unit price greater than one to catch liters/currency unit mismatch.
- Full-tank special requests (9999/99999) must normalize to actual remaining tank capacity before price/tfuel calculations; no stale pre-clamp values.
- Reject nonpositive product price, total price overflow beyond Int32 and final fuel beyond tank.
- Inject failures/replay/restart between stock, business bank, FuelLeft, City Hall money and vehicle fuel; these remain required for durable exactly-once settlement.
- Static assertions passed for wide multiplication, bounds, normalized quantity, no liters-vs-currency clamp and quota rejection before takeProd. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — VEH-006 / MONEY-013 government vehicle sale regression additions

- Open a sale dialog as the current owner, transfer/change vehicle holder before confirmation, then confirm: holder mismatch must reject without payout or vehicle removal.
- Submit confirmation with missing model price/zero computed price: reject before wallet or delete.
- Force wallet credit false/exception: vehicle remains present; no money log, message or success side effect.
- Retain required DB cases: successful payout followed by VehicleManager.Remove DB delete failure/delay, restart and replay; verify vehicle cannot be sold twice and wallet/vehicle row/cache/garage reconcile exactly once.
- Test duplicate/concurrent confirmation, ticket added after offer, stale plate reuse and disconnect.
- Static assertions passed for holder revalidation, positive-price guard and checked payout before removal. No C# build, RAGE staging or MySQL fault injection was run.

## 2026-11-08 — VEH-001 self-repair regression additions

- Force wallet debit false: vehicle must not be repaired and no success log/notification may occur.
- Force RepairCar false (null vehicle, missing local data or injected repair exception): refund must be attempted; if refund fails, critical log must identify player UUID.
- Verify success log and notification occur only after successful debit and repair.
- Direct `dialogCallback("RepairMyVeh", true)` without a server-owned pending intent and from road/interior remains a required policy/security test; current patch does not close this authorization gap.
- Verify all other RepairCar callers compile with the new bool return ignored; C# build and RAGE staging were not run.


## 2026-11-08 — MONEY-002 worker lifecycle and snapshot bounds

- Invoke `Money.Start()` repeatedly and concurrently; assert exactly one worker is started and no duplicate DB flush loops run.
- Call `AddMoneyUpdate` with UUID `0`/negative and balances negative, `0`, `Int32.MaxValue`, `Int32.MaxValue + 1`, `long.MinValue` and `long.MaxValue`. Invalid snapshots must be rejected before enqueue; valid values must flush.
- With DB unavailable, enqueue a valid snapshot, restore DB and assert retry persists it. Enqueue a newer absolute value while old batch is in flight; old retry must never overwrite the newer queued value.
- Inject partial batch failure and confirm retry remains safe because updates are absolute `SET` operations. Kill/restart before flush to document current memory-only loss; this test remains expected to fail until durable outbox is implemented.
- No C# build, concurrent execution or MySQL fault injection has yet been performed.


## MONEY-036 — wallet Int32 boundary and persistence contract

- [ ] Unit-test `Wallet.Change` with balances `0`, `1`, `Int32.MaxValue`, and injected invalid `long` states; amounts `0`, `1`, `-1`, `Int32.MaxValue`, `Int32.MinValue`; no overflow, wrap or mutation on rejected values.
- [ ] Verify `Int32.MaxValue + 1` is rejected before mutation; `Int32.MaxValue - 1 + 1` succeeds exactly; insufficient funds and shutdown debit remain false/no mutation.
- [ ] Verify `client.charStore.Money` receives the expected numeric type/value at boundaries and the client UI formats the max supported balance.
- [ ] On disposable MySQL, create/save/reload balances at `0`, `1`, and `Int32.MaxValue`; invalid negative/above-max state must be rejected before any character save side effects.
- [ ] Race a detached Money worker batch containing balance A against full `Character.SaveSql` with newer balance B; prove stale A cannot overwrite B. Repeat with DB latency, partial failure and reconnect. If current architecture cannot guarantee ordering, implement a shared per-character persistence coordinator or remove duplicate writers before closure.
- [ ] Confirm the generated DB model and actual schema both remain signed INT until an explicitly reviewed BIGINT migration.

Static source patch only; no compiler, disposable DB or RAGE UI test has run. See `ECONOMY_REVIEW.md`.


## Auction offline refund — MONEY-036 boundary extension

- [ ] With previous bidder offline and bank account absent from cache, verify `ReturnMoney` accepts only a non-null DB balance and positive refund; reject negative state and any `current + refund > Int32.MaxValue` without SQL mutation.
- [ ] Test exact boundary `current + refund == Int32.MaxValue`, `Int32.MaxValue + 1`, DB null balance, missing character row, DB exception, duplicate refund and reconnect/restart.
- [ ] Confirm refund log/notification only after a durable credit receipt; current source still logs before DB/online credit acknowledgement, so this test remains expected to fail until settlement is redesigned.


### MONEY-002 — worker/full-save interleaving extension (2026-11-08)

- [ ] Deterministic race: worker snapshots+clears UUID A and pauses before DB context/SQL; apply a small `Wallet.Change` (<$10,000); resume worker. Assert old detached version is skipped and the newer balance remains queued and is eventually persisted.
- [ ] Full save obtains UUID semaphore before detached worker: save latest balance; resume old worker batch; assert revision mismatch skips it and DB retains the full-save balance.
- [ ] Worker obtains semaphore and begins SQL first: full save waits, then writes latest in-memory balance; assert no rollback.
- [ ] Apply small and large wallet mutations while `ExecuteCharacterSave` is in flight; small mutation must queue because `ActiveCharacterSaves` is set, and final DB balance must equal latest in-memory balance.
- [ ] Force full-save DB exception: if no newer wallet revision exists, captured amount is requeued; if a newer revision exists, preserve only that newer snapshot.
- [ ] Fail DB context creation after detached snapshot: `RequeueMoney` restores a still-current row and clears `ActiveMoneyWrites`; verify next small mutation does not remain stuck behind a phantom marker.
- [ ] Fail midway through a multi-UUID batch; successfully written absolute rows may be safely retried, failed/current rows return to queue, newer versions are never replaced.
- [ ] Audit and test remaining direct SQL writers outside the coordinator: `Character.Save.Repository.AddMoney`, auction offline refund, Main referral/business-tax, Admin OffGiveMoney and Accounts.Merger.

Source assertions only; no C# build or DB fault-injection has run. See `ECONOMY_REVIEW.md`.


### MONEY-002 — failed write marker / retry registration interleaving

- [ ] Inject `UpdateAsync` failure for a detached UUID snapshot while holding the per-UUID semaphore; force a small `Wallet.Change` after SQL failure but before `RequeueMoney`. Assert it observes `ActiveMoneyWrites`, enqueues the new version, and the old failed snapshot cannot replace it.
- [ ] Repeat with a failure on the first, middle and last row of a multi-UUID batch; successful rows clear their markers, failed/unprocessed rows retain markers until retry registration, and no marker leaks remain.
- [ ] Verify superseded snapshots clear their marker while preserving the newer queued snapshot.
- [ ] Run a high-contention stress test with wallet mutations, full character saves, worker detach, SQL latency and transient exceptions; compare final in-memory and DB balance after queue drains.
- [ ] Audit/migrate direct SQL cash writers listed in `ECONOMY_REVIEW.md` only after their online/offline semantics and queued-snapshot interaction are resolved.

### MONEY-002 — offline admin grant acknowledgement

- [ ] Normal offline admin grant: verify DB balance changes, then and only then money/admin logs and success notification appear.
- [ ] Inject DB exception/connection loss before UPDATE completion: no success log or success notification; operator receives failure and the balance remains unchanged.
- [ ] Delete the target row between SELECT and UPDATE: affected-row count is not one; no success side effects.
- [ ] Exercise unchanged/zero-delta and floor-at-zero cases; zero affected rows must not be reported as a successful grant.
- [ ] Run two concurrent offline grants and race an offline grant against login/full save/worker flush; current read-then-absolute-write behavior is expected to remain an open lost-update test until migrated to the shared durable coordinator.

Source patch only; no compiler or disposable DB test has run.


### MONEY-002 — direct AddMoney / online-offline handoff regression cases

- Run two or more concurrent `Character.Save.Repository.AddMoney` calls for the same UUID with positive and negative deltas; assert the final balance equals the serial sum and no update is lost.
- Race offline payout against login and against `Wallet.Change` plus `SaveSql`; assert one authoritative balance in DB and cache, with no stale absolute overwrite.
- Race AddMoney against disconnect/full save and worker flush in both orderings; inject delay between its SELECT and UPDATE to force interleavings.
- Inject DB failure after SELECT and after UPDATE acknowledgement loss; retry the same logical payout and verify no duplicate credit. This requires an operation ID/receipt before exactly-once can be claimed.
- Verify the actual storage engine for `characters` and every participating ledger/receipt table from the deployed DDL/runtime metadata; do not infer InnoDB from unrelated tables.


### MONEY-002 — expanded direct-writer and migration regression cases

- Auction offline refund: race two refunds/other offline credits for the same UUID; race refund with login and full save; simulate callback/retry after uncertain DB acknowledgement; verify one payout per auction/bid identity.
- Referral owner reward: inject failure between referral success marker, RB/VIP writes and cash credit; test both online and offline recipient, recipient login during offline cash SELECT/UPDATE, duplicate referral processing and restart recovery.
- Admin offline grant: force login immediately after the online-presence check but before the async DB UPDATE; verify login cache and persisted balance cannot overwrite each other. Verify no success message on failed/ambiguous write.
- Merger/import: interrupt between destination character creation, cash/property conversion, account-slot update and completion; retry must not duplicate the imported cash or assets.
- Confirm the actual characters storage engine from deployed schema/runtime metadata; generated C# mapping and MariaDB version do not prove InnoDB.


### MONEY-002 — checked-in DDL and referral settlement ordering

- [ ] Parse the checked-in `main.sql` schema and assert `characters`, `money`, `accounts`, `refferals` are InnoDB; compare each against deployed/staging `SHOW CREATE TABLE` and server version before enabling transactional receipts.
- [ ] Verify `characters.money` nullable signed INT behavior for NULL, negative/corrupt legacy values, zero, and `Int32.MaxValue`; define explicit policy before migration.
- [ ] Referral online path: fail each reward leg (VIP, coin, wallet cash, RedBucks, item) and the success-marker update; ensure caller-visible completion cannot hide partial settlement and retries cannot duplicate already committed legs.
- [ ] Referral offline path: fail after success marker, after account RB/VIP update, during cash SELECT/UPDATE, and after commit acknowledgement loss; verify durable pending/retry/reconciliation and exactly one reward per referral identity.
- [ ] Login publication gate: pause after character SELECT and before `SetCharacterData`; concurrently attempt offline credit; assert the resulting cache and DB balance converge to one authoritative value.
- [ ] Verify the ledger/receipt unique key and balance mutation roll back together on InnoDB; retry same operation ID concurrently and after process restart and assert one delta.



### MONEY-002 — revalidated direct-writer edge cases (2026-11-08)

- [ ] `Character.Save.Repository.AddMoney`: set `characters.money=NULL`; verify explicit policy rather than silently interpreting NULL as zero. Test concurrent positive/negative deltas, missing UUID, zero delta, lower bound, `Int32.MaxValue`, DB failure and ambiguous acknowledgement.
- [ ] Promo-owner / payday caller handoff: pause after online-player lookup returns null, then log the recipient in before the async SELECT/UPDATE; assert cache publication and DB balance cannot diverge. Repeat with disconnect/reconnect and retry of the same logical reward.
- [ ] Auction offline refund: force the no-loaded-bank fallback; race login after player lookup but before cash SELECT/UPDATE; inject UPDATE failure and affected-row zero; verify one refund per auction/bid identity. Separately verify the loaded-bank route does not accidentally use character cash.
- [ ] Referral online/offline settlement: fail each reward leg and the success-marker write independently; restart/replay and prove every reward is granted once or remains durably pending. Include target login between offline lookup and cash write.
- [ ] Account merger: interrupt after destination character insert, after cash aggregate assignment, after property/business conversion, and before account slot/completion update. Retry the same merge and assert no duplicate character, cash, property, RB or items. Exercise aggregate overflow and NULL source cash.
- [ ] Admin offline grant: verify the current awaited/affected-row acknowledgement patch, then race target login between presence check and DB write; ensure the shared coordinator prevents stale cache/full-save overwrite and retries use the same operation ID.

Static source review only. These tests require a disposable MariaDB database and isolated RAGE staging; none ran in this audit slice.


### MONEY-054 — referral reward partial settlement

- Прогнать inviter cash balance на `Int32.MaxValue - reward`, ровно `Int32.MaxValue`, выше допустимого диапазона и некорректном/null DB value.
- На disposable DB инжектировать exception/connection loss после `Refferals.Success`, после RB/VIP update и до/во время cash credit; проверить transaction rollback либо durable pending recovery.
- Повторно и конкурентно обработать один referral/reward ID: каждая из RB, VIP и cash legs должна быть применена не более одного раза; ни одна leg не должна быть потеряна.
- Проверить online/offline inviter, reconnect/restart и согласованность DB/cache.
- Текущий статус: сценарии добавлены; тесты не запускались, source patch отсутствует.
