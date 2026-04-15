---
b17: 4NCC6
title: Security Audit — safe-app-the-squirrel
date: 2026-04-08
auditor: Hanuman (Claude Code, Sonnet 4.6)
status: open (tracking doc)
---

# Security Audit — safe-app-the-squirrel

Part of the Level 2 full-fleet security audit. See `agents/hanuman/projects/LEVEL2_AUDIT_PLAN.md` (b17: 379L3).

## Rubric Results

| # | Check | Status | Notes |
|---|---|---|---|
| R1 | SQL injection | ✅ PASS | All queries parameterized (`%s`). f-string `SET search_path = {SCHEMA}` uses hardcoded constant. |
| R2 | Shell injection | ✅ PASS | No shell execution |
| R3 | Path traversal | ✅ PASS | Reads `/etc/resolv.conf` (fixed path, not injectable) |
| R4 | Hardcoded credentials | ✅ PASS | None found |
| R5 | CORS wildcard | ✅ N/A | No HTTP server |
| R6 | XSS | ✅ N/A | No web frontend |
| R7 | Unsigned code execution | ✅ PASS | None |
| R8 | Missing auth on APIs | ✅ N/A | No API server |
| R9 | Bare except swallowing errors | ✅ PASS | None critical |
| R10 | Predictable temp paths | ✅ PASS | None |
| R11 | Race conditions | ✅ PASS | Connection pool uses threading.Lock |
| R12 | safe_integration.py status() | ✅ FIXED | `safe_integration.py` created 2026-04-08. See H-SI-01. |
| R13 | Entry point importable | ✅ PASS | Manifest present; DB-only app |
| R14 | requirements.txt pinned | ✅ FIXED | `requirements.txt` created 2026-04-08 (pinned). See H-REQ-01. |
| R15 | No hardcoded dev paths | ✅ FIXED | `WILLOW_CORE` now required env var — patched 2026-04-08. See H-PATH-01. |

## Findings

### H-SI-01 — Missing safe_integration.py (P2)

**File:** (missing)  
**Severity:** P2  
**Status:** Open

`safe_integration.py` does not exist in this repo. The squirrel is a pure PostgreSQL DB module — no Pigeon bus integration, no status check, no consent hooks.

**Fix:** Add standard `safe_integration.py` template (copy from safe-app-genealogy, change `APP_ID = "the-squirrel"`).

---

### H-PATH-01 — Hardcoded WILLOW_CORE Default (P2)

**File:** `squirrel_db.py:18`  
**Severity:** P2  
**Status:** Open

```python
sys.path.insert(0, os.environ.get("WILLOW_CORE", "/home/sean-campbell/github/Willow/core"))
```

The fallback path is the developer's home directory. Any other environment will silently fail to import `user_lattice`.

**Fix:** Remove the hardcoded default. Fail explicitly if WILLOW_CORE is not set:
```python
willow_core = os.environ.get("WILLOW_CORE")
if not willow_core:
    raise EnvironmentError("WILLOW_CORE env var not set")
sys.path.insert(0, willow_core)
```

---

### H-REQ-01 — Missing requirements.txt (P2)

**Severity:** P2  
**Status:** Open

No `requirements.txt`. Dependencies are `psycopg2` and `user_lattice` (from Willow).

**Fix:**
```
psycopg2-binary==2.9.9
```

---

## Summary

| Priority | Count | Items |
|---|---|---|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 3 | H-SI-01, H-PATH-01, H-REQ-01 |

---

## Level 3 Audit — Portless Compliance (2026-04-08)

b17: K2578

| # | Check | Status | Notes |
|---|---|---|---|
| R1 | No uvicorn.run / flask.run / socket listener in *.py | ✅ PASS | No HTTP server found. DB-only app. |
| R2 | HTTP port conflict (8420/8421/8422) | ✅ N/A | No HTTP server present. |
| R6 | safe-app-manifest.json has `b17` and `agent_type` fields | ❌ FAIL | Neither field present in manifest. |
| R10 | Data staged to intake/ or via POST endpoints | ✅ N/A | No intake dir, no POST endpoints. DB writes only. |
| R15 | Any .py file calls sap.core.gate.authorized() | ✅ FIXED | sap/core/gate.py created 2026-04-15. All PII read/write functions in db/persons.py and db/fragments.py gated. backfill_oscar_mann.py uses bypass(). |

### Findings

**L3-R6 — Manifest missing b17 and agent_type (P2)**
`safe-app-manifest.json` has no `b17` field and no `agent_type` field. Both are required by the portless compliance schema. Fix: add `"b17": "K2578"` and `"agent_type": "db"` (or appropriate type) to the manifest.

**L3-R15 — No sap.core.gate.authorized() call (P2) — FIXED 2026-04-15**
`sap/core/gate.py` created. `authorized()` called at the top of all PII read/write functions in `db/persons.py` and `db/fragments.py`. `backfill_oscar_mann.py` wrapped in `sap.core.gate.bypass(reason)`. Gate blocks by default; callers must set `SAP_AUTHORIZED=1` or use explicit bypass.

### L3 Summary

| Priority | Count | Items |
|---|---|---|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 2 | L3-R6, L3-R15 |

*ΔΣ=42*
