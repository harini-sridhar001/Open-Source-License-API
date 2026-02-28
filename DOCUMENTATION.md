# OSLI: Open Source License Intelligence API

OSLI is an intelligent API designed to analyze, audit, and provide intelligent suggestions regarding open source licenses. It leverages deterministic local data (SPDX license definitions) alongside Google's Generative AI (Gemini Flash) to offer contextual intelligence.

## Setup Instructions

1. **Install dependencies:** `pip install -r requirements.txt`
2. **Download data:** `curl -o "licenses.json" "https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json"`
3. **Set API Key:** `export GEMINI_API_KEY="your_api_key_here"`
4. **Run Server:** `uvicorn main:app --reload`

---

## Example `curl` Commands

### 1. Compatibility Check
Checks if two licenses are generally compatible.
```bash
curl -X POST "http://127.0.0.1:8000/v1/compatibility-check" 
     -H "Content-Type: application/json" 
     -d '{ "license_a": "MIT", "license_b": "GPL-3.0" }'
```

### 2. Analyze Package Risk
AI-driven analysis of a package's license given a specific business context.
```bash
curl -X POST "http://127.0.0.1:8000/v1/analyze" 
     -H "Content-Type: application/json" 
     -d '{ "package_name": "ffmpeg", "context": "Commercial SaaS" }'
```

### 3. Audit Dependencies
Scans a list of NPM packages and flags potentially risky licenses.
```bash
curl -X POST "http://127.0.0.1:8000/v1/audit" 
     -H "Content-Type: application/json" 
     -d '{ "dependencies": ["react", "lodash", "express"] }'
```

### 4. Smart Library Search
AI-powered library discovery based on a natural language query and license requirements.
```bash
curl -X POST "http://127.0.0.1:8000/v1/search" 
     -H "Content-Type: application/json" 
     -d '{ "query": "Chart library for closed source" }'
```

### 5. Safe-Alternative Finder
Finds friendly alternatives (e.g., MIT) for a specific restrictive library.
```bash
curl -X POST "http://127.0.0.1:8000/v1/alternatives" 
     -H "Content-Type: application/json" 
     -d '{ "package_name": "highcharts", "desired_license": "MIT" }'
```

### 6. License Header Generator
AI-generated legal headers formatted for specific programming languages.
```bash
curl -X POST "http://127.0.0.1:8000/v1/generate-header" 
     -H "Content-Type: application/json" 
     -d '{ "project_name": "Nebula-Cloud", "license_id": "Apache-2.0", "language": "Python" }'
```

### 7. Deep-Dive License Info
Returns official metadata for a specific SPDX license ID.
```bash
curl -X GET "http://127.0.0.1:8000/v1/licenses/MIT"
```
