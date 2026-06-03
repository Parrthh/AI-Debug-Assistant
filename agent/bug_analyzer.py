# Lets us use terminal commands in Python. We will use it to run pytest.
import subprocess
# Lets us use the system's Python interpreter. We will use it to run pytest.
import sys

# Linking Python's built-in error names to our own bug categories
ERROR_TYPE_MAP = {
    "IndexError": "off_by_one",
    "AssertionError": "off_by_one",
    "TypeError": "type_error",
    "ValueError": "logic_error",
    "RecursionError": "infinite_loop",
    "TimeoutExpired": "infinite_loop"
}

def analyze_bug(bugs_directory):
    # Finds the bug code file from our directory which is any ".py" that does not start with "test_"
    for f in bugs_directory.iterdir():
        if f.suffix == ".py" and not f.name.startswith("test_"):
            bug_file = f
            break
    # Reads the content of the bug_file and captures the output as a string    
    code = bug_file.read_text()

    # Runs the pytest on the bug folder and captures the output as a string
    # We are implementing --timeout = 5 to ensure infinite loop does not hang the process

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(bugs_directory), "-v", "--timeout=5"],
        capture_output = True,
        text = True
    )
    
    # Combines stdout and stderr into one string to scan for errors
    output = result.stdout + result.stderr

    # Default values if there is no match found
    bug_type = "unknown"
    error_message = "unknown"

    # Classify the bug type by scanning output for known Python error keywords
    for error_key, category in ERROR_TYPE_MAP.items():
        if error_key in output:
            bug_type = category
            break
    
    # We will extract the first line that looks like an error message
    # This is stored in the database for Level 1 matching
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("E "):
            error_message = line[2:].strip()
            break

    # Fallback to FAILED line if there is no line found that starts with "E"
    if error_message == "unknown error":
        for line in output.splitlines():
            line = line.strip()
            if "FAILED" in line and not line.startswith("="):
                error_message = line
                break
    
    # Returning everything the pipeline needs as a clean dictionary
    return {
        "bug_type": bug_type,
        "error_message": error_message,
        "code": code,
        "bugs_directory": str(bugs_directory),
        "bug_file": str(bug_file)
    }






