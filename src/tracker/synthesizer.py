"""Digest synthesizer for AI Regulation Tracker."""

from __future__ import annotations

import os
from datetime import date
from tracker.sources import RegulatoryItem


ENGINEERING_IMPLICATIONS = [
    "Review your model risk management documentation against current SR 11-7 expectations. Examiners are asking for it.",
    "If you are deploying AI in consumer-facing decisioning, ensure adverse action notices can reference specific model factors.",
    "Any AI system making consequential decisions in a regulated context should have a complete decision record for replay. This is becoming table stakes.",
    "The window to build governance infrastructure before it is required by examination is closing. Start with the model registry.",
    "Machine-readable compliance controls are the prerequisite for autonomous SDLC. Every narrative control is a deployment blocker.",
    "The four actors who will demand AI decision records -- regulator, plaintiff attorney, board, acquirer -- are all becoming more sophisticated.",
    "Compliance teams are now asking engineering teams for replay capability. If you cannot answer that question, build the answer before the examination.",
]


def generate_digest(
    current: list[RegulatoryItem],
    horizon: list[RegulatoryItem],
    api_key: str,
    issue_number: int,
) -> str:
    """Generate the daily regulatory digest."""
    today = date.today()

    if api_key and (current or horizon):
        return _llm_digest(current, horizon, api_key, issue_number, today)
    return _template_digest(current, horizon, issue_number, today)


def _llm_digest(
    current: list[RegulatoryItem],
    horizon: list[RegulatoryItem],
    api_key: str,
    issue_number: int,
    today: date,
) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        current_text = "\n".join(
            f"- [{i.agency}] {i.title}: {i.summary[:200]}"
            for i in current
        ) or "No new AI-relevant regulatory developments today."

        horizon_text = "\n".join(
            f"- [{i.agency}] {i.title}"
            for i in horizon
        ) or "No upcoming deadlines or proposed rules identified."

        prompt = f"""You are writing the AI Regulation Tracker digest #{issue_number} for {today.strftime('%B %d, %Y')}.

Your audience: CTOs, CISOs, and engineering leaders in regulated financial services who need to understand AI regulatory developments and their engineering implications.

Your voice: direct, technically credible, executive-ready. No fluff. Connect regulatory developments to concrete engineering actions.

New regulatory developments:
{current_text}

Upcoming / horizon items:
{horizon_text}

Write a digest with this exact structure:

## AI Regulation Tracker -- {today.strftime('%B %d, %Y')} -- Issue #{issue_number}

### New This Week
[For each development: agency, what happened, why it matters for engineering teams in regulated industries. 1-2 sentences each. If no new items, say so honestly.]

### On the Horizon
[Upcoming comment deadlines, effective dates, proposed rules. If none, say so.]

### Engineering Implication
[One specific, actionable sentence for engineering leaders. Not generic advice. Specific to this week's developments.]

---
*AI Regulation Tracker monitors OCC, Federal Reserve, CFPB, FDIC, SEC, FCA, ECB, and EU AI Act developments nightly. Follow this repo to receive daily updates. Published by [Brian Pelow](https://github.com/brianpelow).*"""

        response = client.chat.completions.create(
            model="qwen/qwen3-8b:free",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"transforms": ["middle-out"]},
        )
        content = response.choices[0].message.content or ""
        content = content.replace("<think>", "").replace("</think>", "").strip()
        # Remove any thinking blocks
        import re
        content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
        return content if content else _template_digest(current, horizon, issue_number, today)
    except Exception as e:
        print(f"[synthesizer] LLM failed: {e}")
        return _template_digest(current, horizon, issue_number, today)


def _template_digest(
    current: list[RegulatoryItem],
    horizon: list[RegulatoryItem],
    issue_number: int,
    today: date,
) -> str:
    import random
    implication = ENGINEERING_IMPLICATIONS[issue_number % len(ENGINEERING_IMPLICATIONS)]

    lines = [
        f"## AI Regulation Tracker -- {today.strftime('%B %d, %Y')} -- Issue #{issue_number}",
        "",
        "### New This Week",
    ]

    if current:
        for item in current[:5]:
            lines.append(f"- **[{item.agency}]** [{item.title}]({item.url})")
    else:
        lines.append("No new AI-relevant regulatory developments identified today across monitored sources.")

    lines.extend(["", "### On the Horizon"])

    if horizon:
        for item in horizon[:3]:
            lines.append(f"- **[{item.agency}]** [{item.title}]({item.url})")
    else:
        lines.append("No upcoming comment deadlines or proposed rules identified this cycle.")

    lines.extend([
        "",
        "### Engineering Implication",
        implication,
        "",
        "---",
        f"*AI Regulation Tracker monitors OCC, Federal Reserve, CFPB, FDIC, SEC, FCA, ECB, and EU AI Act developments nightly. Follow this repo to receive daily updates. Published by [Brian Pelow](https://github.com/brianpelow).*",
    ])

    return "\n".join(lines)