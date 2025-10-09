# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gewobag-Bot v2.0** is an automated web scraper and application bot that:
1. Extracts apartment listings from the Gewobag housing website (Berlin)
2. Stores listings in a SQLite database with filtering capabilities
3. **Automatically applies to apartments** using Playwright browser automation
4. Fills out application forms with user data from a JSON configuration file

The bot consists of three main Python scripts with advanced anti-detection mechanisms.

## Setup & Development

### Environment Setup
This project uses a Python virtual environment. Always activate it before running commands:

```bash
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

Dependencies:
- `requests` - HTTP requests to fetch apartment listing pages
- `beautifulsoup4` - HTML parsing to extract apartment data
- `apscheduler` - Optional scheduled execution
- `playwright` - Browser automation for application forms

### Configuration Files

**Required configuration files:**

1. **user_data.json** - Personal information for applications
   - Contains: name, email, phone, documents, household info
   - Template is auto-generated on first run
   - **IMPORTANT:** Fill in your real data before running applications!

2. **filter_config.json** - Search filters for apartments
   - Filters: districts (bezirke), rent, size, rooms, WBS requirement
   - Auto-generated with examples on first run

3. **bezirke_verfuegbar.json** - List of available districts
   - Auto-generated from Gewobag website
   - Used as reference for filter_config.json

### Running the Bot

**Main execution script:** `main.py`

```bash
# Initial setup (creates config files and database)
python main.py --setup

# DEFAULT MODE: Full automation (search + apply) - NO ARGUMENTS NEEDED!
python main.py

# Search for apartments only (no applications)
python main.py --scrape

# Apply to apartments already found in database
python main.py --apply

# Full automation: search + apply (explicit)
python main.py --full

# Show browser window for debugging
python main.py --show-browser

# Limit number of applications
python main.py --max 3
```

**IMPORTANT CHANGES v2.1:**
- **Automatic form submission is NOW ENABLED by default** (previously disabled)
- **No command-line arguments needed** - running `python main.py` automatically searches and applies
- **Enhanced error logging** with detailed error messages, types, and recommendations
- **Automatic screenshot capture** on errors for debugging (saved as `error_screenshot_*.png`)
- **Success message detection** to confirm application submission

**Legacy standalone scripts:**
```bash
# Search only
python gewobag-bot.py

# Applications only
python application_bot.py
```

## Architecture

### Three-Script Design

**1. gewobag-bot.py** - Web scraping and data collection
- Fetches apartment listings from Gewobag website
- Parses HTML with BeautifulSoup
- Applies filters (district, rent, size, rooms, WBS)
- Stores listings in SQLite database
- Supports pagination (multi-page results)
- Anti-detection: rotating user-agents, random delays, retry logic

**2. application_bot.py** - Browser automation for applications
- Uses Playwright to control Chrome browser
- Opens apartment detail pages
- Clicks "Anfrage senden" button
- Switches to iframe context
- Fills application form with user data
- Uploads documents (PDF, images)
- Tracks application status in database
- Anti-detection: stealth scripts, human-like typing, random delays

**3. main.py** - Orchestration and CLI interface
- Combines scraping and application functionality
- Provides command-line arguments for different modes
- Manages workflow: scrape → filter → apply
- Handles initial setup and configuration

### Key Functions (gewobag-bot.py)

1. **fetch_html()** - HTTP request with anti-detection headers and retry logic
2. **parse_wohnungen()** - BeautifulSoup parsing of listing page
3. **extract_wohnung_data()** - Individual apartment data extraction
4. **save_to_database()** - SQLite persistence with duplicate detection
5. **fetch_all_pages()** - Pagination handling with random delays
6. **apply_client_side_filters()** - Post-processing filters (WBS, rooms)
7. **scrape_wohnungen()** - Main orchestration function
8. **load_filter_config()** - Load and parse filter configuration
9. **build_url_with_filters()** - Construct URL with query parameters

### Key Functions (application_bot.py)

1. **load_user_data()** - Load personal data from JSON file
2. **setup_browser_context()** - Configure Playwright with anti-detection
3. **fill_application_form()** - Main form automation logic
4. **human_like_typing()** - Simulate human typing with delays
5. **mark_application_in_db()** - Update database with application status
6. **get_unapplied_wohnungen()** - Fetch apartments without applications
7. **apply_to_wohnung()** - Apply to single apartment (with retries)
8. **run_application_bot()** - Main orchestration for batch applications

### Data Model

**SQLite Table: `wohnungen`**
- `id` - Auto-incrementing primary key
- `bezirk` - District (e.g., "Friedrichshain-Kreuzberg")
- `adresse` - Full address
- `titel` - Listing title
- `zimmer` - Number of rooms (e.g., "3 Zimmer")
- `flaeche` - Size (e.g., "80,38 m²")
- `miete` - Total rent (e.g., "ab 933,00€")
- `wbs_erforderlich` - WBS required flag (0 or 1)
- `link` - Unique listing URL (UNIQUE constraint)
- `ts` - Timestamp of database insertion
- **`applied`** - Application sent flag (0 or 1)
- **`applied_ts`** - Timestamp of application
- **`application_status`** - Status: 'success', 'failed', 'pending'
- **`application_error`** - Error message (if failed)

### HTML Parsing Strategy

**Apartment Listings Page:**
- Each apartment in `<div class="angebot-content">`
- Bezirk: `<tr class="angebot-region"><td>...</td></tr>`
- Address: `<address>...</address>`
- Title: `<h3 class="angebot-title">...</h3>`
- Area/Rooms: `<tr class="angebot-area"><td>...</td></tr>`
- Rent: `<tr class="angebot-kosten"><td>...</td></tr>`
- WBS: `<div class="pictograms typ-wbs">` (if present)
- Link: `<div class="angebot-footer"><a href="...">...</a></div>`

**Apartment Detail Page (Application Form):**
- Tab system: `<button data-tab="rental-contact">`
- Form iframe: `<iframe id="contact-iframe" src="...wohnungshelden.de...">`
- Form fields inside iframe (selectors are approximations):
  - Vorname: `input[name*="vorname"]`
  - Nachname: `input[name*="nachname"]`
  - Email: `input[type="email"]`
  - Telefon: `input[type="tel"]`
  - Nachricht: `textarea[name*="message"]`
  - Datenschutz: `input[type="checkbox"]`
  - File upload: `input[type="file"]`

### Anti-Detection Mechanisms

**HTTP Requests (gewobag-bot.py):**
- Rotating user-agents (Chrome, Firefox, Safari, Edge)
- Rotating Accept-Language headers
- Realistic Referer headers (Google searches)
- Random delays between requests (2-7 seconds)
- Retry logic for 403/429 errors (max 3 retries)
- Connection error handling with exponential backoff

**Browser Automation (application_bot.py):**
- Playwright stealth mode
- Randomized user-agents
- Realistic browser viewport (1920x1080)
- Berlin geolocation (52.52°N, 13.40°E)
- German locale and timezone
- WebDriver property masking
- Human-like typing with delays (50-150ms per character)
- Random delays between form fields (0.5-2 seconds)
- Random delays between applications (30-60 seconds)

### Error Handling

**Scraping Errors:**
- Network timeouts (30s default)
- HTTP errors (403, 429, 5xx)
- Request failures (logged, returns empty list)
- Missing HTML elements (listings skipped, logged as warnings)
- SQLite integrity errors (duplicate links caught)
- JSON parsing errors (configuration files)

**Application Errors (Enhanced in v2.1):**
- Playwright timeout errors (60s timeout) - with detailed timeout messages
- Missing form fields (warnings logged, continues)
- iFrame loading failures - specific error message and screenshot
- File upload errors
- Retry logic (max 2 retries per apartment)
- All errors stored in database with status 'failed' and detailed error message
- **Cloudflare/CAPTCHA detection** - automatic detection with recommendations
- **Network error detection** - specific network failure messages
- **Selector error detection** - suggests website structure changes
- **Automatic screenshot capture** - error_screenshot_*.png, timeout_error_*.png, general_error_*.png

### Logging

**Log Files:**
- `gewobag-bot.log` - Scraping operations
- `application-bot.log` - Application operations
- `gewobag-main.log` - Main orchestration logs

**Log Format:**
- `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- Console output (INFO level) + file output (INFO level)
- Emoji indicators for better readability (🌐 ✅ ❌ ⚠️ 🔍 📊 etc.)

## Important Files

### Python Scripts
- **main.py** - Main CLI interface (orchestrates everything)
- **gewobag-bot.py** - Web scraper
- **application_bot.py** - Browser automation bot

### Configuration Files
- **user_data.json** - Personal data for applications (REQUIRED)
- **filter_config.json** - Search filters
- **bezirke_verfuegbar.json** - Available districts (auto-generated)

### Data & Logs
- **gewobag_wohnungen.db** - SQLite database (auto-created)
- **gewobag-bot.log** - Scraping logs
- **application-bot.log** - Application logs
- **gewobag-main.log** - Main logs

### Reference Files
- **view.html** - Example HTML snapshot of Gewobag listings page
- **anfrage.html** - Example HTML snapshot of application form page
- **requirements.txt** - Python dependencies

## Workflow

**Complete automation workflow:**

1. **Setup Phase** (`python main.py --setup`)
   - Initialize SQLite database with schema
   - Create user_data.json template
   - Create filter_config.json template
   - Extract available districts from website
   - Save districts to bezirke_verfuegbar.json

2. **Configuration Phase** (manual)
   - User edits user_data.json with real personal data
   - User edits filter_config.json with desired search filters

3. **Scraping Phase** (`python main.py --scrape`)
   - Load filter configuration
   - Build URL with filters
   - Fetch all paginated listing pages
   - Parse HTML and extract apartment data
   - Apply client-side filters (WBS, rooms)
   - Store new apartments in database
   - Mark duplicates (by link)

4. **Application Phase** (`python main.py --apply`)
   - Load user data from JSON
   - Query database for apartments with `applied = 0`
   - For each apartment:
     - Start Playwright browser
     - Navigate to apartment detail page
     - Click "Anfrage senden" button
     - Wait for iframe to load
     - Fill form fields with user data
     - Upload documents (if configured)
     - Mark as applied in database (status: success/failed)
     - Random delay before next application

5. **Full Automation** (`python main.py --full`)
   - Runs steps 3 + 4 in sequence

## Development Notes

- **Type hints:** All functions use Python type hints
- **Database constraints:** UNIQUE on `link` prevents duplicates
- **Timeouts:** 30s for HTTP requests, 60s for Playwright operations
- **Safety (v2.1 UPDATE):** Automatic form submission is **ENABLED by default** (changed from v2.0)
- **Automatic submission:** Form is submitted automatically after filling, with success detection
- **Headless mode:** Use `--show-browser` flag for debugging
- **Rate limiting:** Built-in delays to avoid detection/blocking (30-60s between applications)
- **Modularity:** Scripts can run standalone or through main.py
- **Error resilience:** Continues processing even if individual apartments fail
- **Screenshot debugging:** Automatic screenshots saved on errors for manual review

## Security & Privacy

- **user_data.json contains sensitive data** - add to .gitignore
- **Never commit personal information** to version control
- **File paths in user_data.json** should point to real documents
- **Verify form contents** before enabling auto-submit
- **Browser fingerprinting:** Anti-detection is not foolproof
- **Rate limiting:** Respect website's terms of service

## Troubleshooting

**Import errors:**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Install Playwright browsers: `playwright install chromium`

**Form fields not found:**
- Run with `--show-browser` to inspect the actual form
- Check iframe source URL (wohnungshelden.de)
- Update selectors in `fill_application_form()` function
- Form structure may change - requires manual inspection

**Applications failing:**
- Check user_data.json for missing/invalid data
- Verify document file paths exist
- Increase timeouts in application_bot.py
- Check application-bot.log for detailed errors

**No apartments found:**
- Verify filter_config.json settings
- Check if filters are too restrictive
- Run with empty filters to see all apartments
- Check gewobag-bot.log for parsing errors
- wenn du neue funktion hinzufügt dann aktualesiere immer @CLAUDE.md  und @README.md
- nutze immer context7 mcp für sicher stellen dass alle tools in letzte vision sind und bei problem von implementieren oder konflikt zwischen tools immer context7 mcp nutzen um beste lösung zu finden