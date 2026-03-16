# We use the OllamaLLM class to communicate with the model running on your laptop
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

class SARGenerator:
    def __init__(self):
        # 1. MODEL INITIALIZATION
        # This connects to the 'llama3.2' model you are downloading via Ollama.
        # If the model isn't running, this is where the 'Connection Refused' error happens.
        self.llm = OllamaLLM(model="llama3.2")

    def generate_narrative(self, transaction_details):
        # 2. PROMPT ENGINEERING
        # We give the AI a 'Persona' (Financial Compliance Expert).
        # This ensures the output sounds like a bank report, not a chat.
        template = """
        You are a Financial Compliance Expert at a major bank. 
        Write a professional Suspicious Activity Report (SAR) narrative based on these details:
        
        DETAILS: {details}
        
        Structure the response as follows:
        - SUMMARY OF ACTIVITY: (What happened?)
        - SUSPICIOUS INDICATORS: (Why is this a red flag?)
        - RECOMMENDATION: (What should the bank do next?)
        
        Keep it formal, objective, and concise.
        """

        # 3. SETUP THE CHAIN
        # We combine the prompt instructions with the AI model logic.
        prompt = PromptTemplate(input_variables=["details"], template=template)
        chain = prompt | self.llm

        # 4. EXECUTION
        # We send the 'masked' details to the AI and wait for the response.
        response = chain.invoke({"details": transaction_details})
        return response

# --- TEST BLOCK ---
if __name__ == "__main__":
    # Once you finish 'ollama pull llama3.2', you can run this file to test it!
    gen = SARGenerator()
    print("🤖 AI is analyzing the transaction...")
    
    # We use dummy data for the test
    test_info = "Customer <NAME> made 3 cash deposits of $9,000 each within 1 hour."
    result = gen.generate_narrative(test_info)
    
    print("\n--- AI GENERATED REPORT ---")
    print(result)