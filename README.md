# OSLI: Open Source License Intelligence API


**OSLI** is an intelligent compliance engine designed to bridge the gap between complex open-source legal jargon and real-world developer workflows. By combining **deterministic SPDX data** with **Gemini AI reasoning**, OSLI provides a developer experience that is predictable, correct, and delightful.

---

## OSLI API Access & Documentation
The OSLI API is officially deployed and ready for use. You can explore the endpoints, view data schemas, and test requests directly from your browser.

Official Website & Full Documentation: https://osli-doc-web-page.harinis4.workers.dev

Interactive API Docs (Swagger UI): https://open-source-license-api.onrender.com/docs

Base API URL: https://open-source-license-api.onrender.com

### 💡 The Inspiration
Every developer has been there: you find the perfect open-source library that solves all your problems, only to realize your company’s legal team might reject it because of a "Copyleft" clause or a restrictive license you don't fully understand. In the high-speed world of modern software engineering, **legal compliance is the ultimate bottleneck.** We built OSLI to act as a "Digital Legal Assistant," turning complex legal jargon into actionable, developer-friendly data.

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
AI-powered library discovery based on specific functionality and license needs.
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

#### **2. Safe-Alternative Finder**
Finds permissive alternatives (e.g., MIT) for a specific restrictive library.
```bash
curl -X POST "http://127.0.0.1:8000/v1/alternatives" \
     -H "Content-Type: application/json" \
     -d '{ "package_name": "highcharts", "desired_license": "MIT" }'
```
**Expected Response:**
```json
{
  "results": [
    {
      "name": "ApexCharts",
      "license": "MIT",
      "reason": "Direct alternative with similar feature set and MIT license."
    },
    {
      "name": "Chart.js",
      "license": "MIT",
      "reason": "Standard for simple interactive charts with an MIT license."
    }
  ]
}
```

#### **3. Deep-Dive License Info**
Returns official SPDX metadata for a specific license ID.
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

#### **4. Analyze Package Risk**
Contextual AI risk scoring (0-100) based on your specific business context.
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

#### **5. Audit Dependencies**
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
    { "package": "ffmpeg", "license": "LGPL-2.1", "status": "WARN" }
  ]
}
```

#### **6. Compatibility Check**
Quick deterministic check if two licenses are legally compatible.
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

#### **7. Conflict Resolution (Legal Patch)**
AI-powered tool to resolve license conflicts between two packages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/resolve-conflicts" \
     -H "Content-Type: application/json" \
     -d '{ "package_a": "ffmpeg", "package_b": "highcharts" }'
```
**Expected Response:**
```json
{
  "has_conflict": true,
  "conflict_reason": "Highcharts commercial license conflicts with LGPL-2.1 requirements.",
  "suggested_alternative": "ApexCharts",
  "alternative_license": "MIT",
  "explanation": "Replacing Highcharts with ApexCharts resolves the conflict."
}
```

---

### ⌨️ Group 3: Automation & DevTools

#### **8. License Header Generator**
Generates a professional legal header for source files.
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
- **404 Not Found**: Package not found on NPM or License ID does not exist.
- **500 Internal Error**: Issues with AI inference or registry timeouts.

**Example 400 Response (Invalid License):**
```json
{
  "detail": "License ID 'Apache' is not recognized. Check https://spdx.org/licenses/ for valid IDs (e.g., 'MIT', 'Apache-2.0')."
}
```
