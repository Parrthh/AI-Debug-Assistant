# Preference-Aware Autonomous Debugging Agent
## Architecture Document

---

## 1. System Overview

This system is an autonomous debugging pipeline that learns from engineer feedback over time. It accepts buggy Python code, uses Claude AI to generate fixes, allows engineers to review and provide feedback, and stores that knowledge so future debugging sessions require progressively less human intervention.

The core insight: learning happens at **two levels** simultaneously.

- **Level 1 — Bug Recognition:** Have we seen this exact/similar bug before? If yes, reuse the stored fix directly.
- **Level 2 — Preference Augmentation:** We haven't seen this bug, but we have learned engineer preferences. Inject them into the Claude prompt to get a better first attempt.

---

## 2. System Architecture — Developer Perspective

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py (Orchestrator)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │           Bug Analyzer               │
          │  - Parses buggy code                 │
          │  - Extracts error message            │
          │  - Classifies bug type               │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │           Memory Engine              │
          │  - Level 1: Bug match lookup         │
          │  - Level 2: Preference retrieval     │
          │  - SQLite backend                    │
          └──────────┬───────────────┬──────────┘
                     │               │
          ┌──────────▼──────┐   ┌───▼──────────────────┐
          │  [L1 HIT]       │   │  [L1 MISS]            │
          │  Apply stored   │   │  Prompt Builder        │
          │  fix directly   │   │  - Bug context        │
          └──────────┬──────┘   │  - Top N preferences  │
                     │          │  - Error + code       │
                     │          └───────────┬───────────┘
                     │                      │
                     │          ┌───────────▼───────────┐
                     │          │   LLM Fix Generator    │
                     │          │   - Calls Claude API   │
                     │          │   - Returns fixed code │
                     │          └───────────┬───────────┘
                     │                      │
          ┌──────────▼──────────────────────▼───────────┐
          │                 Test Runner                   │
          │  - Runs pytest against proposed fix           │
          │  - Records pass/fail                          │
          └──────────────────────┬───────────────────────┘
                                 │
          ┌──────────────────────▼───────────────────────┐
          │              Feedback Manager                  │
          │  - Engineer reviews fix via CLI                │
          │  - Accept / Reject / Provide feedback          │
          │  - Extracts structured preferences via Claude  │
          │  - Persists to SQLite                          │
          └──────────────────────┬───────────────────────┘
                                 │
          ┌──────────────────────▼───────────────────────┐
          │              Benchmark Engine                  │
          │  - Tracks acceptance rate                      │
          │  - Tracks Claude call count                    │
          │  - Tracks human interventions                  │
          │  - Produces improvement report                 │
          └──────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | File | Responsibility |
|---|---|---|
| Orchestrator | `main.py` | Controls end-to-end pipeline flow |
| Bug Analyzer | `agent/bug_analyzer.py` | Parses code, classifies bug type, extracts error message |
| Memory Engine | `agent/memory_engine.py` | L1 bug matching + L2 preference retrieval from SQLite |
| Prompt Builder | `agent/prompt_builder.py` | Assembles Claude prompt from bug context + preferences |
| Fix Generator | `agent/fix_generator.py` | Calls Claude API, returns proposed fix |
| Test Runner | `agent/test_runner.py` | Runs pytest, returns pass/fail result |
| Feedback Manager | `agent/feedback_manager.py` | CLI review interface, preference extraction, persistence |
| Benchmark Engine | `benchmark/benchmark_engine.py` | Tracks and reports metrics across sessions |

---

## 3. Memory Engine — Detailed Design

This is the core of the system. It manages two types of memory.

### 3.1 Level 1 — Bug Recognition Memory

**Purpose:** Recognize bugs we have seen before and reuse accepted fixes directly.

**Matching Strategy — Two-Signal Approach:**

A new bug is matched against stored bugs using two signals combined:

1. **Bug Type Match** — Is the category the same? (e.g., both are `type_error`)
2. **Error Message Similarity** — Does the error message closely resemble a stored one?

**Confidence Tiers:**

| Condition | Confidence | Action |
|---|---|---|
| Bug type AND error message both match | High | Apply stored fix directly, skip Claude |
| Bug type matches only | Medium | Use stored fix as hint, still call Claude |
| Neither matches | None | Full Claude call with preferences injected |

**Why two signals?**
- Error message alone is too rigid — same bug on a different line number would be treated as new
- Bug type alone is too broad — same category can have completely different fixes
- Together they give meaningful, defensible matching

### 3.2 Level 2 — Preference Memory

**Purpose:** Learn engineer style preferences from feedback and inject them into future prompts.

**How preferences are stored:**
When an engineer provides feedback (e.g., *"don't add helper functions"*), Claude extracts a structured preference:

```json
{
  "category": "code_style",
  "rule": "avoid adding helper functions",
  "accepted": true
}
```

**Retrieval — Scoring Formula:**

```
score = (frequency × 0.5) + (recency_score × 0.3) + (acceptance_rate × 0.2)
```

- **Frequency (0.5 weight):** How many times has the engineer expressed this preference? Higher frequency = more stable preference.
- **Recency (0.3 weight):** More recent preferences are more relevant. Engineer style evolves over time.
- **Acceptance Rate (0.2 weight):** Preferences that led to accepted fixes are more reliable signals than those that did not.

**Why these weights?**
- Frequency carries the most weight because repeated signals are the strongest evidence of a genuine, stable preference.
- Recency is secondary — it acts as a freshness filter so outdated preferences do not dominate.
- Acceptance rate is a quality signal — it down-weights preferences that did not actually improve outcomes.

Top 5 scoring preferences are injected into every Claude prompt for new bugs.

---

## 4. Data Model

### 4.1 `bugs` Table — Level 1 Memory
```
bug_id          TEXT PRIMARY KEY
bug_type        TEXT    -- e.g., "off_by_one", "type_error"
error_message   TEXT    -- extracted error string
original_code   TEXT    -- the buggy code
accepted_fix    TEXT    -- the fix the engineer accepted
reuse_count     INTEGER -- how many times this fix was reused
created_at      TEXT
```

### 4.2 `preferences` Table — Level 2 Memory
```
preference_id   TEXT PRIMARY KEY
category        TEXT    -- e.g., "code_style", "architecture"
rule            TEXT    -- e.g., "avoid helper functions"
frequency       INTEGER -- how many times this preference was expressed
acceptance_rate REAL    -- ratio of accepted fixes when this pref was applied
last_seen       TEXT    -- timestamp of most recent occurrence
created_at      TEXT
```

### 4.3 `sessions` Table — Benchmark Tracking
```
session_id        TEXT PRIMARY KEY
bug_id            TEXT
fix_source        TEXT  -- "stored" (L1) or "claude" (L2)
accepted          BOOLEAN
interventions     INTEGER
test_passed       BOOLEAN
resolution_time   REAL
timestamp         TEXT
```

---

## 5. Learning Mechanism Summary

```
Session 1 (cold):
  → No memory → Full Claude call → Engineer gives feedback
  → Store bug + fix + extract preferences

Session 2:
  → Bug matches stored bug (L1) → Reuse fix → Tests pass → Done
  → OR: New bug + preferences injected (L2) → Better Claude fix → Less feedback needed

Session N:
  → L1 hit rate increases → fewer Claude calls needed
  → L2 preferences accumulate → Claude first attempts improve
  → Human interventions decrease measurably
```

---

## 6. Benchmark Metrics

| Metric | How Measured | Expected Trend |
|---|---|---|
| L1 Hit Rate | Stored fix reuses / total bugs | Increases over time |
| Claude Call Rate | Claude calls / total bugs | Decreases over time |
| Fix Acceptance Rate | Accepted fixes / total fixes | Increases over time |
| Human Interventions | Feedback rounds per session | Decreases over time |
| Test Pass Rate | Tests passed / total fixes | Increases over time |

---

## 7. Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Language | Python 3.11+ | Natural fit for LLM tooling |
| LLM | Claude API (claude-sonnet-4-20250514) | Required by assessment |
| Database | SQLite | Lightweight, zero infra, self-contained |
| Test Runner | pytest | Standard Python testing |
| CLI Interface | Python input() | Simple, no dependencies |

---

## 8. Key Design Decisions & Tradeoffs

### Why SQLite over a vector database?
For V1, rule-based retrieval with a scoring formula is sufficient and far simpler to reason about, explain, and debug. A vector DB would add semantic similarity search but also adds significant complexity for a project of this scope. Semantic retrieval is noted as a future improvement.

### Why not fine-tune?
Fine-tuning requires large datasets, is expensive, and does not allow real-time preference updates. Retrieval-augmented preferences are lightweight, explainable, and update instantly from each session.

### Why two-level memory vs. one?
A single preference memory cannot short-circuit Claude calls when an exact bug match exists. Two levels allows the system to demonstrate two distinct types of improvement — recognition-based and preference-based — which makes the benchmark story cleaner and more compelling.
