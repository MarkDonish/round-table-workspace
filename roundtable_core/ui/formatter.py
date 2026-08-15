from __future__ import annotations

import os
import sys
from typing import Any, Sequence


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright Foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_RED = "\033[41m"
    BG_BLUE = "\033[44m"


ROLE_ICONS: dict[str, str] = {
    "security-auditor": "🛡️ ",
    "security": "🛡️ ",
    "performance-specialist": "⚡",
    "performance": "⚡",
    "api-contract-reviewer": "🔌",
    "api": "🔌",
    "database-auditor": "🗄️ ",
    "db": "🗄️ ",
    "engineering": "📐",
    "engineer": "📐",
    "risk": "⚖️ ",
    "taleb": "⚖️ ",
    "munger": "🧠",
    "product": "💡",
    "jobs": "💡",
    "user-advocate": "👤",
    "feynman": "🔬",
    "musk": "🚀",
    "sun": "🔥",
    "pg": "🏛️ ",
    "geohot": "⚡",
    "dario-amodei": "🛡️ ",
    "dario": "🛡️ ",
    "martin-fowler": "📐",
    "fowler": "📐",
}


class TUIFormatter:
    def __init__(self, use_color: bool | None = None) -> None:
        if use_color is None:
            no_color = os.environ.get("NO_COLOR") is not None or os.environ.get("TERM") == "dumb"
            self.use_color = sys.stdout.isatty() and not no_color
        else:
            self.use_color = use_color

    def c(self, text: str, color_code: str) -> str:
        return f"{color_code}{text}{Colors.RESET}" if self.use_color else text

    def bold(self, text: str) -> str:
        return self.c(text, Colors.BOLD)

    def dim(self, text: str) -> str:
        return self.c(text, Colors.DIM)

    def format_ship_check(self, payload: dict[str, Any]) -> str:
        decision = str(payload.get("decision", "revise")).lower()
        confidence = str(payload.get("confidence", "medium"))
        question = str(payload.get("question", "Pre-merge code review"))
        panel_votes: list[dict[str, Any]] = payload.get("panel_votes", [])  # type: ignore
        categories = payload.get("categories", [])
        risks = payload.get("risks", [])
        next_actions = payload.get("next_actions", [])

        # Verdict badge styling
        if decision == "ship":
            badge_text = "  🟢  SHIP  "
            badge = self.c(self.c(badge_text, Colors.BOLD), Colors.BG_GREEN + Colors.BRIGHT_WHITE)
            dec_color = Colors.BRIGHT_GREEN
        elif decision == "reject":
            badge_text = "  🔴  REJECT  "
            badge = self.c(self.c(badge_text, Colors.BOLD), Colors.BG_RED + Colors.BRIGHT_WHITE)
            dec_color = Colors.BRIGHT_RED
        else:
            badge_text = "  🟡  REVISE  "
            badge = self.c(self.c(badge_text, Colors.BOLD), Colors.BG_YELLOW + Colors.BRIGHT_WHITE)
            dec_color = Colors.BRIGHT_YELLOW

        width = 66
        lines = [
            "",
            self.c("╭" + "─" * (width - 2) + "╮", Colors.CYAN),
            self.c("│", Colors.CYAN) + f"  {self.bold('ROUND TABLE WORKSPACE')} · Decision Review Gate".ljust(width + 8) + self.c("│", Colors.CYAN),
            self.c("│", Colors.CYAN) + f"  Verdict: {badge}  {self.c(f'[{decision.upper()}]', dec_color)} (confidence: {confidence})".ljust(width + 32) + self.c("│", Colors.CYAN),
            self.c("│", Colors.CYAN) + f"  Target:  {question[:50]}".ljust(width - 2) + self.c("│", Colors.CYAN),
            self.c("╰" + "─" * (width - 2) + "╯", Colors.CYAN),
            "",
        ]

        # Voting meter
        if panel_votes:
            ship_count = sum(1 for v in panel_votes if v.get("vote") == "ship")
            revise_count = sum(1 for v in panel_votes if v.get("vote") == "revise")
            reject_count = sum(1 for v in panel_votes if v.get("vote") == "reject")
            total = len(panel_votes)

            bar_len = 24
            ship_bars = int((ship_count / total) * bar_len)
            revise_bars = int((revise_count / total) * bar_len)
            reject_bars = bar_len - ship_bars - revise_bars

            meter_str = (
                self.c("█" * ship_bars, Colors.BRIGHT_GREEN)
                + self.c("█" * revise_bars, Colors.BRIGHT_YELLOW)
                + self.c("█" * reject_bars, Colors.BRIGHT_RED)
            )
            stats = f"{self.c(f'{ship_count} Ship', Colors.BRIGHT_GREEN)} · {self.c(f'{revise_count} Revise', Colors.BRIGHT_YELLOW)} · {self.c(f'{reject_count} Reject', Colors.BRIGHT_RED)}"
            lines.append(f"  {self.bold('Panel Votes')} [{meter_str}] ({stats})")
            lines.append("")

            # Panel Cards
            for pv in panel_votes:
                agent = str(pv.get("agent", "reviewer"))
                vote = str(pv.get("vote", "ship")).lower()
                reason = str(pv.get("reason", ""))
                icon = ROLE_ICONS.get(agent, "🔹")

                if vote == "ship":
                    vote_str = self.c("✅ SHIP  ", Colors.BRIGHT_GREEN)
                elif vote == "reject":
                    vote_str = self.c("❌ REJECT", Colors.BRIGHT_RED)
                else:
                    vote_str = self.c("⚠️ REVISE", Colors.BRIGHT_YELLOW)

                lines.append(f"  {icon} {self.bold(agent.ljust(24))} {vote_str}")
                lines.append(f"     {self.dim(reason)}")
                lines.append("")

        if categories:
            cat_list = ", ".join(self.c(c, Colors.CYAN) for c in categories)
            lines.append(f"  {self.bold('Detected Categories')}: {cat_list}")
            lines.append("")

        if risks:
            lines.append(f"  {self.bold('Key Risks & Blindspots')}:")
            for r in risks[:4]:
                lines.append(f"    {self.c('•', Colors.BRIGHT_YELLOW)} {r}")
            lines.append("")

        if next_actions:
            lines.append(f"  {self.bold('Recommended Next Actions')}:")
            for a in next_actions[:3]:
                lines.append(f"    {self.c('→', Colors.BRIGHT_CYAN)} {a}")
            lines.append("")

        return "\n".join(lines)

    def format_debate(self, payload: dict[str, Any]) -> str:
        question = str(payload.get("question", "Architecture Debate"))
        lines = [
            "",
            self.c("╔════════════════════════════════════════════════════════════════╗", Colors.MAGENTA),
            self.c("║", Colors.MAGENTA) + f"  ⚖️  ROUND TABLE DEBATE: {question[:45]}".ljust(66) + self.c("║", Colors.MAGENTA),
            self.c("╚════════════════════════════════════════════════════════════════╝", Colors.MAGENTA),
            "",
        ]
        return "\n".join(lines)


def format_ship_check_terminal(payload: dict[str, Any], use_color: bool | None = None) -> str:
    formatter = TUIFormatter(use_color=use_color)
    return formatter.format_ship_check(payload)


def format_debate_terminal(payload: dict[str, Any], use_color: bool | None = None) -> str:
    formatter = TUIFormatter(use_color=use_color)
    return formatter.format_debate(payload)
