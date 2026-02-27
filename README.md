# Fetch All A-shares Stock List

Download A-share stock codes and names using **Akshare** and save to CSV.

## Requirements

```bash
pip install akshare
```

## Usage
```bash
python fetch_all_ashares.py --out ./all_stocks.csv --verbose
```

## Output
```bash
[INFO] Fetching A-share stock list from akshare...
[INFO] Retrieved 5485 records.
[INFO] Saving to: ./all_stocks.csv
[INFO] File saved successfully.
[INFO] Preview (first 5 rows):
     code   name
0  000001   平安银行
1  000002   万科Ａ
2  000004   *ST国华
3  000006   深振业Ａ
4  000007   全新好
```
