# OSLI: Open Source License Intelligence API

OSLI is an intelligent API designed to analyze, audit, and provide intelligent suggestions regarding open source licenses. It leverages deterministic local data (SPDX license definitions) alongside Google's Generative AI (Gemini Flash) to offer contextual intelligence.

## Why OSLI is Better Than a Generic Google Search
A typical Google search provides disjointed information about a license, which you then have to manually map to your specific business context (e.g., "SaaS startup"). OSLI solves this by combining **deterministic data** (the SPDX License List for standardized reference and local compatibility matrices) with **AI context** (Gemini Flash). This hybrid approach provides direct, structured answers about compatibility, risk, and alternative libraries tailored to your specific use case.

## Setup Instructions

1. **Clone the repository** (or navigate to your project folder).
2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Download the Licenses Data:**
   The application requires the SPDX licenses list (`licenses.json`). Ensure it is downloaded into the project root:
   ```bash
   curl -o "licenses.json" "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"
   ```
4. **Set your Gemini API Key:**
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```
5. **Run the Server:**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`.

## Example `curl` Commands

### 1. Compatibility Check
Checks if two licenses are generally compatible (if an application using `license_a` can depend on a library using `license_b`).

```bash
curl -X POST "http://127.0.0.1:8000/v1/compatibility-check" 
     -H "Content-Type: application/json" 
     -d '{ "license_a": "MIT", "license_b": "GPL-3.0" }'
```

### 2. Analyze Package Risk
Fetches a specific package's license from NPM and uses AI to analyze its risk given a specific use context.

```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze" 
     -H "Content-Type: application/json" 
     -d '{ "package_name": "ffmpeg", "context": "SaaS startup" }'
```

### 3. Audit Dependencies
Loops through an array of NPM dependencies and checks their licenses to flag potentially risky ones.

```bash
curl -X POST "http://127.0.0.1:8000/v1/audit" 
     -H "Content-Type: application/json" 
     -d '{ "dependencies": ["react", "lodash", "express"] }'
```

### 4. Smart Library Search
Uses AI to suggest libraries based on your query, along with their typical licenses and why they fit.

```bash
curl -X POST "http://127.0.0.1:8000/v1/search" 
     -H "Content-Type: application/json" 
     -d '{ "query": "Chart library for closed source" }'
```
