import re
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Predefined educational refusal message
REFUSAL_RESPONSE = (
    "I am a facts-only assistant and cannot provide investment advice, comparisons, or recommendations. "
    "For educational resources on mutual funds, please visit the AMFI Investor Education portal: "
    "https://www.amfiindia.com/investor-corner/education/interest-calculator.html or the SEBI Investor Education website."
)

# Rule-based advisory keywords (Regex patterns)
ADVISORY_KEYWORDS = [
    r"\bshould\s+i\s+(?:buy|invest|choose|sell|pick|withdraw)\b",
    r"\bwhich\s+(?:fund|scheme|one)\s+is\s+(?:better|best|good|safe|recommended)\b",
    r"\bcompare\s+performance\b",
    r"\brecommend\s+me\b",
    r"\bwhere\s+should\s+i\s+invest\b",
    r"\bwill\s+(?:it|this|hdfc)\s+(?:give|grow|make|double)\b",
    r"\b(?:better|best)\s+(?:fund|option|investment|choice)\b",
    r"\bis\s+(?:it|hdfc\s+.*)\s+safe\b",
    r"\bperformance\s+forecast\b",
    r"\bexpected\s+returns\b",
    r"\bshould\s+i\s+go\s+for\b"
]
ADVISORY_REGEX = re.compile("|".join(ADVISORY_KEYWORDS), re.IGNORECASE)

class MutualFundClassifier:
    def __init__(self):
        # Optional Groq client initialization (falls back to rule-based classification if key is absent)
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        
        if self.api_key and "your_groq_api_key" not in self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client for classifier: {e}")

    def is_advisory(self, query_text):
        """
        Determines if a query is advisory or qualitative.
        Returns True if ADVISORY, False if FACTUAL.
        """
        # 1. First sweep: Rule-based regex check
        if ADVISORY_REGEX.search(query_text):
            print("Classifier: Fired rule-based regex guardrail (Advisory intent detected).")
            return True
            
        # 2. Second sweep: LLM Classifier (if Groq client is configured)
        if self.client:
            print("Classifier: Invoking LLM Intent Classifier...")
            system_prompt = (
                "You are an intent classifier for a mutual fund FAQ assistant. Your job is to classify the query as either 'FACTUAL' or 'ADVISORY'.\n\n"
                "Classify as 'ADVISORY' if the user query is:\n"
                "- Asking for advice, suggestions, or opinions on whether to buy, sell, or invest.\n"
                "- Asking for performance forecasts, expected returns, or future predictions.\n"
                "- Asking if a fund is safe, profitable, or suitable for a financial goal.\n"
                "- Asking for comparisons between multiple funds qualitatively (e.g. which is better).\n\n"
                "Classify as 'FACTUAL' if the user query is:\n"
                "- Asking for objective, statistical parameters (e.g. exit load, expense ratio, AUM, manager, launch date, minimum SIP, benchmark name, statement download guide).\n\n"
                "Respond with exactly one word: 'FACTUAL' or 'ADVISORY'. Do not write anything else."
            )
            
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Query: {query_text}"}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.0,
                    max_tokens=5
                )
                result = chat_completion.choices[0].message.content.strip().upper()
                print(f"Classifier: LLM returned classification '{result}'")
                return "ADVISORY" in result
            except Exception as e:
                print(f"Warning: LLM classification failed: {e}. Falling back to factual routing.")
                
        # Fallback to factual if rule didn't hit and API is unavailable
        return False

    def handle_query_intent(self, query_text):
        """
        Processes query intent.
        Returns (is_advisory, sanitized_query_or_refusal_response)
        """
        # 1. Run classifier
        if self.is_advisory(query_text):
            return True, REFUSAL_RESPONSE
            
        return False, query_text

    def classify(self, query_text):
        """
        Convenience wrapper returning (intent_str, refusal_message_or_None).
        intent_str is 'FACTUAL' or 'ADVISORY'.
        Used by the FastAPI pipeline.
        """
        is_adv, response = self.handle_query_intent(query_text)
        if is_adv:
            return "ADVISORY", response
        return "FACTUAL", None

# Singleton helper
_classifier_instance = None

def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = MutualFundClassifier()
    return _classifier_instance
