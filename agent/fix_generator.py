import os
from platform import python_branch
import anthropic
from dotenv import load_dotenv

# Loading environment variables from .env file so we can access ANTHROPIC_API_KEY
load_dotenv()

# Initializing the Anthropic client using the API key from .env
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_fix(bug_context, preferences=None):
    """
    We send the bugged code to Claude and returns the fixed code.
    bug_context: dict returned by bug_analyzer.py
    preferences: list of preference strings, this will be something said by engineers (gets retrieved from the database)
    """

    # Building the preference section of the prompt if any preference exists
    preference_text = ""
    if preferences:
        preference_text = "\n\nEngineer preferences to follow:\n"
        for pref in preferences:
            preference_text += f"- {pref}\n"
    
    # Building the full prompt that will be sent to Claude
    # We will include the bugged code, the error message, and the bug type
    # We will ask Claude to return ONLY the fixed code
    # So that we can write it directly to a file without any cleanup needed
    prompt = f"""You are an expert Python debugger.

Here is a buggy Python function:

```python
{bug_context['code']}
```
The following error was detected:
{bug_context['error_message']}

Bug type: {bug_context['bug_type']}
{preference_text}
Return ONLY the fixed Python code with no explanation, no markdown, no comments added.
Just the raw fixed code.
"""

    # Calls the Claude API with our prompt
    # max_tokens = 1024 is enough for small function fixes

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role":"user", "content":prompt}
        ]
    )

    # Extract the response from Claude and strip any extra whitespace
    fixed_code = message.content[0].text.strip()

    # Removing markdown code blocks if Claude included them
    if fixed_code.startswith("```"):
        lines=fixed_code.splitlines()
        fixed_code = "\n".join(lines[1:-1]).strip()
    return fixed_code