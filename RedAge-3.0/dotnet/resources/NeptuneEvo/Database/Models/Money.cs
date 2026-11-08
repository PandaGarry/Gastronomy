using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Database;
using LinqToDB;
using Redage.SDK;

namespace NeptuneEvo.Database.Models
{
    public class Money
    {
        private static readonly nLog Log = new nLog("Database.Money");
        private static readonly object QueueLock = new object();
        // A fixed stripe count avoids an unbounded per-character semaphore cache.
        private static readonly SemaphoreSlim[] MoneyLocks = Enumerable.Range(0, 64)
            .Select(_ => new SemaphoreSlim(1, 1))
            .ToArray();
        private static readonly object[] MoneySyncLocks = Enumerable.Range(0, 64)
            .Select(_ => new object())
            .ToArray();
        private static readonly Dictionary<int, long> MoneyVersions = new Dictionary<int, long>();
        private static readonly HashSet<int> ActiveMoneyWrites = new HashSet<int>();
        private static readonly HashSet<int> ActiveCharacterSaves = new HashSet<int>();
        private static int _workerStarted;

        private static int GetMoneyLockIndex(int uuid)
        {
            return (uuid & int.MaxValue) % MoneyLocks.Length;
        }

        private static SemaphoreSlim GetMoneyLock(int uuid)
        {
            return MoneyLocks[GetMoneyLockIndex(uuid)];
        }

        public static object GetCharacterMoneySyncLock(int uuid)
        {
            return MoneySyncLocks[GetMoneyLockIndex(uuid)];
        }

        private static long NextMoneyVersion(int uuid)
        {
            long current = MoneyVersions.TryGetValue(uuid, out var version) ? version : 0;
            long next = checked(current + 1);
            MoneyVersions[uuid] = next;
            return next;
        }

        private static long GetMoneyVersion(int uuid)
        {
            return MoneyVersions.TryGetValue(uuid, out var version) ? version : 0;
        }

        // The full character save and the detached money worker must serialize writes
        // to characters.money. Starting a full save advances the version, invalidating
        // any older detached worker snapshot before its SQL UPDATE can run.
        public static async Task ExecuteCharacterSave(int uuid, Func<long> getAmount, Func<long, Task> saveAction)
        {
            if (uuid <= 0 || getAmount == null || saveAction == null)
                throw new ArgumentOutOfRangeException(nameof(uuid), "Invalid character money save.");

            var moneyLock = GetMoneyLock(uuid);
            await moneyLock.WaitAsync();
            long amount = 0;
            long saveVersion = 0;
            bool saveRegistered = false;
            try
            {
                lock (GetCharacterMoneySyncLock(uuid))
                {
                    amount = getAmount();
                    if (amount < 0 || amount > int.MaxValue)
                        throw new ArgumentOutOfRangeException(nameof(getAmount), "Character money is outside the signed INT range.");

                    lock (QueueLock)
                    {
                        saveVersion = NextMoneyVersion(uuid);
                        MoneyUpdateList.Remove(uuid);
                        ActiveCharacterSaves.Add(uuid);
                        saveRegistered = true;
                    }
                }

                await saveAction(amount);
            }
            catch
            {
                // If a newer Wallet change was queued during this save, preserve it.
                if (saveRegistered)
                {
                    lock (QueueLock)
                    {
                        if (GetMoneyVersion(uuid) == saveVersion && !MoneyUpdateList.ContainsKey(uuid))
                            MoneyUpdateList[uuid] = new object[] { uuid, amount, saveVersion };
                    }
                }
                throw;
            }
            finally
            {
                if (saveRegistered)
                {
                    lock (QueueLock)
                        ActiveCharacterSaves.Remove(uuid);
                }
                moneyLock.Release();
            }
        }

        public static void Start()
        {
            // Startup may be invoked more than once by server lifecycle code.
            // Keep exactly one persistence worker per process.
            if (Interlocked.Exchange(ref _workerStarted, 1) != 0)
                return;

            Task.Run(Worker);
        }

        private static async Task Worker()
        {
            while (true)
            {
                List<object[]> donateBatch = new List<object[]>();
                List<object[]> moneyBatch = new List<object[]>();

                try
                {
                    // Snapshot and clear are atomic with respect to all producers.
                    lock (QueueLock)
                    {
                        donateBatch = DonateUpdateList.Values.ToList();
                        DonateUpdateList.Clear();

                        moneyBatch = MoneyUpdateList.Values.ToList();
                        // Track detached rows from snapshot time, not only once SQL starts.
                        // A small Wallet.Change during this hand-off must enqueue a newer snapshot.
                        foreach (var saveData in moneyBatch)
                            ActiveMoneyWrites.Add(Convert.ToInt32(saveData[0]));
                        MoneyUpdateList.Clear();
                    }

                    if (donateBatch.Count > 0 || moneyBatch.Count > 0)
                    {
                        await using var db = new ServerBD("MainDB");

                        if (donateBatch.Count > 0 && !await DonateUpdate(db, donateBatch))
                            RequeueDonate(donateBatch);

                        if (moneyBatch.Count > 0 && !await MoneyUpdate(db, moneyBatch))
                            RequeueMoney(moneyBatch);
                    }
                }
                catch (Exception e)
                {
                    Log.Write($"LogsWorker Exception: {e}");
                    // A failed connection/context creation must not discard the detached batches.
                    RequeueDonate(donateBatch);
                    RequeueMoney(moneyBatch);
                }

                // Do not block a thread-pool thread between asynchronous DB batches.
                await Task.Delay(1000);
            }
        }

        private static readonly Dictionary<string, object[]> DonateUpdateList = new Dictionary<string, object[]>();

        public static void AddDonateUpdate(string login, int amount)
        {
            if (string.IsNullOrWhiteSpace(login))
                return;

            lock (QueueLock)
            {
                DonateUpdateList[login] = new object[] { login, amount };
            }
        }

        private static void RequeueDonate(List<object[]> batch)
        {
            if (batch == null || batch.Count == 0)
                return;

            lock (QueueLock)
            {
                foreach (var saveData in batch)
                {
                    var login = saveData[0].ToString();
                    // Preserve a newer value queued while this batch was being written.
                    if (!DonateUpdateList.ContainsKey(login))
                        DonateUpdateList[login] = saveData;
                }
            }
        }

        private static async Task<bool> DonateUpdate(ServerBD db, List<object[]> donateUpdateList)
        {
            try
            {
                foreach (var saveData in donateUpdateList)
                {
                    await db.Accounts
                        .Where(v => v.Login == saveData[0].ToString())
                        .Set(v => v.Redbucks, Convert.ToInt32(saveData[1]))
                        .UpdateAsync();
                }

                return true;
            }
            catch (Exception e)
            {
                Log.Write($"DonateUpdate Exception: {e}");
                return false;
            }
        }

        private static readonly Dictionary<int, object[]> MoneyUpdateList = new Dictionary<int, object[]>();

        public static void AddMoneyUpdate(int uuid, long amount, bool forceQueue = true)
        {
            // Every wallet mutation advances the version so detached snapshots become
            // stale. Small changes are queued only when a write/save is already in flight
            // or a prior snapshot is pending; large changes retain the existing eager-save policy.
            if (uuid <= 0 || amount < 0 || amount > int.MaxValue)
            {
                Log.Write($"AddMoneyUpdate rejected invalid snapshot (UUID: {uuid}, amount: {amount}).");
                return;
            }

            lock (QueueLock)
            {
                long version = NextMoneyVersion(uuid);
                if (forceQueue || MoneyUpdateList.ContainsKey(uuid) ||
                    ActiveMoneyWrites.Contains(uuid) || ActiveCharacterSaves.Contains(uuid))
                {
                    MoneyUpdateList[uuid] = new object[] { uuid, amount, version };
                }
            }
        }

        private static void RequeueMoney(List<object[]> batch)
        {
            if (batch == null || batch.Count == 0)
                return;

            lock (QueueLock)
            {
                foreach (var saveData in batch)
                {
                    var uuid = Convert.ToInt32(saveData[0]);
                    var version = Convert.ToInt64(saveData[2]);
                    // Never resurrect a snapshot invalidated by a newer wallet/full-save write.
                    if (GetMoneyVersion(uuid) == version && !MoneyUpdateList.ContainsKey(uuid))
                        MoneyUpdateList[uuid] = saveData;
                    // A failed context/batch must not leave a phantom in-flight marker.
                    ActiveMoneyWrites.Remove(uuid);
                }
            }
        }

        private static async Task<bool> MoneyUpdate(ServerBD db, List<object[]> moneyUpdateList)
        {
            try
            {
                foreach (var saveData in moneyUpdateList)
                {
                    int uuid = Convert.ToInt32(saveData[0]);
                    long version = Convert.ToInt64(saveData[2]);
                    var moneyLock = GetMoneyLock(uuid);
                    await moneyLock.WaitAsync();
                    try
                    {
                        bool isCurrent;
                        lock (QueueLock)
                        {
                            isCurrent = GetMoneyVersion(uuid) == version;
                            if (isCurrent)
                                ActiveMoneyWrites.Add(uuid);
                        }

                        // A full character save or newer wallet mutation superseded this
                        // detached absolute snapshot. Do not let it roll the DB balance back.
                        if (!isCurrent)
                            continue;

                        if (isCurrent)
                        {
                            await db.Characters
                                .Where(v => v.Uuid == uuid)
                                .Set(v => v.Money, Convert.ToInt32(saveData[1]))
                                .UpdateAsync();
                        }
                    }
                    finally
                    {
                        // Keep the in-flight marker until after the semaphore is released,
                        // so a wallet mutation in this hand-off window is still queued.
                        moneyLock.Release();
                        lock (QueueLock)
                            ActiveMoneyWrites.Remove(uuid);
                    }
                }

                return true;
            }
            catch (Exception e)
            {
                Log.Write($"MoneyUpdate Exception: {e}");
                return false;
            }
        }
    }
}