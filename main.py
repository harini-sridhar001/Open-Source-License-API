import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import httpx
import google.generativeai as genai

# --- Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# --- Global data ---
licenses_db: Dict[str, Any] = {}

# Hardcoded Compatibility Matrix (Simplified)
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
    global licenses_db
    try:
        with open("licenses.json", "r") as f:
            data = json.load(f)
            for license_info in data.get("licenses", []):
                licenses_db[license_info["licenseId"]] = license_info
        print(f"Loaded {len(licenses_db)} licenses into memory.")
    except FileNotFoundError:
        print("Warning: licenses.json not found.")
    except json.JSONDecodeError:
        print("Error: licenses.json is invalid JSON.")
    yield

app = FastAPI(
    title="OSLI: Open Source License Intelligence API",
    description="Intelligent tools for license analysis, risk assessment, and legal automation.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for the hackathon
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

# Discovery Models
class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    name: str
    license: str
    reason: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

class AlternativesRequest(BaseModel):
    package_name: str
    desired_license: str

class AlternativeResult(BaseModel):
    name: str
    license: str
    reason: str

class AlternativesResponse(BaseModel):
    results: List[AlternativeResult]

class LicenseInfoResponse(BaseModel):
    licenseId: str
    name: str
    seeAlso: List[str]
    isOsiApproved: bool
    isDeprecatedLicenseId: bool
    licenseText: Optional[str] = None

# Risk & Compliance Models
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

class ConflictResolutionRequest(BaseModel):
    package_a: str
    package_b: str
    context: Optional[str] = "Commercial SaaS"

class ConflictResolutionResponse(BaseModel):
    has_conflict: bool
    conflict_reason: Optional[str] = None
    suggested_alternative: Optional[str] = None
    alternative_license: Optional[str] = None
    explanation: str

# Automation Models
class HeaderRequest(BaseModel):
    project_name: str
    license_id: str
    language: str
    copyright_holder: Optional[str] = None

class HeaderResponse(BaseModel):
    header_text: str

# --- Helper ---
def extract_npm_license(package_data: dict) -> str:
    license_data = package_data.get("license") or package_data.get("licenses")
    if isinstance(license_data, dict):
        return license_data.get("type", "Unknown")
    elif isinstance(license_data, list) and len(license_data) > 0:
        return license_data[0].get("type", "Unknown") if isinstance(license_data[0], dict) else str(license_data[0])
    elif isinstance(license_data, str):
        return license_data
    return "Unknown"

# --- Endpoints ---

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirects the root path to the interactive API documentation."""
    return RedirectResponse(url="/docs")

# GROUP 1: Discovery & Research
@app.post("/v1/search", response_model=SearchResponse, tags=["Discovery & Research"])
async def search_libraries(request: SearchRequest):
    """AI-powered search to find the right libraries based on your license needs."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Find 3 libraries for: '{request.query}'. Respond in JSON array with name, license, reason."
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return SearchResponse(results=json.loads(text.strip()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {e}")

@app.post("/v1/alternatives", response_model=AlternativesResponse, tags=["Discovery & Research"])
async def find_alternatives(request: AlternativesRequest):
    """Finds friendly alternatives (e.g. MIT) for a restrictive library."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Find 3 alternatives to '{request.package_name}' with license '{request.desired_license}'. Respond in JSON array with name, license, reason."
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return AlternativesResponse(results=json.loads(text.strip()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {e}")

@app.get("/v1/licenses/{license_id}", response_model=LicenseInfoResponse, tags=["Discovery & Research"])
async def get_license_info(license_id: str):
    """Returns official SPDX metadata for a specific license ID."""
    if license_id not in licenses_db:
        raise HTTPException(status_code=404, detail="License not found.")
    data = licenses_db[license_id]
    return LicenseInfoResponse(
        licenseId=data.get("licenseId"),
        name=data.get("name"),
        seeAlso=data.get("seeAlso", []),
        isOsiApproved=data.get("isOsiApproved", False),
        isDeprecatedLicenseId=data.get("isDeprecatedLicenseId", False)
    )

# GROUP 2: Risk & Compliance
@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["Risk & Compliance"])
async def analyze_package(request: AnalyzeRequest):
    """Analyzes the risk of a specific NPM package for your business context."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")

    async with httpx.AsyncClient() as client:
        res = await client.get(f"https://registry.npmjs.org/{request.package_name}")
        if res.status_code != 200: raise HTTPException(status_code=404, detail="Package not found")
        pkg_license = extract_npm_license(res.json())

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Analyze risk for '{request.package_name}' ({pkg_license}) in context '{request.context}'. Respond in JSON: risk_score (0-100), summary, warnings (list)."
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return AnalyzeResponse(**json.loads(text.strip()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {e}")

@app.post("/v1/audit", response_model=AuditResponse, tags=["Risk & Compliance"])
async def audit_dependencies(request: AuditRequest):
    """Batch scans a list of dependencies for safety warnings."""
    results = []
    safe_licenses = ["MIT", "Apache-2.0", "ISC", "BSD-2-Clause", "BSD-3-Clause", "WTFPL"]
    async with httpx.AsyncClient() as client:
        for dep in request.dependencies:
            try:
                res = await client.get(f"https://registry.npmjs.org/{dep}")
                pkg_license = extract_npm_license(res.json()) if res.status_code == 200 else "Unknown"
                status = "SAFE" if pkg_license in safe_licenses else "WARN"
                results.append(AuditItem(package=dep, license=pkg_license, status=status))
            except:
                results.append(AuditItem(package=dep, license="Error", status="WARN"))
    return AuditResponse(results=results)

@app.post("/v1/compatibility-check", response_model=CompatibilityResponse, tags=["Risk & Compliance"])
async def compatibility_check(request: CompatibilityRequest):
    """Quick deterministic check if two licenses are compatible."""
    a, b = request.license_a, request.license_b
    if a not in COMPATIBILITY_MATRIX or b not in COMPATIBILITY_MATRIX.get(a, {}):
        return CompatibilityResponse(compatible=False, reason="Data missing for this pair.")
    is_compatible = COMPATIBILITY_MATRIX[a][b]
    reason = f"{a} is compatible with {b}." if is_compatible else f"{a} conflicts with {b}."
    return CompatibilityResponse(compatible=is_compatible, reason=reason)

@app.post("/v1/resolve-conflicts", response_model=ConflictResolutionResponse, tags=["Risk & Compliance"])
async def resolve_conflicts(request: ConflictResolutionRequest):
    """Detects conflicts and suggests a 'Legal Patch' (alternative library)."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")

    async with httpx.AsyncClient() as client:
        res_a = await client.get(f"https://registry.npmjs.org/{request.package_a}")
        res_b = await client.get(f"https://registry.npmjs.org/{request.package_b}")
        if res_a.status_code != 200 or res_b.status_code != 200:
            raise HTTPException(status_code=404, detail="Package(s) not found.")
        lic_a, lic_b = extract_npm_license(res_a.json()), extract_npm_license(res_b.json())

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Check conflict: {request.package_a} ({lic_a}) vs {request.package_b} ({lic_b}). If conflict, suggest alternative for one. Respond JSON: has_conflict, conflict_reason, suggested_alternative, alternative_license, explanation."
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.endswith("```"): text = text[:-3]
        return ConflictResolutionResponse(**json.loads(text.strip()))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {e}")

# GROUP 3: Automation & DevTools
@app.post("/v1/generate-header", response_model=HeaderResponse, tags=["Automation & DevTools"])
async def generate_header(request: HeaderRequest):
    """Generates a professional legal header to prepend to your source files."""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")

    holder = request.copyright_holder or request.project_name
    from datetime import datetime
    year = datetime.now().year

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Generate a {request.license_id} header for project '{request.project_name}' in {request.language} for holder '{holder}' (Year {year}). Raw text only, no markdown."
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines[-1] == "```": lines = lines[:-1]
            text = "\n".join(lines).strip()
        return HeaderResponse(header_text=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {e}")
