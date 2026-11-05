def triage(issue):
    text = issue.lower()

    if any(word in text for word in ["crash", "down", "data loss", "security", "cannot login"]):
        priority = "HIGH"
    elif any(word in text for word in ["error", "bug", "failed", "broken", "not working"]):
        priority = "MEDIUM"
    else:
        priority = "LOW"

    if "?" in issue or text.startswith(("how ", "why ", "what ")):
        category = "QUESTION"
    elif any(word in text for word in ["feature", "request", "would like", "please add"]):
        category = "FEATURE REQUEST"
    else:
        category = "BUG"

    print("\n--- PATCHPILOT TRIAGE ---")
    print("Summary:", issue[:150])
    print("Category:", category)
    print("Suggested priority:", priority)
    print("Why: Based on the reported wording and potential impact.")
    print("Missing information: Steps to reproduce, expected result, actual result.")
    print("Questions:")
    print("1. What steps caused this issue?")
    print("2. What did you expect to happen?")
    print("3. What happened instead?")
    print("Suggested role: Developer")
    print("Next action: Review the report and approve investigation.")
    print("-------------------------")

print("PatchPilot - Free Bug Triage Prototype")
issue = input("\nDescribe a bug: ").strip()

if issue:
    triage(issue)
else:
    print("No issue entered.")
