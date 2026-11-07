# Статический review NewCasino Horses / Inside Track

Проверены `NewCasino/horses/Horses.cs`, `Roulette/BetData.cs`, client `src_client/casino/horses/index.js`, CEF `src_cef/src/views/casino/horse/index.svelte`, общий disconnect path `Players/Disconnect/Repository.cs` и `SessionData.IsCasinoGame`. Проверка статическая; RAGE race, DB settlement и reconnect tests не выполнялись.

## CAS-012 — выигравшая лошадь раскрывается до disconnect-refund deadline

**Уверенность: высокая по code flow; приоритет: критичный для денежной целостности. Не исправлено.**

В `ChoiceRaters` сервер выбирает `WinHorse`, ставит его первым в передаваемом порядке и отправляет всем игрокам в casino radius `client.horse.START_RACING(seed, WinHorse, ...)`. Перед отправкой устанавливается `GameStart = DateTime.Now.AddSeconds(3)`. Следующий этап завершает race через 15 секунд.

`Horses.Disconnect` возвращает полную ставку, если `Bet > 0 && GameStart >= DateTime.Now`, и вызывается как центральным disconnect handler, так и `PlayerDeath`. Получив `START_RACING`, игрок видит winning horse в аргументе `firstHorse`; если его ставка проигрывает, он может намеренно disconnect/death до трёхсекундного deadline и получить ставку назад, а выигравшую ставку оставить в игре. Это исходозависимый выбор после публичного раскрытия результата.

**Исправление не внесено:** согласовать аварийный disconnect policy. Нужен server-owned round/bet lifecycle с чётким commit-before-reveal, exactly-once outcome settlement и offline payout; не удалять refund grace без оценки crash/network-timeout semantics.

## CAS-013 — bet remote не связан с активным casino session или физическим местоположением

**Уверенность: высокая; приоритет: высокий, если доступ к ставке должен быть только через игровой стол. Не исправлено.**

`server.horse.setBet` обрабатывает `CMD_SelectHorse` и проверяет character, global `curentScreen == 0`, `HorsesWorking` и `CanIChange`. Он не проверяет `SessionData.IsCasinoGame == "Horses"`, факт `SIT_SLOT`, proximity/interior/dimension или нахождение игрока в casino. Поэтому прямой remote event может делать ставку в течение betting phase из любого места.

Дополнительно `SIT_SLOT` не подтверждает server-side позицию/interior и ставит `IsCasinoGame = "Horses"`; client-side interior ID/colshape не являются authorization. Это позволяет обойти UI interaction и может затронуть другие casino/session restrictions.

**Исправление не внесено:** определить intended physical access policy; затем проверять активный server-side session/round и authoritative casino interaction/location. Тестировать forged bet без SIT_SLOT, вне casino, в другом dimension/interior и в другой casino game.

## CAS-014 — horse, stake, debit и payout не проверяются как единая операция

**Уверенность: высокая; приоритет: высокий для денежного состояния и прогресса.**

CEF задаёт horse ID `1..6` и ставку `$500..$50,000`. Server handler не валидирует `horse`, минимальную/максимальную сумму и принимает `money == 0`, поскольку `UpdateData.CanIChange` запрещает отрицательные значения, но считает ноль допустимым. `PlayerData.Add` выполняется до `Wallet.Change`, а bool result списания игнорируется. Нулевой bet может всё равно выдать BattlePass reward `55` и изменить quest stage/completion; при concurrent balance changes неуспешное списание способно оставить активную ставку.

При выигрыше выплата строится как `int payment = Bet + Convert.ToInt32(Bet * 2)` (фактически 3x gross) с арифметикой `int`; результат `Wallet.Change` игнорируется, но пишутся casino/money logs и success notification. CEF maximum не защищает forged remote stake, поэтому при большом доступном балансе умножение/сложение может overflow и изменить payout sign/amount. Неизвестный horse ID не может совпасть с `WinHorse 1..6`, но может быть принят как заведомо проигрывающая ставка.

**Исправление не внесено до подтверждения intended limits:** валидировать horse enum и approved min/max; атомарно/идемпотентно принимать только после подтверждённого debit; рассчитывать payout в checked `long` и проверять wallet bounds; rewards/logs/state менять только после принятия ставки.

## CAS-015 — `TEARS_SLOT` произвольно сбрасывает общий casino-session marker

**Уверенность: высокая; приоритет: средний/высокий для session authorization.**

`server.horse.TEARS_SLOT` не проверяет `IsCasinoGame`, наличие активной horses session или `PlayerData`; любой вызов для игрока с `SessionData` отправляет client close event и делает `sessionData.IsCasinoGame = null`. Этот marker также используют Blackjack/Roulette/Spin и он блокирует некоторые командные действия (например, cuff/dice). Игрок может вызвать horse event, оставаясь записанным в другом casino `PlayerData`, и снять только общий guard. Обратная сторона — `SIT_SLOT` без проверки текущего marker может перезаписать другой casino marker значением `Horses`.

**Исправление не внесено:** привязать teardown к owning game/session token; reject cross-game session overwrite/clear и проверять, что player действительно вышел из соответствующего game state. Проверить допустимый порядок `CMD_SelectHorse -> tears_slot`, так как обычный bet handler сам очищает marker сразу после ставки.

## CAS-016 — exception/concurrent mutation может навсегда остановить глобальный race scheduler

**Уверенность: высокая в failure-state flow; вероятность гонки требует runtime confirmation; приоритет: высокий для доступности и settlement.**

`GameInterval` выставляет глобальный `StateInWork = true` перед обработкой переходов и возвращает его в `false` только в конце успешной ветки; внешний catch лишь логирует исключение. При исключении `GameStatus` может остаться `Racing`/`WinScreen`, а следующий tick сразу выходит из-за `StateInWork == true`, что блокирует весь будущий race lifecycle.

В ветке `Racing` перечисление `PlayerData.Keys` защищено `lock(PlayerData)`, но `CMD_SelectHorse` вызывает `PlayerData.Add` до lock, `Disconnect` делает `Remove` без lock, а `WinScreen` заменяет весь dictionary без lock. Disconnect во время payout enumeration может кинуть collection-modified exception после частичных выплат; catch оставит scheduler stuck и последующие wagers/outcomes не обработаются. Другие исключения во время per-player payout имеют аналогичный risk.

**Исправление не внесено:** единая сериализация state transitions и все dictionary mutations под тем же lock/actor; `try/finally` для StateInWork; отдельный идемпотентный per-bet settlement с обработкой ошибок без потери остальных игроков. Fuzz concurrent bet/disconnect/death и injected payout/notification failures на test DB.

## Вероятности и расчёт выплат

`WinHorse = random.Next(1, 7)` равномерно выбирает одну из шести лошадей. Результат вставляется в позицию `curentRandomHours[0]` и передаётся как `firstHorse`; bet на совпавшую лошадь получает `Bet + 2*Bet`, то есть 3x gross. При равном выборе и одинаковом multiplier для каждого номера теоретический gross return составляет `(1/6) * 3 = 50%` ставки, net expected result — `−50%`. Это арифметика текущей static policy, не подтверждение того, что владелец утвердил такой house edge. Используется обычный `System.Random`; crypto-grade RNG/seed unpredictability для ставок не подтверждены.

## Проверки на staging / test account

1. Попытка `setBet` без `SIT_SLOT`, вне casino, в чужом dimension/interior; horse IDs `0`, `7`, `int.MinValue`/`int.MaxValue`; проверить отсутствие wallet/quest/reward mutation.
2. Bets `$0`, negative, 1, CEF min/max, выше `$50,000`, близко к `Int32` overflow, insufficient funds и forced `Wallet.Change=false`; сверить balance, `PlayerData`, quest/BattlePass, logs, notification и result.
3. На обычном `START_RACING` выяснить, видит ли клиент/модифицированный клиент `WinHorse` до settlement; disconnect за 0–3 секунды после reveal при проигрышном и выигрышном outcome, смерть, network timeout, reconnect/restart.
4. Прямой `TEARS_SLOT` при активном Blackjack/Roulette/Spin; проверить сохранность server PlayerData и требуемых cuff/dice restrictions; проверить ordinary Horse bet teardown.
5. Во время `GameInterval` спровоцировать disconnect/death, параллельный bet около phase edge и injected exceptions; убедиться, что `StateInWork` сбрасывается, следующая гонка запускается, все bets settle exactly once.
6. Simulate server crash до/после bet debit, winning result, wallet credit и log/notification; определить durable ledger/recovery requirements.

## Границы

CAS-012..016 статически подтверждены по локальному control flow, но не проверены в RAGE runtime/DB. Требования к house edge, stake limits, disconnect refunds и физическому доступу к horses table нужно согласовать. Не считать gambling coverage завершённым.
