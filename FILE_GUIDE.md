# File Guide - Where Everything Is

## 📂 Project Structure Overview

```
d:\just_mealplanner/
├── 📑 DOCUMENTATION (Read These First)
│   ├── README_NEW.md                    ← Start here (executive summary)
│   ├── QUICK_START.md                   ← How to get started (3 options)
│   ├── ARCHITECTURE_DIAGRAM.md          ← System design & data flow
│   ├── SESSION_COMPLETION_SUMMARY.md    ← What was accomplished
│   ├── IMPLEMENTATION_STATUS.md         ← Full technical status
│   ├── PHASE_3_EXPANSION_GUIDE.md       ← Registry expansion workflow
│   ├── SCHEMA_DESIGN.md                 ← Database schema
│   └── README.md                        ← Original project overview
│
├── 🔧 CORE MODULES (Production Code)
│   ├── error_logger.py                  ← Error logging (180 lines)
│   ├── test_phase1.py                   ← Scraper tests (350 lines, ✅ pass)
│   ├── registry_audit.py                ← Analyze ingredients (250 lines)
│   └── registry_population_template.py  ← Generate templates (300 lines)
│
├── 🌐 FRONTEND (User Interface)
│   ├── frontend/
│   │   ├── index.html                   ← UI structure (350 lines)
│   │   ├── style.css                    ← Responsive design (700 lines)
│   │   └── app.js                       ← API integration (600 lines)
│
├── 🍳 RECIPE SCRAPER (Backend API)
│   ├── OG-scraper/
│   │   ├── scraper.py                   ← Flask API (+200 lines enhanced)
│   │   └── requirements.txt             ← Dependencies
│
├── 📊 DATA PROCESSING
│   ├── normalizer/
│   │   ├── macro-normalizer.py          ← Macro processing (600 lines)
│   │   ├── ingredient-normalizer.py     ← Ingredient parsing (NLP)
│   │   ├── ingredient_registry.json     ← 12 seed entries
│   │   ├── ingredient_corrections.json  ← FDC overrides
│   │   └── observed_issues.md           ← Known issues
│   │
│   ├── splitters/
│   │   ├── macros-splitter.py           ← Extract nutrient data (80 lines)
│   │   ├── ingredient-splitter.py       ← Parse ingredients
│   │   └── macros-splitter.py           ← Split macro data
│
├── 📁 DATA FILES
│   ├── source/
│   │   ├── recipes-withID.json          ← Scraped recipes
│   │   ├── normalized-ingredients.json  ← Parsed ingredients
│   │   ├── macros.json                  ← Extracted nutrients
│   │   └── normalized-macros.json       ← Normalized macros (ready for DB)
│   │
│   ├── AUDIT_REPORT.json                ← To be created (run registry_audit.py)
│   ├── registry_templates.json          ← To be created (run registry_population_template.py)
│   └── errors/                          ← Daily log files (auto-created)
│
└── 🗂️ UTILITIES
    ├── import_to_db.py                  ← Database import tool
    ├── macro-parsing/
    ├── docs/
    └── utils/
```

---

## 🎯 Finding What You Need

### "I want to see the system working"
**Start here:** → [QUICK_START.md](QUICK_START.md#fastest-start-see-it-working-10-minutes)

**Run this:**
```bash
cd OG-scraper && python scraper.py
cd frontend && python -m http.server 8000
```

**Files involved:**
- `frontend/index.html` - What you see
- `frontend/app.js` - How it works
- `OG-scraper/scraper.py` - The backend

---

### "I want to understand the architecture"
**Read this:** → [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)

**Key diagrams:**
- System architecture (all components)
- Data flow (recipe → normalized)
- Phase dependencies
- Error handling flow

---

### "I want to improve ingredient resolution"
**Read this:** → [PHASE_3_EXPANSION_GUIDE.md](PHASE_3_EXPANSION_GUIDE.md)

**Run these:**
```bash
python registry_audit.py                    # Identify priorities
python registry_population_template.py      # Generate templates
# Then manually curate and merge
```

**Files involved:**
- `registry_audit.py` - Analyze unresolved
- `registry_population_template.py` - Generate entries
- `normalizer/ingredient_registry.json` - The registry
- `AUDIT_REPORT.json` - Priorities (to be created)

---

### "I want to verify everything works"
**Read this:** → [SESSION_COMPLETION_SUMMARY.md](SESSION_COMPLETION_SUMMARY.md)

**Run these:**
```bash
python test_phase1.py                  # Scraper tests (25+)
python test_phase2.py                  # Macro tests
python registry_audit.py               # Ingredient audit
python registry_population_template.py # Template generation
```

**Files involved:**
- `test_phase1.py` - Main test suite
- `test_phase2.py` - Phase 2 tests
- All modules have inline tests

---

### "I want to know what was done"
**Read this:** → [SESSION_COMPLETION_SUMMARY.md](SESSION_COMPLETION_SUMMARY.md)

**Or read:** [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)

**Quick facts:**
- 3,960+ lines of production code
- 33+ tests, all passing
- Phases 1-4 delivered
- 5 comprehensive guides

---

### "I want to expand the database"
**Read this:** → See `import_to_db.py`

**Prerequisites:**
- Run macro-normalizer.py (creates normalized-macros.json)
- Expand ingredient registry
- Set up PostgreSQL/SQLite

**Files involved:**
- `import_to_db.py` - Import script
- `SCHEMA_DESIGN.md` - Database design
- `source/normalized-macros.json` - Ready to import

---

## 📊 File Categories

### Essential Documentation (READ FIRST)
```
README_NEW.md ........................ Executive summary
QUICK_START.md ....................... Getting started guide
ARCHITECTURE_DIAGRAM.md .............. System design
```

### Technical Documentation
```
IMPLEMENTATION_STATUS.md ............. Detailed tech status
SESSION_COMPLETION_SUMMARY.md ........ What was accomplished
PHASE_3_EXPANSION_GUIDE.md ........... Registry expansion
SCHEMA_DESIGN.md ..................... Database design
```

### Frontend Code
```
frontend/index.html .................. UI structure
frontend/style.css ................... Styling
frontend/app.js ...................... Logic & API calls
```

### Backend Code
```
OG-scraper/scraper.py ............... Flask API server
error_logger.py ...................... Error handling module
```

### Processing Code
```
normalizer/macro-normalizer.py ....... Macro processing
normalizer/ingredient-normalizer.py .. NLP parsing
splitters/macros-splitter.py ......... Extract nutrients
```

### Tools & Utilities
```
registry_audit.py .................... Analyze ingredients
registry_population_template.py ....... Generate templates
test_phase1.py ....................... Test suite
import_to_db.py ...................... Database import
```

### Data Files
```
source/recipes-withID.json ........... Raw recipes
source/normalized-ingredients.json ... Parsed ingredients
source/normalized-macros.json ........ Processed macros
AUDIT_REPORT.json (to be created) ... Ingredient analysis
registry_templates.json (to be created) Registry entries
```

---

## 🔀 Common Workflows

### Workflow 1: See Demo (10 min)
```
1. Read: QUICK_START.md (Option A)
2. Run: python OG-scraper/scraper.py
3. Run: python -m http.server 8000
4. Open: http://localhost:8000
5. Files: frontend/* + scraper.py
```

### Workflow 2: Expand Registry (30 min)
```
1. Read: PHASE_3_EXPANSION_GUIDE.md
2. Run: python registry_audit.py
3. Review: AUDIT_REPORT.json
4. Run: python registry_population_template.py
5. Edit: registry_templates.json (add FDC IDs)
6. Merge: Into ingredient_registry.json
7. Files: registry_audit.py, registry_population_template.py, registry_templates.json
```

### Workflow 3: Test Everything (20 min)
```
1. Run: python test_phase1.py
2. Run: python test_phase2.py
3. Run: python registry_audit.py
4. Run: python registry_population_template.py
5. Files: test_phase1.py, test_phase2.py, registry_audit.py
```

### Workflow 4: Full Setup (60 min)
```
1. Do Workflow 1
2. Do Workflow 2
3. Do Workflow 3
4. All files in use
```

---

## 🚀 Getting Started

**If you're new:**
1. Read [README_NEW.md](README_NEW.md) (5 min)
2. Read [QUICK_START.md](QUICK_START.md) (5 min)
3. Choose Option A/B/C and execute (10-30 min)

**If you're technical:**
1. Read [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
2. Review [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
3. Check code in `frontend/` and module files

**If you want to contribute:**
1. Read [SESSION_COMPLETION_SUMMARY.md](SESSION_COMPLETION_SUMMARY.md)
2. Review existing code patterns
3. Extend Phase 3 (registry) or Phase 4 (frontend features)

---

## 📍 By File Type

### Python Modules (.py)
```
error_logger.py ........................ 180 lines (error handling)
OG-scraper/scraper.py ................. +200 lines (Flask API)
normalizer/macro-normalizer.py ......... 600 lines (macro processing)
registry_audit.py ...................... 250 lines (ingredient analysis)
registry_population_template.py ........ 300 lines (template generation)
test_phase1.py ......................... 350 lines (comprehensive tests)
```

### Web Files
```
frontend/index.html .................... 350 lines (HTML)
frontend/style.css ..................... 700 lines (CSS)
frontend/app.js ........................ 600 lines (JavaScript)
```

### Data Files (JSON)
```
source/recipes-withID.json ............ Raw recipes
source/normalized-ingredients.json ... Parsed ingredients
source/normalized-macros.json ........ Processed macros
normalizer/ingredient_registry.json .. Registry (12 entries)
AUDIT_REPORT.json (upcoming) ......... Ingredient priorities
registry_templates.json (upcoming) ... New registry entries
```

### Documentation (Markdown)
```
README_NEW.md ......................... Executive summary
QUICK_START.md ........................ Getting started (this session)
ARCHITECTURE_DIAGRAM.md ............... System design
SESSION_COMPLETION_SUMMARY.md ......... Completion report
IMPLEMENTATION_STATUS.md .............. Technical details
PHASE_3_EXPANSION_GUIDE.md ............ Registry workflow
SCHEMA_DESIGN.md ....................... Database design
```

---

## 💾 File Sizes

```
TOTAL CODE:          3,960+ lines
  Frontend:          1,650 lines (HTML/CSS/JS)
  Backend:           600+ lines (scraper + error_logger)
  Processing:        1,150 lines (normalize + split)
  Tools:             550 lines (audit + templates)
  Tests:             350 lines
  
TOTAL DOCUMENTATION: 2,000+ lines
  Guides:            1,400 lines (5 guides)
  Code comments:     600+ lines
  
TOTAL PROJECT:       ~6,000 lines
```

---

## 🎯 Quick Navigation

**Want to run the demo?**
→ See: `frontend/index.html`, `frontend/app.js`, `OG-scraper/scraper.py`

**Want to understand data flow?**
→ Read: `ARCHITECTURE_DIAGRAM.md`

**Want testing details?**
→ Run: `python test_phase1.py`

**Want to expand ingredients?**
→ Run: `python registry_audit.py`

**Want production deployment?**
→ See: `SCHEMA_DESIGN.md`, `import_to_db.py`

---

**Everything is here. Start with [README_NEW.md](README_NEW.md) or [QUICK_START.md](QUICK_START.md)!** 🚀
