import subprocess
import sys
from pathlib import Path

# from test_analyzer import bugs_directory

def run_tests(bug_context, fixed_code):
    """
    Writing the fixed code to a temporary file and runs pytest against it
    Return a dict with pass/fail result and test output
    """
    bugs_directory = Path(bug_context["bugs_directory"])
    bug_file = Path(bug_context["bug_file"])

    # Writing claude's fixed code to the original bugged file temporarily
    # We back up the original so we can restore it after testing
    original_code = bug_file.read_text()
    bug_file.write_text(fixed_code)

    # Running pytest on the bug folder with the fixed code in place
    result = subprocess.run(
        [sys.executable, "-m","pytest", str(bugs_directory), "-v", "--timeout=5"],
        capture_output = True,
        text=True
    )

    # Restore the original bug code after testing
    # This ensures the bug stays in place for future runs
    bug_file.write_text(original_code)

    # Combine output for readability
    output = result.stdout + result.stderr

    # pytest returns 0 if all tests passed, non-zero if any failed
    passed = result.returncode == 0

    return {
        "passed": passed,
        "output": output
    }
