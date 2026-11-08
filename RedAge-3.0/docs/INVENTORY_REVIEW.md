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


## INV-012 — vehicle trunk inventory lacks per-operation session/access revalidation

**Уверенность: высокая в отсутствии повторных проверок; приоритет: средний/высокий, open-trunk access policy requires owner confirmation.**

- `Core/Selecting.cs:372-381` checks only that the supplied vehicle exists and is within 5m. In `vehicleSelected` branch 3 (`:471+`), the server allows vehicle inventory for Personal/Garage/Fraction/Organization/OrganizationGarage access types. For non-admins it checks that the trunk is open, but does not repeat the owner/key, fraction membership, organization membership or minimum-rank checks present in branch 1 when opening the trunk.
- The branch sets `vehicleLocalData.BagInUse`, stores the vehicle in `sessionData.SelectData.SelectedVeh`, and calls `LoadOtherItemsData` with the vehicle SQL ID/plate. `LoadOtherItemsData` (`Chars/Repository.cs:2877-2903`) calls `OtherClose` and stores only `sessionData.InventoryOtherLocationName`; it does not bind an authorized vehicle-inventory session with expiry, position, dimension, door or access data.
- Generic inventory remotes `server.gamemenu.inventory.move`, `.move.stack` and `.use` (`Chars/Events.cs:185-219`) directly call `ItemsMove`, `ItemsMoveStack` and `ItemsUse`. Those methods (`Chars/Repository.cs:4882-4965`, `4933+`, `5305+`) check the special read-only-tent state but do not revalidate vehicle owner/key/rank, distance, dimension, door state or that the selected vehicle is still the active container. `ItemsUse` on `ArrayName == "other"` adds the item to the caller's inventory and clears the other slot.
- Consequently, once a vehicle container is opened, subsequent direct inventory operations rely on the mutable session location string. A modified client can attempt extraction after moving away, changing dimension, closing/replacing the vehicle context, or losing membership/access. Initial 5m proximity and trunk-open checks do not protect later operations. The exact event sequence and whether a public open trunk is intended to be lootable by any nearby player require staging and gameplay-owner policy confirmation.

**Impact boundary:** no claim of confirmed theft or successful cross-owner extraction is made. Static evidence establishes missing server-side per-operation context revalidation and a generic item extraction path. If open-trunk public access is intended, the missing proximity/session freshness checks remain a separate concern.

**Remediation (not implemented):** issue a short-lived vehicle-inventory intent bound to player, exact vehicle entity/plate, access class, holder/key or faction/org membership and rank, position/dimension, trunk state and expiry. Validate/consume this intent on every move/stack/use/drop endpoint; close/revoke on movement, dimension change, door close, vehicle deletion/replacement, membership/key revocation, timeout and disconnect. Keep the policy for physically open trunks explicit, but never let a stale `InventoryOtherLocationName` alone authorize a mutation.

**Regression:** open own, key-shared, foreign, faction, organization and organization-garage trunks; test member/rank changes and open-trunk public policy. After opening, walk beyond 5m, change dimension, close trunk, despawn/replace vehicle, revoke key/leave faction or organization, and replay direct move/stack/use/drop events using `other`; all stale contexts must be rejected without cache/DB changes. Verify legitimate nearby authorized access and normal close/reopen. Requires disposable RAGE/MySQL staging.


## Container entry-point map — static continuation (2026-11-08)

The LoadOtherItemsData call-site search found these server container families. This is an entry-point inventory, not proof that every policy has been fully tested:

- Vehicle: Core/Selecting.cs vehicleSelected branch 3; one-time access/trunk/range checks are not rebound to each item operation (INV-012); reservation cleanup gap is VEH-012.
- Furniture safes: Core/Selecting.cs object selection passes a furniture_<houseId> location after the object/house interaction flow. Generic item remotes do not revalidate that same house/object context on every mutation; retain under INV-003 pending complete ACL/ownership trace.
- Fraction stocks: Fractions/Fbi.cs, Sheriff.cs, Army.cs, Cityhall.cs, Police.cs and Fractions/Manager.cs. Entry flows check faction, duty/open-stock and/or rank, but OnFracStock is not reset; openWeaponStock checks only current fraction ID and rank, not duty/open-stock/location/dimension. This stale session is tracked as INV-015; generic move/stack/use handlers still do not repeat active authorization.
- Organization stock: Organizations/Manager.cs checks organization status, stock-open state and InsideOrganizationID at open; generic item mutations do not repeat membership/rank/stock state.
- Personal warehouse: Chars/Stock.cs opens warehouse_<character UUID> through the quest Perform flow. The storage key is player-specific; verify quest-intent and postal-stock location/session on staging rather than assuming NPC UI is a server authorization boundary.
- Tents: Inventory/Tent/Repository.cs opens own or visitor tent. Visitor read-only server guards are tracked in INV-002; stale own/visitor context remains in INV-003 scope.
- AirDrop: Events/AirDrop/Repository.cs has separate hack, lock-progress and loot-open remotes; missing exact drop/dimension/proximity binding is INV-013.
- MatWar: Fractions/Manager.cs has separate start-hack, lock-progress and loot-open remotes; missing active-war/spatial/session binding and stale event inventory lifecycle are INV-014.
- HeliCrash: Events/HeliCrash/Repository.cs opens through the HeliCrash colshape interaction; verify exact crash object/range/dimension and session freshness for every item operation under INV-003.
- Weapon components / key ring: Chars/Repository.cs also uses LoadOtherItemsData for weapon_<itemSqlId> and CarKey_<itemSqlId>; these are item-owned subcontainers and require source-item ownership/existence checks on every mutation.

Across these families, ItemsMove, ItemsMoveStack and ItemsUse remain shared mutation endpoints. Entry-time ACL checks are not a substitute for server-side validation of the current container intent, owner/object identity, player location/dimension, role/rank and allowed item/slot pairs. Keep INV-003 as the umbrella policy gap and concrete INV-012..014 findings as separate entry-point cases.

- Organization stock: Organizations/Manager.cs checks organization status, stock-open state and InsideOrganizationID at open; RemovePlayer clears InsideOrganizationID without closing/revoking the container, while generic item mutations do not repeat membership/rank/stock state. Post-exit stale context is tracked as INV-016.

- Furniture safes: Core/Selecting.cs objectSelected checks the object, range, InsideHouseID and owner/roommate/burglary access at open. HouseManager.RemovePlayer clears InsideHouseID on exit without closing the container; generic item mutations do not repeat those checks. Post-exit stale context is tracked as INV-017.


## Remaining container traces — open, not yet registered as findings (2026-11-08)

- Personal warehouse: WarehouseEnter/WarehouseExit switch IsInPostalStock and dimension, but WarehouseExit does not close the other inventory; Stock.Perform opens the per-character UUID storage without checking IsInPostalStock. qMain.QuestPerform does require an active npc_stock quest record, but no current NPC-range/warehouse-dimension check was found in this path. The storage key is the caller's own UUID, so the currently supported impact is a location-rule bypass for personal storage, not cross-player theft. Confirm intended design before creating an issue.
- HeliCrash: opening is reached through a server colshape interaction; InHeliCrash uses the box health/key-clamp state, while OpenHeliCrash itself does not revalidate the current box index/health. The generic item handlers do not bind operations to the current crash box or range, and no explicit close-on-leave path was found. Confirm interaction framework guarantees and event lifecycle on staging.
- Weapon and CarKey subcontainers: ItemsUse opens weapon_<parent SqlId> and CarKey_<keyring SqlId>. LoadOtherItemsData stores only the location string; it does not store a server-side parent-item intent. Generic mutations do not revalidate that the parent weapon/keyring still exists and remains owned by the player. Trace trade/drop/delete/replacement and close behavior before registering a separate finding.

These remain audit TODOs, not confirmed vulnerabilities. Add owner-approved behavior and direct-remote regression tests before closing the container audit.

- HeliCrash key clamp: InHeliCrash installs KeyClampData before GetHealth checks ArmyLockpick; generic keyClamp.end trusts client value and HeliCrash End can unlock on value 0 without proving a successful keyDown/reservation. This is a distinct high-severity remote bypass tracked as INV-018; see HELICRASH_KEYCLAMP_REVIEW.md.


## INV-019 — weapon/key-ring parent ownership is not rebound to the open subcontainer

Static trace completed:
- Weapon component and key-ring panes are opened from parent SqlId; LoadOtherItemsData records only `InventoryOtherLocationName`.
- GetLocationName/GetItemData/SetItemData route generic `other` mutations through that string without verifying parent existence or current owner.
- ItemsMove/ItemsMoveStack/ItemsUse do not revoke the pane when the parent moves; ItemsUse can retrieve child items into the caller inventory.
- The source-level stale-context path is confirmed. Cross-owner extraction and any client-side automatic close behavior remain staging questions; no live theft/duplication is claimed.

See `WEAPON_KEYRING_SUBCONTAINER_REVIEW.md` for remediation and the regression matrix. Warehouse location policy and HeliCrash open/range lifecycle remain explicit, bounded staging/policy TODOs rather than asserted findings.
