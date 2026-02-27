Getting **accurate, up‑to‑date A‑share data for free** is possible — but we need to design around throttling, anti‑scraping limits, and unstable endpoints (especially from sources like Eastmoney, Sina Finance, and Tencent Finance).

Below are practical, production‑style strategies to **record data safely as you pull it**, minimize loss, and survive timeouts.

---

# 1️⃣ Write‑As‑You‑Go (Never Batch in Memory)

### ❌ Risky

Pull 4,000 stocks → store in memory → save at end
→ One timeout = total loss.

### ✅ Safer

Save **each stock immediately after fetch**

Example pattern:

```python
for stock in stock_list:
    try:
        data = fetch(stock)
        save_to_db(data)     # commit immediately
        mark_completed(stock)
    except Exception as e:
        log_error(stock, e)
```

**Why this works:**

* Crash only loses current symbol
* You can resume later
* No re-fetching successful records

---

# 2️⃣ Maintain a Progress Table (Checkpointing)

Create a lightweight tracking table:

| stock_code | last_update | status  |
| ---------- | ----------- | ------- |
| 000001.SZ  | 2026-02-27  | done    |
| 000002.SZ  | NULL        | pending |

When script restarts:

```
SELECT stock_code FROM table WHERE status != 'done'
```

This avoids:

* Duplicate API calls
* Hitting rate limits unnecessarily
* Losing track after interruption

---

# 3️⃣ Incremental Updates Only

Do NOT pull full history daily.

Instead:

* Store latest date per stock
* Only fetch new rows

Example logic:

```python
last_date = get_last_date(stock)
data = fetch(stock, start=last_date)
append(data)
```

This:

* Reduces traffic by 95%+
* Avoids triggering anti-bot systems
* Keeps database small & fast

---

# 4️⃣ Use Local Raw Snapshots (JSON/CSV Logging Layer)

Before cleaning data, dump raw response:

```python
with open(f"raw/{stock}_{date}.json", "w") as f:
    f.write(response.text)
```

Benefits:

* If parsing fails → you still have raw data
* You can reprocess later
* Protects against API structure changes

---

# 5️⃣ Use Multiple Free Sources (Failover Strategy)

Many Chinese retail data sites mirror exchange feeds.

Common free sources:

* Shanghai Stock Exchange
* Shenzhen Stock Exchange
* Tushare (limited free tier)
* AkShare (wrapper over public endpoints)

Strategy:

```
Try primary source
If fails → fallback to secondary
If fails → queue for retry
```

---

# 6️⃣ Respectful Rate Limiting (Very Important)

Instead of:

```python
time.sleep(0.2)
```

Use:

* Random jitter
* Adaptive delay after failure

Example:

```python
import random, time

delay = random.uniform(0.8, 1.5)
time.sleep(delay)
```

After HTTP 429 or timeout:

```
sleep 30–120 seconds
```

This dramatically reduces IP bans.

---

# 7️⃣ Automatic Retry with Backoff

Use exponential backoff:

```python
for attempt in range(5):
    try:
        return fetch()
    except:
        time.sleep(2 ** attempt)
```

Retry schedule:
1s → 2s → 4s → 8s → 16s

---

# 8️⃣ Daily Snapshot Strategy (For Real‑Time Data)

If you need near real‑time:

Instead of querying constantly:

* Pull entire market snapshot at 15:05
* Store full daily snapshot
* Derive analytics locally

This reduces:

* Intraday throttling
* Unnecessary repeated hits

---

# 9️⃣ Local Time‑Series Database (Best Long‑Term Solution)

Instead of CSV files, use:

* SQLite (simple & stable)
* PostgreSQL (scalable)
* TimescaleDB (optimized for time-series)

Schema example:

```
(stock_code, trade_date) PRIMARY KEY
```

Prevents duplicate rows automatically.

---

# 🔟 Run Pull Jobs During Off‑Peak Hours

Chinese financial sites throttle heavily during:

* 09:15–11:30
* 13:00–15:00

Safer windows:

* After 18:00 CST
* Early morning before 08:00

---

# 11️⃣ Build a “Retry Queue” File

If something fails:

```
failed.txt
```

Append stock code.

After main run finishes:

* Process failed list separately
* With longer delay

---

# 12️⃣ Consider Exchange Official Data Dumps

Both:

* Shanghai Stock Exchange
* Shenzhen Stock Exchange

Provide:

* End‑of‑day files
* Corporate announcements
* CSV bulk downloads

These are:

* More stable
* Less restricted
* Legally safer

---

# 13️⃣ Hash Your Data to Detect Corruption

Store a hash:

```python
import hashlib
hash = hashlib.md5(response.content).hexdigest()
```

If file corrupted → detect automatically.

---

# 14️⃣ Log Everything

Maintain:

* success.log
* error.log
* retry.log

Log:

* Timestamp
* Stock code
* Source
* Response time
* HTTP status

When bans happen, logs reveal patterns.

---

# 15️⃣ Advanced: Distributed IP Strategy (If Legal In Your Region)

If you're doing large scale:

* Rotate IP
* Use proxy pool carefully
* Respect site terms

⚠️ Always review TOS before automation.

---

# Practical “Safe & Free” Architecture

```
Scheduler (cron)
     ↓
Fetch 1 stock
     ↓
Immediate save
     ↓
Mark complete
     ↓
Retry queue if fail
     ↓
Daily snapshot
```

---

# Most Reliable Free Stack Today

If you want minimal pain:

* Use AkShare for pulling
* Store in SQLite
* Run after market close
* Incremental updates only
* Retry + backoff enabled

That setup survives most throttling issues.