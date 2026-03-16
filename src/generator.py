"""
generator.py
------------
Uses a locally-running Ollama model (Llama 3.2 by default) to generate
formal Suspicious Activity Report (SAR) narratives from anonymised
transaction details.

Requires Ollama to be running:
    ollama serve
    ollama pull llama3.2
"""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate


# ── Prompt template ────────────────────────────────────────────────────────
SAR_TEMPLATE = """
You are a Senior Financial Compliance Officer at a major international bank.
Your job is to write formal, professional Suspicious Activity Reports (SARs)
for submission to regulatory authorities.

Based on the following anonymised transaction details, write a complete SAR narrative.

TRANSACTION DETAILS:
{details}

Structure your response EXACTLY as follows (keep the headings):

SUMMARY OF ACTIVITY:
[2-3 sentences describing what happened: who, what amounts, what method, when]

SUSPICIOUS INDICATORS:
[Bullet list of specific red flags — be precise, cite amounts and patterns]

REGULATORY CONTEXT:
[Mention relevant regulations: BSA, FinCEN rules, structuring thresholds, etc.]

RECOMMENDATION:
[Concrete next steps: EDD, SAR filing deadline, account actions, record retention]

Rules:
- Use formal, objective, third-person language only.
- Do NOT speculate about guilt — only report observable facts and patterns.
- Do NOT include any real names (the input has already been anonymised).
- Keep the total response under 400 words.
"""


class SARGenerator:
    def __init__(self, model: str = "llama3.2", timeout: int = 120):
        """
        Connects to the locally-running Ollama instance.

        Args:
            model:   The Ollama model name to use. Default: llama3.2
            timeout: Request timeout in seconds.
        """
        try:
            self.llm = OllamaLLM(model=model, timeout=timeout)
            self.model = model
            print(f"[Generator] Connected to Ollama model: {model}")
        except Exception as e:
            raise RuntimeError(
                f"[Generator] Could not connect to Ollama.\n"
                f"  Make sure Ollama is running: `ollama serve`\n"
                f"  And the model is pulled: `ollama pull {model}`\n"
                f"  Error: {e}"
            )

    def generate_narrative(self, transaction_details: str) -> str:
        """
        Generates a formal SAR narrative from anonymised transaction details.

        Args:
            transaction_details: Anonymised description of the suspicious activity.

        Returns:
            A formatted SAR narrative string, or an error message if generation fails.
        """
        if not transaction_details or not transaction_details.strip():
            return "Error: No transaction details provided."

        prompt = PromptTemplate(
            input_variables=["details"],
            template=SAR_TEMPLATE,
        )
        chain = prompt | self.llm

        try:
            print(f"[Generator] Sending request to {self.model}...")
            response = chain.invoke({"details": transaction_details})
            print("[Generator] Narrative generated successfully.")
            return response.strip()
        except Exception as e:
            error_msg = (
                f"[Generator] ERROR: Could not generate narrative.\n"
                f"  Is Ollama still running? Try: ollama serve\n"
                f"  Error: {e}"
            )
            print(error_msg)
            # Return a fallback template so the app doesn't break
            return self._fallback_narrative(transaction_details)

    def _fallback_narrative(self, details: str) -> str:
        """
        Returns a basic templated narrative when the LLM is unavailable.
        Ensures the UI always shows something meaningful.
        """
        return (
            "SUMMARY OF ACTIVITY:\n"
            "The system detected suspicious financial activity based on the provided "
            f"transaction details. Details: {details[:200]}...\n\n"
            "SUSPICIOUS INDICATORS:\n"
            "• Automated pattern matching flagged this transaction for review.\n"
            "• Manual review by a compliance officer is required.\n\n"
            "REGULATORY CONTEXT:\n"
            "Transactions meeting BSA reporting thresholds require SAR filing within 30 days.\n\n"
            "RECOMMENDATION:\n"
            "Escalate to AML Compliance Officer immediately. "
            "NOTE: This is a fallback narrative — the AI model was unavailable. "
            "Please review the raw transaction data manually."
        )


# ── Self-test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    gen = SARGenerator()
    print("Sending test transaction to AI...")

    test_details = (
        "Subject <n> made 3 cash deposits of $9,000 each within 90 minutes "
        "at different branches in <LOCATION>. Total: $27,000. "
        "No business purpose documented."
    )

    result = gen.generate_narrative(test_details)
    print("\n─── AI Generated SAR Narrative ───")
    print(result)
