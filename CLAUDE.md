# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gewobag-Bot** is a web scraper that extracts apartment listings from the Gewobag housing website (Berlin) and stores them in a SQLite database. The bot runs as a single-file Python script with optional scheduled execution.

## Setup & Development

### Environment Setup
This project uses a Python virtual environment. Always activate it before running commands:

```bash
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

Dependencies:
- `requests` - HTTP requests to fetch apartment listing pages
- `beautifulsoup4` - HTML parsing to extract apartment data
- `apscheduler` - Optional scheduled execution (currently disabled by default)

### Running the Bot

**Single execution:**
```bash
python gewobag-bot.py
```

This will:
1. Fetch the Gewobag apartment listings page
2. Parse all `<div class="angebot-content">` elements
3. Extract apartment details (bezirk, adresse, titel, flaeche, miete, link)
4. Store new listings in `gewobag_wohnungen.db` (SQLite)
5. Print results to console
6. Log all operations to `gewobag-bot.log`

**Enable scheduled execution:**
Uncomment the last 3 lines in the `if __name__ == "__main__":` block to enable hourly automated scraping via APScheduler.

## Architecture

### Single-file Design
All functionality is contained in `gewobag-bot.py`. The script follows a functional architecture with clear separation of concerns:

1. **fetch_html()** - HTTP request handling with custom User-Agent
2. **parse_wohnungen()** - BeautifulSoup parsing of listing page
3. **extract_wohnung_data()** - Individual apartment data extraction from HTML structure
4. **save_to_database()** - SQLite persistence with duplicate detection (via UNIQUE constraint on link)
5. **scrape_wohnungen()** - Main orchestration function
6. **print_wohnungen()** - Console output formatting
7. **scheduled_job()** / **run_scheduler()** - Optional APScheduler integration

### Data Model

**SQLite Table: `wohnungen`**
- `id` - Auto-incrementing primary key
- `bezirk` - District (e.g., "Friedrichsfelde")
- `adresse` - Full address
- `titel` - Listing title
- `flaeche` - Size info (e.g., "3 Zimmer | 80,38 m²")
- `miete` - Total rent (e.g., "ab 933,00€")
- `link` - Unique listing URL (UNIQUE constraint prevents duplicates)
- `ts` - Timestamp of database insertion

### HTML Parsing Strategy

The script expects Gewobag's HTML structure:
- Each apartment is in `<div class="angebot-content">`
- Within each div:
  - Bezirk: `<tr class="angebot-region"><td>...</td></tr>`
  - Address: `<address>...</address>`
  - Title: `<h3 class="angebot-title">...</h3>`
  - Area: `<tr class="angebot-area"><td>...</td></tr>`
  - Rent: `<tr class="angebot-kosten"><td>...</td></tr>`
  - Link: `<div class="angebot-footer"><a href="...">...</a></div>`

### Error Handling

- Network timeouts (30s default)
- Request failures (logged, returns empty list)
- Missing HTML elements (individual listings skipped, logged as warnings)
- SQLite integrity errors (duplicate links are caught and counted)
- All errors logged to both file and stdout

### Logging

Two-handler setup:
- Console output (INFO level)
- File output to `gewobag-bot.log` (INFO level)
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Important Files

- **gewobag-bot.py** - Main script (all code)
- **gewobag_wohnungen.db** - SQLite database (auto-created)
- **gewobag-bot.log** - Execution logs (auto-created)
- **view.html** - Example HTML snapshot of Gewobag listings page (for development reference)
- **requirements.txt** - Python dependencies

## Development Notes

- The script uses type hints (`List[Dict[str, str]]`, `Optional[str]`, etc.)
- Database uses `UNIQUE` constraint on `link` column to prevent duplicate entries
- The `REQUEST_TIMEOUT` is set to 30 seconds
- User-Agent mimics Chrome browser to avoid potential blocks
- Scheduler is disabled by default - must be manually enabled in code
