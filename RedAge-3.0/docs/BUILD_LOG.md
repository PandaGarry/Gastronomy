# Журнал сборки и проверок

Не добавлять сюда секреты, токены, production endpoints или содержимое credential-bearing файлов.

## Baseline — 2026-11-07

### Среда

- Node.js `v22.22.3`, npm `10.9.8`; .NET SDK/MSBuild/Mono, MySQL/MariaDB и Docker отсутствуют.
- RAM sandbox около 3.8 GiB.
- Snapshot частичный; отсутствуют RAGE:MP runtime/server binaries, полные `client_packages` и часть UI/game assets.

### Статические проверки

- JSON: 167 из 167 файлов успешно разобраны Python JSON parser.
- JS syntax: 335 из 337 файлов проходят `node --check`. Два исключения описаны в `ISSUES.md` и сейчас не находятся в активных entry/import цепочках.
- Credential scan: обнаруженные в `Main.cs` hard-coded/commented website DB credentials удалены из локальной копии; после очистки scan не нашёл literal DB connections, secret assignments или private keys в проверенных исходниках. Upstream остаётся неизменённым; владелец должен проверить/ротировать свои значения.
- SQL seed: три файла содержат 145 `CREATE TABLE` declarations и MySQL-specific procedures/`DELIMITER`. Импорт не выполнялся; нужен настоящий disposable MySQL, generic parser недостаточен.

### Client webpack

- Временная копия `src_client`; `npm install --ignore-scripts --no-audit --no-fund`; `NODE_OPTIONS=--openssl-legacy-provider npm run build -- --mode production`.
- Результат: **успешно**, webpack `5.112.2`; bundle около 1.12 MiB в этой разрешённой временной сборке.
- Build был в `/tmp`; исходники и production output в RedAge snapshot не менялись. Без tracked lockfile результат пока не воспроизводим.

### CEF/Svelte

- Обычный install: **ERESOLVE** из-за peer требования `cache-loader@4.1.0` (webpack 4) при manifest webpack 5.
- Временный install с `--legacy-peer-deps` прошёл. `npm audit` на его временном resolved graph: 49 advisories (5 critical, 21 high, 22 moderate, 1 low); upstream lockfile отсутствует.
- Build с неполным snapshot: **неуспешен ожидаемо** из-за не включённых изображений/шрифтов/медиа, 1256 webpack errors и многочисленные Svelte accessibility warnings.
- Полные `src_cef/src` assets получались только во временную папку для проверки; production webpack завершился OOM/exit 137 на лимите памяти среды. Второй запуск с отключённой минификацией тоже завершился exit 137. В RedAge source folder эти дополнительные assets не копировались.
- Следующий запуск CEF — на более мощном build-agent после фиксации Node/npm/lockfile; посмотреть источник большого потребления RAM (minification, source maps, asset graph).

### Не выполнено

- .NET compile/test — заблокировано отсутствием .NET SDK.
- SQL import и backup/restore — заблокированы отсутствием MySQL/MariaDB.
- RAGE:MP server/client smoke test — заблокирован отсутствием полного runtime/assets и рабочего staging.


### 2026-11-08 — money/bank patch validation environment

- Checked the active execution environment: `dotnet`, `msbuild`, `csc`, `mcs`, `mysql` and `mariadb` are not installed.
- Therefore no C# compilation, unit/integration execution or MySQL fault injection was performed for MONEY-002/MONEY-003/property settlement patches.
- Static source assertions were executed against the current `redage/audit-continuation` branch for bank locking, two-leg transfer mutation, positive amount/overflow guards, one-shot ATM confirmation, revision-aware save retry, dirty marking, concurrent delete queue, and migrated bank/property call sites. Assertions passed; they are not a substitute for compiler/runtime tests.
- RAGE:MP staging and multi-client tests remain unavailable. Do not close affected findings or claim runtime validation.


### 2026-11-08 — MONEY-002 worker follow-up static verification

- Source patch: one-worker startup guard, `Task`-based loop with nonblocking delay, and `AddMoneyUpdate` validation against UUID and signed DB INT balance range.
- Static assertions checked the guard, async worker signature, delay, range validation and removal of blocking `Thread.Sleep`. Assertions passed; no C# compiler is available, so compilation was not performed.
- No concurrency test, MySQL fault injection, restart/crash durability test or RAGE staging test was run. Queue remains in-memory only.


### 2026-11-08 — MONEY-036 wallet range patch static assertions

- Re-fetched the working-branch sources and asserted: `Wallet.Change` uses checked `long` addition; rejects negative and above-`Int32.MaxValue` results before mutation; full `Character.SaveSql` rejects invalid balances before bank/other save side effects; generated DB model still maps `characters.money` to signed `int(11)`; `Money.AddMoneyUpdate` validates its snapshot range; offline auction refund validates DB balance and widened result before narrowing.
- Assertions passed after correcting one documentation-status matcher. These are textual/static assertions, not C# compilation or executable unit tests.
- Environment check: Node `v22.16.0` present; `dotnet`, `msbuild`, `csc`, `mcs`, `mysql` and `mariadb` unavailable. No build, DB round-trip/fault injection, worker concurrency or RAGE UI test was performed.


### 2026-11-08 — MONEY-002 detached worker hand-off static review

- Verified the queue snapshot marks each detached UUID in `ActiveMoneyWrites` under the same `QueueLock` before `MoneyUpdateList.Clear()` and before DB context creation. This ensures a small `Wallet.Change` during the detach→SQL interval queues a newer revision.
- Verified one snapshot marker loop and one cleanup in `RequeueMoney`; normal `MoneyUpdate` cleanup remains in its per-row `finally`. Revision checks prevent an old detached absolute snapshot from overwriting a newer full-save/wallet version.
- Verified `SaveSql` uses `ExecuteCharacterSave` and the shared UUID synchronization lock; `Wallet.Change` advances the revision while holding the same monitor.
- Static source assertions only. No .NET compiler, MySQL instance or RAGE:MP runtime available; no concurrency/fault-injection test executed.
