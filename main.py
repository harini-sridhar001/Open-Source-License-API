import asyncio
import json
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
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
        print("Warning: licenses.json not found. Run 'curl -o licenses.json https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json'")
    except json.JSONDecodeError:
        print("Error: licenses.json is invalid JSON.")
    yield

app = FastAPI(
    title="OSLI: Open Source License Intelligence API",
    description="Intelligent tools for license analysis, risk assessment, and legal automation. Built for HackIllinois 2026.",
    version="1.1.0",
    lifespan=lifespan,
    contact={
        "name": "OSLI Support",
        "url": "https://github.com/spdx/license-list-data",
    }
)

# Enable CORS for Hackathon compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class SearchRequest(BaseModel):
    query: str = Field(..., example="Chart library for a closed-source SaaS")

class SearchResult(BaseModel):
    name: str
    license: str
    reason: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

class AlternativesRequest(BaseModel):
    package_name: str = Field(..., example="highcharts")
    desired_license: str = Field(..., example="MIT")

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

class CompatibilityRequest(BaseModel):
    license_a: str = Field(..., example="MIT")
    license_b: str = Field(..., example="GPL-3.0")

class CompatibilityResponse(BaseModel):
    compatible: bool
    reason: str

class AnalyzeRequest(BaseModel):
    package_name: str = Field(..., example="mongodb")
    context: str = Field(..., example="Commercial closed-source SaaS")

class AnalyzeResponse(BaseModel):
    risk_score: int
    summary: str
    warnings: List[str]

class AuditRequest(BaseModel):
    dependencies: List[str] = Field(..., example=["react", "lodash", "ffmpeg"])

class AuditItem(BaseModel):
    package: str
    license: str
    status: str

class AuditResponse(BaseModel):
    results: List[AuditItem]

class ConflictResolutionRequest(BaseModel):
    package_a: str = Field(..., example="ffmpeg")
    package_b: str = Field(..., example="highcharts")
    context: Optional[str] = "Commercial SaaS"

class ConflictResolutionResponse(BaseModel):
    has_conflict: bool
    conflict_reason: Optional[str] = None
    suggested_alternative: Optional[str] = None
    alternative_license: Optional[str] = None
    explanation: str

class HeaderRequest(BaseModel):
    project_name: str = Field(..., example="Nebula")
    license_id: str = Field(..., example="MIT")
    language: str = Field(..., example="Python")
    copyright_holder: Optional[str] = None

class HeaderResponse(BaseModel):
    header_text: str

# --- Helpers ---

def validate_license_id(license_id: str):
    """Ensures a license ID is a valid SPDX identifier."""
    if license_id not in licenses_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"License ID '{license_id}' is not recognized. Check https://spdx.org/licenses/ for valid IDs (e.g., 'MIT', 'Apache-2.0')."
        )

async def call_gemini_ai(prompt: str):
    """Unified wrapper for AI calls with specific error handling."""
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI services are unavailable (Missing API Key)."
        )

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await asyncio.to_thread(model.generate_content, prompt)
        text = response.text.strip()
        
        # Strip potential markdown code blocks
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        return json.loads(text.strip())
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI returned a malformed response. This usually happens with complex requests; please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Error: {str(e)}"
        )

async def get_npm_data(package_name: str):
    """Fetches data from NPM with specific error handling."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"https://registry.npmjs.org/{package_name}")
            if res.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Package '{package_name}' not found on NPM."
                )
            res.raise_for_status()
            return res.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The NPM Registry is currently unreachable. Please try again later."
            )

def extract_npm_license(package_data: dict) -> str:
    """Safely extracts license info from complex NPM metadata."""
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
    """Redirects to the interactive API documentation."""
    return RedirectResponse(url="/docs")

@app.post("/v1/search", response_model=SearchResponse, tags=["Discovery & Research"])
async def search_libraries(request: SearchRequest):
    """AI-powered search for libraries based on license requirements."""
    prompt = f"Find 3 libraries for: '{request.query}'. Respond in JSON array with name, license, reason. No extra text."
    data = await call_gemini_ai(prompt)
    return SearchResponse(results=data)

@app.post("/v1/alternatives", response_model=AlternativesResponse, tags=["Discovery & Research"])
async def find_alternatives(request: AlternativesRequest):
    """Finds permissive alternatives for a restrictive library."""
    validate_license_id(request.desired_license)
    prompt = f"Find 3 alternatives to '{request.package_name}' with license '{request.desired_license}'. Respond in JSON array with name, license, reason. No extra text."
    data = await call_gemini_ai(prompt)
    return AlternativesResponse(results=data)

@app.get("/v1/licenses/{license_id}", response_model=LicenseInfoResponse, tags=["Discovery & Research"])
async def get_license_info(license_id: str):
    """Returns official SPDX metadata for a specific license ID."""
    if license_id not in licenses_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License '{license_id}' not found. Try 'Apache-2.0' instead of 'Apache'."
        )
    data = licenses_db[license_id]
    return LicenseInfoResponse(
        licenseId=data.get("licenseId"),
        name=data.get("name"),
        seeAlso=data.get("seeAlso", []),
        isOsiApproved=data.get("isOsiApproved", False),
        isDeprecatedLicenseId=data.get("isDeprecatedLicenseId", False)
    )

@app.post("/v1/analyze", response_model=AnalyzeResponse, tags=["Risk & Compliance"])
async def analyze_package(request: AnalyzeRequest):
    """Analyzes the risk of a specific NPM package for your business context."""
    pkg_data = await get_npm_data(request.package_name)
    pkg_license = extract_npm_license(pkg_data)

    prompt = f"Analyze risk for '{request.package_name}' ({pkg_license}) in context '{request.context}'. Respond in JSON: risk_score (0-100), summary, warnings (list). No extra text."
    data = await call_gemini_ai(prompt)
    return AnalyzeResponse(**data)

@app.post("/v1/audit", response_model=AuditResponse, tags=["Risk & Compliance"])
async def audit_dependencies(request: AuditRequest):
    """Batch scans a list of dependencies for safety warnings."""
    results = []
    safe_licenses = ["MIT", "Apache-2.0", "ISC", "BSD-2-Clause", "BSD-3-Clause", "WTFPL"]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.get(f"https://registry.npmjs.org/{dep}") for dep in request.dependencies]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, res in enumerate(responses):
            dep_name = request.dependencies[i]
            if isinstance(res, httpx.Response) and res.status_code == 200:
                pkg_license = extract_npm_license(res.json())
                status_str = "SAFE" if pkg_license in safe_licenses else "WARN"
                results.append(AuditItem(package=dep_name, license=pkg_license, status=status_str))
            else:
                results.append(AuditItem(package=dep_name, license="Unknown/Error", status="WARN"))
                
    return AuditResponse(results=results)

@app.post("/v1/compatibility-check", response_model=CompatibilityResponse, tags=["Risk & Compliance"])
async def compatibility_check(request: CompatibilityRequest):
    """Quick deterministic check if two licenses are compatible."""
    validate_license_id(request.license_a)
    validate_license_id(request.license_b)
    
    a, b = request.license_a, request.license_b
    if a not in COMPATIBILITY_MATRIX or b not in COMPATIBILITY_MATRIX.get(a, {}):
        return CompatibilityResponse(
            compatible=False, 
            reason=f"Detailed data for '{a}' vs '{b}' is missing. Try /v1/resolve-conflicts for AI analysis."
        )
    
    is_compatible = COMPATIBILITY_MATRIX[a][b]
    reason = f"{a} is compatible with {b}." if is_compatible else f"{a} conflicts with {b}."
    return CompatibilityResponse(compatible=is_compatible, reason=reason)

@app.post("/v1/resolve-conflicts", response_model=ConflictResolutionResponse, tags=["Risk & Compliance"])
async def resolve_conflicts(request: ConflictResolutionRequest):
    """Detects conflicts and suggests a 'Legal Patch' (alternative library)."""
    data_a = await get_npm_data(request.package_a)
    data_b = await get_npm_data(request.package_b)
    lic_a, lic_b = extract_npm_license(data_a), extract_npm_license(data_b)

    prompt = f"Check conflict: {request.package_a} ({lic_a}) vs {request.package_b} ({lic_b}). If conflict, suggest alternative for one. Respond JSON: has_conflict, conflict_reason, suggested_alternative, alternative_license, explanation. No extra text."
    data = await call_gemini_ai(prompt)
    return ConflictResolutionResponse(**data)

@app.post("/v1/generate-header", response_model=HeaderResponse, tags=["Automation & DevTools"])
async def generate_header(request: HeaderRequest):
    """Generates a professional legal header for source files."""
    validate_license_id(request.license_id)
    holder = request.copyright_holder or request.project_name
    year = 2026

    prompt = f"Generate a {request.license_id} header for project '{request.project_name}' in {request.language} for holder '{holder}' (Year {year}). Raw text only, no markdown."
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="AI services unavailable.")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await asyncio.to_thread(model.generate_content, prompt)
        return HeaderResponse(header_text=response.text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Header Error: {str(e)}")
