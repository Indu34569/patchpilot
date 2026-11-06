
import re


def triage(issue):
    text = " ".join(issue.strip().split())
    lower = text.lower()

    # Category
    if not text:
        category = "QUESTION"
    elif re.search(r"\b(feature request|please add|would like|wish we could|new feature)\b", lower):
        category = "FEATURE REQUEST"
    elif "?" in text or lower.startswith(("how ", "why ", "what ", "where ", "when ", "can ", "does ")):
        category = "QUESTION"
    else:
        category = "BUG"

    # Priority
    if re.search(r"\b(security vulnerability|data breach|unauthorized access|exposed credentials)\b", lower):
        priority = "CRITICAL"
        explanation = "A potential security vulnerability could expose users or systems."
    elif re.search(r"\b(data loss|lost data|service outage|system down|all users affected|production down)\b", lower):
        priority = "CRITICAL"
        explanation = "The report indicates data loss or a widespread service outage."
    elif category != "BUG":
        priority = "LOW"
        explanation = f"This is a {category.lower()}, not a confirmed production bug."
    elif re.search(r"\b(login failure|cannot login|can't log in|unable to log in|crash|crashes)\b", lower):
        priority = "HIGH"
        explanation = "A crash or login failure can block important user workflows."
    elif re.search(r"\b(error|failed|broken|not working|incorrect|unexpected)\b", lower):
        priority = "MEDIUM"
        explanation = "The report describes broken or unexpected behavior, but gives no evidence of a widespread outage."
    else:
        priority = "LOW"
        explanation = "No clear severe-impact or urgent failure signal was found."

    # Summary
    if not text:
        summary = "No report text was provided."
    else:
        first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
        summary = first[:157].rstrip(" ,;") + ("..." if len(first) > 160 else "")
        if summary and summary[-1] not in ".!?":
            summary += "."

    # Missing information and follow-up questions
    checks = [
        ("steps to reproduce", r"\b(steps to reproduce|reproduce|first click|then click)\b",
         "What steps reproduce this issue?"),
        ("expected result", r"\b(expected|should happen|supposed to)\b",
         "What did you expect to happen?"),
        ("actual result", r"\b(actual|instead|but it|happens when)\b",
         "What happened instead?"),
        ("app version", r"\b(version|build|v\d+\.\d+)\b",
         "Which app version are you using?"),
        ("platform", r"\b(mac|macos|windows|linux|android|ios|browser|desktop)\b",
         "Which device, operating system, or browser are you using?"),
        ("frequency", r"\b(always|every time|sometimes|occasionally|once|intermittent)\b",
         "Does this happen every time or only sometimes?"),
        ("logs or error details", r"\b(logs?|stack trace|error message|screenshot)\b",
         "Can you share the relevant error message or logs?"),
    ]

    missing = []
    questions = []

    if not text:
        missing = ["report text"]
        questions = ["What issue would you like PatchPilot to triage?"]
    elif category == "BUG":
        for label, pattern, question in checks:
            if not re.search(pattern, lower):
                missing.append(label)
                if len(questions) < 3:
                    questions.append(question)
    elif category == "FEATURE REQUEST":
        if not re.search(r"\b(problem|pain point|would help|so that)\b", lower):
            missing.append("problem or use case")
            questions.append("What problem would this feature solve?")
        if not re.search(r"\b(users?|team|customers?|developers?)\b", lower):
            missing.append("who would benefit")
            questions.append("Who would benefit from this feature?")
        if not re.search(r"\b(success|acceptance|so that|able to)\b", lower):
            missing.append("success criteria")
            questions.append("What would a successful version look like?")
    else:
        if not re.search(r"\b(tried|attempted|checked|searched|looked)\b", lower):
            missing.append("what has already been tried")
            questions.append("What have you already tried?")
        if not re.search(r"\b(want to|need to|goal|hoping|so that)\b", lower):
            missing.append("desired outcome")
            questions.append("What outcome are you hoping for?")

    # Suggested team role
    roles = [
        (r"\b(login|password|authentication|auth|sso|mfa)\b", "Identity & Access engineer"),
        (r"\b(security|vulnerability|permission|unauthorized)\b", "Security engineer"),
        (r"\b(upload|attachment|download|file)\b", "Files & Storage engineer"),
        (r"\b(search|index)\b", "Search engineer"),
        (r"\b(database|sql|postgres)\b", "Database engineer"),
        (r"\b(message|channel|chat|notification)\b", "Messaging engineer"),
        (r"\b(button|layout|display|screen|interface)\b", "Frontend engineer"),
    ]

    suggested_role = "Developer"
    for pattern, role in roles:
        if re.search(pattern, lower):
            suggested_role = role
            break

    if category == "QUESTION":
        suggested_role = "Support engineer"
    elif category == "FEATURE REQUEST":
        suggested_role = "Product manager"

    next_action = (
        "Human approval required: review the report and approve the suggested "
        "investigation before assigning or changing anything."
    )

    return {
        "summary": summary,
        "category": category,
        "priority": priority,
        "priority_explanation": explanation,
        "missing_information": missing,
        "follow_up_questions": questions[:3],
        "suggested_role": suggested_role,
        "next_action": next_action,
        "requires_human_approval": True,
    }


def main():
    print("PatchPilot - Free Bug Triage Prototype")
    issue = input("\nDescribe an issue: ").strip()

    if not issue:
        print("No issue entered.")
        return

    result = triage(issue)

    print("\n--- PATCHPILOT TRIAGE ---")
    print("Summary:", result["summary"])
    print("Category:", result["category"])
    print("Priority:", result["priority"])
    print("Why:", result["priority_explanation"])
    print("Missing information:", ", ".join(result["missing_information"]) or "None identified")
    print("Follow-up questions:")
    for number, question in enumerate(result["follow_up_questions"], 1):
        print(f"{number}. {question}")
    print("Suggested role:", result["suggested_role"])
    print("Next action:", result["next_action"])
    print("Human approval required:", result["requires_human_approval"])
    print("-------------------------")


if __name__ == "__main__":
    main()
