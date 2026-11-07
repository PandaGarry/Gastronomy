# Статический review NewCasino Lucky Wheel

Проверены `NewCasino/LuckyWheel/LuckyWheel.cs`, клиентские `src_client/casino/luckyWheel/index.js` и `events.js`, `CharacterData.IsLucky`, save/reset paths и prize-grant helpers. Это статический проход; animation, persistence, inventory-full и concurrency cases не запускались.

## CAS-017 — daily prize можно инициировать remote event из любого места; cooldown общий на всех

**Уверенность: высокая; приоритет: высокий для доступа к бесплатным prizes и доступности. Не исправлено.**

`luckywheel.cometoluckywheel` вызывает `ComeToLuckyWheel`, который проверяет только глобальный `WaitFor` и `player.CharacterData.IsLucky`. Server-side proximity, interior/dimension, casino entry, alive/cuffed state и character/session null guard отсутствуют. Client проверяет расстояние 3 m, но forged remote обходится. После вызова сервер назначает исход и ставит shared data; `luckywheel.finishspin` может завершить приз напрямую, без подтверждения, что игрок стоял у колеса или прошёл animation flow.

`WaitFor` — один общий static `DateTime` для всего сервера, который eligible игрок обновляет на 21 секунду. Поэтому remote-only игрок может инициировать daily spin и одновременно блокировать остальные попытки на global cooldown. Это может быть intended сериализацией одного физического колеса, но сервер не привязывает её к владельцу/позиции; массовые аккаунты способны удерживать global cooldown. `ComeToLuckyWheel` также dereference-ит `player.CharacterData.IsLucky` до null-check.

**Исправление не внесено:** server-side casino proximity/interior/dimension/access validation; per-player persisted claim state + server-owned wheel lock с owner/expiry/token; explicit character/session validation и rate limiting. Отдельно решить, действительно ли один физический wheel должен блокировать весь сервер 21 секунд.

## CAS-018 — частичная/неуспешная выдача всё равно потребляет daily spin

**Уверенность: высокая по code flow; приоритет: высокий для reward consistency.**

`FinishSpin` вызывает призовые методы, затем всегда сбрасывает shared keys и ставит `CharacterData.IsLucky = true`; успешность grant обычно не проверяется:

- денежный outcome и заполненный-инвентарь compensation вызывают `Wallet.Change`, но bool result игнорируется; игроку всё равно отправляется общий success announcement и daily eligibility расходуется.
- clothes/unique costume вызывают `AddNewItem`, но возвращаемый slot ID/status игнорируется. Костюм состоит из трёх отдельных inserts (`Feet`, `Leg`, `Top`), без предварительного inventory capacity check/transaction; возможна частичная выдача с тем же `IsLucky=true`.
- weapon/mystic ветки проверяют free slot, но не проверяют результат `WeaponRepository.GiveWeapon`/`AddNewItem`; inventory меняется между preflight и grant.
- vehicle: при общем max vehicle count есть денежная compensation; но при достижении max конкретного garage ветка только показывает уведомление и `return`-ит без машины и без compensation. Внешний `FinishSpin` затем всё равно сообщает `Эксклюзивная машина`, очищает shared state и ставит `IsLucky=true`.
- `VehicleManager.Create` не возвращает grant status в этом call site; его результат нельзя reconcile-ить с wheel claim.

`IsLucky` сохраняется в `Character.Save.Repository.SaveSql`; на disconnect character save ставится в отдельный async task. Мгновенный crash после prize grant и до durable save может потерять daily marker; устойчивость marker/prize pair к crash не доказана.

**Исправление не внесено:** сформировать prize plan и проверить capacity/garage до claim, транзакционно/идемпотентно выдать приз или однозначную compensation, потребовать success result каждого grant; durable claim ID/ledger должен записываться ровно один раз с prize outcome. Test full inventory/garage, grant return failure, DB failure/restart, fast disconnect/reconnect.

## CAS-019 — wheel claim state не оформлен как durable consume-once operation

**Уверенность: средняя; concurrency/replay требуется runtime confirmation; приоритет: высокий для бесплатного ценного prize.**

`LUCKY_WHEEL_CALL`/`LUCKY_WHEEL_WIN` — две shared-data keys; `SpinLuckyWheel` лишь заново записывает `CALL=true`, не меняя state на `Started`/`Claiming`. `FinishSpin` не consume-ит claim до внешних side effects и не имеет explicit lock, nonce, result receipt или per-player processing guard. Обычный последовательный повтор после успешного finish становится no-op, поскольку shared keys сброшены; поэтому без concurrent/reentrant behavior duplicate grant не утверждается. Но exceptions/partial side effects до reset могут оставить claim доступным для повторного finish, а disconnect/restart/persistence не связаны с durable receipt. `CharacterData.IsLucky` устанавливается лишь в конце выдачи.

**Исправление не внесено:** explicit states `Reserved -> Spinning -> Claiming -> Granted`, atomic consume/unique daily claim before external effects, persistent grant receipt и recovery/retry/compensation. Подтвердить точную сериализацию remote callbacks RAGE и проверить simultaneous/replay calls.

## Розыгрыш: статически рассчитанные категории/ожидания

`Rnd.Next(0,20)` делит исходы на 20 nominally equiprobable slots. Текущая mapping:

| Категория | Wheel indexes | Доля |
|---|---|---:|
| Одежда | 0, 8, 12, 16 | 20% |
| Игровые деньги | 2, 6, 14, 19 | 20% |
| Эксклюзивная машина | 18 | 5% |
| Мистический предмет | 1, 5, 9, 13, 17 | 25% |
| Оружие | 3, 7, 10, 15 | 20% |
| Уникальный костюм | 11 | 5% |
| RedBucks | 4 | 5% |

Для cash outcome `Rnd.Next(1780, 62742)` выдаёт `[1780, 62741]`, среднее `32,260.5`; ожидаемый фиксированный cash component — **$6,452.10 за одну daily spin** (20% × mean amount). RedBucks outcome `Rnd.Next(50,100)` выдаёт `[50,99]`, mean `74.5`; ожидаемый RB component — **3.725 RedBucks за spin** (5% × mean). Это не полный economic EV: vehicle, equipment, clothing и fallback compensation требуют согласованных value assumptions. .NET `Random` uniform/predictability assumptions и actual timing/reset policy не runtime-tested.

## Staging/test account matrix

1. Call `luckywheel.cometoluckywheel` и `luckywheel.finishspin` без нахождения у колеса, outside casino/interior/dimension, без loaded character; проверить выдачу, errors, daily marker и другие игроки.
2. Два игрока одновременно, rapid/replay `ComeTo`, `Spin`, `FinishSpin`, incomplete/disconnected animation и общий 21-second lock; проверить exclusive owner, rate limit и no duplicate prizes.
3. По каждому из 20 исходов сверить exact item/cash/RB/vehicle grant, notifications, `IsLucky` и logs; inventory full по каждому item grant, три-part costume partial failure, garage global/type cap, insufficient/overflow wallet, failed `VehicleManager.Create`/`AddNewItem`/`GiveWeapon`.
4. Disconnect/crash сразу до, во время и после reward; reconnect после async character save failure/restart; проверить daily reset и durable exactly-once claim.
5. Сверить вероятностную mapping и ожидаемый fixed cash/RB component с approved game economy; не вводить prize value changes без владельца.

## Границы

CAS-017..019 основаны на source/CEF/save-path review, но не подтверждены RAGE runtime/DB. Ключевой scope — server-side eligibility, award idempotency/failure consistency и ownership/global cooldown policy; не считать казино полностью проверенным.
