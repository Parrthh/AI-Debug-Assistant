import os
from platform import python_branch
import anthropic
from dotenv import load_dotenv

from agent.prompt_builder import build_prompt

# Loading environment variables from .env file so we can access ANTHROPIC_API_KEY
load_dotenv()

# Initializing the Anthropic client using the API key from .env
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_fix(bug_context, preferences=None):
    """
    Send the code with bug to Claude and returns the fixed code.
    bug_context: dict returned by bug_analyzer.py
    preferences: list of preferenc strings from memory engine
    """

    # Build the prompt using prompt_builder
    # Preferences are injected here if available from memory engine
    prompt = build_prompt(bug_context, preferences)

    # Calls the Claude API
    message = client.messages.create(
        model = "claude-sonnet-4-20250514",
        max_tokens = 1024,
        messages = [{"role":"user","content": prompt}] 
    )

    # Extract the response and strip any whitespaces
    fixed_code = message.content[0].text.strip()

    # Removing the markdown code blocks if Claude included them
    if fixed_code.startswith("```"):
        lines = fixed_code.splitlines()
        fixed_code = "\n".join(lines[1:-1]).strip()
    
    return fixed_code