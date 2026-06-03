import sys
import time
from pathlib import Path 
from dotenv import load_dotenv
from agent.bug_analyzer import analyze_bug
from agent.fix_generator import generate_fix
from agent.test_runner import run_tests
from agent.memory_engine import initialize_db, find_matching_bug, get_top_preferences, increment_reuse_count
from agent.feedback_manager import collect_feedback
from test_analyzer import bugs_directory

# Load environment variables from .env
load_dotenv()

def run_pipeline(bugs_directory):
    """
    Runs the debugging pipeline on a given bug directory
    Currently, we are running the pipeline without memory or feedback - just analyze, fix, and test.
    """

    # Initialize the database on every run
    initialize_db()

    print(f"\n{'='*60}")
    print(f"Running pipeline on: {bugs_directory}")
    print(f"{'='*60}")

    start_time = time.time()

    # Step - 1: Analyzing the bug
    print("\n[Step 1] - Analyzing the bug...")
    bug_context = analyze_bug(Path(bugs_directory))
    print(f" Bug Type: {bug_context['bug_type']}")
    print(f" Error Message: {bug_context['error_message']}")
    print(f" File: {bug_context['bug_file']}")

    # Step - 2: Check Level 1 memory for a matching bug
    print("\n[Step 2] Checking memory for matching bug...")
    confidence, match = find_matching_bug(bug_context)

    if confidence == "high" and match:
        # L1 HIT - resuse stored fix directly
        print(f"L1 HIT - High confidence match here. Reusing stored fix")
        # Accepted_fix column
        fixed_code = match[3]
        # bug_id column
        bug_id = match[0]
        increment_reuse_count(bug_id)
        fix_source = "stored"

        # Run tests on stored fix
        print("\n[Step 3] Running tests on stored fix...")
        test_result = run_tests(bug_context, fixed_code)

        if test_result["passed"]:
            print("Stored fix passed the tests.")
        else:
            print("Stored fix failed - falling back to Claude...")
            fixed_code = None
    
    if confidence != "high" or not match or fixed_code is None:
        # L1 MISS - retrieve preference and call Claude
        print(f"L1 MISS - Retrieving preferences for Claude prompt...")
        preferences = get_top_preferences()

        if preferences:
            print(f" Found {len(preferences)} preferences to inject.")
        else:
            print(" No preferences found - cold run.")

        fix_source = "claude"

        # Step 3 - Generate fix with Claude
        print("\n[Step 3] Generating fix with Claude...")
        fixed_code = generate_fix(bug_context, preferences)
        print(" Fix generated successfully.")

        # Step 4 - Run tests
        print("\n[Step 4] Running tests against fix...")
        test_result = run_tests(bug_context,fixed_code)

    # Step 5 - Collect engineer feedback
    resolution_time = time.time() - start_time
    collect_feedback(bug_context, fixed_code, test_result["passed"], resolution_time)

if __name__ == "__main__":
    # Default to bug_01 if no argument provided
    bugs_directory = sys.argv[1] if len(sys.argv) > 1 else "bugs/bugs_01_off_by_one"
    run_pipeline(bugs_directory)