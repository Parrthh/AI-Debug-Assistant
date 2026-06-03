from mimetypes import init
import sys
import time 
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agent.bug_analyzer import analyze_bug
from agent.fix_generator import generate_fix
from agent.test_runner import run_tests
from agent.memory_engine import (
    initialize_db, find_matching_bug, get_top_preferences,
    increment_reuse_count, store_bug, store_session
)

load_dotenv()

# All 5 bug directories
BUGS_DIRS = [
    "bugs/bug_01_off_by_one",
    "bugs/bug_02_type_error",
    "bugs/bug_03_logic_error",
    "bugs/bug_04_edge_case",
    "bugs/bug_05_infinite_loop",
]

def run_single_bug(bugs_directory, auto_accept = True):
    """
    Runs the pipeline on a single bug without CLI interaction
    auto_accept = True means we automatically accept Claude's fix
    If tests pass - no human input needed for benchmarking
    Returns a dict of metrics for this run
    """
    start_time = time.time()

    # Step - 1: Analyze the Bug
    bug_context = analyze_bug(Path(bugs_directory))

    # Step - 2: Check Level 1 memory
    confidence, match = find_matching_bug(bug_context)

    claude_called = False
    fix_source = "stored"
    fixed_code = None

    if confidence == "high" and match:
        # L1 HIT - Reuse stored fix
        fixed_code = match[3]
        increment_reuse_count(match[0])
        fix_source = "stored"
    else:
        # L1 MISS - Call Claude with preferences
        preferences = get_top_preferences()
        fixed_code = generate_fix(bug_context, preferences)
        claude_called = True
        fix_source = "claude"

    # Step - 3: Run tests
    test_result = run_tests(bug_context, fixed_code)

    # Step - 4: Auto accept if tests pass
    accepted = False
    if test_result["passed"] and auto_accept:
        store_bug(bug_context, fixed_code)
        accepted = True
    
    resolution_time = time.time() - start_time

    # Store session for tracking
    store_session(
        bug_id = bug_context.get("bug_type","unknown"),
        fix_source=fix_source,
        accepted = accepted,
        interventions = 0,
        test_passed = test_result["passed"],
        resolution_time = resolution_time
    )

    return {
        "bugs_directory": bugs_directory,
        "bug_type": bug_context["bug_type"],
        "fix_source": fix_source,
        "claude_called": claude_called,
        "test_passed": test_result["passed"],
        "accepted": accepted,
        "resolution_time": round(resolution_time, 2)
    }

def run_benchmark():
    """
    Runs all 5 bugs twice:
    - Cold Run: Clears memory first, runs all bugs
    - Warm Run: Runs all bugs again with accumulated memory
    Prints a comparison report
    """

    initialize_db()

    print("\n" + "="*60)
    print("BENCHMARK ENGINE")
    print("="*60)

    # COLD RUN
    print("\n COLD RUN - No memory, fresh start")
    print("-" * 60)

    cold_results = []
    for bugs_directory in BUGS_DIRS:
        print(f" Running {bugs_directory}...")
        result = run_single_bug(bugs_directory, auto_accept = True)
        cold_results.append(result)
        status = "Tests Passed!" if result["test_passed"] else "Tests Failed!"
        source = "STORED" if not result["claude_called"] else "CLAUDE"
        print(f" {status} {result['bug_type']} - {source} - {result['resolution_time']}s")

    # WARM RUN
    print("\n WARM RUN - Memory accumulated from cold run")
    print("-" * 60)

    warm_results = []
    for bugs_directory in BUGS_DIRS:
        print(f" Running {bugs_directory}...")
        result = run_single_bug(bugs_directory, auto_accept = True)
        warm_results.append(result)
        status = "Tests Passed!" if result["test_passed"] else "CLAUDE"
        source = "STORED" if not result["claude_called"] else "CLAUDE"
        print(f" {status} {result['bug_type']} - {source} - {result['resolution_time']}s")
    
    # REPORT
    print("\n" + "=" * 60)
    print("BENCHMARK REPORT")
    print("=" * 60)

    # Calculate cold metrics
    cold_claude_calls = sum(1 for r in cold_results if r["claude_called"])
    cold_test_pass = sum(1 for r in cold_results if r["test_passed"])
    cold_accepted = sum(1 for r in cold_results if r["accepted"])
    cold_l1_hits = sum(1 for r in cold_results if not r["claude_called"])
    cold_avg_time = sum(r["resolution_time"] for r in cold_results) / len(cold_results)

    # Calculate warm metrics
    warm_claude_calls = sum(1 for r in warm_results if r["claude_called"])
    warm_test_pass = sum(1 for r in warm_results if r["test_passed"])
    warm_accepted = sum(1 for r in warm_results if r["accepted"])
    warm_l1_hits = sum(1 for r in warm_results if not r["claude_called"])
    warm_avg_time = sum(r["resolution_time"] for r in warm_results) / len(warm_results)

    total = len(BUGS_DIRS)

    print(f"\n{'Metric':<30} {'Cold Run':>12} {'Warm Run':>12} {'Delta':>10}")
    print("-" * 66)
    print(f"{'L1 Hit Rate':<30} {f'{cold_l1_hits}/{total}':>12} {f'{warm_l1_hits}/{total}':>12} {f'+{warm_l1_hits - cold_l1_hits}':>10}")
    print(f"{'Claude Calls':<30} {f'{cold_claude_calls}/{total}':>12} {f'{warm_claude_calls}/{total}':>12} {f'{warm_claude_calls - cold_claude_calls}':>10}")
    print(f"{'Test Pass Rate':<30} {f'{cold_test_pass}/{total}':>12} {f'{warm_test_pass}/{total}':>12} {f'+{warm_test_pass - cold_test_pass}':>10}")
    print(f"{'Acceptance Rate:':<30} {f'{cold_accepted}/{total}':>12} {f'{warm_accepted}/{total}':>12} {f'+{warm_accepted - cold_accepted}':>10}")
    print(f"{'Average Resolution Time':<30} {f'{cold_avg_time:.2f}s':>12} {f'{warm_avg_time:.2f}s':>12} {f'{warm_avg_time - cold_avg_time:.2f}s':>10}")
    print("="*66)

    print("\n Benchmark complete.")

if __name__ == "__main__":
    run_benchmark()