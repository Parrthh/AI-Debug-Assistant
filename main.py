import sys
from pathlib import Path 
from dotenv import load_dotenv
from agent.bug_analyzer import analyze_bug
from agent.fix_generator import generate_fix
from agent.test_runner import run_tests
from test_analyzer import bugs_directory

# Load environment variables from .env
load_dotenv()

def run_pipeline(bugs_directory):
    """
    Runs the debugging pipeline on a given bug directory
    Currently, we are running the pipeline without memory or feedback - just analyze, fix, and test.
    """

    print(f"\n{'='*60}")
    print(f"Running pipeline on: {bugs_directory}")
    print(f"{'='*60}")

    # Step - 1: Analyzing the bug
    # Runs pytest, captures error, classifies bug type
    print("\n[Step 1] - Analyzing the bug...")
    bug_context = analyze_bug(Path(bugs_directory))
    print(f" Bug Type: {bug_context['bug_type']}")
    print(f" Error Message: {bug_context['error_message']}")
    print(f" File: {bug_context['bug_file']}")

    # Step - 2: Generating a fix using Claude
    # Currently, we are still not using preferences
    print("\n[Step 2] - Generating fix with Claude...")
    fixed_code = generate_fix(bug_context)
    print(" Fix generated successfully")

    # Step 3 - Running tests against the fix
    # Temporarily replacing the bugged code with fix, running pytest, restores original
    print("\n[Step 3] - Running tests against the fix...")
    test_result = run_tests(bug_context, fixed_code)

    # Step 4 - Printing result
    if test_result["passed"]:
        print("\n Tests Passed - Claude's fix is correct")
    else:
        print("\n Tests Failed - Claude's fix are not working")

    print("\nFixed code:")
    print("-" * 40)
    print(fixed_code)
    print("-" * 40)

    return {
        "bug_context": bug_context,
        "fixed_code": fixed_code,
        "test_result": test_result
    }

if __name__ == "__main__":
    # Default to bug_01 if no argument provided
    bugs_directory = sys.argv[1] if len(sys.argv) > 1 else "bugs/bug_01_off_by_one"
    run_pipeline(bugs_directory)