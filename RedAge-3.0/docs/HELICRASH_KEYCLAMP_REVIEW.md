# HeliCrash key-clamp remote review

## INV-018 — direct keyClamp.end can bypass HeliCrash lockpick and minigame

**Приоритет: высокий; direct-remote bypass statically confirmed. Runtime reproduction not performed.**

### Evidence

- Events/HeliCrash/Repository.cs InHeliCrash (:469-501) installs KeyClampData for the player while the player is inside a locked HeliCrash box colshape. It assigns EndCB = End and GetHealthCB = GetHealth, then calls KeyClamp.SetKeyClamp. This happens before GetHealth is invoked and before the server verifies possession of an ArmyLockpick.
- The ArmyLockpick check is inside GetHealth (:561-589), which is reached through the separate keyClamp.keyDown remote. It sets heliBox.IsHack = player only after the keydown path passes the lockpick check.
- Functions/KeyClamp.cs OnEnd (:159-174) checks only that KeyClampData exists, then calls EndCB(player, value). It does not require a prior successful GetHealthCB/keyDown, an active IsHack reservation, or server-calculated progress.
- Client bind.js sends keyClamp.end with a client-supplied integer value (:997 and :1048); this value is not authoritative.
- HeliCrash.Repository.End (:504-558) checks character, KeyClampData, ColShapesData and box index, then directly assigns heliBox.Health = value (:525). If the client sends 0, it performs a 50% unlock roll. It does not verify heliBox.IsHack == player, possession of ArmyLockpick or elapsed minigame progress.
- On failure, End resets heliBox.Health to MaxHealth and heliBox.IsHack to null but does not clear the player's KeyClampData. The player can call keyClamp.end(0) again without going through GetHealth/ArmyLockpick validation. On success, the box is unlocked and the callback removes an ArmyLockpick only if one happens to be present, so a caller without one is not charged.
- OpenHeliCrash then loads the helicrash_<index> inventory after the box is unlocked.

### Impact boundary

A player who enters the HeliCrash box colshape while it is locked receives KeyClampData. A forged direct keyClamp.end(0) can skip the server's lockpick check and client-side minigame; repeated attempts after a failed 50% roll remain possible because the callback leaves KeyClampData installed. This can unlock event loot without consuming an ArmyLockpick. Static path is clear; successful runtime unlock and loot extraction still require staging reproduction.

### Remediation (not implemented)

- Make KeyClamp.OnEnd reject unless the server has an active, player-owned hack reservation created by a successful GetHealthCB/keyDown.
- Bind reservation to exact HeliCrash box index/event generation and the current player; require heliBox.IsHack == player at completion.
- Do not accept client health as authoritative. Track progress/time server-side and validate completion bounds and monotonicity.
- Consume one ArmyLockpick atomically and exactly once when a valid attempt is completed; no item consumption or lock mutation on forged/replayed calls.
- Clear KeyClampData and heliBox.IsHack on success, failure, cancel, exit, timeout, box removal, event reset and disconnect. Ensure failure does not leave a reusable completion token.
- In the generic KeyClamp OnEnd, validate callback presence and a server-owned intent rather than trusting arbitrary callback invocation from a client remote.

### Regression matrix

- Enter locked HeliCrash box without ArmyLockpick; direct keyClamp.end(0) must reject, lock health unchanged, no unlock roll.
- Enter with ArmyLockpick but do not press/hold the key; direct keyClamp.end(0) must reject.
- Complete valid keydown/minigame sequence; success/failure outcome is server-derived and exactly one ArmyLockpick is consumed per completed attempt.
- Replay keyClamp.end(0), send negative/oversized values, send before keyClamp.keyDown and after keyup; all invalid transitions reject.
- On a failed roll, verify old KeyClampData is cleared and no free retry is possible. On success, verify all players' clamp sessions for that exact box are revoked.
- Exit the colshape, move away, replace/end HeliCrash event or disconnect mid-attempt; stale completion must not change box health.
- Two players race for the same box; only the current server reservation owner may complete or release it.

**Scope boundary:** INV-018 is the HeliCrash lockpick/minigame remote bypass. It is separate from the HeliCrash open-container range/session TODO and the AirDrop/MatWar event lock issues INV-013/014.
