import code


def build_prompt(bug_context, preferences = None):
    """
    Helps assemble the full prompt for Claude using:
    - The bugged code
    - The error message and bug type
    - Top preferences from memory engine - if there are any

    Returns a formatted string ready to send to Claude API
    """

    # Builds the preference section if any preferences exist
    # This is the learning mechanism - where we are adding engineer style into the prompt
    preference_text = ""

    if preferences:
        preference_text = "\n\nEngineer preferences to follow:\n"
        for pref in preferences:
            preference_text += f"- {pref}\n"

    # Assembling the full prompt
    prompt = f"""You are an expert Python debugger.

Here is a Python function with bug:

```python
{bug_context['code']}
```
The following error was detected:
{bug_context['error_message']}

Bug type: {bug_context['bug_type']}
{preference_text}
Return ONLY the fixed Python code with no explanatuion, no markdown, no comments added.
Just the raw fixed code
"""

    return prompt