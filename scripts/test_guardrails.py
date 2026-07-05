import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

try:
    from services.pii_scrubber import PIIScrubber
    from services.classifier import get_classifier
except Exception as e:
    print(f"Error importing services: {e}")
    sys.exit(1)

# PII Test Cases
PII_TESTS = [
    ("My PAN card is ABCDE1234F and my phone number is 9876543210.", 
     "My PAN card is [REDACTED PAN] and my phone number is [REDACTED PHONE]."),
    ("Aadhaar card details: 5678 1234 9012. Email: user.name_123@sub.domain.com", 
     "Aadhaar card details: [REDACTED AADHAAR]. Email: [REDACTED EMAIL]"),
    ("My transaction OTP is 123456 and folio number is 98765432.", 
     "My transaction OTP is 123456 and folio number is [REDACTED SENSITIVE ID].")
]

# Intent Test Cases (Factual vs Advisory)
INTENT_TESTS = [
    ("What is the expense ratio of HDFC Mid Cap Fund?", False), # Factual
    ("Should I invest in HDFC Focused Fund?", True),            # Advisory
    ("Which fund is better: HDFC Mid Cap or HDFC Flexi Cap?", True), # Advisory
    ("What is the exit load of HDFC Large Cap?", False),       # Factual
    ("Is HDFC Mid Cap Opportunities Fund safe for retirement?", True) # Advisory (Subtle)
]

def test_pii():
    print("--- Running PII Scrubber Tests ---")
    all_passed = True
    for idx, (raw, expected_prefix) in enumerate(PII_TESTS):
        scrubbed = PIIScrubber.scrub_query(raw)
        print(f"Test {idx+1}:")
        print(f"  Raw:      {raw}")
        print(f"  Scrubbed: {scrubbed}")
        
        # Simple checks to ensure redactions are present
        if "REDACTED" not in scrubbed:
            print("  Result:   FAIL (No redaction occurred)")
            all_passed = False
        else:
            print("  Result:   PASS")
    print(f"PII Scrubber Overall: {'PASS' if all_passed else 'FAIL'}\n")
    return all_passed

def test_intent():
    print("--- Running Intent Classifier Tests ---")
    classifier = get_classifier()
    all_passed = True
    
    for idx, (query, expected_advisory) in enumerate(INTENT_TESTS):
        is_advisory, response_or_query = classifier.handle_query_intent(query)
        print(f"Test {idx+1}: '{query}'")
        print(f"  Classified: {'ADVISORY' if is_advisory else 'FACTUAL'}")
        if is_advisory:
            print(f"  Refusal:    {response_or_query[:100]}...")
            
        if is_advisory != expected_advisory:
            print(f"  Result:     FAIL (Expected {'ADVISORY' if expected_advisory else 'FACTUAL'})")
            all_passed = False
        else:
            print("  Result:     PASS")
            
    print(f"Intent Classifier Overall: {'PASS' if all_passed else 'FAIL'}\n")
    return all_passed

def main():
    print("Starting Phase 4 Guardrails Verification...\n")
    pii_ok = test_pii()
    intent_ok = test_intent()
    
    if pii_ok and intent_ok:
        print("[SUCCESS] All guardrail checks passed successfully!")
    else:
        print("[FAIL] Some guardrail checks failed. Please check logs.")

if __name__ == "__main__":
    main()
