import os
import sys
import json
import time
import re
from datetime import datetime
from unittest.mock import patch

# Ensure the root directory is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastapi.testclient import TestClient
    from main import app
    from services.generator import MutualFundGenerator
except Exception as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

GOLDEN_DATASET_PATH = "tests/golden_dataset.json"
RAW_FUNDS_PATH = "data/raw_funds.json"
EVAL_SUMMARY_PATH = "data/eval_summary.md"

# Load raw funds data to generate realistic factual answers
if not os.path.exists(RAW_FUNDS_PATH):
    print(f"Error: Raw funds JSON not found at {RAW_FUNDS_PATH}. Please run scrape script first.")
    sys.exit(1)

with open(RAW_FUNDS_PATH, "r", encoding="utf-8") as f:
    RAW_FUNDS = json.load(f)


def mock_generate_response(self, query_text, contexts):
    """
    Generates a deterministic factual response based on the top retrieved context's fund name.
    Matches the schema parameters of HDFC funds in raw_funds.json.
    """
    if not contexts:
        return "I am sorry, but I cannot find that information in the official documents."

    # Get metadata from the top retrieved context
    meta = contexts[0].get("metadata", {})
    fund_name = meta.get("fund_name", "")
    source_url = meta.get("source_url", "https://groww.in")

    # Clean query for matching
    q = query_text.lower()

    # Find matching fund in raw_funds.json
    fund_details = None
    for f in RAW_FUNDS:
        # Check if the scheme name or parts of it match
        if (f["scheme_name"].strip().lower() == fund_name.strip().lower() or
                fund_name.strip().lower() in f["scheme_name"].strip().lower() or
                f["scheme_name"].strip().lower() in fund_name.strip().lower()):
            fund_details = f
            break

    if not fund_details:
        return f"I am sorry, but I cannot find details for {fund_name}."

    url = fund_details["source_url"]

    # Generate mock LLM answer matching the query intent
    if "expense ratio" in q:
        val = fund_details.get("expense_ratio") or "0.75%"
        return f"The expense ratio of {fund_details['scheme_name']} is {val}. You can read more about it at {url}."
    elif "minimum sip" in q or "min sip" in q:
        val = fund_details.get("min_sip_investment") or "100"
        return f"The minimum SIP investment amount is INR {val}. For more details, visit {url}."
    elif "manager" in q:
        val = fund_details.get("fund_manager") or "the fund manager"
        return f"The scheme is managed by {val}. Check {url} for additional manager profiles."
    elif "isin" in q:
        val = fund_details.get("isin") or "N/A"
        return f"The ISIN code for the scheme is {val}. Refer to {url} for confirmation."
    elif "exit load" in q:
        val = fund_details.get("exit_load") or "Nil"
        return f"The exit load is: {val} Visit {url} for details."
    elif "launch date" in q:
        val = fund_details.get("launch_date") or "01-Jan-2013"
        return f"The launch date of this direct plan is {val}. For details, check {url}."
    elif "benchmark" in q:
        val = fund_details.get("benchmark_index") or "benchmark"
        return f"The benchmark index of the fund is {val}. Check details at {url}."
    elif "risk" in q:
        val = fund_details.get("risk_classification") or "Moderately High"
        return f"The risk classification is {val}. Visit {url} to view the riskometer."
    elif "lock-in" in q or "lock in" in q:
        val = fund_details.get("elss_lock_in") or "Nil"
        return f"The lock-in period for this fund is {val}. More details can be found at {url}."
    elif "nav" in q:
        nav_val = fund_details.get("nav") or "229.594"
        nav_date = fund_details.get("nav_date") or "03-Jul-2026"
        return f"The Net Asset Value (NAV) of {fund_details['scheme_name']} is {nav_val} INR as of {nav_date}. You can find more details at {url}."
    elif "turnover" in q:
        val = fund_details.get("portfolio_turnover") or "13"
        return f"The portfolio turnover ratio of {fund_details['scheme_name']} is {val}%. For details, visit {url}."
    elif "face value" in q:
        val = fund_details.get("face_value") or "10"
        return f"The face value of the fund units is {val} INR. Refer to {url} for confirmation."
    elif "rating" in q or "star" in q:
        val = fund_details.get("groww_rating") or "5"
        return f"The scheme has a Groww rating of {val} Stars. Check details at {url}."
    elif "statement" in q or "report" in q or "download" in q:
        return f"To download capital gains statements, please log in to the Groww platform. Visit {url} for support."
    else:
        return f"The requested scheme information for {fund_details['scheme_name']} can be viewed at {url}."


def main():
    if not os.path.exists(GOLDEN_DATASET_PATH):
        print(f"Error: Golden dataset not found at {GOLDEN_DATASET_PATH}.")
        sys.exit(1)

    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    tests = dataset.get("tests", [])
    print(f"Loaded {len(tests)} test cases from {GOLDEN_DATASET_PATH}.\n")

    print("Initializing FastAPI TestClient and loading components...")
    
    # We apply patch to mock LLM generation if GROQ_API_KEY is not a real key
    api_key = os.getenv("GROQ_API_KEY", "")
    use_mock_llm = not api_key or "your_groq_api_key" in api_key or os.getenv("FORCE_MOCK_LLM") == "1"
    
    if use_mock_llm:
        print("[MOCK MODE] Emulating LLM generation and classification offline.")
        generator_patch = patch.object(MutualFundGenerator, "generate_response", mock_generate_response)
        generator_patch.start()
        from services.classifier import MutualFundClassifier
        classifier_patch = patch.object(MutualFundClassifier, "__init__", lambda self_obj: setattr(self_obj, "client", None) or setattr(self_obj, "api_key", None))
        classifier_patch.start()
    else:
        print("[REAL MODE] GROQ_API_KEY is configured. Invoking real Groq API.")

    results = []
    category_metrics = {}

    # Context manager to trigger lifespan events
    with TestClient(app) as client:
        print("\nStarting evaluation run...")
        for t in tests:
            query_id = t["id"]
            query = t["query"]
            category = t["category"]
            expected_intent = t["expected_intent"]
            keywords = t["keywords"]

            # Run with latency measurement
            start_time = time.time()
            response = client.post("/api/chat", json={"message": query})
            latency = time.time() - start_time

            status_code = response.status_code
            if status_code != 200:
                print(f"[{query_id}] FAIL - HTTP status code {status_code}")
                results.append({
                    "id": query_id,
                    "query": query,
                    "category": category,
                    "status": "FAIL",
                    "latency_ms": latency * 1000,
                    "error": f"HTTP status code {status_code}",
                    "answer": "",
                    "intent": "ERROR",
                    "pii_detected": False
                })
                continue

            data = response.json()
            answer = data["answer"]
            intent = data["intent"]
            pii_detected = data["pii_detected"]
            warnings = data["validation_warnings"]
            source_url = data["source_url"]

            # Validation assertions
            passed = True
            failure_reasons = []

            # 1. Intent check
            if intent != expected_intent:
                passed = False
                failure_reasons.append(f"Expected intent '{expected_intent}' but got '{intent}'")

            # 2. PII scrub check (if query is edge_case_pii, PII should be detected)
            if "edge_case_pii" in category and not pii_detected:
                passed = False
                failure_reasons.append("Expected PII to be detected but it was not")

            # 3. Check for keywords
            for kw in keywords:
                # Allow matching redacted placeholders
                if kw.lower() not in answer.lower():
                    # Handle special edge case: when we expect redacted placeholder but it can be in the answer/redacted text
                    if kw.startswith("[REDACTED"):
                        # If PII was scrubbed, let's verify if pii_detected is True
                        if not pii_detected:
                            passed = False
                            failure_reasons.append(f"Expected scrubbed PII but no PII detected")
                    else:
                        passed = False
                        failure_reasons.append(f"Missing expected keyword '{kw}' in response")

            # 4. Check for maximum sentences (<=3 for factual schemes, refusal doesn't strictly have to check it but we still do)
            if intent == "FACTUAL":
                # Temporarily mask URLs and count sentences
                masked = re.sub(r"https?://[^\s)>\]\"']+", "__URL__", answer)
                # Strip the footer
                body = masked.split("Last updated from sources")[0].strip()
                # Strip source parenthetical
                body = re.sub(r"\s*\(Source:\s*[^\)]+\)\s*$", "", body)
                sentences = re.split(r"(?<=[.!?])\s+", body.strip())
                sentences = [s for s in sentences if s.strip()]
                sentence_count = len(sentences)
                if sentence_count > 3:
                    passed = False
                    failure_reasons.append(f"Factual answer has {sentence_count} sentences (max 3 allowed)")

            # 5. Check for exact one citation URL if FACTUAL
            if intent == "FACTUAL" and source_url:
                urls = re.findall(r"https?://[^\s)>\]\"']+", answer)
                # Filter to unique whitelisted URLs
                unique_urls = list(set(urls))
                if len(unique_urls) != 1:
                    passed = False
                    failure_reasons.append(f"Expected exactly 1 citation URL, but found {len(unique_urls)}: {unique_urls}")
                elif source_url not in unique_urls[0]:
                    passed = False
                    failure_reasons.append(f"Citation URL '{unique_urls[0]}' does not match primary source '{source_url}'")

            # Record category metrics
            if category not in category_metrics:
                category_metrics[category] = {"total": 0, "passed": 0, "latency_sum": 0}
            category_metrics[category]["total"] += 1
            category_metrics[category]["latency_sum"] += latency
            if passed:
                category_metrics[category]["passed"] += 1

            status_str = "PASS" if passed else "FAIL"
            print(f"[{query_id}] Category: {category:20} | Status: {status_str:4} | Latency: {latency*1000:6.1f}ms | Query: {query[:50]}")
            if not passed:
                print(f"      Reasons: {', '.join(failure_reasons)}")

            results.append({
                "id": query_id,
                "query": query,
                "category": category,
                "status": status_str,
                "latency_ms": latency * 1000,
                "reasons": failure_reasons,
                "answer": answer,
                "intent": intent,
                "pii_detected": pii_detected
            })

    if use_mock_llm:
        generator_patch.stop()

    # Aggregate overall stats
    total_queries = len(tests)
    passed_queries = sum(1 for r in results if r["status"] == "PASS")
    overall_accuracy = (passed_queries / total_queries) * 100
    avg_latency_ms = (sum(r["latency_ms"] for r in results) / total_queries)

    print(f"\n==========================================")
    print(f"Evaluation Run Complete")
    print(f"Overall Accuracy : {overall_accuracy:.2f}% ({passed_queries}/{total_queries})")
    print(f"Average Latency  : {avg_latency_ms:.1f}ms")
    print(f"==========================================\n")

    # Generate the Markdown Report (eval_summary.md)
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = f"""# E2E System Evaluation Report: Mutual Fund FAQ Assistant

**Date of Evaluation Run:** `{today_str}`  
**Pipeline Mode:** `{"MOCK LLM" if use_mock_llm else "REAL GROQ API"}`  

## 📊 Executive Summary

| Metric | Value | Status / Gate |
|---|---|---|
| **Total Test Queries** | `{total_queries}` | — |
| **Passed Queries** | `{passed_queries}` | — |
| **System Accuracy** | **`{overall_accuracy:.2f}%`** | {"✅ PASS" if overall_accuracy >= 95 else "⚠️ WARNING (Target >= 95%)"} |
| **Average Response Latency** | `{avg_latency_ms:.1f}ms` | {"✅ PASS (< 1500ms)" if avg_latency_ms < 1500 else "❌ FAIL (>= 1500ms)"} |

---

## 🔬 Category Breakdown

| Category | Total Queries | Passed | Accuracy | Avg Latency |
|---|---|---|---|---|
"""
    for cat, metrics in category_metrics.items():
        cat_acc = (metrics["passed"] / metrics["total"]) * 100
        cat_avg_lat = (metrics["latency_sum"] / metrics["total"]) * 1000
        report += f"| `{cat}` | {metrics['total']} | {metrics['passed']} | **{cat_acc:.1f}%** | {cat_avg_lat:.1f}ms |\n"

    report += """
---

## 📝 Detailed Query Evaluation Results

| ID | Category | Query | Intent | PII | Status | Latency | Comments |
|---|---|---|---|---|---|---|---|
"""
    for r in results:
        reasons_str = "; ".join(r.get("reasons", [])) if r.get("reasons") else "N/A"
        query_snippet = r["query"].replace("|", "\\|")
        # Truncate comment if too long
        report += f"| {r['id']} | `{r['category']}` | {query_snippet} | `{r['intent']}` | `{'Yes' if r['pii_detected'] else 'No'}` | `{'PASS' if r['status'] == 'PASS' else 'FAIL'}` | {r['latency_ms']:.1f}ms | {reasons_str} |\n"

    # Write report
    os.makedirs(os.path.dirname(EVAL_SUMMARY_PATH), exist_ok=True)
    with open(EVAL_SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report written successfully to {EVAL_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
