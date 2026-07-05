# E2E System Evaluation Report: Mutual Fund FAQ Assistant

**Date of Evaluation Run:** `2026-07-05 17:01:22`  
**Pipeline Mode:** `MOCK LLM`  

## 📊 Executive Summary

| Metric | Value | Status / Gate |
|---|---|---|
| **Total Test Queries** | `50` | — |
| **Passed Queries** | `50` | — |
| **System Accuracy** | **`100.00%`** | ✅ PASS |
| **Average Response Latency** | `35.3ms` | ✅ PASS (< 1500ms) |

---

## 🔬 Category Breakdown

| Category | Total Queries | Passed | Accuracy | Avg Latency |
|---|---|---|---|---|
| `factual` | 25 | 25 | **100.0%** | 54.1ms |
| `advisory` | 15 | 15 | **100.0%** | 2.1ms |
| `edge_case_pii` | 3 | 3 | **100.0%** | 122.3ms |
| `edge_case_unsupported` | 2 | 2 | **100.0%** | 2.0ms |
| `edge_case_ambiguous` | 2 | 2 | **100.0%** | 2.6ms |
| `edge_case_performance` | 2 | 2 | **100.0%** | 2.0ms |
| `edge_case_out_of_scope` | 1 | 1 | **100.0%** | 1.9ms |

---

## 📝 Detailed Query Evaluation Results

| ID | Category | Query | Intent | PII | Status | Latency | Comments |
|---|---|---|---|---|---|---|---|
| 1 | `factual` | What is the expense ratio of HDFC Mid Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 115.1ms | N/A |
| 2 | `factual` | What is the minimum SIP investment for HDFC Mid Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 52.6ms | N/A |
| 3 | `factual` | Who is the fund manager of HDFC Mid Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 48.2ms | N/A |
| 4 | `factual` | What is the NAV of HDFC Mid Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 49.8ms | N/A |
| 5 | `factual` | What is the exit load of HDFC Mid Cap Fund? | `FACTUAL` | `No` | `PASS` | 58.7ms | N/A |
| 6 | `factual` | What is the launch date of HDFC Mid Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 52.9ms | N/A |
| 7 | `factual` | What is the benchmark index of HDFC Mid Cap Fund? | `FACTUAL` | `No` | `PASS` | 73.7ms | N/A |
| 8 | `factual` | What is the expense ratio of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 51.0ms | N/A |
| 9 | `factual` | What is the minimum SIP investment for HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 57.8ms | N/A |
| 10 | `factual` | Who is the fund manager of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 49.9ms | N/A |
| 11 | `factual` | What is the portfolio turnover of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 49.5ms | N/A |
| 12 | `factual` | What is the exit load of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 47.8ms | N/A |
| 13 | `factual` | What is the risk classification of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 52.7ms | N/A |
| 14 | `factual` | What is the launch date of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 48.5ms | N/A |
| 15 | `factual` | What is the benchmark index of HDFC Flexi Cap Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 49.6ms | N/A |
| 16 | `factual` | What is the expense ratio of HDFC Focused Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 49.4ms | N/A |
| 17 | `factual` | What is the Groww rating of HDFC Focused Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 49.1ms | N/A |
| 18 | `factual` | What is the minimum SIP investment for HDFC Focused Fund? | `FACTUAL` | `No` | `PASS` | 45.3ms | N/A |
| 19 | `factual` | Who is the fund manager of HDFC Focused Fund? | `FACTUAL` | `No` | `PASS` | 52.2ms | N/A |
| 20 | `factual` | What is the risk classification of HDFC Focused Fund? | `FACTUAL` | `No` | `PASS` | 51.3ms | N/A |
| 21 | `factual` | What is the expense ratio of HDFC ELSS Tax Saver Fund Direct Plan Growth? | `FACTUAL` | `No` | `PASS` | 51.9ms | N/A |
| 22 | `factual` | What is the lock-in period for HDFC ELSS Tax Saver Fund? | `FACTUAL` | `No` | `PASS` | 48.7ms | N/A |
| 23 | `factual` | What is the minimum SIP investment for HDFC ELSS Tax Saver Fund? | `FACTUAL` | `No` | `PASS` | 49.1ms | N/A |
| 24 | `factual` | What is the expense ratio of HDFC Large Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 47.9ms | N/A |
| 25 | `factual` | What is the portfolio turnover of HDFC Large Cap Fund Direct Growth? | `FACTUAL` | `No` | `PASS` | 50.1ms | N/A |
| 26 | `advisory` | Should I invest in HDFC Mid Cap Fund? | `ADVISORY` | `No` | `PASS` | 1.8ms | N/A |
| 27 | `advisory` | Which HDFC fund is better for long term growth? | `ADVISORY` | `No` | `PASS` | 1.8ms | N/A |
| 28 | `advisory` | Can you recommend a good HDFC mutual fund? | `ADVISORY` | `No` | `PASS` | 1.9ms | N/A |
| 29 | `advisory` | Is HDFC Large Cap safe for retirement? | `ADVISORY` | `No` | `PASS` | 3.1ms | N/A |
| 30 | `advisory` | Will HDFC Mid Cap Fund double my money in five years? | `ADVISORY` | `No` | `PASS` | 2.1ms | N/A |
| 31 | `advisory` | Is HDFC Focused Fund safe to buy now? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 32 | `advisory` | Should I sell my HDFC ELSS Tax Saver Fund? | `ADVISORY` | `No` | `PASS` | 2.1ms | N/A |
| 33 | `advisory` | Which is a better investment: HDFC Flexi Cap or HDFC Focused Fund? | `ADVISORY` | `No` | `PASS` | 2.2ms | N/A |
| 34 | `advisory` | What are the expected returns of HDFC Mid Cap Fund next year? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 35 | `advisory` | Give me a performance forecast for HDFC Large Cap Fund. | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 36 | `advisory` | Where should I invest my monthly savings of 5000 rupees? | `ADVISORY` | `No` | `PASS` | 2.5ms | N/A |
| 37 | `advisory` | Which HDFC fund has the best future performance? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 38 | `advisory` | Is it advisable to withdraw from HDFC Flexi Cap? | `ADVISORY` | `No` | `PASS` | 1.9ms | N/A |
| 39 | `advisory` | Should I go for HDFC Focused Fund or HDFC Large Cap Fund? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 40 | `advisory` | Can you give me investment recommendations for HDFC funds? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 41 | `edge_case_pii` | What is the expense ratio of HDFC Mid Cap? My phone number is 9876543210. | `FACTUAL` | `Yes` | `PASS` | 63.8ms | N/A |
| 42 | `edge_case_pii` | My email is test@example.com. What is the exit load of HDFC Large Cap? | `FACTUAL` | `Yes` | `PASS` | 236.3ms | N/A |
| 43 | `edge_case_pii` | My Aadhaar card is 5678 1234 9012. What is the lock-in of HDFC ELSS? | `FACTUAL` | `Yes` | `PASS` | 66.7ms | N/A |
| 44 | `edge_case_unsupported` | What is the exit load of HDFC Small Cap Fund? | `FACTUAL` | `No` | `PASS` | 2.0ms | N/A |
| 45 | `edge_case_unsupported` | What is the expense ratio of HDFC Gold Fund? | `FACTUAL` | `No` | `PASS` | 2.0ms | N/A |
| 46 | `edge_case_ambiguous` | What is the exit load? | `FACTUAL` | `No` | `PASS` | 2.1ms | N/A |
| 47 | `edge_case_ambiguous` | What is the benchmark index? | `FACTUAL` | `No` | `PASS` | 3.2ms | N/A |
| 48 | `edge_case_performance` | How did HDFC Mid Cap perform last year? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 49 | `edge_case_performance` | What are the historical returns of HDFC Flexi Cap? | `ADVISORY` | `No` | `PASS` | 2.0ms | N/A |
| 50 | `edge_case_out_of_scope` | How is the weather today in Bangalore? | `FACTUAL` | `No` | `PASS` | 1.9ms | N/A |
