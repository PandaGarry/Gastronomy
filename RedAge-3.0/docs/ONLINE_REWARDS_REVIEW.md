# Time-based rewards and achievement state — статический review

Обновлено: 2026-11-07. Scope: `TimeInfo`/`Achievements` persistence, minute/hour save cadence, online-time rewards, and active fixed-index reads. Статический аудит; DB/RAGE runtime, fault injection и regression tests не выполнялись.

## Выводы

### MONEY-011 — time-based rewards can be replayed after a stale character checkpoint

**Статус: открыто; средний приоритет; высокая уверенность в source-level durability gap, фактический replay зависит от crash/partial-write ordering.** Прямой remote-triggered server crash не установлен.

Основные ссылки:

- `dotnet/resources/NeptuneEvo/Main.cs:854-856` — `savedb` запущен периодически с интервалом один час; `playedMins` срабатывает каждую минуту.
- `Main.cs:3706-3712` — каждый минутный проход обновляет `TimeInfo` в памяти (`GetCurrencyTime`, затем `TotalTime`, `TodayTime`, `MonthTime` и прочее).
- `Main.cs:3721-3754` — дневные пороги 120/180/240/300/480 минут выдают соответственно 1 RB, Case0, 2 RB, Case1, затем 4 RB + Case2; все условия — точное равенство.
- `Main.cs:3758-3762` — при `MonthTime == 18000` выдаётся 500 RB.
- `Main.cs:3520-3537` — `OnlineReward` вызывает RB grant через `Chars/UpdateData.cs:25-38` (`accountData.RedBucks += value`, затем `Money.AddDonateUpdate`) и только затем ставит notification flag; achievement не является claim/idempotency gate. `Database/Models/Money.cs:20-74` flush-ит absolute RB values отдельным worker-ом.
- `Character/Save/Repository.cs:48-100` — `Time` сохраняется как JSON-поле `Characters.Time` только в общем character save.
- `Players/Disconnect/Repository.cs:336-352` — обычный disconnect отдельно запускает account save и character save.
- `Core/Admin.cs:289-369` — `SaveServer` отдельно сохраняет character/account; вызывается часовым timer и admin command. Перечень всех `Character.Save.Repository.SaveSql` call sites в исходниках — disconnect и два admin save paths; постоянного per-minute character save нет.
- `Character/Load/Repository.cs:135-142` — при reconnect `TimeInfo` загружается из `Characters.Time`; только exception попадает в fallback. JSON literal `null` успешно десериализуется в null и не нормализуется.
- `database/main.sql:584` и generated model `Database/Server/ServerStruct.generated.cs:357` — `characters.time` имеет nullable varchar mapping/DDL (DDL задаёт default, но не `NOT NULL`).
- `Character/Models/TimeInfo.cs:12-44` — `TodayTime`/`MonthTime` находятся именно в этом сохраняемом объекте.

Между успешными character snapshots награда и checkpoint могут разойтись: RB update выполняется через независимую от `Characters.Time` account save queue/операцию, а Case grants вставляются в warehouse отдельной async DB-операцией (`Chars/Repository.cs:4050-4112`). Если durable grant уже прошёл, а процесс аварийно завершился до следующего character save (или account/item и character writes завершились частично), reconnect загрузит старый счётчик. При достижении того же exact threshold сервер снова выполнит grant. Аналогично может быть повторён месячный 500 RB reward. Возможна и обратная потеря награды, если checkpoint сохранён, а асинхронный grant ещё нет. Это не exactly-once settlement.

Graceful disconnect и hourly/admin save уменьшают окно, но не обеспечивают атомарность. Не доказано, что игрок может инициировать нужный server crash; не считать это подтверждённым удалённым exploit без воспроизведения.

**Remediation (не внедрено):** durable claim/receipt keyed by character + reward period + threshold, с уникальным constraint и атомарной фиксацией claim вместе с grant/ledger; повторный обработчик должен сверять receipt и быть идемпотентным. Для warehouse grants использовать durable operation ID/outbox, не полагаться на in-memory time checkpoint. Сохранение одной лишь частотой snapshot не является exactly-once fix.

**Regression/fault-injection:** выдача на каждом дневном и месячном пороге; crash после claim, после RB queue flush, после warehouse insert, до/во время character save; повторный login и повторный tick; DB failure каждого шага; два параллельных save/tick; доказать один persisted reward на claim и отсутствие false success/потери/дублирования. Проверить также daily reset через `GetCurrencyTime` на смене дня и месячное rollover.

### PROG-005 — deserialized short Achievements array is not normalized before fixed-index access

**Статус: открыто; низкий/средний приоритет; source path подтверждён, наличие коротких production rows неизвестно.** Это robustness/data-integrity finding, не утверждение о существующей повреждённой production DB.

- Новые персонажи получают список из 401 `false` в `Character/Create/Repository.cs`.
- При загрузке `Character/Load/Repository.cs` десериализует `character.Achiev` в `List<bool>`; успешный JSON вида `[]`/`[false]` принимается как есть и не дополняется до 401. Null/ошибка попадают в fallback 401 false, поэтому риск относится к syntactically valid short JSON.
- Активные места читают/пишут индексы 16, 17, 23, 24, 27, 18, 22 и 21 (`Main.cs`, `Events/TankRoyale.cs`, `Core/Vehicle.cs`, `Core/SeatingArrangements.cs`, `Chars/Repository.cs`). Упоминания 19/25/26 в `Chars/Repository.cs` находятся в закомментированном блоке.
- Индексация короткого списка бросает `ArgumentOutOfRangeException`; во всех найденных активных местах есть catch, поэтому подтверждённого unhandled exception/process crash нет. В `OnlineReward` локальный catch логирует ошибку после RB grant/messages (index 16 читается уже после grant). В `playedMinutesTrigger` broad catch завершает весь текущий minute pass, поэтому malformed player может помешать обработке следующих игроков; at 180/300/480 Case grant предшествует Achievement index. `TankRoyale_Tick` ловит вокруг всего tick, а `onPlayerEnterVehicleHandler`, `OnSeatingArrangements` и `UseEat` также ловят вокруг соответствующей операции/callback; short list может оборвать оставшуюся часть конкретного flow/tick. Индексы 19/25/26 находятся в закомментированном блоке.
- UI пункт achievements в `src_cef/src/views/player/menu/elements/rewardslist/index.svelte` закомментирован; активные flags в найденных местах преимущественно управляют tutorial/notification, а не служат самостоятельной защитой reward issuance.

**Remediation (не внедрено):** нормализовать успешно десериализованный список в одном load boundary: null-safe, сохранить существующие значения, дополнять `false` как минимум до максимального реально используемого индекса + 1; предпочтительно заменить magic indexes на helper/enum с bounds invariant. Не расширять автоматически malformed/oversized values без установленного upper bound/serialization policy.

**Regression:** тестировать `Achiev` JSON null/invalid/empty и list lengths 16, 17, 18, 21, 22, 23, 24, 25, 27, 28 и canonical 401; после load проверить все активные achievement sites и успешность соседних игровых действий/обработки других игроков; проверить save→reload, idempotent migration и сохранение старых true flags.


### PROG-006 — nullable `characters.time` can load as null and abort the shared minute pass

**Статус: открыто; низкий/средний приоритет; failure path подтверждён по коду/DDL, наличие affected rows неизвестно.**

`characters.time` в `database/main.sql:584` допускает SQL NULL (`varchar(250) DEFAULT ...`, без `NOT NULL`); generated `Character.Time` string mapping в `ServerStruct.generated.cs:357` тоже помечен `Nullable`. При загрузке `Character/Load/Repository.cs:135-142` `JsonConvert.DeserializeObject<TimeInfo>(character.Time)` не выбрасывает exception для JSON literal `null`, поэтому fallback `catch` не выполняется и `characterData.Time` становится null (перезаписывая model initializer `new TimeInfo()`). `Main.GetCurrencyTime` затем dereference-ит `Time.Year`/прочие поля без null check; вызов идёт из `playedMinutesTrigger` для каждого подключённого персонажа (`Main.cs:3706-3712`). Внешний catch всего `playedMinutesTrigger` (`Main.cs:3789-3792`) логирует ошибку и прекращает minute pass, включая обработку всех игроков после проблемного персонажа; пока запись не исправлена, ситуация повторяется каждый pass. Это подтверждённое поведение при null row, но реальная база не проверялась.

**Remediation (не внедрено):** в load boundary нормализовать null/empty/JSON-null/invalid `Time` в новый `TimeInfo` и записать корректное значение при ближайшем save; добавить defensive guard в `GetCurrencyTime`. На DB уровне после clean migration/backfill рассмотреть `NOT NULL` с корректным default. Ошибка одного игрока не должна прекращать обработку остальных: изолировать try/catch per player в minute loop.

**Regression:** SQL NULL, C# null, empty string, JSON `null`, malformed JSON, valid old/default JSON; load→minute tick→save→reload; null-time player перед и после здоровых игроков в очереди — все остальные должны получить один minute tick/reward, не бросать обработчик, а проблемная запись должна быть repaired. Проверить staging schema migration/backfill до установки `NOT NULL`.

## Ограничения и статус

- В исходниках нет общего achievement-list validation/migration до index reads.
- Нет evidence о частоте/наличии коротких `Achiev` rows в реальной базе.
- Не запускались C# build, MySQL fault-injection, RAGE smoke tests или crash/reconnect сценарии.
- Никакие production/security severity оценки по реальным DB данным не делались.
