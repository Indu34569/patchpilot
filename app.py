
import re


def triage(issue):
    text = " ".join(issue.strip().split())
    lower = text.lower()

    # Detect bug indicators
    bug_pattern = (
        r"\b(?:crash(?:es|ed|ing)?|freez(?:e|es|ing|ed)?|froze|frozen|"
        r"hang(?:s|ing)?|stops? responding|not responding|unresponsive|"
        r"not working|broken|fails?|failed|failure|error|exception|"
        r"incorrect|unexpected|glitch|bug|defect|won't load|"
        r"doesn't load|cannot load|unable to load)\b"
    )

    critical_pattern = (
        r"\b(?:security vulnerability|data breach|unauthorized access|"
        r"exposed credentials|data loss|lost data|service outage|"
        r"system down|production down|all users affected)\b"
    )

    has_bug_signal = bool(re.search(bug_pattern, lower))
    critical = bool(re.search(critical_pattern, lower))

    # Category
    if not text:
        category = "QUESTION"
    elif has_bug_signal:
        category = "BUG"
    elif re.search(
        r"\b(feature request|please add|would like|wish we could|new feature)\b",
        lower
    ):
        category = "FEATURE REQUEST"
    elif (
        "?" in text
        or lower.startswith((
            "how ", "why ", "what ", "where ", "when ",
            "can ", "does ", "is ", "are "
        ))
    ):
        category = "QUESTION"
    else:
        category = "BUG"

    # Priority
    if critical:
        priority = "CRITICAL"
        explanation = (
            "The report indicates a potential security incident, "
            "data loss, or widespread service outage."
        )
    elif category != "BUG":
        priority = "LOW"
        explanation = (
            f"This is a {category.lower()}, not a confirmed production bug."
        )
    elif re.search(
        r"\b(?:crash(?:es|ed|ing)?|login failure|cannot login|"
        r"can't log in|unable to log in)\b",
        lower
    ):
        priority = "HIGH"
        explanation = (
            "A crash or login failure can block important user workflows."
        )
    elif has_bug_signal:
        priority = "MEDIUM"
        explanation = (
            "The report describes broken or unexpected behavior, "
            "but does not establish a widespread outage."
        )
    else:
        priority = "LOW"
        explanation = "No clear severe-impact or urgent failure signal was found."

    # Summary
    if not text:
        summary = "No report text was provided."
    else:
        first = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
        summary = first[:157].rstrip(" ,;") + (
            "..." if len(first) > 160 else ""
        )
        if summary and summary[-1] not in ".!?":
            summary += "."

    # Area detection
    area_rules = [
        (r"\b(login|password|authentication|auth|sso|mfa)\b", "auth"),
        (r"\b(security|vulnerability|permission|unauthorized)\b", "security"),
        (r"\b(upload|attachment|download|file)\b", "files"),
        (r"\b(search|index)\b", "search"),
        (r"\b(database|sql|postgres)\b", "database"),
        (r"\b(message|channel|chat|notification)\b", "messaging"),
        (r"\b(dashboard|report|reports|analytics)\b", "dashboard"),
        (r"\b(button|layout|display|screen|interface|frontend|page|ui)\b", "frontend"),
    ]

    area = "unknown"

    for pattern, detected_area in area_rules:
        if re.search(pattern, lower):
            area = detected_area
            break

    # Missing information and follow-up questions
    checks = [
        (
            "steps to reproduce",
            r"\b(steps to reproduce|reproduce|first click|then click)\b",
            "What steps reproduce this issue?"
        ),
        (
            "expected result",
            r"\b(expected|should happen|supposed to)\b",
            "What did you expect to happen?"
        ),
        (
            "actual result",
            r"\b(actual|instead|but it|happens when)\b",
            "What happened instead?"
        ),
        (
            "app version",
            r"\b(version|build|v\d+\.\d+)\b",
            "Which app version are you using?"
        ),
        (
            "platform",
            r"\b(mac|macos|windows|linux|android|ios|browser|desktop)\b",
            "Which device, operating system, or browser are you using?"
        ),
        (
            "frequency",
            r"\b(always|every time|sometimes|occasionally|once|intermittent)\b",
            "Does this happen every time or only sometimes?"
        ),
        (
            "logs or error details",
            r"\b(logs?|stack trace|error message|screenshot)\b",
            "Can you share the relevant error message or logs?"
        ),
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
        if not re.search(
            r"\b(problem|pain point|would help|so that)\b", lower
        ):
            missing.append("problem or use case")
            questions.append("What problem would this feature solve?")

        if not re.search(
            r"\b(users?|team|customers?|developers?)\b", lower
        ):
            missing.append("who would benefit")
            questions.append("Who would benefit from this feature?")

        if not re.search(
            r"\b(success|acceptance|so that|able to)\b", lower
        ):
            missing.append("success criteria")
            questions.append("What would a successful version look like?")

    else:
        if not re.search(
            r"\b(tried|attempted|checked|searched|looked)\b", lower
        ):
            missing.append("what has already been tried")
            questions.append("What have you already tried?")

        if not re.search(
            r"\b(want to|need to|goal|hoping|so that)\b", lower
        ):
            missing.append("desired outcome")
            questions.append("What outcome are you hoping for?")

    # Suggested role based on area
    area_roles = {
        "auth": "Identity & Access engineer",
        "security": "Security engineer",
        "files": "Files & Storage engineer",
        "search": "Search engineer",
        "database": "Database engineer",
        "messaging": "Messaging engineer",
        "dashboard": "Frontend engineer",
        "frontend": "Frontend engineer",
    }

    suggested_role = area_roles.get(area, "Developer")

    if category == "QUESTION":
        suggested_role = "Support engineer"
    elif category == "FEATURE REQUEST":
        suggested_role = "Product manager"

    next_action = (
        "Human approval required: review the report and approve the "
        "suggested investigation before assigning or changing anything."
    )

    return {
        "summary": summary,
        "category": category,
        "priority": priority,
        "priority_explanation": explanation,
        "area": area,
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
    print("Area:", result["area"])
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
