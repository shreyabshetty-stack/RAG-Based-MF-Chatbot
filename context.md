# Project Context: Mutual Fund FAQ Assistant (Facts-Only Q&A)

This document establishes the context, objectives, requirements, and constraints of the **RAG-based Mutual Fund FAQ Assistant**, derived from the [Problem Statement](file:///d:/RAG%20Based%20MF%20Chatbot/docs/problemstatement.txt).

---

## 📌 Project Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant answers objective, verifiable queries by retrieving information exclusively from official public sources, such as:
* Asset Management Company (AMC) websites
* Association of Mutual Funds in India (AMFI)
* Securities and Exchange Board of India (SEBI)

> [!IMPORTANT]
> **No Investment Advice:** The assistant must strictly avoid providing investment advice, opinions, recommendations, or performance comparisons. Every response must be objective, factual, concise, and backed by a single, verified source link.

---

## 🎯 Objectives

Implement a lightweight, Retrieval-Augmented Generation (RAG) assistant that:
1. **Factual Q&A:** Answers factual questions about specific mutual fund schemes using official documents.
2. **Curated Corpus:** Operates on a specific corpus of official URLs.
3. **Traceability:** Provides concise, source-backed answers with citation links.

---

## 👥 Target Users

* **Retail Investors:** Comparing mutual fund schemes and seeking factual data.
* **Customer Support & Content Teams:** Seeking to resolve repetitive mutual fund queries efficiently.

---

## 🛠️ Scope of Work

### 1. Corpus Definition
Use the following 5 official Groww scheme URLs for the dataset:
* [HDFC Mid-Cap Opportunities Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth)
* [HDFC Flexi Cap Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth)
* [HDFC Focused 30 Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth)
* [HDFC ELSS Tax Saver Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth)
* [HDFC Top 100 Fund (Direct Growth)](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth)

### 2. FAQ Assistant Requirements
* **Factual Scope:** Answer details like:
  * Expense ratio
  * Exit load
  * Minimum SIP amount
  * ELSS lock-in period
  * Riskometer classification
  * Benchmark index
  * Account statement/tax report download steps
* **Response Guidelines:**
  * Max **3 sentences** per answer.
  * Exactly **one citation link** per response.
  * Mandatory footer format: `Last updated from sources: <date>`

### 3. Refusal & Guardrails
* **Advisory Queries:** Must refuse queries like *"Should I invest in this fund?"* or *"Which fund is better?"*
* **Refusal Response Style:** 
  * Polite, clear, and reinforcing the facts-only constraint.
  * Provide an educational link (e.g., to AMFI or SEBI resources).

### 4. User Interface (Minimalist)
* A welcoming landing page or chat area.
* Three pre-defined example questions to guide the user.
* Highly visible disclaimer: **“Facts-only. No investment advice.”**

---

## ⚠️ Constraints & Compliance

> [!WARNING]
> Adhering to these constraints is critical for financial regulatory compliance and user trust.

* **Data Verification:** Only use official AMC, AMFI, or SEBI sources. Third-party blogs, forums, or aggregator websites are strictly prohibited.
* **Privacy & PII Security:** Do **not** collect, store, or process:
  * PAN / Aadhaar numbers
  * Bank account details
  * OTPs
  * Email addresses or phone numbers
* **No Speculation:** Performance queries must refer users to the official factsheet link instead of doing custom return calculations or comparisons.

---

## 🏆 Success Criteria

* **Accuracy:** Retrieval accuracy of facts matching the source corpus.
* **Compliance:** Zero instances of advisory outputs or recommendations.
* **Format Adherence:** Every answer contains exactly one citation and the correct footer format.
* **UI/UX:** Minimalist, clean, and intuitive layout.
