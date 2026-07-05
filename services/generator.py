import os
import time
import logging
from dotenv import load_dotenv
from groq import Groq, RateLimitError, APIStatusError

# Load environment variables from .env
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Groq Free Tier Rate Limits
GROQ_RATE_LIMITS = {
    "requests_per_minute": 30,
    "requests_per_day": 1000,
    "tokens_per_minute": 12000,
    "tokens_per_day": 100000
}

# Model config
DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_OUTPUT_TOKENS = 250     # Bounded output length (keeps token usage predictable)
MAX_RETRIES = 3             # Maximum retry attempts on rate limit hit
RETRY_BASE_DELAY_SECS = 2  # Exponential backoff base (doubles each retry)

# Fallback message when all retries are exhausted
RATE_LIMIT_FALLBACK = (
    "I am currently unable to fetch the latest details due to high demand. "
    "Please try again in a few moments. "
    "You can refer directly to HDFC mutual fund details on the Groww website."
)


class MutualFundGenerator:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.client = None
        if not self.api_key or "your_groq_api_key" in self.api_key:
            logger.warning(
                "GROQ_API_KEY environment variable is missing or placeholder. "
                "The generator will return a configuration warning message for queries."
            )
        else:
            self.client = Groq(api_key=self.api_key)
        logger.info("Groq client initialized successfully.")
        logger.info(
            "Groq Rate Limits: %d req/min | %d req/day | %d tokens/min | %d tokens/day",
            GROQ_RATE_LIMITS["requests_per_minute"],
            GROQ_RATE_LIMITS["requests_per_day"],
            GROQ_RATE_LIMITS["tokens_per_minute"],
            GROQ_RATE_LIMITS["tokens_per_day"]
        )

    def _build_prompts(self, query_text, contexts):
        """Constructs the system and user prompts from retrieved context."""
        context_blocks = []
        for i, ctx in enumerate(contexts):
            meta = ctx.get("metadata", {})
            source_url = meta.get("source_url", "https://groww.in")
            context_blocks.append(
                f"Source {i+1} [URL: {source_url}]:\n{ctx['text']}"
            )
        context_str = "\n\n".join(context_blocks)

        system_prompt = (
            "You are a facts-only Q&A assistant for mutual fund schemes. Your reference context is Groww.\n"
            "Your goal is to answer user queries using ONLY the factual context provided below.\n"
            "Do not provide investment advice, recommendations, opinions, or performance projections.\n"
            "Do not make return calculations or performance comparisons. Refuse advisory queries.\n"
            "If the answer is not present in the context, state: "
            "'I am sorry, but I cannot find that information in the official documents.'\n\n"
            "Strict Formatting Constraints:\n"
            "1. Limit your answer to a maximum of 3 sentences.\n"
            "2. You must include exactly one source citation URL in your answer. "
            "This URL must be copied exactly from the context block sources. "
            "Do not hallucinate or modify the links.\n"
            "3. Keep the tone completely objective, professional, and regulatory-compliant. "
            "Avoid words like 'buy', 'sell', 'should', 'recommend', or 'better'."
        )

        user_prompt = f"Context:\n{context_str}\n\nQuery: {query_text}"
        return system_prompt, user_prompt

    def generate_response(self, query_text, contexts):
        """
        Generates a facts-only response with exponential backoff retry on Groq rate limits.
        """
        if not contexts:
            return "I am sorry, but I cannot find that information in the official documents."

        if not self.client:
            logger.error("Groq client is not configured. GROQ_API_KEY is missing or is a placeholder.")
            return (
                "The LLM backend is not configured. Please set a valid GROQ_API_KEY in the .env file "
                "and restart the server to enable AI-generated answers."
            )

        system_prompt, user_prompt = self._build_prompts(query_text, contexts)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info("Calling Groq API (attempt %d/%d)...", attempt, MAX_RETRIES)
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=DEFAULT_MODEL,
                    temperature=0.0,  # Deterministic factual response
                    max_tokens=MAX_OUTPUT_TOKENS
                )

                # Log approximate token usage
                usage = chat_completion.usage
                if usage:
                    logger.info(
                        "Groq usage - Prompt tokens: %d | Completion tokens: %d | Total: %d",
                        usage.prompt_tokens,
                        usage.completion_tokens,
                        usage.total_tokens
                    )

                return chat_completion.choices[0].message.content.strip()

            except RateLimitError as e:
                # HTTP 429: Rate limit hit
                if attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY_SECS * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    logger.warning(
                        "Groq rate limit hit (HTTP 429). Waiting %ds before retry %d/%d. Error: %s",
                        delay, attempt, MAX_RETRIES, str(e)
                    )
                    time.sleep(delay)
                else:
                    logger.error("Groq rate limit persists after %d retries. Returning fallback.", MAX_RETRIES)
                    return RATE_LIMIT_FALLBACK

            except APIStatusError as e:
                logger.error("Groq API error (status %s): %s", e.status_code, str(e))
                return f"Error communicating with Groq API (status {e.status_code}). Please try again."

            except Exception as e:
                logger.error("Unexpected error calling Groq API: %s", str(e))
                return f"An unexpected error occurred: {e}"

        return RATE_LIMIT_FALLBACK


# Simple singleton initialization helper
_generator_instance = None


def get_generator():
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = MutualFundGenerator()
    return _generator_instance
