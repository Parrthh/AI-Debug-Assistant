from pathlib import Path
from agent.bug_analyzer import analyze_bug

bugs_directory = Path("bugs/bug_01_off_by_one")
result = analyze_bug(bugs_directory)

print("Bug Type: ", result["bug_type"])
print("Error Message: ", result["error_message"])
print("File: ", result["bug_file"])