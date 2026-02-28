import json
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import google.generativeai as genai

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Global data
licenses_db: Dict[str, Any] = {}

# Hardcoded Compatibility Matrix (Simplified)
# MIT, Apache-2.0, GPL-2.0, GPL-3.0, BSD-3-Clause, AGPL-3.0, LGPL-3.0, MPL-2.0
# Matrix maps License A -> License B -> Compatible (True/False)
COMPATIBILITY_MATRIX = {
    "MIT": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": True, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    },
    "Apache-2.0": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": False, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": False
    },
    "GPL-2.0": {
        "MIT": True, "Apache-2.0": False, "GPL-2.0": True, "GPL-3.0": False,
        "BSD-3-Clause": True, "AGPL-3.0": False, "LGPL-3.0": True, "MPL-2.0": False
    },
    "GPL-3.0": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": False, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    },
    "BSD-3-Clause": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": True, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    },
    "AGPL-3.0": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": False, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    },
    "LGPL-3.0": {
        "MIT": True, "Apache-2.0": True, "GPL-2.0": False, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    },
    "MPL-2.0": {
        "MIT": True, "Apache-2.0": False, "GPL-2.0": True, "GPL-3.0": True,
        "BSD-3-Clause": True, "AGPL-3.0": True, "LGPL-3.0": True, "MPL-2.0": True
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load licenses on startup
    global licenses_db
    try:
        with open("licenses.json", "r") as f:
            data = json.load(f)
            # Create O(1) lookup dictionary by licenseId
            for license_info in data.get("licenses", []):
                licenses_db[license_info["licenseId"]] = license_info
        print(f"Loaded {len(licenses_db)} licenses into memory.")
    except FileNotFoundError:
        print("Warning: licenses.json not found. Please ensure it is present.")
    except json.JSONDecodeError:
        print("Error: licenses.json is invalid JSON.")
    yield

app = FastAPI(title="OSLI: Open Source License Intelligence API", lifespan=lifespan)

# Models
class CompatibilityRequest(BaseModel):
    license_a: str
    license_b: str

class CompatibilityResponse(BaseModel):
    compatible: bool
    reason: str

class AnalyzeRequest(BaseModel):
    package_name: str
    context: str

class AnalyzeResponse(BaseModel):
    risk_score: int
    summary: str
    warnings: List[str]

class AuditRequest(BaseModel):
    dependencies: List[str]

class AuditItem(BaseModel):
    package: str
    license: str
    status: str

class AuditResponse(BaseModel):
    results: List[AuditItem]

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    name: str
    license: str
    reason: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

# Helper
def extract_npm_license(package_data: dict) -> str:
    license_data = package_data.get("license") or package_data.get("licenses")
    if isinstance(license_data, dict):
        return license_data.get("type", "Unknown")
    elif isinstance(license_data, list) and len(license_data) > 0:
        return license_data[0].get("type", "Unknown") if isinstance(license_data[0], dict) else str(license_data[0])
    elif isinstance(license_data, str):
        return license_data
    return "Unknown"

# Endpoints
@app.post("/v1/compatibility-check", response_model=CompatibilityResponse)
async def compatibility_check(request: CompatibilityRequest):
    a = request.license_a
    b = request.license_b

    if a not in COMPATIBILITY_MATRIX or b not in COMPATIBILITY_MATRIX.get(a, {}):
         return CompatibilityResponse(
            compatible=False,
            reason=f"Compatibility matrix does not contain data for {a} vs {b}."
        )

    is_compatible = COMPATIBILITY_MATRIX[a][b]
    
    if is_compatible:
        reason = f"{a} is considered compatible with {b} based on general guidelines."
    else:
        reason = f"{a} may pose compatibility issues with {b}."

    return CompatibilityResponse(compatible=is_compatible, reason=reason)

@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze_package(request: AnalyzeRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing. Please set GEMINI_API_KEY.")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"https://registry.npmjs.org/{request.package_name}")
            if res.status_code == 404:
                raise HTTPException(status_code=404, detail="Package not found")
            res.raise_for_status()
            pkg_data = res.json()
            pkg_license = extract_npm_license(pkg_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch package data: {e}")

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f'''
    Analyze the risk of using the NPM package '{request.package_name}' which has the license '{pkg_license}'.
    The context of use is: '{request.context}'.
    
    Respond STRICTLY in JSON format with exactly these fields:
    - "risk_score": integer (0 to 100)
    - "summary": string
    - "warnings": array of strings
    
    Do NOT wrap the output in markdown code blocks like ```json. Output raw JSON only.
    '''
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        return AnalyzeResponse(
            risk_score=data.get("risk_score", 50),
            summary=data.get("summary", "Analysis complete."),
            warnings=data.get("warnings", [])
        )
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI inference error: {e}")


@app.post("/v1/audit", response_model=AuditResponse)
async def audit_dependencies(request: AuditRequest):
    results = []
    # Simplified status check logic
    safe_licenses = ["MIT", "Apache-2.0", "ISC", "BSD-2-Clause", "BSD-3-Clause", "WTFPL"]
    
    async with httpx.AsyncClient() as client:
        for dep in request.dependencies:
            try:
                res = await client.get(f"https://registry.npmjs.org/{dep}")
                if res.status_code == 404:
                    results.append(AuditItem(package=dep, license="Not Found", status="WARN"))
                    continue
                res.raise_for_status()
                pkg_data = res.json()
                pkg_license = extract_npm_license(pkg_data)
                
                status = "SAFE" if pkg_license in safe_licenses else "WARN"
                results.append(AuditItem(package=dep, license=pkg_license, status=status))
            except Exception:
                results.append(AuditItem(package=dep, license="Error", status="WARN"))

    return AuditResponse(results=results)


@app.post("/v1/search", response_model=SearchResponse)
async def search_libraries(request: SearchRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key is missing.")

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f'''
    Act as a Smart Search for open source libraries.
    The user wants: '{request.query}'
    
    Provide exactly 3 library suggestions.
    Respond STRICTLY in JSON format as an array of objects.
    Each object must have these exact fields:
    - "name": string
    - "license": string (typical license)
    - "reason": string (why it fits)
    
    Do NOT wrap the output in markdown code blocks like ```json. Output raw JSON only.
    '''
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        return SearchResponse(results=data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI inference error: {e}")