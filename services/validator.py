import re
from datetime import datetime

# Whitelisted Groww URLs
ALLOWED_SOURCE_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in"  # Procedural chunk URL
]

# Advisory keywords to screen in generated outputs
ADVISORY_OUTPUT_TERMS = [
    r"\bshould\s+(?:consider|buy|invest|choose|sell|pick|avoid|stay)\b",
    r"\bi\s+recommend\b",
    r"\bit\s+is\s+(?:advisable|recommended|suggested|good|safe|better)\s+to\b",
    r"\b(?:you|one)\s+(?:should|must|ought\s+to)\s+invest\b",
    r"\bbetter\s+(?:choice|option|fund|scheme)\b",
    r"\bexpected\s+(?:to\s+)?(?:grow|return|perform)\b",
    r"\bwill\s+(?:grow|give|yield|generate|return)\b",
]
ADVISORY_OUTPUT_REGEX = re.compile("|".join(ADVISORY_OUTPUT_TERMS), re.IGNORECASE)

# URL extractor
URL_PATTERN = re.compile(r"https?://[^\s)>\]\"']+")

class ResponseValidator:
    @staticmethod
    def count_sentences(text):
        """
        Counts sentences by splitting on common sentence-ending punctuation.
        Avoids counting ellipses, URLs with dots, etc.
        """
        # Temporarily mask URLs to avoid confusing sentence counter
        masked = URL_PATTERN.sub("__URL__", text)
        # Split on sentence-terminating characters followed by whitespace or end of string
        sentences = re.split(r"(?<=[.!?])\s+", masked.strip())
        # Filter out empty strings
        sentences = [s for s in sentences if s.strip()]
        return len(sentences)

    @staticmethod
    def extract_urls(text):
        return URL_PATTERN.findall(text)

    @staticmethod
    def is_advisory_leak(text):
        return bool(ADVISORY_OUTPUT_REGEX.search(text))

    @staticmethod
    def inject_footer(text, source_url):
        """
        Appends the required footer to the response.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        footer = f"\n\nLast updated from sources: {today_str}. Source: {source_url}"
        return text.strip() + footer

    @staticmethod
    def fix_url_if_needed(text, expected_url):
        """
        If the response contains no valid whitelisted URL or contains an incorrect URL,
        replaces it with the expected_url from context metadata.
        """
        urls_found = URL_PATTERN.findall(text)

        # If there is exactly one URL and it is exactly the expected_url, keep it as is.
        if len(urls_found) == 1 and urls_found[0] == expected_url:
            return text

        # Otherwise, strip all URLs found and inject the expected one
        for url in urls_found:
            text = text.replace(url, "").strip()
        
        text = text + f" (Source: {expected_url})"
        return text

    def validate_and_format(self, llm_response, context_source_url):
        """
        Validates the LLM response against all constraints and injects the footer.
        Returns (is_valid, formatted_response, errors)
        """
        warnings = []
        errors = []
        response = llm_response.strip()

        # Check 1: Sentence limit <= 3 (auto-correctable: truncate to 3)
        sentence_count = self.count_sentences(response)
        if sentence_count > 3:
            warnings.append(f"Response has {sentence_count} sentences (max 3). Truncating...")
            # Truncate to first 3 sentences
            masked = URL_PATTERN.sub("__URL__", response)
            parts = re.split(r"(?<=[.!?])\s+", masked.strip())
            first_three_masked = " ".join(parts[:3])
            # Restore URLs
            all_urls = URL_PATTERN.findall(response)
            for url in all_urls:
                first_three_masked = first_three_masked.replace("__URL__", url, 1)
            response = first_three_masked

        # Check 2: Fix URL compliance (auto-correctable: inject whitelisted URL)
        response = self.fix_url_if_needed(response, context_source_url)

        # Check 3: Advisory output leak (hard failure - cannot be auto-corrected)
        if self.is_advisory_leak(response):
            errors.append("Advisory language detected in generated response. Falling back to safe answer.")
            return False, None, warnings + errors

        # Inject footer
        formatted = self.inject_footer(response, context_source_url)

        # Only hard errors (advisory leak) mark is_valid=False; warnings are auto-corrected
        is_valid = len(errors) == 0
        return is_valid, formatted, warnings
