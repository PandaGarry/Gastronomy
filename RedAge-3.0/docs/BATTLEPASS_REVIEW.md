# BattlePass progression and reward-claim review

Статус: частичный статический review. Проверены remote handlers `open`, `take`, `takeAll`, `buyLvl`, `setMissions`, `skip`, reward dispatch and save/load call sites. Исходники не менялись; полный progression/reward producer inventory и runtime persistence tests остаются незавершёнными. В ходе callsite trace найден отдельный Sapper case `PROG-001` (см. `SAPPER_REVIEW.md`): completion event засчитывает task до проверки игры.

## CAS-027 — reward receipt не сохраняется вместе с prize grant

**Уверенность: высокая в раздельном lifecycle; приоритет: высокий для ценных/дублируемых наград. Crash window статически обоснован, runtime injection не выполнен.**

`Take`/`TakeAll` в `BattlePass/Repository.cs` сначала вызывают `GiveBonus`, после чего добавляют ID в `TookReward`/`TookRewardPremium` только в памяти (`Repository.cs`, примерно 741–829). Явного сохранения записи в этих handlers нет. В просмотренном checkout `BattlePass.Repository.Save` вызывается из `Character.Save.Repository.SaveSql`; этот character-save вызывается при обычном disconnect и отдельных admin paths, но не из claim handlers и не найден как периодическая BattlePass save задача. При этом item grant `AddNewItemWarehouse` добавляет локальный item и запускает отдельный async DB insert. Поэтому возможен crash/restart после успешной prize insert, но до сохранения `TookReward`: после reload старая receipt state позволит забрать ту же награду ещё раз. Подобный разрыв возможен и для других reward sinks, у которых grant пережил restart.

**Remediation:** durable per-character/season/reward claim ID с уникальным DB constraint и transactional/idempotent grant, либо durable pending/committed receipt с retry/compensation. Не полагаться на disconnect save для claim idempotency.

**Проверки:** взять item/money/RedBucks reward, дождаться подтверждения grant persistence, аварийно завершить процесс до disconnect-save, reconnect; повторить для `takeAll` и premium reward. Проверить exactly-once across crash points до/после ledger commit и отсутствие пропущенной награды.

## CAS-028 — failed/partial prize grant всё равно помечается забранным

**Уверенность: высокая по control flow; приоритет: высокий для надёжности выдачи.**

`GiveBonus` (`Repository.cs`, примерно 678–739) возвращает `void` и ловит исключения внутри себя. Внутренние grant results в рассмотренных ветках не подтверждаются: `Wallet.Change` вызывается без проверки bool; `AddNewItemWarehouse` тоже возвращает void и самостоятельно глотает исключения/асинхронную DB insert ошибку; RedBucks helper также не возвращает grant status. После возврата из `GiveBonus` `Take` и `TakeAll` безусловно добавляют reward ID к списку забранных. Для mission cash reward `SetMissions` аналогично меняет `IsReward` до/вокруг grant и игнорирует результат `Wallet.Change`.

Следствие: balance overflow, DB outage/insert failure или другой grant exception может оставить claim consumed с generic success response при отсутствующей/частичной награде. `takeAll` затрудняет определение, какая из нескольких prize grants не прошла.

**Remediation:** grant API должен возвращать подтверждённый результат или durable receipt; атомарно фиксировать claim only after grant commit либо записывать pending claim и обеспечивать повтор/компенсацию. Все wallet/item/RedBucks/VIP grant steps должны быть individually observable; не показывать success при fail.

**Проверки:** отказать по очереди в Wallet.Change, item insert, RedBucks persistence, VIP update и одной из `takeAll` наград; проверить claimed IDs, retry, user notification, logs и фактический баланс/предметы. Повторные remote calls не должны ни терять, ни дублировать приз.

## Инвентаризация `UpdateReward` producers — продолжается

Static scan по `NeptuneEvo/**/*.cs` (line/block comments исключены) нашёл **209** non-comment `BattlePass.Repository.UpdateReward(...)` source invocation lines. В Season4 task catalog — 106 distinct IDs; каждый из них имеет хотя бы один invocation. Дополнительно 55 IDs из call sites отсутствуют в Season4 list, всего **72** invocation lines. `UpdateReward` ищет задачу через `FirstOrDefault` и немедленно returns при `null`, поэтому эти calls в текущей hardwired Season4 конфигурации гарантированно no-op. Возможно, это остатки прошлых сезонов, но intended status пока не подтверждён.

Эта inventory — не validation всех producers: ещё не проверена полностью последовательность «remote/event → действие действительно выполнено → reward ID», duplicate/replay/rate limits и возможные cross-player effects. Отдельный проверенный no-game Sapper task path описан как `PROG-001` в `SAPPER_REVIEW.md`.

## Дополнительные проверки endpoints

- `buyLvl` индексирует `BattlePassBuyLvls[index]` без явной range guard (`Repository.cs`, около 958–967). Некорректный индекс сейчас выглядит как exception/no purchase, а не как доказанная награда/валютный bypass; добавить negative/large-index robustness test и безопасную validation.
- `Take` проверяет допустимый level (`award.Id < Lvl`), premium entitlement и duplicate ID в памяти. `TakeAll` также фильтрует по текущему level и premium state. Это полезные server-side guards, но они не устраняют crash/persistence/partial-grant проблемы выше.
- `SetMissions` использует серверный `MissionData`, task completion и `isActiveBox`; client передаёт только task ID. Проверена базовая цепочка, но полный enumeration всех callers `UpdateReward`, сезонные resets и все mission/XP sources ещё не завершены.

## Staging/failure test plan

1. Для каждого reward type взять обычный и premium prize; проверять `TookReward*`, account/character balances, inventory SQL rows, warehouse cache, VIP expiry и GameLog.
2. Перезапускать процесс в точках: до grant, после grant до claim marker, после marker in-memory до save, после durable receipt до client response.
3. Повторять `take`/`takeAll` одновременно и sequentially; проверять single claim, отсутствие частичных повторных выдач и честные сообщения.
4. Mission reward/skip: forced wallet and persistence failures, повторные remote callbacks, refresh/selection order, daily/weekly reset и 20/20 completion reward.
5. `buyLvl`: индексы `-1`, `0`, `2`, `3`, `int.MinValue`, `int.MaxValue`; insufficient/exact/near-exhausted RedBucks; level `MaxLvl-1` и повторные calls; проверять цену, cap, experience, durable state.

## Границы

Нет C# build, disposable DB или RAGE runtime. Статический review не доказывает фактический callback concurrency и момент завершения async insert. CAS-027/028 открыты до forced-crash/failure regression tests; покрытие BattlePass не означает завершение аудита Quests/Achievements/всей progression подсистемы.

## Дополнение — Main waypoint / house / repair progress producer slice (2026-11-07)

Проверены три call sites из частичного `UpdateReward` producer inventory:

- `Main.ClientEvent_SyncWP` (`Main.cs:1158-1176`) получает `X,Y` от client remote; требует character, нахождение в vehicle, отличного от отправителя server-reported driver и валидного character у водителя, затем вызывает `UpdateReward(player,126)` и пересылает waypoint. Client `src_client/main.js:360-369` вызывает событие для нем-driver vehicle occupant только при непустом waypoint. Это выглядит как сам operation task 126 (“передать метку водителю, будучи пассажиром”); явный forged-payload/range test и driver UI response остаются staging tasks. Отдельный confirmed progression bypass не зарегистрирован.
- `lockCarPressed` даёт ID 125/124 только после нахождения в EnterHouse/ExitHouse shape, `sessionData.HouseID`, owner/roommate authorization и фактического изменения замка (`Main.cs:2215-2246`). Однако IDs 124 и 125 отсутствуют в текущем Season4 task catalog, поэтому `UpdateReward` по текущему helper на них no-op.
- `RepairMyVeh` callback в `Main.cs:2416-2441` зовёт ID 13, которого также нет в current catalog; этот вызов не продвигает Season4. Сама service callback boundary отдельно заведена как `VEH-001` в `VEHICLE_REPAIR_REVIEW.md`.

Эта выборочная проверка не считается полным producer trace и не меняет 209-call-line inventory. Остальные producers и daily/weekly task assignment paths всё ещё требуют end-to-end review.
