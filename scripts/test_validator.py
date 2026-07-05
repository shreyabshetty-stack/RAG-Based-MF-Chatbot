import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from services.validator import ResponseValidator
except Exception as e:
    print(f"Error importing validator: {e}")
    sys.exit(1)

validator = ResponseValidator()

# Format: (mock_llm_output, context_source_url, expect_valid)
VALIDATION_TESTS = [
    # Test 1: Valid 2-sentence response with 1 correct URL
    (
        "The expense ratio of HDFC Mid Cap Fund Direct Growth is 0.75%. "
        "For more details, visit https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth.",
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        True
    ),
    # Test 2: 4-sentence response (should be truncated to 3)
    (
        "The exit load is 1% if redeemed within 1 year. "
        "This applies to all equity schemes. "
        "It is calculated on the redeemed amount. "
        "It helps deter early redemptions.",
        "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
        True  # Valid after truncation
    ),
    # Test 3: Advisory leak in response (should fail)
    (
        "HDFC Focused Fund is a good fund. You should invest in it as it is expected to grow significantly.",
        "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
        False
    ),
    # Test 4: Missing URL in response (should auto-inject)
    (
        "The minimum SIP investment for HDFC ELSS Tax Saver Fund is 500 INR. "
        "The mandatory lock-in period for ELSS funds is 3 years.",
        "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
        True  # Valid after URL injection
    )
]

def run_tests():
    print("--- Running Output Validator Tests ---\n")
    all_passed = True

    for idx, (mock_response, source_url, expected_valid) in enumerate(VALIDATION_TESTS):
        print(f"Test {idx + 1}:")
        print(f"  Input: {mock_response[:100]}...")
        
        is_valid, formatted, warnings = validator.validate_and_format(mock_response, source_url)

        if warnings:
            for w in warnings:
                print(f"  [WARN] {w}")

        if is_valid == expected_valid:
            print(f"  Outcome: {'VALID' if is_valid else 'INVALID'}")
            if is_valid and formatted:
                print(f"  Formatted Response:\n    {formatted.strip()}")
            print("  Result: PASS\n")
        else:
            print(f"  Outcome: {'VALID' if is_valid else 'INVALID'} (Expected: {'VALID' if expected_valid else 'INVALID'})")
            print("  Result: FAIL\n")
            all_passed = False

    print(f"Validator Overall: {'[SUCCESS] All tests passed!' if all_passed else '[FAIL] Some tests failed.'}")

if __name__ == "__main__":
    run_tests()
