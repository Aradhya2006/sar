"""
risk.py
-------
Rule-based risk scoring engine for SAR Automator.
Analyses transaction text and amount to assign a risk level
(Low / Medium / High) and a numeric score 0–100.

This module is intentionally kept separate so scoring rules can be
updated without touching the main pipeline.
"""

import re


# ── Rule weights ───────────────────────────────────────────────────────────
# Each rule is a (description, regex_pattern_or_None, points) tuple.
# If regex is None the rule is evaluated by the caller (e.g. amount thresholds).
RULES = [
    # Amount-based (handled separately below)
    # Pattern-based rules
    ("Multiple transactions detected",      r"\b(multiple|separate|\d+\s*(transfers?|deposits?|transactions?))\b", 25),
    ("International / overseas transfer",   r"\b(wire transfer|overseas|international|offshore|foreign|swift)\b",  20),
    ("Rapid succession / same day",         r"\b(90 min|within an hour|same day|minutes apart|rapid)\b",           15),
    ("Round-number structuring pattern",    r"\$[89],\d{3}",                                                        20),
    ("No documented business purpose",      r"\b(no (business )?purpose|undocumented|no documentation)\b",         10),
    ("Shell / anonymised entity involved",  r"\b(shell|anonymous|nominee|bearer)\b",                               20),
    ("Cash transactions",                   r"\b(cash|currency)\b",                                                10),
    ("High-risk jurisdiction",              r"\b(cayman|bahamas|panama|bvi|isle of man|jersey)\b",                 20),
    ("Crypto / digital asset involvement",  r"\b(crypto|bitcoin|ethereum|usdt|blockchain|digital asset)\b",        15),
    ("Layering indicators",                 r"\b(layer|smurfs?|structur(ing|ed)|placement)\b",                     30),
]


class RiskScorer:
    """
    Scores a transaction description on a 0–100 scale and assigns
    a Low / Medium / High risk label.
    """

    # Thresholds
    HIGH_THRESHOLD   = 60
    MEDIUM_THRESHOLD = 30

    # Amount scoring breakpoints (USD)
    AMOUNT_BANDS = [
        (50_000, 40, "Amount ≥ $50,000 (very high value)"),
        (25_000, 35, "Amount ≥ $25,000 (high value)"),
        (10_000, 30, "Amount ≥ $10,000 (BSA reporting threshold)"),
        (5_000,  20, "Amount ≥ $5,000 (elevated)"),
        (1_000,  10, "Amount ≥ $1,000 (moderate)"),
    ]

    def score(self, text: str, amount: float = 0.0) -> dict:
        """
        Evaluates the transaction and returns a full risk assessment.

        Args:
            text:   Raw or anonymised transaction description.
            amount: Numeric transaction amount (optional; also extracted
                    from text if not provided).

        Returns:
            Dict with keys:
                score  (int 0-100)
                level  ('Low', 'Medium', or 'High')
                flags  (list[str] — descriptions of triggered rules)
                color  (hex string for UI display)
        """
        total_score = 0
        flags: list[str] = []
        text_lower = text.lower()

        # ── Amount scoring ─────────────────────────────────────────────────
        # Use provided amount; also try to extract from text as fallback
        effective_amount = amount or self._extract_amount(text)
        for threshold, points, description in self.AMOUNT_BANDS:
            if effective_amount >= threshold:
                total_score += points
                flags.append(description)
                break  # Only fire the highest matching band

        # ── Pattern-based rules ────────────────────────────────────────────
        for description, pattern, points in RULES:
            if re.search(pattern, text_lower, re.IGNORECASE):
                total_score += points
                flags.append(description)

        # Cap at 100
        total_score = min(total_score, 100)

        # ── Level assignment ───────────────────────────────────────────────
        if total_score >= self.HIGH_THRESHOLD:
            level = "High"
            color = "#E24B4A"
        elif total_score >= self.MEDIUM_THRESHOLD:
            level = "Medium"
            color = "#EF9F27"
        else:
            level = "Low"
            color = "#639922"

        return {
            "score": total_score,
            "level": level,
            "flags": flags,
            "color": color,
        }

    @staticmethod
    def _extract_amount(text: str) -> float:
        """
        Tries to extract the largest dollar amount mentioned in the text.
        Returns 0.0 if none found.
        """
        matches = re.findall(r"\$[\d,]+(?:\.\d{1,2})?", text)
        amounts = []
        for m in matches:
            try:
                amounts.append(float(m.replace("$", "").replace(",", "")))
            except ValueError:
                pass
        return max(amounts, default=0.0)


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scorer = RiskScorer()

    tests = [
        ("Small single deposit of $500", 500),
        ("Customer made 3 separate deposits of $9,000 each in the same day", 27000),
        ("Wire transfer of $15,000 to an overseas offshore account in the Cayman Islands", 15000),
        ("Cash deposit of $200", 200),
    ]

    print(f"{'Description':<70} {'Score':>6}  {'Level':<8}")
    print("─" * 90)
    for desc, amt in tests:
        result = scorer.score(desc, amt)
        print(f"{desc[:68]:<70} {result['score']:>6}  {result['level']:<8}")
        for flag in result["flags"]:
            print(f"  ↳ {flag}")
