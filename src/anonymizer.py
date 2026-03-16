"""
anonymizer.py
-------------
Uses Microsoft Presidio to detect and mask PII in transaction text
before it is sent to the LLM, ensuring no real customer data is exposed.
"""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class SARAnonymizer:
    def __init__(self):
        """
        Initialises both Presidio engines.
        Requires the spaCy model to be downloaded first:
            python -m spacy download en_core_web_lg
        """
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            print("[Anonymizer] Presidio engines loaded successfully.")
        except Exception as e:
            raise RuntimeError(
                f"[Anonymizer] Could not load Presidio engines. "
                f"Did you run: python -m spacy download en_core_web_lg ?\n{e}"
            )

    def mask_data(self, text: str) -> str:
        """
        Detects PII entities in `text` and replaces them with safe placeholders.

        Supported entities:
            - PERSON          → <NAME>
            - EMAIL_ADDRESS   → <EMAIL>
            - LOCATION        → <LOCATION>
            - PHONE_NUMBER    → partially masked with '*'
            - CREDIT_CARD     → partially masked with '*'

        Returns:
            The anonymised string with all PII replaced.
        """
        if not text or not text.strip():
            return text

        # ── 1. Analysis Phase ──────────────────────────────────────────────
        # Tell Presidio which entity types to look for.
        results = self.analyzer.analyze(
            text=text,
            entities=[
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "PERSON",
                "LOCATION",
                "CREDIT_CARD",
            ],
            language="en",
        )

        # ── 2. Operator / Replacement Rules ───────────────────────────────
        # Define exactly how each entity type should be replaced.
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<NAME>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            # Mask all but the last 4 digits of phone numbers
            "PHONE_NUMBER": OperatorConfig(
                "mask",
                {
                    "chars_to_mask": 6,
                    "masking_char": "*",
                    "from_end": True,
                },
            ),
            # Mask all but the last 4 digits of credit card numbers
            "CREDIT_CARD": OperatorConfig(
                "mask",
                {
                    "chars_to_mask": 12,
                    "masking_char": "*",
                    "from_end": False,
                },
            ),
        }

        # ── 3. Anonymization Phase ─────────────────────────────────────────
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators,
        )

        return anonymized_result.text

    def get_detected_entities(self, text: str) -> list[dict]:
        """
        Returns a list of detected PII entities without masking them.
        Useful for displaying a 'privacy audit' summary in the UI.

        Returns:
            List of dicts: [{"entity_type": str, "text": str, "score": float}]
        """
        if not text or not text.strip():
            return []

        results = self.analyzer.analyze(
            text=text,
            entities=[
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "PERSON",
                "LOCATION",
                "CREDIT_CARD",
            ],
            language="en",
        )

        detected = []
        for r in results:
            detected.append(
                {
                    "entity_type": r.entity_type,
                    "text": text[r.start : r.end],
                    "confidence": round(r.score, 2),
                }
            )
        return detected


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = SARAnonymizer()

    test_string = (
        "Transfer of $10,000 from Aradhya Ranjan to a branch in Mumbai. "
        "Contact: aradhya@ranjan.com, +91-9876543210. "
        "Card used: 4111 1111 1111 1234."
    )

    print("─── Original Text ───")
    print(test_string)

    print("\n─── Detected PII ───")
    for entity in engine.get_detected_entities(test_string):
        print(f"  [{entity['entity_type']}]  \"{entity['text']}\"  (confidence: {entity['confidence']})")

    print("\n─── Masked Text ───")
    print(engine.mask_data(test_string))
