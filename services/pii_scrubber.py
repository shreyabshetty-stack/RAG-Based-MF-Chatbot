import re

# Regex patterns for various PII targets
PAN_PATTERN = re.compile(r"\b[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}\b")
AADHAAR_PATTERN = re.compile(r"\b[2-9]{1}\d{3}\s\d{4}\s\d{4}\b|\b[2-9]{1}\d{11}\b")
PHONE_PATTERN = re.compile(r"\+?91[-.\s]?[6-9]\d{9}\b|\b[6-9]\d{9}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
OTP_CONTEXT_PATTERN = re.compile(r"\b(?:otp|one[- ]time[- ]password|pin)\s*(?:is\s*)?:?\s*\b\d{4,8}\b", re.IGNORECASE)

# Folio numbers / general multi-digit sensitive numbers (e.g. 6 to 16 digits)
FOLIO_OR_SENSITIVE_NUM_PATTERN = re.compile(r"\b\d{6,16}\b")

class PIIScrubber:
    @staticmethod
    def scrub_query(query_text):
        """
        Redacts sensitive PII attributes (PAN, Aadhaar, phone, email, OTPs) from user query text.
        """
        if not query_text:
            return query_text

        # 1. Redact Email addresses
        scrubbed = EMAIL_PATTERN.sub("[REDACTED EMAIL]", query_text)
        
        # 2. Redact PAN card numbers
        scrubbed = PAN_PATTERN.sub("[REDACTED PAN]", scrubbed)
        
        # 3. Redact Aadhaar card numbers
        scrubbed = AADHAAR_PATTERN.sub("[REDACTED AADHAAR]", scrubbed)
        
        # 4. Redact OTP sequences matching context
        scrubbed = OTP_CONTEXT_PATTERN.sub("[REDACTED OTP/PIN]", scrubbed)
        
        # 5. Redact Phone numbers
        scrubbed = PHONE_PATTERN.sub("[REDACTED PHONE]", scrubbed)
        
        # 6. Redact generic Folio / Multi-digit sensitive account identifiers (6+ digits)
        # Avoid overriding previous redaction text strings (like [REDACTED PHONE]) by checking word boundary of raw digits
        scrubbed = FOLIO_OR_SENSITIVE_NUM_PATTERN.sub("[REDACTED SENSITIVE ID]", scrubbed)
        
        return scrubbed

    def scrub(self, query_text):
        """
        Convenience wrapper returning (cleaned_text, pii_was_detected).
        Used by the FastAPI pipeline.
        """
        cleaned = self.scrub_query(query_text)
        pii_detected = cleaned != query_text
        return cleaned, pii_detected
