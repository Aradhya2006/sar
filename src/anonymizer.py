# We import the tools to find (Analyze) and hide (Anonymize) PII.
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class SARAnonymizer:
    def __init__(self):
        # Initialize the Engines. 
        # The analyzer uses the 'en_core_web_lg' model you are downloading.
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        except Exception as e:
            print(f"Error: Could not load engines. Did you download the spacy model? {e}")

    def mask_data(self, text):
        """
        Takes raw text and replaces sensitive info with placeholders.
        """
        # 1. ANALYSIS PHASE
        # We tell the engine to look for specific 'Entities' (Names, Emails, etc.)
        results = self.analyzer.analyze(
            text=text, 
            entities=["PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON", "LOCATION", "CREDIT_CARD"],
            language='en'
        )

        # 2. OPERATOR PHASE
        # Here we define the "Replacement Rules". 
        # For names, we want the word <NAME>. For phones, we want to mask it with '*'.
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<NAME>"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "<LOCATION>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
            "PHONE_NUMBER": OperatorConfig("mask", {
                "chars_to_mask": 6, 
                "masking_char": "*", 
                "from_end": True
            }),
        }

        # 3. ANONYMIZATION PHASE
        # We combine the original text with the findings and the rules.
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        
        # Return the 'cleaned' string
        return anonymized_result.text

# --- TEST BLOCK ---
# This only runs if you play this file directly (python src/anonymizer.py)
if __name__ == "__main__":
    engine = SARAnonymizer()
    
    # Test case with your name to see if it masks correctly!
    test_string = "Transfer of $10,000 from Aradhya Ranjan to a branch in Mumbai. Contact: 9876543210."
    
    print("--- Original Text ---")
    print(test_string)
    
    print("\n--- Masked Text ---")
    print(engine.mask_data(test_string))