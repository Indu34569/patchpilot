"""PatchPilot - a small, local bug-triage assistant.

This prototype uses transparent keyword rules and only the Python standard
library. It never performs an action automatically: every next action is
returned with ``requires_human_approval=True``.
"""

from __future__ import annotations

import re

BUG = "BUG"
QUESTION = "QUESTION"
FEATURE_REQUEST = "FEATURE REQUEST"

CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _compile_rules(
    rows: tuple[tuple[str, int, str], ...],
) -> tuple[tuple[re.Pattern[str], int, str], ...]:
    return tuple(
        (re.compile(pattern, re.IGNORECASE), weight, label)
        for pattern, weight, label in rows
    )


def _match_rules(
    text: str,
    rules: tuple[tuple[re.Pattern[str], int, str], ...],
) -> list[tuple[str, str, int]]:
    """Return (label, matched text, weight) for each distinct matching rule."""

    matches: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    for pattern, weight, label in rules:
        match = pattern.search(text)
        if match and label not in seen:
            seen.add(label)
            evidence = " ".join(match.group(0).split())
            matches.append((label, evidence, weight))
    return matches


def _normalise(text: str) -> str:
    return (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )


def _one_sentence_summary(text: str) -> str:
    """Build a short summary that contains exactly one sentence."""

    text = " ".join(text.split())
    if not text:
        return "No report text was provided."

    sentences = re.split(r"(?<=[.!?])\s+", text)
    parts: list[str] = []
    for sentence in sentences[:2]:
        part = sentence.strip().rstrip(".!?")
        if part:
            parts.append(part)
        if len("; ".join(parts)) >= 80:
            break

    summary = "; ".join(parts).strip(" ;,.")
    if len(summary) > 160:
        summary = summary[:157].rsplit(" ", 1)[0].rstrip(" ;,.")
    if not summary:
        summary = "Report text could not be summarised"
    return summary + "."


# ---------------------------------------------------------------------------
# Category rules
# ---------------------------------------------------------------------------

FEATURE_RULES = _compile_rules(
    (
        (r"\bfeature request\b", 4, "explicitly called a feature request"),
        (
            r"\b(?:please add|add support for|could we have|can we have|can you add)\b",
            3,
            "asks for new functionality",
        ),
        (
            r"\b(?:would be (?:nice|great|helpful)|it would be (?:nice|great|helpful))\b",
            3,
            "describes a desired improvement",
        ),
        (r"\b(?:enhancement|suggestion)\b", 2, "enhancement or suggestion wording"),
    )
)

QUESTION_RULES = _compile_rules(
    (
        (
            r"^\s*(?:how|why|what|where|when|who|which|can|could|should|is|are|do|does|did)\s+",
            2,
            "starts with a question word",
        ),
        (
            r"\b(?:how do i|how can i|is there a way|where can i|what is the best way|can you help)\b",
            3,
            "asks for guidance",
        ),
        (r"\?", 1, "includes a question mark"),
    )
)

BUG_RULES = _compile_rules(
    (
        (
            r"\b(?:crash(?:es|ed|ing)?|traceback|segfault|panic(?:s|ked)?)\b",
            4,
            "crash or traceback",
        ),
        (
            r"\b(?:outage|production (?:is )?down|service unavailable|nobody can|"
            r"all users|data loss|lost data|messages? disappeared|corrupt(?:ed|ion)?)\b",
            4,
            "outage or data loss",
        ),
        (
            r"\b(?:security vulnerability|vulnerability|exploit|CVE-\d+|data breach|"
            r"breached|compromised|XSS|cross-site scripting|SQL injection|CSRF|RCE|"
            r"remote code execution|privilege escalation|auth(?:entication|orization)? bypass)\b",
            4,
            "security vulnerability",
        ),
        (
            r"\b(?:regression|used to work|worked before|since (?:the )?(?:last |latest )?(?:update|upgrade))\b",
            3,
            "regression",
        ),
        (
            r"\b(?:error|exception|fail(?:s|ed|ing|ure)?|broken)\b",
            3,
            "error or failure",
        ),
        (
            r"\b(?:can'?t|cannot|unable to|not working|doesn'?t work|locked out|"
            r"won'?t (?:start|open|load|send))\b",
            3,
            "blocked action",
        ),
        (
            r"\b(?:bug|defect|glitch|incorrect|wrong|missing|unexpected)\b",
            2,
            "incorrect behavior",
        ),
        (
            r"\b(?:slow|lag(?:gy|ging)?|delayed?|timeout|timed out)\b",
            2,
            "performance issue",
        ),
        (
            r"\b(?:typo|misspell(?:ed|ing)?|cosmetic)\b",
            2,
            "low-impact defect",
        ),
        (r"\b(?:403|404|413|500|502|503|504)\b", 2, "HTTP error code"),
    )
)

# A real defect signal should beat a question-shaped title, but a feature
# request that merely mentions a word like "error" should still be a feature.
DEFECT_HINT = re.compile(
    r"\b(?:crash(?:es|ed|ing)?|traceback|segfault|panic(?:s|ked)?|error|exception|"
    r"fail(?:s|ed|ing|ure)?|broken|regression|bug|defect|glitch|typo|misspell(?:ed|ing)?|"
    r"incorrect|wrong|missing|outage|down|data loss|corrupt(?:ed|ion)?|not working|"
    r"security vulnerability|vulnerability|exploit|locked out)\b|"
    r"\b(?:can'?t|cannot|unable to)\s+(?:log ?in|sign ?in)\b",
    re.IGNORECASE,
)

STRONG_BUG_HINT = re.compile(
    r"\b(?:crash(?:es|ed|ing)?|traceback|segfault|outage|production (?:is )?down|"
    r"data loss|lost data|messages? disappeared|security vulnerability|vulnerability|"
    r"exploit|data breach|compromised|corrupt(?:ed|ion)?|regression|broken|not working|"
    r"locked out)\b|"
    r"\b(?:can'?t|cannot|unable to)\s+(?:log ?in|sign ?in)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Priority rules
# ---------------------------------------------------------------------------

CRITICAL_RULES = _compile_rules(
    (
        (
            r"\b(?:security vulnerability|vulnerability|exploit|CVE-\d+|data breach|"
            r"breached|compromised|XSS|cross-site scripting|SQL injection|CSRF|RCE|"
            r"remote code execution|privilege escalation|auth(?:entication|orization)? bypass)\b",
            1,
            "security vulnerability",
        ),
        (
            r"\b(?:leaked?|exposed?)\s+(?:tokens?|secrets?|credentials?|passwords?)\b",
            1,
            "leaked credentials",
        ),
        (
            r"\b(?:data loss|lost data|deleted data|wiped data|messages? disappeared|"
            r"files? (?:are )?gone|data (?:is )?gone|corrupt(?:ed|ion)?)\b",
            1,
            "data loss or corruption",
        ),
        (
            r"\b(?:outage|production (?:is )?down|service (?:is )?(?:down|unavailable)|"
            r"server (?:is )?down|nobody can|total (?:outage|failure))\b",
            1,
            "service outage",
        ),
        (
            r"\b(?:all users|all customers|every user|everyone|whole team)\b",
            1,
            "all-user impact",
        ),
        (r"\b(?:p0|sev(?:erity)?\s*1)\b", 1, "marked P0/SEV-1"),
    )
)

HIGH_RULES = _compile_rules(
    (
        (
            r"\b(?:can'?t|cannot|unable to)\s+(?:log ?in|sign ?in)\b|"
            r"\blogin\s+(?:fails?|failed|broken|error|issue|problem)\b|"
            r"\blocked out\b|"
            r"\bsign[- ]?in\s+(?:fails?|failed|broken)\b",
            1,
            "login failure",
        ),
        (
            r"\b(?:crash(?:es|ed|ing)?|traceback|segfault|panic(?:s|ked)?)\b",
            1,
            "crash",
        ),
        (
            r"\b(?:regression|used to work|worked before|since (?:the )?(?:last |latest )?(?:update|upgrade))\b",
            1,
            "regression",
        ),
        (
            r"\b(?:cannot|can'?t|unable to|blocked|blocker|locked out)\b",
            1,
            "blocked workflow",
        ),
        (
            r"\b(?:every time|consistently|always|100%)\b",
            1,
            "consistent failure",
        ),
        (r"\b(?:500|502|503|504)\b", 1, "server error"),
        (
            r"\b(?:not working|broken|won'?t start|fails to start)\b",
            1,
            "broken feature",
        ),
    )
)

MEDIUM_RULES = _compile_rules(
    (
        (
            r"\b(?:error|exception|fail(?:s|ed|ing|ure)?)\b",
            1,
            "error or failure",
        ),
        (
            r"\b(?:slow|slowly|lag(?:gy|ging)?|delayed?|late|timeout|timed out)\b",
            1,
            "slow or delayed behavior",
        ),
        (
            r"\b(?:missing|incorrect|wrong|unexpected)\b",
            1,
            "incorrect result",
        ),
        (
            r"\b(?:sometimes|intermittent|occasionally|randomly)\b",
            1,
            "intermittent behavior",
        ),
        (r"\b(?:403|404|413)\b", 1, "client-side error"),
        (r"\b(?:bug|defect|glitch)\b", 1, "reported as a bug"),
    )
)

LOW_RULES = _compile_rules(
    (
        (r"\b(?:typo|misspell(?:ed|ing)?|spelling)\b", 1, "typo"),
        (
            r"\b(?:cosmetic|minor|nit|alignment|padding|font|colou?r)\b",
            1,
            "cosmetic issue",
        ),
        (r"\b(?:docs?|documentation|readme)\b", 1, "documentation issue"),
    )
)


# ---------------------------------------------------------------------------
# Missing information, area, and role rules
# ---------------------------------------------------------------------------

BUG_INFO_CHECKS = (
    (
        "app version/build",
        re.compile(r"\b(?:v?\d+\.\d+(?:\.\d+)?|version|build(?: number)?)\b", re.IGNORECASE),
        "Which app version and build are you using?",
    ),
    (
        "platform",
        re.compile(
            r"\b(?:ios|android|iphone|ipad|windows|macos|mac os|linux|desktop app|"
            r"web app|browser|chrome|firefox|safari|edge)\b",
            re.IGNORECASE,
        ),
        "Which platform are you using (web, desktop, iOS, Android), and which version?",
    ),
    (
        "steps to reproduce",
        re.compile(
            r"\b(?:steps to reproduce|to reproduce|reproduce|when i|after i|then i)\b"
            r"|(?:^|\n)\s*\d+[.)]\s",
            re.IGNORECASE,
        ),
        "What are the exact steps to reproduce the issue?",
    ),
    (
        "expected vs actual behavior",
        re.compile(
            r"\b(?:expected|actual|instead of|should (?:be|show|say|return|work))\b",
            re.IGNORECASE,
        ),
        "What did you expect to happen, and what happened instead?",
    ),
    (
        "logs or screenshots",
        re.compile(
            r"\b(?:logs?|traceback|stack trace|error message|screenshot|screen shot|console)\b",
            re.IGNORECASE,
        ),
        "Can you share the relevant logs, error text, or a screenshot?",
    ),
    (
        "frequency",
        re.compile(
            r"\b(?:every time|always|sometimes|intermittent|occasionally|once|randomly|"
            r"consistently|all the time|\d+\s*(?:times|attempts))\b",
            re.IGNORECASE,
        ),
        "How often does this happen: every time, sometimes, or only once?",
    ),
)

FEATURE_INFO_CHECKS = (
    (
        "problem or use case",
        re.compile(
            r"\b(?:problem|need|use case|because|so that|pain point)\b",
            re.IGNORECASE,
        ),
        "What problem would this feature solve for your team?",
    ),
    (
        "who would benefit",
        re.compile(
            r"\b(?:team|teams|users?|customers?|admins?|developers?|everyone|community)\b",
            re.IGNORECASE,
        ),
        "Who would use this feature most?",
    ),
    (
        "success criteria",
        re.compile(
            r"\b(?:success|acceptance|would let|able to|so that)\b",
            re.IGNORECASE,
        ),
        "What would a successful version of this feature look like?",
    ),
)

QUESTION_INFO_CHECKS = (
    (
        "what has already been tried",
        re.compile(r"\b(?:tried|attempted|checked|looked|searched)\b", re.IGNORECASE),
        "What have you already tried?",
    ),
    (
        "desired outcome",
        re.compile(
            r"\b(?:so that|in order to|want to|need to|goal|hoping)\b",
            re.IGNORECASE,
        ),
        "What outcome are you hoping for?",
    ),
)

AREAS = (
    (
        re.compile(
            r"\b(?:auth(?:entication|orization)?|login|log in|sign in|signin|password|"
            r"passcode|sso|saml|oauth|mfa|2fa|session|access token|refresh token)\b",
            re.IGNORECASE,
        ),
        "auth",
        "Identity & Access engineer",
    ),
    (
        re.compile(
            r"\b(?:search|searching|index|indexing|elasticsearch|query results?)\b",
            re.IGNORECASE,
        ),
        "search",
        "Search engineer",
    ),
    (
        re.compile(
            r"\b(?:upload|uploads|attachment|attachments|file|files|image|download|"
            r"storage|s3|413)\b",
            re.IGNORECASE,
        ),
        "uploads",
        "Files & Storage engineer",
    ),
    (
        re.compile(
            r"\b(?:notification|notifications|email|e-mail|push|unread|badge|alert)\b",
            re.IGNORECASE,
        ),
        "notifications",
        "Notifications engineer",
    ),
    (
        re.compile(
            r"\b(?:permission|permissions|role|roles|admin|guest|access denied|"
            r"private channel|403|forbidden)\b",
            re.IGNORECASE,
        ),
        "permissions",
        "Platform security engineer",
    ),
    (
        re.compile(
            r"\b(?:call|calls|voice|video|screen ?share|webrtc|microphone|camera)\b",
            re.IGNORECASE,
        ),
        "calls",
        "Calls engineer",
    ),
    (
        re.compile(
            r"\b(?:webhook|slash command|plugin|bot|api|integration|oauth app)\b",
            re.IGNORECASE,
        ),
        "integrations",
        "Integrations engineer",
    ),
    (
        re.compile(
            r"\b(?:database|db|migration|postgres|postgresql|mysql|sql|query)\b",
            re.IGNORECASE,
        ),
        "database",
        "Database engineer",
    ),
    (
        re.compile(r"\b(?:ios|android|iphone|ipad|mobile app)\b", re.IGNORECASE),
        "mobile",
        "Mobile engineer",
    ),
    (
        re.compile(
            r"\b(?:desktop|electron|system tray|tray|windows|macos|mac os|linux)\b",
            re.IGNORECASE,
        ),
        "desktop",
        "Desktop client engineer",
    ),
    (
        re.compile(
            r"\b(?:slow|slowness|lag|latency|timeout|timed out|memory|cpu)\b",
            re.IGNORECASE,
        ),
        "performance",
        "Backend performance engineer",
    ),
    (
        re.compile(
            r"\b(?:button|layout|theme|dark mode|light mode|css|render|rendering|"
            r"modal|header|font|icon|alignment|padding|colou?r)\b",
            re.IGNORECASE,
        ),
        "ui",
        "Frontend/Design engineer",
    ),
    (
        re.compile(
            r"\b(?:message|messages|post|posts|channel|channels|dm|direct message|"
            r"thread|reply|mention|reaction|emoji)\b",
            re.IGNORECASE,
        ),
        "messaging",
        "Messaging engineer",
    ),
)


# ---------------------------------------------------------------------------
# Classification and priority
# ---------------------------------------------------------------------------


def _classify(text: str) -> tuple[str, list[tuple[str, str, int]]]:
    feature_matches = _match_rules(text, FEATURE_RULES)
    question_matches = _match_rules(text, QUESTION_RULES)
    bug_matches = _match_rules(text, BUG_RULES)

    feature_score = sum(weight for _, _, weight in feature_matches)
    question_score = sum(weight for _, _, weight in question_matches)
    bug_score = sum(weight for _, _, weight in bug_matches)

    if feature_score >= 2 and not STRONG_BUG_HINT.search(text):
        return FEATURE_REQUEST, feature_matches
    if DEFECT_HINT.search(text) or (bug_score >= 2 and bug_score >= question_score):
        return BUG, bug_matches
    if question_score > 0:
        return QUESTION, question_matches
    if bug_score > 0:
        return BUG, bug_matches
    return QUESTION, []


def _priority(category: str, text: str) -> tuple[str, str]:
    if category != BUG:
        return (
            LOW,
            f"Priority {LOW} because this is a {category}, not a production bug report.",
        )

    critical_matches = _match_rules(text, CRITICAL_RULES)
    if critical_matches:
        details = ", ".join(
            f"{label} ('{evidence}')" for label, evidence, _ in critical_matches
        )
        return (
            CRITICAL,
            f"Priority {CRITICAL} because the report matches: {details}. "
            "Security, data-loss, and outage reports are treated as critical.",
        )

    high_matches = _match_rules(text, HIGH_RULES)
    if high_matches:
        details = ", ".join(
            f"{label} ('{evidence}')" for label, evidence, _ in high_matches
        )
        explanation = f"Priority {HIGH} because the report matches: {details}."
        if any(label == "login failure" for label, _, _ in high_matches):
            explanation += (
                " Login failures are HIGH by default; they become CRITICAL only "
                "when an outage or all-user impact is also reported."
            )
        return HIGH, explanation

    medium_matches = _match_rules(text, MEDIUM_RULES)
    if medium_matches:
        details = ", ".join(
            f"{label} ('{evidence}')" for label, evidence, _ in medium_matches
        )
        return (
            MEDIUM,
            f"Priority {MEDIUM} because the report matches: {details}. "
            "No critical or high-impact signals were found.",
        )

    low_matches = _match_rules(text, LOW_RULES)
    if low_matches:
        details = ", ".join(
            f"{label} ('{evidence}')" for label, evidence, _ in low_matches
        )
        return (
            LOW,
            f"Priority {LOW} because the report only matches low-impact signals: {details}.",
        )

    return (
        LOW,
        f"Priority {LOW} because no crash, outage, security, data-loss, "
        "blocked-workflow, or broad-impact signals were found.",
    )


# ---------------------------------------------------------------------------
# Missing information, area, and next action
# ---------------------------------------------------------------------------


def _missing_information(category: str, raw_text: str) -> tuple[list[str], list[str]]:
    if not raw_text.strip():
        return (
            ["report text"],
            ["What issue would you like PatchPilot to triage?"],
        )

    if category == BUG:
        checks = BUG_INFO_CHECKS
    elif category == FEATURE_REQUEST:
        checks = FEATURE_INFO_CHECKS
    else:
        checks = QUESTION_INFO_CHECKS

    missing = [
        label for label, pattern, _ in checks if not pattern.search(raw_text)
    ]
    questions = [
        question
        for _, pattern, question in checks
        if not pattern.search(raw_text)
    ]
    return missing, questions[:3]


def _infer_area(text: str) -> tuple[str, str, str]:
    for pattern, area, role in AREAS:
        match = pattern.search(text)
        if match:
            return area, role, " ".join(match.group(0).split())
    return "unknown", "On-call triage engineer", ""


def _category_reason(
    category: str,
    matches: list[tuple[str, str, int]],
) -> str:
    if matches:
        details = ", ".join(
            f"{label} ('{evidence}')" for label, evidence, _ in matches
        )
        return f"Category {category} because the report matches: {details}."
    return (
        f"Category {category} because no clear bug or feature signals were "
        "found; clarification is needed."
    )


def _suggested_role(category: str, area_role: str) -> str:
    if category == FEATURE_REQUEST:
        return "Product manager"
    if category == QUESTION:
        return "Support engineer"
    return area_role


def _next_action(category: str, priority: str, role: str) -> str:
    if category == FEATURE_REQUEST:
        return (
            "Human approval required: send this request to product review with "
            "a product manager; do not promise a delivery date."
        )
    if category == QUESTION:
        return (
            "Human approval required: route this question to a support engineer "
            "and reply with an answer or a clarification request."
        )
    if priority == CRITICAL:
        return (
            f"Human approval required: escalate to the {role} and open a P0 "
            "incident; confirm scope and user impact before changing production."
        )
    if priority == HIGH:
        return (
            f"Human approval required: ask the reporter for the missing details, "
            f"then assign the report to a {role} for reproduction and a fix estimate."
        )
    if priority == MEDIUM:
        return (
            f"Human approval required: queue the report for {role} triage and "
            "request the missing details before scheduling work."
        )
    return (
        f"Human approval required: add the report to the low-priority backlog "
        f"for {role} and batch it with related fixes."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def triage(issue: str) -> dict[str, object]:
    """Return a structured triage proposal for one report.

    The result is a plain dictionary so it is easy to print, inspect, or send
    to a future integration. No action is taken automatically.
    """

    if issue is None:
        issue = ""
    if not isinstance(issue, str):
        issue = str(issue)

    raw_text = _normalise(issue).strip()
    text = " ".join(raw_text.split())

    if not text:
        category = QUESTION
        category_matches: list[tuple[str, str, int]] = []
        priority = LOW
        priority_explanation = (
            f"Priority {LOW} because no report text was provided; there is "
            "nothing to rate as a production bug."
        )
        area = "unknown"
        area_role = "On-call triage engineer"
        area_evidence = ""
        missing_information = ["report text"]
        follow_up_questions = ["What issue would you like PatchPilot to triage?"]
        summary = "No report text was provided."
    else:
        category, category_matches = _classify(text)
        priority, priority_explanation = _priority(category, text)
        area, area_role, area_evidence = _infer_area(text)
        missing_information, follow_up_questions = _missing_information(
            category, raw_text
        )
        summary = _one_sentence_summary(text)

    suggested_role = _suggested_role(category, area_role)
    next_action = _next_action(category, priority, suggested_role)

    reasons = [
        _category_reason(category, category_matches),
        priority_explanation,
    ]
    if area_evidence:
        reasons.append(f"Area {area} inferred from '{area_evidence}'.")
    else:
        reasons.append("No area keyword matched; route to the on-call triage engineer.")

    return {
        "summary": summary,
        "category": category,
        "priority": priority,
        "priority_explanation": priority_explanation,
        "reasons": reasons,
        "missing_information": missing_information,
        "follow_up_questions": follow_up_questions[:3],
        "suggested_role": suggested_role,
        "area": area,
        "next_action": next_action,
        "requires_human_approval": True,
        "approval_status": "PENDING",
    }


# ---------------------------------------------------------------------------
# Interactive demo
# ---------------------------------------------------------------------------


def print_result(result: dict[str, object]) -> None:
    print("\n--- PATCHPILOT TRIAGE ---")
    print("Summary:", result["summary"])
    print("Category:", result["category"])
    print("Priority:", result["priority"])
    print("Priority explanation:", result["priority_explanation"])
    print("Area:", result["area"])
    print("Reasons:")
    for reason in result["reasons"]:  # type: ignore[union-attr]
        print("  -", reason)

    print("Missing information:")
    missing = result["missing_information"]  # type: ignore[assignment]
    if missing:
        for item in missing:
            print("  -", item)
    else:
        print("  - none")

    print("Follow-up questions:")
    questions = result["follow_up_questions"]  # type: ignore[assignment]
    if questions:
        for number, question in enumerate(questions, start=1):
            print(f"  {number}. {question}")
    else:
        print("  - none")

    print("Suggested team role:", result["suggested_role"])
    print("Next action:", result["next_action"])
    print("Requires human approval:", "yes" if result["requires_human_approval"] else "no")
    print("Approval status:", result["approval_status"])
    print("-------------------------")


def main() -> None:
    print("PatchPilot - local bug triage (standard library only)")
    print("No data leaves this machine.")
    try:
        issue = input("\nDescribe a bug, question, or feature request: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nNo input received. Exiting.")
        return

    if not issue:
        print("No issue entered. Nothing to triage.")
        return

    print_result(triage(issue))


if __name__ == "__main__":
    main()
