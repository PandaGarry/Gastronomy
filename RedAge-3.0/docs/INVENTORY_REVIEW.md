# Статический review inventory remote flows

Фокус текущего прохода: `Chars/Events.cs`, `Chars/Repository.cs`, `Inventory/Tent/Repository.cs`, `Database/Models/Items.cs`, client/CEF inventory drag-and-drop. Полный inventory review ещё не завершён: use/drop/trade/storage ownership и все item handlers остаются в очереди.

## INV-001 — remote stack-move позволял увеличить stack отрицательным count

**Уверенность: высокая; приоритет: критичный.**

`Chars.Events.InventoryMoveStack` принимал `count` от клиента и напрямую передавал его в `Chars.Repository.ItemsMoveStack`. В исходном методе не было `count > 0`, `count <= source.Count` или same-slot проверки. При выборе одного и того же item/слота и `count = -1` обе переменные были отдельными копиями одной записи: target count уменьшался, затем source count увеличивался; оба `SetItemData` обновляли один SQL ID, причём последняя запись сохраняла увеличенное количество. Таким образом, remote event мог дублировать stack без соответствующего source debit.

**Локальная правка внесена, но ещё не собрана и не runtime-tested:** `ItemsMoveStack` теперь отвергает non-positive count, пустой/неположительный источник, count выше источника, совпадающие source/target slot и неподходящий target item. При полном переносе source slot очищается через запись с исходным SQL ID. Требуется проверить все легальные перемещения, per-slot max stack и SQL delete/update ordering перед закрытием issue.

## INV-002 — read-only tent inventory можно было изменять вызовом remote move

**Уверенность: высокая по коду; приоритет: критичный для сохранности имущества.**

`Inventory.Tent.Repository.OpenTent` открывает чужую палатку с `isMyTent: false`; CEF `isMove` явно блокирует передачу предметов из такого окна. Но серверные `InventoryMove`/`InventoryMoveStack` до локальной правки не проверяли owner/read-only state и в `ItemsMove`/`ItemsMoveStack` применяли команды к `sessionData.InventoryOtherLocationName`. Клиент мог обойти CEF и вызвать remote move напрямую, пытаясь переместить содержимое `tent_<owner UUID>`.

**Локальная mitigation внесена, но не проверена на runtime:** server-side `IsReadOnlyOpenedTent` теперь используется в move/stack, use, drop, drop-editor/object-placement и stack operations; только внутренний tent-purchase flow (`isBuy`) разрешён через соответствующий path. Операции с открытой палаткой другого UUID запрещаются; собственная палатка остаётся доступной. Нужны реальные tests для visitor/owner/reconnect/close/stale session и покупок.

## INV-003 — часть правил типа слота/контейнера выполняется только в клиентском CEF

**Уверенность: высокая в различии client/server paths; последствия зависят от конкретного container flow. Приоритет: высокий.**

CEF `isMove` проверяет разрешённость item/slot и container-specific rules (например, item types в safe/wardrobe/fraction storage, read-only container, tent ownership). Серверный `ItemsMove` в основном получает элементы по переданным location/index и делает `SetItemData`; соответствующая общая policy validation на server side не видна. Клиентские ограничения можно обойти вызовом remote event напрямую. Tent read-only случай отдельно закрыт локальной mitigation (`INV-002`); остальные container rules ещё не исправлены.

**Следующий шаг:** перенести shared authoritative policy в server service; привязать разрешение к server session/container instance, ownership/rank/distance/dimension и item class. Не принимать CEF `OtherInfo` как доказательство доступа. Проверить все call sites `LoadOtherItemsData` и object type mappings.

## INV-004 — item persistence queue может терять update/delete

**Уверенность: высокая; приоритет: высокий.** Файл `Database/Models/Items.cs`.

- `ItemsUpdate` (`Dictionary`) и `ItemsDelete` (`List`) пишутся из игровых операций и читаются background worker без общей синхронизации.
- Worker делает snapshot → `Clear()` до DB flush; ошибка DB/flush оставляет pending operation вне очереди; exception ловится, retry/dead-letter нет.
- Concurrent `AddItemUpdate`/`AddItemDelete` во время snapshot/clear может дать race/lost operation. `IsItemUpdate` также читает mutable dictionary без synchronization.
- `ItemsMoveStack` и `SetItemData` записывают source/target раздельно; общей транзакции inventory move нет. При crash/failure возможны устаревшая запись, восстановление удалённого предмета или несогласованные source/target.

**Исправление (не внесено):** единый thread-safe mutation queue с atomic batch handoff; durable/retryable write batches; transactional source/target mutations и conditional version/ownership checks. Тестировать DB outage, restart, concurrent moves/deletes и eventual cache/DB reconciliation.

## INV-005 — move/stack path не доказывает все slot limits и source/container access

**Уверенность: средняя/высокая; приоритет: высокий до завершения проверки.**

В текущем серверном move path нет полной серверной проверки maximum stack/carry cap и всех разрешённых пар location/slot. Подозрительные и граничные значения должны блокироваться сервером независимо от UI. В рамках текущей локальной mitigation проверены лишь negative/zero/over-source count и same-slot case; per-slot overflow, ammo special limits и доступ к остальным `other` inventory типам остаются открытыми.

## INV-006 — NoteCreate принимает произвольный item ID и всегда вставляет новую запись

**Уверенность: высокая; приоритет: средний/высокий.** Файлы `Chars/Events.cs:224-235`, `Chars/Repository.cs:6448-6488, 6920-6947`, `database/main.sql` (`notes`).

Remote `server.note.create` принимает `type`, `ItemId`, имя и текст; сервер не сверяет `ItemId` с предметом, открытым этим игроком/в его разрешённом инвентаре, и не проверяет item ownership/type. `NoteCreate` всегда делает `InsertAsync`; в `notes` нет primary/unique key на `Item_Id`, а `LoadNoteThread` читает `FirstOrDefault` по этому ID. Подмена/угадывание SQL item ID может создать запись для чужого предмета; повторные сохранения добавляют дубликаты, поэтому конкретное редактирование не гарантирует обновление показываемой записи. Имя ограничено `varchar(46)` в БД, а серверный input bound не подтверждён.

**Исправление (не внесено):** серверный expiring note-edit intent, созданный только после проверки нужного `Note/LoveNote` в допустимом location; на save сверять session intent, item SQL ID/type/ownership и bounds. Хранить одну запись на item с уникальным constraint и transactionally upsert/update; сохранять авторство/аудит где требуется. Не полагаться на CEF-переданный ID.

## Staging regression matrix

- вызвать remote stack move с count: `-1`, `0`, `1`, ровно source count, source count + 1, `int.MaxValue`; проверить source/target/DB rows.
- same source/target location+slot при любом count; inventory state должен быть неизменен.
- попытаться переместить item из чужой палатки и в неё прямыми remote вызовами; нет изменения cache или DB; собственная палатка работает.
- invalid item/slot pairs в safe/wardrobe/fraction/vehicle/warehouse; политика работает независимо от CEF.
- полное заполнение source/target stack, ammo/carry limits, пустой/устаревший container session.
- одновременно выполнять move, consume, drop, close/disconnect; затем restart и сверить точную сумму item counts и SQL IDs.
- отключить test DB на flush, затем восстановить; update/delete batch не теряется и не применяется дважды.

## INV-007 — negative case-open count увеличивал stack кейсов

Кейс-roulette item consumption — отдельный remote inventory path. До патча отрицательный `count` проходил `RouletteOpenCase`, пустой `RouletteCreate` не выдавал reward, но `RemoveIndex` вычитал отрицательное значение и увеличивал stack кейсов. Локально внесены guards в open/create и общий `RemoveIndex`; подробный call/data-flow, second-order BattlePass effect и staging matrix находятся в [ROULETTE_REVIEW.md](ROULETTE_REVIEW.md). Patch не собран и не runtime-tested.
