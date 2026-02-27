For **quarterly fundamental data (5,000+ A‑share stocks)** the main challenges are:

* Anti‑scraping throttling
* Partial failures (timeouts mid-run)
* Duplicate inserts
* Structure changes
* Re-fetching unchanged quarters

Below is a **production‑safe architecture** specifically for large‑scale quarterly fundamental collection in Python.

---

# 🎯 Core Principle

> Quarterly fundamentals change slowly.
> You should **update by reporting period**, not by stock.

Instead of:

```
for stock in 5000 stocks:
    fetch all quarters
```

Do:

```
for quarter in reporting_periods:
    fetch all stocks for that quarter
```

This reduces API calls dramatically.

---

# ✅ Best Free Sources

Most Python users rely on:

* AkShare (wraps public endpoints like Eastmoney)
* Tushare (free tier limited but structured)

For large-scale free pulling, **AkShare bulk endpoints per quarter** are usually more stable than per-stock calls.

---

# 🏗 Recommended Architecture

## 1️⃣ Database First (Avoid CSV)

Use SQLite or PostgreSQL.

Table design:

```sql
CREATE TABLE income_statement (
    stock_code TEXT,
    report_date TEXT,
    revenue REAL,
    net_profit REAL,
    ...
    PRIMARY KEY (stock_code, report_date)
);
```

Primary key prevents duplicates automatically.

---

## 2️⃣ Quarter-Based Pulling (Much Faster)

Most providers allow:

```
Fetch income statement for 2025-09-30
→ returns ALL stocks
```

That means:

Instead of:

```
5000 stocks × 20 quarters = 100,000 calls
```

You do:

```
20 quarters = 20 calls
```

Huge difference.

---

## 3️⃣ Immediate Write + Chunk Commit

Never hold full quarter in memory.

Example:

```python
df = fetch_quarter("2025-09-30")

for _, row in df.iterrows():
    insert_to_db(row)

conn.commit()
```

Or batch every 500 rows.

---

## 4️⃣ Progress Table (Critical for Stability)

Create:

```sql
CREATE TABLE fetch_progress (
    report_date TEXT PRIMARY KEY,
    status TEXT,
    last_update TIMESTAMP
);
```

Workflow:

* Before fetching quarter → check status
* After success → mark as done

If script crashes:

* Resume only unfinished quarters

---

## 5️⃣ Incremental Strategy (Real-World Use)

Quarterly fundamentals only change:

* After earnings release
* Or restatement

So you only need to:

* Re-fetch latest 2 quarters
* Keep historical frozen

Example:

```
Today = Feb 2026
Fetch only:
2025-12-31
2025-09-30
```

---

## 6️⃣ Retry + Backoff Layer

Wrap every API call:

```python
import time

def safe_fetch(func, *args):
    for attempt in range(5):
        try:
            return func(*args)
        except Exception:
            time.sleep(2 ** attempt)
    return None
```

---

## 7️⃣ Raw JSON Backup (Important)

Before parsing:

```python
with open(f"raw/{quarter}.json", "w") as f:
    f.write(response_text)
```

If parsing fails later, you don’t lose data.

---

## 8️⃣ Run After Market Close

Avoid:

* 9:00–15:00 CST

Better:

* After 18:00 CST
* Weekends

Sources like Eastmoney throttle more during trading hours.

---

# 🚀 Optimized Workflow for 5000+ Stocks

```
1. Generate quarter list (last 10 years)
2. For each quarter:
       if not done:
            fetch bulk data
            write to DB
            mark done
3. Re-fetch latest 2 quarters weekly
```

Total runtime usually < 10 minutes if bulk endpoints used.

---

# ⚡ If Bulk Endpoint Not Available

Fallback strategy:

### Multi-process with throttle control

Use:

```python
concurrent.futures.ThreadPoolExecutor(max_workers=3)
```

Keep workers low (2–4).
Too many → IP ban.

---

# 🔒 Data Integrity Checks

After each quarter:

* Count rows (should be ~5000)
* Check missing stock codes
* Log anomalies

---

# 🧠 Advanced: Hash Check for Quarter

Store:

```
quarter_hash
```

If hash unchanged → skip parsing.

---

# 💡 Realistic Expectation

For 5000 stocks:

| Method                | API Calls | Stability  |
| --------------------- | --------- | ---------- |
| Per stock per quarter | 100k+     | ❌ unstable |
| Bulk per quarter      | ~40       | ✅ stable   |

Bulk strategy wins.

---

# 🏆 Recommended Stack

* Python
* AkShare
* SQLite
* Quarter-based bulk pulling
* Exponential retry
* Progress tracking

This setup is stable even on free IP.

---







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