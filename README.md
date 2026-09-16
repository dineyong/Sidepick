# SidePick PoC

SidePick is a small proof of concept that uses official Naver APIs to discover product candidates worth investigating for online sellers.

It does not estimate sales, revenue, or exact search volume. It only uses:

- Naver Shopping Search API: product result count, product titles, prices, brand, maker, mall and category fields.
- Naver DataLab Shopping Insight API: relative shopping click trend ratios.
- Local SQLite snapshots: data collected by this project over time.

## Project Structure

```text
SidePick/
  sidepick/
    cli.py               # command line entry point
    config.py            # env/config loading
    naver.py             # official Naver API client
    keyword_extractor.py # candidate keyword extraction from product titles
    db.py                # SQLite schema and writes
    scoring.py           # SidePick Score calculation from collected data
    pipeline.py          # end-to-end PoC flow
    report.py            # console and local HTML report
  data/                  # local SQLite DB, ignored by git
  reports/               # generated local reports, ignored by git
```

## What You Need To Prepare

1. Create a Naver Developers application.
2. Enable these APIs for the application:
   - Search API
   - DataLab Shopping Insight API
3. Copy `.env.example` to `.env`.
4. Fill:
   - `NAVER_CLIENT_ID`
   - `NAVER_CLIENT_SECRET`
5. Fill the three `SIDEPICK_CATEGORY_ID_*` values if you want trend scoring.
   - DataLab requires Naver Shopping `cat_id`.
   - Open a Naver Shopping category page and copy the `cat_id` query parameter.
   - If left blank, the PoC still runs Shopping Search discovery, but trend scores are `0`.

## Windows Setup

```powershell
cd SidePick
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`, then run:

```powershell
python -m sidepick.cli discover --top 20
```

## macOS Setup

```bash
cd SidePick
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then run:

```bash
python -m sidepick.cli discover --top 20
```

## Output

The command prints TOP candidates in the console and writes:

- SQLite DB: `data/sidepick.db`
- Local HTML report: `reports/latest.html`
- JSON report: `reports/latest.json`

## Current Scoring

SidePick Score is computed only from collected data:

- Demand / trend: up to 40 points from Shopping Insight latest relative click ratio and recent change.
- Competition: up to 30 points from Naver Shopping Search `total`, favoring lower competition among collected candidates.
- Price attractiveness: up to 20 points from median product price, favoring practical seller-friendly price ranges.
- Trend persistence: up to 10 points from repeated non-declining trend periods.

If DataLab category IDs are missing or DataLab returns no data, trend-related components become `0`; the report explains that in the reason field.

