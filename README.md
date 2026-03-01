# OSLI: Open Source License Intelligence API


**OSLI** is an intelligent compliance engine designed to bridge the gap between complex open-source legal jargon and real-world developer workflows. By combining **deterministic SPDX data** with **Gemini AI reasoning**, OSLI provides a developer experience that is predictable, correct, and delightful.

---

## 📖 Project Story

### 💡 The Inspiration
Every developer has been there: you find the perfect open-source library that solves all your problems, only to realize your company’s legal team might reject it because of a "Copyleft" clause or a restrictive license you don't fully understand. In the high-speed world of modern software engineering, **legal compliance is the ultimate bottleneck.** We built OSLI to act as a "Digital Legal Assistant," turning complex legal jargon into actionable, developer-friendly data.

### 🚀 How We Built It
OSLI is built on an "Intelligence-First" architecture.
- **The Body (FastAPI):** High-performance framework with automatic interactive documentation.
- **The Memory (SPDX Data):** Integrated official SPDX license database for deterministic lookups.
- **The Brain (Google Gemini 1.5 Flash):** Handles the "gray areas"—analyzing risks based on specific business contexts.

### 🧠 Challenges We Faced
Mapping the NPM registry's messy license metadata was our biggest hurdle. We built a robust extraction engine to normalize strings, lists, and objects into a single source of truth for our analysis engine.

---

## 🛠 Tech Stack
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Intelligence:** [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **Registry Integration:** [Httpx](https://www.python-httpx.org/)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/)

---

## 🚀 Quick Start (Localhost)

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Download the SPDX Data:**
   ```bash
   curl -o "licenses.json" "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
   ```
3. **Set your API Key:**
   ```bash
   export GEMINI_API_KEY="your_actual_key"
   ```
4. **Run the API:**
   ```bash
   uvicorn main:app --reload
   ```
   *Access the interactive docs at: http://127.0.0.1:8000/docs*

---

## 🏗 API Reference & Examples

### 🔍 Group 1: Discovery & Research

#### **1. Smart Library Search**
AI-powered library discovery based on license requirements.
```bash
curl -X POST "http://127.0.0.1:8000/v1/search" \
     -H "Content-Type: application/json" \
     -d '{ "query": "Chart library for a closed-source SaaS" }'
```
**Expected Response:**
```json
{
  "results": [
    {
      "name": "Chart.js",
      "license": "MIT",
      "reason": "Highly popular, permissive MIT license, and easy to integrate."
    },
    {
      "name": "ApexCharts",
      "license": "MIT",
      "reason": "Modern interactive charts with a commercial-friendly MIT license."
    }
  ]
}
```

#### **2. Deep-Dive License Info**
Returns official metadata for a specific SPDX license ID.
```bash
curl -X GET "http://127.0.0.1:8000/v1/licenses/MIT"
```
**Expected Response:**
```json
{
  "licenseId": "MIT",
  "name": "MIT License",
  "seeAlso": ["https://opensource.org/licenses/MIT"],
  "isOsiApproved": true,
  "isDeprecatedLicenseId": false
}
```

---

### 🛡️ Group 2: Risk & Compliance

#### **3. Analyze Package Risk**
Contextual AI risk scoring (0-100) based on your business model.
```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{ "package_name": "mongodb", "context": "Commercial closed-source SaaS" }'
```
**Expected Response:**
```json
{
  "risk_score": 85,
  "summary": "High risk due to SSPL license in a commercial SaaS context.",
  "warnings": [
    "SSPL is not OSI-approved.",
    "Potential requirement to open-source your infrastructure code."
  ]
}
```

#### **4. Audit Dependencies**
Batch "Traffic Light" scan (SAFE/WARN) for a list of packages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/audit" \
     -H "Content-Type: application/json" \
     -d '{ "dependencies": ["react", "lodash", "ffmpeg"] }'
```
**Expected Response:**
```json
{
  "results": [
    { "package": "react", "license": "MIT", "status": "SAFE" },
    { "package": "lodash", "license": "MIT", "status": "SAFE" },
    { "package": "ffmpeg", "license": "LGPL-2.1", "status": "WARN" }
  ]
}
```

#### **5. Compatibility Check**
Quick deterministic check if two licenses are compatible.
```bash
curl -X POST "http://127.0.0.1:8000/v1/compatibility-check" \
     -H "Content-Type: application/json" \
     -d '{ "license_a": "MIT", "license_b": "GPL-3.0" }'
```
**Expected Response:**
```json
{
  "compatible": true,
  "reason": "MIT is compatible with GPL-3.0."
}
```

---

### ⌨️ Group 3: Automation & DevTools

#### **6. License Header Generator**
AI-generated legal headers formatted for specific programming languages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/generate-header" \
     -H "Content-Type: application/json" \
     -d '{ "project_name": "Nebula", "license_id": "MIT", "language": "Python" }'
```
**Expected Response:**
```json
{
  "header_text": "# Copyright (c) 2026 Nebula\n# Licensed under the MIT License."
}
```

---

## ⚠️ Error Handling & Correctness

OSLI prioritizes informative feedback over generic errors. We follow standard HTTP status codes:

- **200 OK**: Request was successful.
- **400 Bad Request**: Invalid SPDX License ID or missing parameters.
- **404 Not Found**: Package not found on NPM or License ID does not exist in SPDX database.
- **500 Internal Server Error**: Issues with AI inference or upstream registry timeouts.

**Example 400 Response (Invalid License):**
```json
{
  "detail": "License ID 'Apache' is not recognized. Check https://spdx.org/licenses/ for valid IDs (e.g., 'MIT', 'Apache-2.0')."
}
```
