"""
monitor.py
----------
Automated batch fraud scanner.
Reads a CSV of transactions, detects structuring patterns (multiple
deposits that together exceed the $10,000 BSA reporting threshold),
and files SAR reports automatically.

Expected CSV columns:
    customer_name  (str)   — customer full name
    amount         (float) — transaction amount in USD
    date           (str)   — optional, transaction date
    branch         (str)   — optional, branch or location
    type           (str)   — optional, e.g. 'deposit', 'wire'
"""

import io
import pandas as pd
from anonymizer import SARAnonymizer
from generator import SARGenerator
from database import SARDatabase
from risk import RiskScorer


# ── Constants ──────────────────────────────────────────────────────────────
STRUCTURING_THRESHOLD = 10_000   # Total amount that triggers a flag
MIN_TRANSACTIONS = 2             # Minimum number of txns to flag structuring


class FraudMonitor:
    def __init__(self):
        self.anon = SARAnonymizer()
        self.gen = SARGenerator()
        self.db = SARDatabase()
        self.risk_scorer = RiskScorer()
        print("[Monitor] FraudMonitor initialised.")

    def auto_scan(self, csv_source) -> list[dict]:
        """
        Reads a CSV file, detects structuring fraud, generates SAR reports,
        and saves them to MongoDB.

        Args:
            csv_source: Either a file path (str) OR a Streamlit UploadedFile object.
                        Both are handled correctly.

        Returns:
            A list of alert dicts for the UI, one per flagged customer.
            Each dict contains: name, total, transaction_count, risk_level,
                                report_id, narrative.
        """
        # ── Load CSV (handles both str paths and Streamlit UploadedFile) ──
        df = self._load_csv(csv_source)
        if df is None or df.empty:
            print("[Monitor] No data loaded from CSV.")
            return []

        # ── Validate required columns ─────────────────────────────────────
        if "customer_name" not in df.columns or "amount" not in df.columns:
            raise ValueError(
                "[Monitor] CSV must contain 'customer_name' and 'amount' columns."
            )

        # Coerce amount to numeric; drop unparseable rows
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df = df.dropna(subset=["amount"])

        # ── Aggregate by customer ─────────────────────────────────────────
        summary = (
            df.groupby("customer_name")["amount"]
            .agg(total_amount="sum", transaction_count="count")
            .reset_index()
        )

        # ── Apply structuring rule ────────────────────────────────────────
        flagged = summary[
            (summary["total_amount"] >= STRUCTURING_THRESHOLD) &
            (summary["transaction_count"] >= MIN_TRANSACTIONS)
        ]

        results = []
        for _, row in flagged.iterrows():
            customer = row["customer_name"]
            total = row["total_amount"]
            count = int(row["transaction_count"])

            # Get any extra context from the raw rows for this customer
            customer_rows = df[df["customer_name"] == customer]
            extra_context = self._build_context(customer_rows)

            # 1. Build the alert description (raw — contains real name)
            alert_details = (
                f"Customer {customer} made {count} separate transactions "
                f"totalling ${total:,.2f} USD. {extra_context} "
                f"This pattern is consistent with financial structuring to avoid "
                f"BSA reporting thresholds."
            )

            # 2. Risk scoring
            risk = self.risk_scorer.score(alert_details, total)

            # 3. Mask PII before sending to AI
            masked = self.anon.mask_data(alert_details)

            # 4. Generate SAR narrative
            narrative = self.gen.generate_narrative(masked)

            # 5. Save to MongoDB
            report_id = self.db.save_report(
                raw_data=alert_details,
                masked_text=masked,
                ai_narrative=narrative,
                risk_level=risk["level"],
                risk_score=risk["score"],
                risk_flags=risk["flags"],
            )

            results.append({
                "name": customer,
                "total": total,
                "transaction_count": count,
                "risk_level": risk["level"],
                "risk_score": risk["score"],
                "report_id": str(report_id),
                "narrative": narrative,
            })

            print(f"[Monitor] Flagged: {customer} — ${total:,.2f} — {risk['level']} risk")

        print(f"[Monitor] Scan complete. {len(results)} fraud pattern(s) detected.")
        return results

    def _load_csv(self, source) -> pd.DataFrame | None:
        """
        Loads a CSV from either a file path string or a Streamlit UploadedFile.
        """
        try:
            if isinstance(source, str):
                # Regular file path
                return pd.read_csv(source)
            elif hasattr(source, "read"):
                # Streamlit UploadedFile — must seek back to start first
                source.seek(0)
                return pd.read_csv(source)
            elif isinstance(source, bytes):
                return pd.read_csv(io.BytesIO(source))
            else:
                print(f"[Monitor] Unknown CSV source type: {type(source)}")
                return None
        except Exception as e:
            print(f"[Monitor] Failed to read CSV: {e}")
            return None

    def _build_context(self, rows: pd.DataFrame) -> str:
        """
        Builds a human-readable summary of additional CSV columns if present.
        """
        parts = []
        if "type" in rows.columns:
            types = rows["type"].dropna().unique()
            if len(types):
                parts.append(f"Transaction types: {', '.join(types)}.")
        if "branch" in rows.columns:
            branches = rows["branch"].dropna().unique()
            if len(branches) > 1:
                parts.append(f"Conducted at {len(branches)} different branches.")
        if "date" in rows.columns:
            dates = rows["date"].dropna().unique()
            if len(dates) == 1:
                parts.append(f"All on {dates[0]}.")
            elif len(dates) > 1:
                parts.append(f"Spanning {len(dates)} different dates.")
        return " ".join(parts)


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    # Create a small test CSV
    test_csv = "test_transactions.csv"
    pd.DataFrame([
        {"customer_name": "Aradhya Ranjan", "amount": 4900, "type": "deposit", "branch": "Main St"},
        {"customer_name": "Aradhya Ranjan", "amount": 4900, "type": "deposit", "branch": "Oak Ave"},
        {"customer_name": "Aradhya Ranjan", "amount": 4900, "type": "deposit", "branch": "Park Rd"},
        {"customer_name": "Jane Smith",     "amount": 500,  "type": "deposit", "branch": "Main St"},
    ]).to_csv(test_csv, index=False)

    monitor = FraudMonitor()
    alerts = monitor.auto_scan(test_csv)

    print(f"\n{len(alerts)} alert(s) generated:")
    for a in alerts:
        print(f"  {a['name']} — ${a['total']:,.2f} — {a['risk_level']} risk — ID: {a['report_id']}")

    os.remove(test_csv)
