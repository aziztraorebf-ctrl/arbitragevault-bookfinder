# ArbitrageVault - Code Style Rules

**Effective Date** : 2 Novembre 2025
**Version** : 1.0
**Owner** : Aziz Trabelsi + Claude Code

---

## CRITICAL RULE: NO EMOJIS IN EXECUTABLE CODE

This rule is **ABSOLUTE** and **NON-NEGOTIABLE** in this project.

---

## 1. Emojis STRICTLY FORBIDDEN

### File Extensions (NEVER USE EMOJIS)
- `.py` (Python files)
- `.ts`, `.tsx` (TypeScript / React)
- `.js`, `.jsx` (JavaScript)
- `.json` (JSON configuration)
- `.yaml`, `.yml` (YAML configuration)
- `.sql` (SQL migrations)
- `.env`, `.env.local` (Environment files)
- Alembic migration files
- Test files (`test_*.py`)
- Log files

### Locations (NEVER USE EMOJIS)
- Code comments: `# This is wrong: 🚀`
- Docstrings: `"""This breaks: ✅"""`
- String literals in code: `print("Error: 🔴")`
- Function/variable names: `def start_🚀(): ...`
- Error messages: `raise ValueError("Failed: ❌")`
- Print statements: `logger.info("Done ✓")`

### Why This Matters

Emojis in code cause:
- **Encoding issues** in CI/CD pipelines
- **Parsing errors** in linters (pylint, eslint)
- **Compilation failures** in build systems
- **UTF-8 conflicts** in file processing
- **Silent bugs** in log aggregation (Sentry)
- **Compatibility issues** in cross-platform deployments

**Impact**: Production breaks, deployment fails, monitoring breaks.

---

## 2. Emojis ALLOWED (Use Freely)

### File Extensions (EMOJIS OK)
- `.md` (Markdown files)
- `.txt` (Plain text documentation)

### Examples of Files Where Emojis Are OK
- `compact_current.md` - Phase status updates
- `compact_master.md` - Project memory
- `phase_*.md` - Phase reports
- `ARCHITECTURE.md` - Documentation
- `KNOWN_ISSUES.md` - Issue documentation
- Git commit messages (optional)
- This file itself

### Why Emojis Help Here
- Improves visual clarity and scannability
- Breaks up dense text blocks
- Helps users quickly identify sections
- No execution or parsing involved

---

## 3. Self-Check Before Writing Code

### Before Every `Write` or `Edit` Operation

```
STEP 1: Check file extension
  IF extension IN [.py, .ts, .tsx, .js, .json, .yaml, .sql]:
    THEN no_emojis_allowed = TRUE
  ELSE IF extension IN [.md, .txt]:
    THEN emojis_ok = TRUE

STEP 2: Scan code for emojis
  FIND ALL emoji characters in proposed code
  IF emojis_found AND no_emojis_allowed:
    THEN remove_emojis_before_writing()
  ELSE IF emojis_found AND emojis_ok:
    THEN proceed_normally()

STEP 3: Verify file will execute/parse correctly
  IF file_is_executable OR file_has_linting:
    THEN ascii_only = TRUE (strict check)
```

---

## 4. Examples

### WRONG (Emojis in Python)
```python
# This code will cause issues:

def analyze_product(asin: str) -> dict:
    """Analyze product with ROI calculation ✅"""

    # Fetch Keepa data 🚀
    product = get_keepa_product(asin)

    # Calculate ROI 📊
    roi = calculate_roi(product)

    if roi > 30:
        logger.info(f"Good product found: {asin} ✓")
    else:
        raise ValueError(f"Poor ROI: {roi}% ❌")

    return {"asin": asin, "roi": roi, "status": "✅"}
```

**Problems**:
- UTF-8 encoding errors in logs
- Linting failures
- CI/CD pipeline breaks
- Silent emoji-stripping in some parsers

---

### CORRECT (ASCII Only in Python)
```python
# This code is clean and reliable:

def analyze_product(asin: str) -> dict:
    """Analyze product with ROI calculation."""

    # Fetch Keepa data
    product = get_keepa_product(asin)

    # Calculate ROI
    roi = calculate_roi(product)

    if roi > 30:
        logger.info(f"Good product found: {asin}")
    else:
        raise ValueError(f"Poor ROI: {roi}%")

    return {"asin": asin, "roi": roi, "status": "success"}
```

**Benefits**:
- Pure ASCII, zero encoding issues
- Passes all linters
- CI/CD compatible
- Logs are clean and parseable

---

### CORRECT (Emojis in Markdown Documentation)
```markdown
# Phase 5 Status Report

## Overview
- Status: 🟢 Ready to start
- Backend: ✅ Production-ready
- Frontend: ⏳ In development
- Database: ✅ Operational

## Key Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Backend uptime | 99.9% | ✅ |
| Keepa balance | 670 tokens | 🟡 Medium |
| Cache hit rate | 70% | ✅ |

## Next Steps
1. Deploy frontend Netlify 🚀
2. Run E2E tests ✓
3. Monitor production 📊
```

**Benefits**:
- Improves readability
- Helps users scan document quickly
- No execution/parsing involved
- Perfectly safe

---

## 5. Tools & CI/CD Integration

### Linters That Reject Emojis in Code
- `pylint` (Python) - warns on non-ASCII
- `eslint` (JavaScript) - may flag encoding issues
- `black` (Python formatter) - clean ASCII output
- Type checkers that process file encoding

### What Gets Rejected
```
ERROR: Non-ASCII character in source file
ERROR: Encoding declaration needed for Unicode
ERROR: String literal contains emoji (UTF-8 issue)
```

---

## 6. How Claude Will Enforce This

### In Every Session
1. **Read this file** at session start
2. **Check file extension** before every write
3. **Scan for emojis** in executable files
4. **Auto-correct** if mistake detected
5. **Report** if unable to fix

### Self-Correction Protocol
```
IF emoji_detected_in_code_file:
  1. Remove emoji immediately
  2. Replace with clear ASCII comment
  3. Notify user of correction
  4. Re-verify file is clean
```

### Example Correction
**Before** (Detected):
```python
# Fetch data 🔍
data = fetch_keepa_product(asin)
```

**After** (Auto-corrected):
```python
# Fetch data from Keepa API
data = fetch_keepa_product(asin)
```

**Message to User**: "Removed emoji from code file, replaced with ASCII comment"

---

## 7. Exceptions (VERY RARE)

### When Emojis Might Be Acceptable
1. **Placeholder text** : Only in comments marked `TODO` (avoid even here)
2. **Documentation strings** : Only if not parsed by systems
3. **Type hints** : NO - use clear ASCII types

### Policy: When in Doubt
- **Default: NO EMOJIS**
- Ask user if uncertain
- Better safe than sorry

---

## 8. Checklist for Code Review

Before committing any code:

- [ ] No emojis in `.py` files
- [ ] No emojis in `.ts`, `.tsx` files
- [ ] No emojis in `.js` files
- [ ] No emojis in `.json` files
- [ ] No emojis in `.yaml` files
- [ ] No emojis in SQL or migrations
- [ ] No emojis in environment files
- [ ] No emojis in test files
- [ ] Markdown files can have emojis (encouraged)
- [ ] Code comments are clear ASCII
- [ ] Docstrings are clear ASCII
- [ ] Error messages are clear ASCII

---

## 9. Communication

### How to Reference This Rule
- "Follow CODE_STYLE_RULES.md"
- "Rule 1: No emojis in executable code"
- "Check file extension before writing"

### Where to Report Issues
If you catch an emoji in code:
1. Report it to @aziztrabelsi
2. Reference this document
3. Provide file path and line number
4. Include context

---

## 10. Version History

### v1.0 (2 Nov 2025)
- Initial rule set
- Comprehensive examples
- Self-check protocol
- Clear exceptions
- CI/CD integration notes

---

**Last Updated**: 2 Novembre 2025
**Status**: Active and enforced
**Owner**: Claude Code + Aziz Trabelsi
