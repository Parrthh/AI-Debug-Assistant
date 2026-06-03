# KHARKAR-PARTH-SOREN-INTERVIEW

## Project:
Build an end-to-end debugging pipeline that captures engineer preferences and improves its ability to autonomously steer fixes over time. The pipeline should:

• Accept a buggy codebase or snippet as input.
• Use an AI model to propose and implement a fix.
• Allow an engineer to review and optionally steer or correct the fix.
• Persist and learn from that feedback so future runs require less manual steering.
• Demonstrate, in some measurable way, that the pipeline improves over iterations.

The design of the learning/feedback mechanism is the core of this project. How you structure
preference capture, storage, and retrieval is up to you — that is the design problem we want to
see you solve.

---

## How It Works

The system learns at two levels simultaneously:

- **Level 1 — Bug Recognition:** Have we seen this exact bug before? If yes, reuse the stored fix directly — no Claude call needed.
- **Level 2 — Preference Augmentation:** New bug, but we have learned engineer preferences. Inject them into the Claude prompt to get a better first attempt.

---

## Project Structure

```
├── bugs/                        
│   ├── bug_01_off_by_one/       
│   ├── bug_02_type_error/       
│   ├── bug_03_logic_error/      
│   ├── bug_04_edge_case/        
│   └── bug_05_infinite_loop/    
├── agent/
│   ├── bug_analyzer.py          
│   ├── fix_generator.py         
│   ├── test_runner.py           
│   ├── memory_engine.py         
│   ├── prompt_builder.py        
│   └── feedback_manager.py      
├── benchmark/
│   └── benchmark_engine.py      
├── data/
│   └── memory.db                
├── main.py                      
├── requirements.txt
└── .env                         
```
---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/Kharkar-Parth-Soren-Interview.git
cd Kharkar-Parth-Soren-Interview
```

### 2. Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your API key
Create a `.env` file in the root:
ANTHROPIC_API_KEY=your_api_key_here

---

## Running the Pipeline

Run on a specific bug:
```bash
python main.py bugs/bug_01_off_by_one
python main.py bugs/bug_02_type_error
python main.py bugs/bug_03_logic_error
python main.py bugs/bug_04_edge_case
python main.py bugs/bug_05_infinite_loop
```

The pipeline will:
1. Analyze the bug and classify its type
2. Check memory for a matching bug (Level 1)
3. If no match — retrieve preferences and call Claude (Level 2)
4. Run tests against the fix
5. Ask you to review, provide feedback, or accept

---

## Running the Benchmark

```bash
python benchmark/benchmark_engine.py
```

Runs all 5 bugs twice — cold run with no memory, then warm run with accumulated memory — and produces a comparison report.

---

## Benchmark Results

| Metric | Cold Run | Warm Run | Delta |
|---|---|---|---|
| L1 Hit Rate | 0/5 | 5/5 | +5 |
| Claude Calls | 5/5 | 0/5 | -5 |
| Test Pass Rate | 5/5 | 5/5 | +0 |
| Acceptance Rate | 5/5 | 5/5 | +0 |
| Avg Resolution Time | 4.05s | 3.03s | -1.02s |

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Storage | SQLite | Lightweight, zero infra, self-contained |
| Memory type | Rule-based + scoring formula | Explainable, works with small dataset |
| Matching | Two-signal (bug_type + error_message) | Balances precision and flexibility |
| Learning levels | Two (L1 recognition + L2 preferences) | Demonstrates two distinct improvement dimensions |
| Fine-tuning | Not used | Requires large dataset, expensive, no real-time updates |
| Vector DB | Not used in V1 | Adds complexity without enough gain at this scale |

---

## Future Improvements

- Semantic memory retrieval using vector databases
- Multi-engineer preference profiles
- Repository-level memory
- Reinforcement-learning style ranking of successful fixes
- GitHub integration for real codebase debugging
