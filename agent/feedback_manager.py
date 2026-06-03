import os
import json
from platform import architecture
import anthropic
from anyio.lowlevel import T
from dotenv import load_dotenv
from agent.memory_engine import store_bug, store_preference, store_session

load_dotenv()

client = anthropic.Anthropic(api_key = os.getenv("ANTHROPIC_API_KEY"))

def extract_preference(feedback_text):
    # Calling Claude to extract a structured preference from free-text feedback,
    # Returns a dict with category, rule, and accepted fields

    prompt = f"""Extract a structured preference from this engineer feedback.
Return JSON only with fields: category, rule, accepted(boolean).
Categories: code_style, architecture, naming, error_handling, preformance, other

Feedback: "{feedback_text}"

Return only valid JSON, no explanation, no markdown."""

    message = client.messages.create(
        model = "claude-sonnet-4-20250514",
        max_tokens = 256,
        messages = [{"role":"user","content":prompt}]
    )

    response_text = message.content[0].text.strip()

    # Remove markdown if present
    if response_text.startswith("```"):
        lines = response_text.splitlines()
        response_text = "\n".join(lines[1:-1]).strip()

    # Parsing the JSON response
    preference = json.loads(response_text)
    return preference

def collect_feedback(bug_context, fixed_code, test_passed, resolution_time):
    """
    CLI Interface for engineer to review the fix
    Handles accept / reject / feedback flow.
    Stores the result in the database
    Returns True if fix was accepted, else False
    """

    interventions = 0

    print("\n" + "=" * 60)
    print("ENGINEER's REVIEW")
    print("=" * 60)
    print("\nFixed code:")
    print("-" * 40)
    print(fixed_code)
    print("-" * 40)

    if test_passed:
        print("\n Tests passed.")
    else:
        print("\n Tests failed.")

    # Ask the engineer for there review
    while True:
        print("\nWhat would you like to do?")
        print(" [1] Accept fix")
        print(" [2] Reject fix")
        print(" [3] Any feedback?")

        choice = input("\nYour choice between (1/2/3): ").strip().lower()

        if choice == "1":
            # If engineer accepted the fix
            print("\n Fix accepted. Storing in memory now...")
            store_bug(bug_context, fixed_code)
            store_session(
                bug_id = bug_context.get("bug_type","unknown"),
                fix_source = "claude",
                accepted = True,
                interventions = interventions,
                test_passed = test_passed, 
                resolution_time = resolution_time
            )
            return True

        elif choice == "2":
            # If engineer rejected the fix
            print("\n Fix Rejected.")
            store_session(
                bug_id = bug_context.get("bug_type", "unknown"),
                fix_source = "claude",
                accepted = False,
                interventions = interventions,
                test_passed = test_passed,
                resolution_time = resolution_time
            )
            return False

        elif choice == "3":
            # If engineer provides feedback
            interventions += 1
            feedback = input("\nYour feedback: ").strip()

            if feedback:
                print("\nExtracting preference from feedback...")
                try:
                    preference = extract_preference(feedback)
                    store_preference(
                        category = preference.get("category","other"),
                        rule = preference.get("rule",feedback),
                        accepted = preference.get("accepted", True)
                    )
                    print(f" Preference stored: {preference.get('rule')}")
                except Exception as e:
                    print(f" Could not extract preference: {e}")
            print("\nContinue reviewing the fix above.")

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
