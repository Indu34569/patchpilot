
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from app import triage

BASE_URL = "http://localhost:57801/api/v4"
TEAM_NAME = "switch"
CHANNEL_NAME = "patchpilot"
POLL_INTERVAL = 3


def api_request(path, method="GET", data=None):
    token = os.environ.get("MATTERMOST_TOKEN")
    if not token:
        raise RuntimeError("MATTERMOST_TOKEN is missing.")

    body = json.dumps(data).encode("utf-8") if data is not None else None

    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        result = response.read()
        return json.loads(result.decode("utf-8")) if result else {}


def format_reply(result):
    missing = result.get("missing_information", [])
    questions = result.get("follow_up_questions", [])

    return (
        f"### PatchPilot Triage\n\n"
        f"**Summary:** {result.get('summary', 'Not available')}\n\n"
        f"**Category:** {result.get('category', 'Not classified')}\n\n"
        f"**Priority:** {result.get('priority', 'Not assessed')}\n\n"
        f"**Why:** {result.get('priority_explanation', 'Not available')}\n\n"
        f"**Area:** {result.get('area', 'unknown')}\n\n"
        f"**Suggested role:** {result.get('suggested_role', 'Not available')}\n\n"
        f"**Next action:** {result.get('next_action', 'Review report')}\n\n"
        f"**Missing information:**\n"
        + (
            "\n".join(f"- {item}" for item in missing)
            if missing else "- None identified"
        )
        + "\n\n**Follow-up questions:**\n"
        + (
            "\n".join(f"- {item}" for item in questions)
            if questions else "- No follow-up questions needed"
        )
        + "\n\n_Human review required. No external actions were taken._"
    )


def main():
    print("Connecting to Mattermost...")

    me = api_request("/users/me")
    bot_id = me["id"]

    team = urllib.parse.quote(TEAM_NAME, safe="")
    channel_name = urllib.parse.quote(CHANNEL_NAME, safe="")

    channel = api_request(
        f"/teams/name/{team}/channels/name/{channel_name}"
    )
    channel_id = channel["id"]

    print(f"Authenticated as: {me.get('username', 'PatchPilot')}")
    print(f"Channel found: {channel.get('display_name', CHANNEL_NAME)}")
    print("PatchPilot Mattermost bridge connected.")
    print("Watching #PatchPilot. Press Ctrl+C to stop.")

    # Remember every message already handled during this run.
    processed_post_ids = set()

    # Start from now; don't process old channel messages.
    last_check = int(time.time() * 1000)

    while True:
        try:
            data = api_request(
                f"/channels/{channel_id}/posts?since={last_check}"
            )

            posts = data.get("posts", {})
            order = data.get("order", [])

            new_posts = [
                posts[post_id]
                for post_id in order
                if post_id in posts
            ]

            new_posts.sort(
                key=lambda post: post.get("create_at", 0)
            )

            for post in new_posts:
                post_id = post.get("id")

                # Critical duplicate protection.
                if not post_id or post_id in processed_post_ids:
                    continue

                # Mark as processed BEFORE generating a reply.
                processed_post_ids.add(post_id)

                last_check = max(
                    last_check,
                    post.get("create_at", 0)
                )

                # Never reply to the bot's own messages.
                if post.get("user_id") == bot_id:
                    continue

                message = post.get("message", "").strip()
                if not message:
                    continue

                print(f"\nNew message: {message[:120]}")

                result = triage(message)
                reply = format_reply(result)

                api_request(
                    "/posts",
                    method="POST",
                    data={
                        "channel_id": channel_id,
                        "message": reply,
                        "root_id": post.get("root_id") or post_id,
                    },
                )

                print("Triage reply posted once.")

        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            print(f"Mattermost API error ({error.code}): {details[:500]}")

        except urllib.error.URLError as error:
            print(f"Cannot reach Mattermost: {error.reason}")

        except Exception as error:
            print(f"Bridge error: {error}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPatchPilot bridge stopped.")
    except Exception as error:
        print(f"\nCould not start PatchPilot: {error}")
