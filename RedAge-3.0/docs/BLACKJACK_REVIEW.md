# Статический review NewCasino Blackjack

Проверены remote handlers `server.blackjack.character_occupy_place`, `setBet`, `move`, `character_leave_place`; game state machine `BlackJackGame`, payout/disconnect paths и CEF/client controls. Это частичный статический проход; RAGE runtime не запускался.

## CAS-003 — произвольный table ID создавал неограниченные серверные table records

**Уверенность: высокая; приоритет: высокий для доступности. Локальный patch внесён, не собран/tested.**

До patch `BlackjackOpen` делал `DealerData.Add(Index, new BlackjackDealerInfo())` до проверки `characterData.InCasino`, без bounds для client-supplied `Index`. Аутентифицированный игрок мог отправлять новые `Index` и увеличивать глобальный dictionary, даже если затем обработчик отклонял его за пределами казино. Для валидного стола `SlotId` также индексировался/сохранялся без server-side seat range, а проверка одного и того же игрока была только внутри выбранного `DealerData[Index]`; повторные join requests в коротком 4-секундном setup window могли создавать несколько seat/list records.

**Локальная mitigation:** проверить `0 <= Index < BlackjackData.Count` и `1 <= SlotId <= 4`, отвергать NaN/Infinity для координат и rotation, не допускать, чтобы игрок уже находился в PlayerData/любом `DealerData.Players`, и выполнять `DealerData.Add` только после этих checks и casino eligibility. Это ограничивает unbounded-key path и повторное cross-table enlistment в обычном serialized flow. Нужны staging-тесты; общий dictionary всё ещё требует concurrency review.

## CAS-004 — BlackjackOpen доверяет координатам клиента и телепортирует игрока

**Уверенность: высокая; приоритет: критичный для server authority. Не исправлено.**

`characterData.InCasino` выставляется при серверном взаимодействии с casino portal (`MoneySystem/Casino.cs`), но `BlackjackOpen` принимает от клиента `PosX/PosY/PosZ/Rotation` и прямо выполняет `player.Position = new Vector3(...)`, не сверяя эти координаты с выбранным столом/seat или серверной геометрией. До локальной проверки enum client мог также прислать invalid table/seat IDs; после нового bounds guard произвольный teleport по still-unvalidated finite coordinates остаётся возможен. Клиентский `blackjack.js` формирует легальные seat coordinates из локального `cfg/main.js`, но эти значения не являются доказательством доступа и могут быть подменены.

**Исправление не внесено:** нужен server-owned table/seat position map (либо доверенная entity/colshape context), а сервер должен сам вычислять destination и rotation. Добавить dimension/interior и proximity/access validation; не принимать координаты назначения от клиента. Требуется staging test с remote вызовом из казино на произвольную позицию и проверка casino-state cleanup. Не заменять на приблизительный общий bounding box без проверки геометрии/переходов.

## CAS-005 — move event не подтверждает активный ход и разрешённость Split/Double

**Уверенность: высокая; приоритет: высокий для правил/ожиданий казино. Не исправлено до полного state-machine/staging review.**

`BlackjackMove` лишь проверяет `PlayerData.ContainsKey(player)` и записывает произвольную `move` string; он не сверяет `DealerFocus`, фазу `BJTableData.State`, активный decision window или допустимое действие в данной руке. Обработчик состояния позже потребляет `bInfo.Move`.

В state machine первой руки (`Blackjack.cs`, около 650–750) сервер обрабатывает `double` и `split` для `bInfo.Hand.Count < 5`, но не проверяет для double исходное число карт/однократность, а для split — ровно две карты равного rank и отсутствие уже существующей split hand. UI (`blackjack.js::openBtn`, CEF `index.svelte`) показывает double только при двух картах и split только для пары; прямой remote вызов обходит эти клиентские правила. Double/split списывают дополнительную ставку, меняют `Rate` и меняют ожидаемый odds/payout path. Возможны также заранее queued move values до active turn.

**Исправление не внесено:** нужна authoritative action policy в server state machine: активный player/turn/phase, строгий enum, no queued stale moves, double только при допустимом hand count, split только при допустимой паре/одном split (по согласованным правилам). Перед изменением правил сверить intended blackjack semantics; тестировать все переходы split/double/hit/stand и таймауты на staging.

## CAS-006 — повторный `setBet` повторно списывал деньги, но заменял сохранённый bet

**Уверенность: высокая по code flow; приоритет: средний для баланса игрока. Patch внесён, не собран/tested.**

CEF после отправки `setBet` сразу ставит `isBet=false`, однако до patch сервер не проверял `bInfo.Join`. Повторный forged `server.blackjack.setBet` при ещё не начавшейся игре заново списывал `money`, затем перезаписывал `bInfo.Rate = money`; предыдущая ставка оставалась списанной, но не учитывалась в игровом settlement/refund. Кроме того, результат `Wallet.Change` игнорировался, после чего игроку ставили `Join=true` и запускали game timer даже при неуспешном списании.

**Локальная mitigation:** уже поставивший ставку игрок (`bInfo.Join`) не может повторно submit до нового hand lifecycle; ставочная state mutation выполняется только после успешного `Wallet.Change`. Легальная CEF-последовательность отправляет один bet за руку; проверка повторного setBet и отказа Wallet.Change требуется на staging.

## CAS-007 — table-specific bet maximum проверяется только в CEF

**Уверенность: высокая в различии client/server; приоритет: высокий при intended CEF limits. Patch не внесён.**

CEF даёт min/max в зависимости от стола (минимум 50, максимум 25,000 или 100,000), но `SetBet` на сервере отвергает только `money < 50` и проверяет, что у игрока хватает денег; server-side max/table configuration нет. Поэтому direct remote request может поставить выше UI maximum. Payout/state code использует `int` (`bInfo.Rate * 2`, split/double multiplication, `wincount`), так что очень крупный forged rate может overflow/испортить settlement, даже если ordinary UI values безопасны.

**Исправление не внесено:** подтвердить intended limits у владельца; перенести min/max в server-owned config, использовать checked/bounded payout arithmetic и тестировать extreme funds/overflow. Не вводить балансные значения только на основании CEF без staging/согласования.

## Проверки на staging

1. `character_occupy_place`: invalid/extreme table/seat IDs, spam новых IDs до casino entry, повторные/параллельные join на нескольких столах, NaN/Infinity/вне casino coordinates; сверить `DealerData`, `PlayerData`, seat lists, session и player position.
2. Перехватить/подменить `PosX/Y/Z/Rotation` с действительного casino entry; сервер должен выбирать только destination выбранного server-side table/seat; сверить dimension/interior/position.
3. `setBet`: valid min/max, below/above, второй submit до старта, игровой старт между requests, insufficient funds/forced `Wallet.Change=false`; balance, `Rate`, `Join`, chips/logs должны соответствовать ровно одной принятой ставке.
4. `move`: любой move до начала, не в свой ход, вне decision phase, stale/replay; `split` для не-пары, после hit и повторный split; `double` после hit/повторный; нельзя менять wallet/hand по запрещённому действию.
5. Проверить high stakes/overflow boundaries, split+double settlement, natural blackjack, dealer bust, push, player/dealer disconnect/death и failure/reconnect reconciliation.

## Границы

`CAS-003` и `CAS-006` — narrow server input/state mitigations, пока unverified. `CAS-004/005/007` остаются открытыми. Нет C# build, MySQL test DB или RAGE runtime; payout и действия не тестировались в игре.
