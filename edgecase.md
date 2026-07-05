# Edge Case & Corner Scenario Analysis

This document identifies potential edge cases, risks, and mitigation strategies for the RAG-based Mutual Fund FAQ Assistant, aligned with the [System Architecture](file:///d:/RAG%20Based%20MF%20Chatbot/architecture.md) and [Project Context](file:///d:/RAG%20Based%20MF%20Chatbot/context.md).

---

## 🔍 1. Input Intent & Guardrail Edge Cases

### 1.1 Subtle or Implicit Advisory Queries
* **Scenario:** The user asks a question that implies seeking advice without using explicit trigger words (e.g., *"Is HDFC Mid-Cap safe for retirement?"* or *"Will I make money in HDFC ELSS?"*).
* **Risk:** The classifier fails to identify the advisory intent, and the retriever retrieves factual risk data, leading the LLM to construct a response that could be construed as investment advice.
* **Mitigation:**
  * Define a comprehensive list of implicit advisory patterns in the Intent Classifier prompt.
  * Any question asking for qualitative judgments (*"safe"*, *"good"*, *"better"*, *"profitable"*, *"recommended"*) must be flagged as advisory.

### 1.2 Multi-Scheme Factual Queries
* **Scenario:** The user queries factual details about two funds at once (e.g., *"What is the expense ratio of HDFC Mid-Cap vs HDFC Large Cap?"*).
* **Risk:** The assistant is constrained to provide **exactly one citation link**. Citing one fund leaves the other uncited, violating the transparency rule. Citing both violates the single-citation constraint.
* **Mitigation:**
  * **Rule:** If multiple funds are detected, the system will split the context but prioritize citing the first fund mentioned.
  * **Alternative:** The backend will intercept multi-fund factual queries and instruct the LLM to:
    1. Answer for the primary/first fund.
    2. Cite the first fund.
    3. Add a note: *"For HDFC Large Cap details, please query separately."*

### 1.3 Out-of-Corpus Factual Queries
* **Scenario:** The user asks a factual question about an HDFC fund that is NOT among the 5 specified URLs (e.g., *"What is the exit load of HDFC Gold Fund?"*).
* **Risk:** The retriever finds zero matches in the vector database, but the LLM uses its pre-trained general knowledge to answer, resulting in a hallucinated or unverified response.
* **Mitigation:**
  * Restrict database retrieval filters strictly to the 5 corpus identifiers.
  * If the vector database return score is below a strict confidence threshold (indicating no relevant context for the 5 selected funds), the system must execute an out-of-scope refusal:
    > *"I can only provide information on the 5 supported HDFC mutual fund schemes. Please visit the official HDFC AMC site for other funds."*

---

## 🔗 2. Retrieval & Citation Edge Cases

### 2.1 Ambiguous Fund References
* **Scenario:** The user asks: *"What is the exit load?"* or *"What is the benchmark?"* without specifying which of the 5 funds they mean.
* **Risk:** The retriever fetches chunks from random funds, and the LLM constructs an answer using data from one fund (e.g., HDFC Large Cap) while the user was thinking of another.
* **Mitigation:**
  * The retriever checks if the query contains a clear fund identifier (e.g., "Mid-Cap", "Flexi Cap", "Focused", "Tax Saver", "Large Cap/Top 100").
  * If no fund is identified, the system bypasses generation and asks a clarifying question:
    > *"Please specify which fund you are referring to: HDFC Mid-Cap, HDFC Flexi Cap, HDFC Focused 30, HDFC ELSS Tax Saver, or HDFC Top 100."*

### 2.2 Numerical Performance Queries
* **Scenario:** The user asks: *"How did HDFC Mid-Cap perform last year?"* or *"What are the returns of HDFC Top 100?"*
* **Risk:** Groww pages contain historical return percentages. If the LLM generates a response quoting historical returns, it might violate the constraint: *"No performance comparisons or return calculations. For performance-related queries, provide a link to the official factsheet only."*
* **Mitigation:**
  * The Intent Classifier routes return/performance-related keywords directly to a specialized performance responder.
  * The responder replies:
    > *"For historical performance and returns of HDFC Mid-Cap Opportunities Fund, please refer directly to the official factsheet: https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth."*

---

## 📝 3. Output Format Constraints

### 3.1 Sentence-Count Violation (Complex Information)
* **Scenario:** The user asks about a highly complex topic (e.g., exit load tiers: *"What is the exit load of HDFC Mid-Cap?"* which has rules for redemptions under 1 year, over 1 year, systemic transfers, etc.).
* **Risk:** The LLM fails to summarize the complex schedule within the strict **3-sentence limit**, causing the output validator to block the response.
* **Mitigation:**
  * Ingestion chunks must pre-summarize complex schedules into concise text.
  * The system prompt instructs the LLM: *"If the schedule is complex, summarize the main rule and refer to the source URL for detailed tiers."*
  * If the post-validator detects $>3$ sentences, it falls back to a pre-defined safe summary or attempts a second fast LLM call with a stronger compression prompt.

### 3.2 URL Validation Failures
* **Scenario:** The LLM hallucinates a source URL, outputs a broken link, or references a general Groww homepage instead of the specific scheme page.
* **Risk:** The output contains a citation that is invalid or does not match the actual page from which the data was retrieved.
* **Mitigation:**
  * **Link Whitelisting:** The post-validator compares the generated URL against the list of 5 allowed Groww URLs.
  * If the URL doesn't match the whitelist, the validator replaces it with the correct whitelisted URL for that specific fund.

---

## 🔒 4. PII & Security Edge Cases

### 4.1 Masking Folio & Transaction Numbers
* **Scenario:** A user asks: *"Why is my transaction status for folio 1234/567 pending?"*
* **Risk:** The system receives and processes sensitive account details (PII), violating privacy constraints.
* **Mitigation:**
  * In addition to scanning for PAN, Aadhaar, phone numbers, and emails, the PII filter must mask standard folio formats, transaction IDs, and any numeric sequence of 6 or more digits.
  * Replacement rule: Replace matches with `[REDACTED]`.

---

## ⚡ 5. API Latency & Reliability

### 5.1 Groq API Rate Limiting (HTTP 429)
* **Scenario:** Under heavy user traffic, the Groq API rate limits are hit.
* **Risk:** The chat interface hangs or displays raw API error codes to the user.
* **Groq Free Tier Limits (as of 2026):**

  | Limit Type        | Value    |
  |-------------------|----------|
  | Requests/minute   | 30       |
  | Requests/day      | 1,000    |
  | Tokens/minute     | 12,000   |
  | Tokens/day        | 100,000  |

* **Mitigation:**
  * `services/generator.py` implements **exponential backoff** on `HTTP 429 RateLimitError`:
    * Retry 1: wait **2 seconds**
    * Retry 2: wait **4 seconds**
    * Retry 3: wait **8 seconds**
    * After 3 failed retries, return a static fallback response.
  * Token usage is logged at every API call (`prompt_tokens`, `completion_tokens`, `total_tokens`) for future monitoring.
  * `max_tokens=250` per call keeps per-request token consumption bounded and predictable.
  * If retries fail, return a polite, pre-formatted static response:
    > *"I am currently unable to fetch the latest details due to high demand. Please try again in a few moments. You can refer directly to HDFC mutual fund details on the Groww website."*
