# PatchPilot 🛠️

**An AI-assisted bug-triage teammate for Mattermost, with Switch collaboration.**

PatchPilot helps development teams turn bug reports into structured triage summaries, identify priority and affected areas, and collect missing information before a human makes a decision.

## What it does

- Classifies incoming reports as bugs, questions, or feature requests.
- Assigns a priority: Critical, High, Medium, or Low.
- Detects likely affected areas such as authentication, security, files, search, database, messaging, dashboard, and frontend.
- Suggests a responsible engineering role.
- Identifies missing information and asks follow-up questions.
- Provides a recommended next action.
- Requires human approval before any external changes.

## Demo architecture

1. A user posts a report in the Mattermost `#PatchPilot` channel.
2. The local Python Mattermost bridge detects the message.
3. PatchPilot's deterministic triage rules generate a structured response.
4. The conversation is visible through the Switch-connected Mattermost workspace.
5. A human reviews the recommendation.

**Important:** The current triage engine uses local Python rules. It does not depend on a paid AI API. The Switch room provides collaboration visibility; the separate Switch OpenCode agent workflow is still experimental.

## Tech stack

- Python
- Mattermost
- Switch
- Streamlit dashboard
- Local development environment

## Run locally

Clone the repository:

```bash
git clone https://github.com/Indu34569/patchpilot.git
cd patchpilot
```

Run the dashboard:

```bash
streamlit run web_app.py
```

Run the Mattermost bridge:

```bash
printf "Paste your Mattermost bot token (hidden): "
read -s MATTERMOST_TOKEN
echo
export MATTERMOST_TOKEN
python3 mattermost_bridge.py
```

Keep the bridge terminal open while testing.

The local Mattermost instance used during development is `http://localhost:57801`.

## Safety and human oversight

PatchPilot is designed as a human-in-the-loop assistant.

- It suggests; humans decide.
- It does not automatically assign or close issues.
- It does not modify external systems.
- It asks for missing details instead of assuming them.
- Bot credentials should be kept private and never committed to Git.

## Current status

- [x] Local triage engine
- [x] Streamlit dashboard
- [x] Mattermost bot and message replies
- [x] Switch-connected Mattermost conversation visibility
- [ ] Successful response from the separate Switch OpenCode agent workflow

## Built for Flip the Switch Hackathon 2026

WeMakeDevs × DevTools Academy — Switch AI

**Project:** PatchPilot