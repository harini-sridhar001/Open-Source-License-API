# OSLI: Open Source License Intelligence API


**OSLI** is an intelligent compliance engine designed to bridge the gap between complex open-source legal jargon and real-world developer workflows. By combining **deterministic SPDX data** (State) with **Gemini AI reasoning** (Intelligence), OSLI provides a developer experience that is predictable, correct, and delightful.

---

## 🛠 Tech Stack
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Chosen for its high performance and automatic OpenAPI/Swagger generation).
- **Intelligence:** [Google Gemini 1.5 Flash](https://ai.google.dev/) (Used for contextual risk analysis and logical reasoning).
- **State Management:** Local In-Memory SPDX Database (Loaded from `licenses.json` on startup for O(1) lookups).
- **Registry Integration:** [Httpx](https://www.python-httpx.org/) (Asynchronous fetching of real-time metadata from the NPM registry).

---

## 🌍 Live API & Documentation

The OSLI API is deployed and ready for use. You can explore the interactive documentation and test endpoints directly from your browser:

- **Interactive API Docs (Swagger UI):** [https://open-source-license-api.onrender.com/docs](https://open-source-license-api.onrender.com/docs)
- **Base API URL:** `https://open-source-license-api.onrender.com`

> **Note:** Since this is a live deployment, you can replace `http://127.0.0.1:8000` with `https://open-source-license-api.onrender.com` in any of the example `curl` commands below to test them against the production server.

---

## 🚀 Quick Start (Localhost)

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Download the State (SPDX Data):**
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

## 🏗 API Design & Reference

OSLI is organized into three logical modules. All endpoints return **JSON**.

### 🔍 Group 1: Discovery & Research
*Finding the right tools and understanding their rules.*

#### **1. Smart Library Search**
AI-powered library discovery based on license requirements.
```bash
curl -X POST "http://127.0.0.1:8000/v1/search" \
     -H "Content-Type: application/json" \
     -d '{ "query": "Chart library for closed source" }'
```

#### **2. Safe-Alternative Finder**
Finds permissive alternatives (e.g. MIT) for a restrictive library.
```bash
curl -X POST "http://127.0.0.1:8000/v1/alternatives" \
     -H "Content-Type: application/json" \
     -d '{ "package_name": "highcharts", "desired_license": "MIT" }'
```

#### **3. Deep-Dive License Info**
Returns official metadata for a specific SPDX license ID.
```bash
curl -X GET "http://127.0.0.1:8000/v1/licenses/MIT"
```

---

### 🛡️ Group 2: Risk & Compliance
*Validating dependencies and resolving legal conflicts.*

#### **4. Analyze Package Risk**
Contextual AI risk scoring (0-100) based on your business model.
```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze" \
     -H "Content-Type: application/json" \
     -d '{ "package_name": "mongodb", "context": "Commercial closed-source SaaS" }'
```

#### **5. Audit Dependencies**
Batch "Traffic Light" scan (SAFE/WARN) for a list of packages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/audit" \
     -H "Content-Type: application/json" \
     -d '{ "dependencies": ["react", "lodash", "ffmpeg"] }'
```

#### **6. Compatibility Check**
Quick deterministic check if two licenses are compatible.
```bash
curl -X POST "http://127.0.0.1:8000/v1/compatibility-check" \
     -H "Content-Type: application/json" \
     -d '{ "license_a": "MIT", "license_b": "GPL-3.0" }'
```

#### **7. Legal Patch Suggester (Conflict Resolution)**
Detects conflicts and suggests an alternative library to fix the issue.
```bash
curl -X POST "http://127.0.0.1:8000/v1/resolve-conflicts" \
     -H "Content-Type: application/json" \
     -d '{ "package_a": "ffmpeg", "package_b": "highcharts" }'
```

---

### ⌨️ Group 3: Automation & DevTools
*Streamlining legal chores during development.*

#### **8. License Header Generator**
AI-generated legal headers formatted for specific programming languages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/generate-header" \
     -H "Content-Type: application/json" \
     -d '{ "project_name": "Nebula", "license_id": "MIT", "language": "Python" }'
```

---

## ⚠️ Error Handling & Correctness

OSLI prioritizes informative feedback over generic errors. We follow standard HTTP status codes:

- **200 OK**: Request was successful.
- **400 Bad Request**: Missing parameters or invalid JSON.
- **404 Not Found**: The package name provided does not exist in the NPM registry.
- **500 Internal Server Error**: Issues with AI inference or upstream registry timeouts.

**Example 404 Response:**
```json
{
  "detail": "Package 'non-existent-lib' was not found in the NPM registry."
}
```

---

## 💡 Innovation & Utility
OSLI uses **Stateful Data** (the SPDX database) to ensure legal correctness, and **Generative AI** to provide human-readable strategy. It solves the "License Paradox": knowing a license is `GPL` is easy, but knowing *why* that's a problem for your specific codebase/project file is what OSLI delivers.
