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
