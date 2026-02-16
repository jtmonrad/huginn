"""
Newsletter Generator & Sender
==============================
Generates a newsletter using Claude and sends it via Resend.

Usage (called automatically by GitHub Actions):
    python newsletter.py <newsletter-id>

Example:
    python newsletter.py biosecurity
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
import resend

# Directory containing newsletter config files
NEWSLETTERS_DIR = Path(__file__).parent / "newsletters"

# Mapping of timezone names to ZoneInfo objects
TIMEZONE_MAP = {
    "US/Eastern": "US/Eastern",
    "US/Central": "US/Central",
    "US/Mountain": "US/Mountain",
    "US/Pacific": "US/Pacific",
    "Europe/London": "Europe/London",
    "Europe/Berlin": "Europe/Berlin",
    "Asia/Tokyo": "Asia/Tokyo",
    "UTC": "UTC",
}


def load_config(newsletter_id):
    """Load a newsletter's JSON config file."""
    config_path = NEWSLETTERS_DIR / f"{newsletter_id}.json"
    if not config_path.exists():
        print(f"Error: Newsletter '{newsletter_id}' not found.")
        print(f"Expected config at: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        return json.load(f)


def get_local_now(tz_name):
    """Get the current datetime in the given timezone."""
    tz_key = TIMEZONE_MAP.get(tz_name, "UTC")
    try:
        tz = ZoneInfo(tz_key)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def generate_newsletter(config):
    """
    Call Claude with web search enabled to generate the newsletter.
    Claude will automatically search the web for current information,
    then write the newsletter based on what it finds.
    """
    client = anthropic.Anthropic()

    tz_name = config.get("schedule", {}).get("timezone", "US/Eastern")
    now = get_local_now(tz_name)
    today = now.strftime("%B %d, %Y")

    print(f"Calling Claude ({config['model']}) with web search...")

    prompt = (
        f"Today's date is {today}.\n\n"
        f"{config['prompt'].strip()}\n\n"
        "Use web search to find real, current developments and news. "
        "Output ONLY the newsletter content — no preamble or commentary "
        "about your search process."
    )

    messages = [{"role": "user", "content": prompt}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}]

    # Claude may pause during long search sequences — keep going until done
    all_content = []
    total_searches = 0

    while True:
        response = client.messages.create(
            model=config["model"],
            max_tokens=4000,
            tools=tools,
            messages=messages,
        )

        all_content.extend(response.content)

        # Count searches in this response
        usage = getattr(response.usage, "server_tool_use", None)
        if usage:
            count = (
                usage.get("web_search_requests", 0)
                if isinstance(usage, dict)
                else getattr(usage, "web_search_requests", 0)
            )
            total_searches += count

        # If Claude paused mid-turn (long search), continue
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": "Please continue."})
            print(f"  Searching... ({total_searches} searches so far)")
        else:
            break

    # Extract only the text blocks (skip search query/result blocks)
    text_parts = [block.text for block in all_content if hasattr(block, "text")]
    newsletter_text = "\n".join(text_parts)

    print(f"Generated ({len(newsletter_text)} chars, {total_searches} web searches)")
    return newsletter_text


def format_as_html(text, config):
    """Convert the newsletter text into a styled HTML email."""
    lines = text.split("\n")
    html_lines = []

    for line in lines:
        s = line.strip()
        if not s:
            html_lines.append("")
            continue

        # Markdown conversions
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
        s = re.sub(
            r"\[(.+?)\]\((.+?)\)",
            r'<a href="\2" style="color: #1a5276;">\1</a>',
            s,
        )

        if s.startswith("### "):
            html_lines.append(
                f'<h3 style="color: #2c3e50; margin-top: 20px; margin-bottom: 8px; font-size: 16px;">{s[4:]}</h3>'
            )
        elif s.startswith("## "):
            html_lines.append(
                f'<h2 style="color: #2c3e50; margin-top: 24px; margin-bottom: 10px; font-size: 18px; border-bottom: 1px solid #eee; padding-bottom: 6px;">{s[3:]}</h2>'
            )
        elif s.startswith("# "):
            html_lines.append(
                f'<h1 style="color: #1a5276; margin-top: 0; margin-bottom: 16px; font-size: 22px;">{s[2:]}</h1>'
            )
        elif s.startswith("- ") or s.startswith("* "):
            html_lines.append(
                f'<li style="margin-bottom: 6px; line-height: 1.6;">{s[2:]}</li>'
            )
        elif re.match(r"^\d+\.\s", s):
            item_text = re.sub(r"^\d+\.\s", "", s)
            html_lines.append(
                f'<li style="margin-bottom: 6px; line-height: 1.6;">{item_text}</li>'
            )
        else:
            html_lines.append(
                f'<p style="margin: 0 0 12px 0; line-height: 1.6;">{s}</p>'
            )

    body = "\n".join(html_lines)

    tz_name = config.get("schedule", {}).get("timezone", "US/Eastern")
    now = get_local_now(tz_name)
    date_display = now.strftime("%B %d, %Y")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:Georgia,'Times New Roman',serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f5f5;padding:20px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:4px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
<tr><td style="background-color:#1a5276;padding:28px 32px;text-align:center;">
<h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:normal;letter-spacing:0.5px;">{config['name']}</h1>
<p style="color:#aed6f1;margin:8px 0 0 0;font-size:14px;">{date_display}</p>
</td></tr>
<tr><td style="padding:32px;color:#333333;font-size:15px;">{body}</td></tr>
<tr><td style="background-color:#f8f9fa;padding:20px 32px;text-align:center;border-top:1px solid #eee;">
<p style="color:#999999;font-size:12px;margin:0;">Generated by Claude &middot; Sent via Resend</p>
</td></tr>
</table>
</td></tr>
</table>
</body></html>"""


def send_email(html, config):
    """Send the newsletter via Resend."""
    resend.api_key = os.environ["RESEND_API_KEY"]

    tz_name = config.get("schedule", {}).get("timezone", "US/Eastern")
    now = get_local_now(tz_name)
    date_short = now.strftime("%b %d, %Y")
    subject = config["subject_template"].format(date=date_short)

    print(f"Sending to {config['recipient_email']}...")

    result = resend.Emails.send(
        {
            "from": config["sender_email"],
            "to": [config["recipient_email"]],
            "subject": subject,
            "html": html,
        }
    )

    print(f"Sent! Resend ID: {result['id']}")
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python newsletter.py <newsletter-id>")
        print("Example: python newsletter.py biosecurity")
        sys.exit(1)

    newsletter_id = sys.argv[1]
    print(f"{'=' * 50}")
    print(f"NEWSLETTER: {newsletter_id}")
    print(f"{'=' * 50}")

    # Load config
    config = load_config(newsletter_id)
    print(f"Loaded: {config['name']}")

    # Generate content
    try:
        text = generate_newsletter(config)
    except anthropic.AuthenticationError:
        print("\nERROR: Invalid Anthropic API key.")
        print("Check your ANTHROPIC_API_KEY secret in GitHub Settings.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR generating newsletter: {e}")
        sys.exit(1)

    # Format as HTML email
    html = format_as_html(text, config)
    print("HTML formatted")

    # Send
    try:
        send_email(html, config)
    except KeyError:
        print("\nERROR: RESEND_API_KEY not set.")
        print("Check your RESEND_API_KEY secret in GitHub Settings.")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR sending email: {e}")
        sys.exit(1)

    print("\nDone! Check your inbox.")


if __name__ == "__main__":
    main()
