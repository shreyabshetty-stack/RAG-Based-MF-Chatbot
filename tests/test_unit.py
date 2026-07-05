import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import json
import re

# Ensure the root directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.ingest import scrape_fund_data
from services.classifier import MutualFundClassifier, get_classifier, REFUSAL_RESPONSE
from services.pii_scrubber import PIIScrubber
from services.validator import ResponseValidator, ALLOWED_SOURCE_URLS


class TestIngestionParser(unittest.TestCase):
    """Test the scrape_fund_data parser logic on mock HTML documents."""

    def setUp(self):
        self.mock_server_data = {
            "scheme_name": "HDFC Test Mid Cap Fund",
            "expense_ratio": "0.75",
            "exit_load": "1% exit load.",
            "min_sip_investment": 100,
            "benchmark_name": "NIFTY Midcap 150 TR Index",
            "risk": "Moderately High",
            "fund_manager": "Test Manager",
            "launch_date": "01-Jan-2013",
            "aum": 50000.5,
            "isin": "INF179K01XYZ",
            "nav": 229.594,
            "nav_date": "03-Jul-2026",
            "portfolio_turnover": 13,
            "face_value": 10,
            "groww_rating": 5,
            "crisil_rating": 4
        }
        self.mock_next_data = {
            "props": {
                "pageProps": {
                    "mfServerSideData": self.mock_server_data
                }
            }
        }
        self.valid_html = (
            f"<html><body>"
            f"<script id=\"__NEXT_DATA__\" type=\"application/json\">"
            f"{json.dumps(self.mock_next_data)}"
            f"</script>"
            f"</body></html>"
        )

    @patch("urllib.request.urlopen")
    def test_successful_parsing(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = self.valid_html.encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        result = scrape_fund_data(url)

        self.assertIsNotNone(result)
        self.assertEqual(result["scheme_name"], "HDFC Test Mid Cap Fund")
        self.assertEqual(result["expense_ratio"], "0.75%")
        self.assertEqual(result["exit_load"], "1% exit load.")
        self.assertEqual(result["min_sip_investment"], 100)
        self.assertEqual(result["elss_lock_in"], "Nil")
        self.assertEqual(result["risk_classification"], "Moderately High")
        self.assertEqual(result["benchmark_index"], "NIFTY Midcap 150 TR Index")
        self.assertEqual(result["fund_manager"], "Test Manager")
        self.assertEqual(result["launch_date"], "01-Jan-2013")
        self.assertEqual(result["aum_in_cr"], 50000.5)
        self.assertEqual(result["isin"], "INF179K01XYZ")
        self.assertEqual(result["nav"], 229.594)
        self.assertEqual(result["nav_date"], "03-Jul-2026")
        self.assertEqual(result["portfolio_turnover"], "13")
        self.assertEqual(result["face_value"], 10)
        self.assertEqual(result["groww_rating"], 5)
        self.assertEqual(result["crisil_rating"], 4)
        self.assertEqual(result["source_url"], url)

    @patch("urllib.request.urlopen")
    def test_elss_lock_in_logic(self, mock_urlopen):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = self.valid_html.encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Test ELSS fund URL triggers 3 years lock-in
        elss_url = "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"
        result = scrape_fund_data(elss_url)
        self.assertIsNotNone(result)
        self.assertEqual(result["elss_lock_in"], "3 years")

    @patch("urllib.request.urlopen")
    def test_missing_next_data(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html><body>No scripts here</body></html>"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = scrape_fund_data("https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth")
        self.assertIsNone(result)

    @patch("urllib.request.urlopen")
    def test_empty_server_side_data(self, mock_urlopen):
        malformed_next_data = {"props": {"pageProps": {"mfServerSideData": {}}}}
        malformed_html = (
            f"<html><script id=\"__NEXT_DATA__\">"
            f"{json.dumps(malformed_next_data)}"
            f"</script></html>"
        )
        mock_response = MagicMock()
        mock_response.read.return_value = malformed_html.encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        result = scrape_fund_data("https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth")
        self.assertIsNone(result)


class TestGuardrailClassifier(unittest.TestCase):
    """Test the MutualFundClassifier intent safety controls."""

    def test_regex_advisory_detection(self):
        classifier = get_classifier()
        
        # Test cases that should trigger regex guardrail (advisory)
        advisory_queries = [
            "Should I buy HDFC Mid Cap?",
            "Which HDFC fund is better for growth?",
            "Can you recommend a good fund?",
            "Where should I invest my money?",
            "Will HDFC Large Cap double my money in 5 years?",
            "Is HDFC Mid Cap Opportunities Fund safe for retirement?",
            "What is the expected returns of HDFC Focused Fund?",
            "Should I go for HDFC ELSS?"
        ]
        for q in advisory_queries:
            with self.subTest(query=q):
                self.assertTrue(classifier.is_advisory(q), f"Query '{q}' should be classified as ADVISORY")

    def test_regex_factual_allowance(self):
        classifier = get_classifier()
        
        # Test cases that should pass rule-based guardrail (factual)
        factual_queries = [
            "What is the expense ratio of HDFC Mid Cap?",
            "What is the exit load of HDFC Large Cap?",
            "Minimum SIP investment HDFC Focused",
            "Tell me the launch date of HDFC ELSS Tax Saver",
            "Who is the fund manager of HDFC Equity Fund?",
            "How can I download HDFC statements?",
            "What is the benchmark of HDFC Top 100?"
        ]
        
        # We need to temporarily mock Groq client to None to ensure it doesn't try to call LLM if key is present
        with patch.object(classifier, 'client', None):
            for q in factual_queries:
                with self.subTest(query=q):
                    self.assertFalse(classifier.is_advisory(q), f"Query '{q}' should be classified as FACTUAL")

    @patch("services.classifier.Groq")
    def test_llm_classification(self, mock_groq_class):
        # Configure mock Groq client behavior
        mock_client = MagicMock()
        mock_chat = MagicMock()
        mock_completion = MagicMock()
        
        mock_completion.choices = [MagicMock(message=MagicMock(content="ADVISORY"))]
        mock_chat.completions.create.return_value = mock_completion
        mock_client.chat = mock_chat
        
        classifier = MutualFundClassifier()
        classifier.client = mock_client
        
        # This query has no keywords matching regex but LLM returns ADVISORY
        is_adv = classifier.is_advisory("Do you think this fund fits my long term portfolio?")
        self.assertTrue(is_adv)
        mock_chat.completions.create.assert_called_once()


class TestPIIScrubber(unittest.TestCase):
    """Test the PIIScrubber's ability to redact PII types."""

    def test_email_scrubbing(self):
        raw = "Send details to tester.123_abc@my-domain.co.in please."
        expected = "Send details to [REDACTED EMAIL] please."
        self.assertEqual(PIIScrubber.scrub_query(raw), expected)

    def test_pan_scrubbing(self):
        raw = "My PAN number is ABCDE1234F."
        expected = "My PAN number is [REDACTED PAN]."
        self.assertEqual(PIIScrubber.scrub_query(raw), expected)

    def test_aadhaar_scrubbing(self):
        raw_spaced = "Aadhaar: 5678 1234 9012."
        expected_spaced = "Aadhaar: [REDACTED AADHAAR]."
        self.assertEqual(PIIScrubber.scrub_query(raw_spaced), expected_spaced)

        raw_joined = "My Aadhaar is 567812349012."
        expected_joined = "My Aadhaar is [REDACTED AADHAAR]."
        self.assertEqual(PIIScrubber.scrub_query(raw_joined), expected_joined)

    def test_phone_scrubbing(self):
        raw_basic = "Contact me at 9876543210."
        expected_basic = "Contact me at [REDACTED PHONE]."
        self.assertEqual(PIIScrubber.scrub_query(raw_basic), expected_basic)

        raw_prefix = "Call +91-9876543210 now."
        expected_prefix = "Call [REDACTED PHONE] now."
        self.assertEqual(PIIScrubber.scrub_query(raw_prefix), expected_prefix)

    def test_otp_scrubbing(self):
        raw_otp = "My OTP is 482103."
        expected_otp = "My [REDACTED OTP/PIN]."
        self.assertEqual(PIIScrubber.scrub_query(raw_otp), expected_otp)

        raw_pin = "One-time-password: 1234"
        expected_pin = "[REDACTED OTP/PIN]"
        self.assertEqual(PIIScrubber.scrub_query(raw_pin), expected_pin)

    def test_folio_sensitive_id_scrubbing(self):
        # Folios or numbers between 6 and 16 digits
        raw_folio = "My folio number is 987654321."
        expected_folio = "My folio number is [REDACTED SENSITIVE ID]."
        self.assertEqual(PIIScrubber.scrub_query(raw_folio), expected_folio)

    def test_combo_scrubbing(self):
        raw = "Email user@domain.com, PAN ABCDE1234F, Aadhaar 9999 8888 7777, Phone 9123456789."
        expected = "Email [REDACTED EMAIL], PAN [REDACTED PAN], Aadhaar [REDACTED AADHAAR], Phone [REDACTED PHONE]."
        self.assertEqual(PIIScrubber.scrub_query(raw), expected)


class TestResponseValidator(unittest.TestCase):
    """Test the ResponseValidator checking, fixing, and footer injection rules."""

    def test_sentence_counter(self):
        validator = ResponseValidator()
        
        # Basic 3 sentences
        self.assertEqual(validator.count_sentences("Sentence one. Sentence two? Sentence three!"), 3)
        # URLs containing dots should not count as sentence breaks
        self.assertEqual(
            validator.count_sentences("Visit https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth for details. Thank you."),
            2
        )
        # Decimal numbers should not count as sentence breaks
        self.assertEqual(
            validator.count_sentences("The expense ratio is 0.75%. This is very low."),
            2
        )

    def test_extract_urls(self):
        validator = ResponseValidator()
        text = "Check HDFC at https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth and SEBI at https://sebi.gov.in"
        self.assertEqual(
            validator.extract_urls(text),
            ["https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth", "https://sebi.gov.in"]
        )

    def test_is_advisory_leak(self):
        validator = ResponseValidator()
        
        self.assertTrue(validator.is_advisory_leak("You should invest in this fund immediately."))
        self.assertTrue(validator.is_advisory_leak("I recommend HDFC Large Cap."))
        self.assertTrue(validator.is_advisory_leak("It is advisable to buy this scheme."))
        self.assertTrue(validator.is_advisory_leak("This fund will grow by 15% next year."))
        
        self.assertFalse(validator.is_advisory_leak("The expense ratio of HDFC Mid Cap is 0.75%."))

    def test_fix_url_if_needed(self):
        validator = ResponseValidator()
        target_url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        
        # Case 1: No URL present -> Inject
        text1 = "The minimum investment is 100 INR."
        fixed1 = validator.fix_url_if_needed(text1, target_url)
        self.assertIn(target_url, fixed1)
        
        # Case 2: Incorrect URL present -> Replace and Inject
        text2 = "Check details here: https://invalid-url.com/scheme."
        fixed2 = validator.fix_url_if_needed(text2, target_url)
        self.assertIn(target_url, fixed2)
        self.assertNotIn("invalid-url.com", fixed2)

        # Case 3: Correct URL present -> No Change
        text3 = f"Refer to {target_url} for details."
        fixed3 = validator.fix_url_if_needed(text3, target_url)
        self.assertEqual(text3, fixed3)

    def test_validate_and_format(self):
        validator = ResponseValidator()
        target_url = "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        
        # Case 1: Normal valid response
        resp1 = "The expense ratio is 0.75%. The minimum SIP investment is 100 INR."
        is_valid, formatted, warnings = validator.validate_and_format(resp1, target_url)
        self.assertTrue(is_valid)
        self.assertIn(target_url, formatted)
        self.assertIn("Last updated from sources:", formatted)
        self.assertEqual(len(warnings), 0)

        # Case 2: Too long response (>3 sentences) -> Truncate warning
        resp2 = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        is_valid, formatted, warnings = validator.validate_and_format(resp2, target_url)
        self.assertTrue(is_valid)
        text_without_source = re.sub(r"\s*\(Source:\s*[^\)]+\)\s*$", "", formatted.split("\n\n")[0])
        self.assertEqual(validator.count_sentences(text_without_source), 3)
        self.assertTrue(any("Truncating" in w for w in warnings))

        # Case 3: Response with advisory leak -> Reject
        resp3 = "The fund is very safe and I recommend investing in it."
        is_valid, formatted, warnings = validator.validate_and_format(resp3, target_url)
        self.assertFalse(is_valid)
        self.assertIsNone(formatted)
        self.assertTrue(any("Advisory language detected" in w for w in warnings))


class TestMutualFundRetriever(unittest.TestCase):
    """Test MutualFundRetriever class using mocked HTTP calls for embeddings."""

    @patch("requests.post")
    @patch("chromadb.PersistentClient")
    @patch("os.path.exists")
    def test_get_embedding_success(self, mock_exists, mock_chroma_client, mock_post):
        mock_exists.return_value = True
        
        # Configure mock response for requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "[0.1, 0.2, 0.3]"
        mock_response.json.return_value = [0.1, 0.2, 0.3]
        mock_post.return_value = mock_response
        
        from services.retriever import MutualFundRetriever
        retriever = MutualFundRetriever()
        
        emb = retriever._get_embedding("test query")
        self.assertEqual(emb, [0.1, 0.2, 0.3])
        mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()

