from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import os
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fisamy Dashboard BFF", version="1.0.0")

# CORS configuration - locked to your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dev.fisamy.work",
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Add localhost for dev
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# Environment variables
CODER_API_TOKEN = os.getenv("CODER_API_TOKEN")
CODER_HOST = os.getenv("CODER_HOST", "https://coder.fisamy.work")
CODER_URL = os.getenv("CODER_URL", CODER_HOST)  # Fallback for backward compatibility
DOMAIN_MANAGER_TOKEN = os.getenv("DOMAIN_MANAGER_TOKEN")
DOMAIN_MANAGER_URL = os.getenv("DOMAIN_MANAGER_URL", "https://domain-manager.fisamy.work")

# Pydantic models matching the dashboard contract
class Plan(BaseModel):
    name: str
    vcpu: int
    ram_gb: int
    disk_gb: int

class User(BaseModel):
    id: str
    name: str
    plan: Plan

class Usage(BaseModel):
    vcpu: int
    ram_gb: int
    disk_gb: int

class Template(BaseModel):
    id: str
    name: str
    tagline: Optional[str] = None
    recommended: Optional[bool] = False

class Workspace(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    templateName: Optional[str] = None
    status: str  # "running" | "stopped" | "starting" | "stopping" | "suspended"

class DomainBinding(BaseModel):
    id: str
    domain: str
    workspaceId: Optional[str] = None
    status: str  # "verified" | "pending" | "error"

class CreateWorkspaceRequest(BaseModel):
    templateId: str
    name: str

class CreateDomainRequest(BaseModel):
    domain: str
    workspaceId: Optional[str] = None

# Simple auth middleware (replace with your actual auth)
async def get_current_user(request: Request):
    # TODO: Implement your actual auth (session cookie, JWT, etc.)
    # For now, return a mock user - replace this with real auth
    return {
        "id": "user-123",
        "name": "Demo User",
        "plan": {
            "name": "Pro Plan",
            "vcpu": 8,
            "ram_gb": 32,
            "disk_gb": 100
        }
    }

# Coder API helper
async def coder_api(endpoint: str, method: str = "GET", data: dict = None):
    headers = {
        "Authorization": f"Bearer {CODER_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{CODER_URL}{endpoint}", headers=headers)
        elif method == "POST":
            response = await client.post(f"{CODER_URL}{endpoint}", headers=headers, json=data)
        elif method == "DELETE":
            response = await client.delete(f"{CODER_URL}{endpoint}", headers=headers)
        
        if response.status_code >= 400:
            logger.error(f"Coder API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Coder API error")
        
        return response.json()

# Domain Manager API helper
async def domain_manager_api(endpoint: str, method: str = "GET", data: dict = None):
    headers = {
        "Authorization": f"Bearer {DOMAIN_MANAGER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{DOMAIN_MANAGER_URL}{endpoint}", headers=headers)
        elif method == "POST":
            response = await client.post(f"{DOMAIN_MANAGER_URL}{endpoint}", headers=headers, json=data)
        
        if response.status_code >= 400:
            logger.error(f"Domain Manager API error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Domain Manager API error")
        
        return response.json()

# API Endpoints matching the dashboard contract

@app.get("/me", response_model=User)
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info and plan"""
    return user

@app.get("/usage", response_model=Usage)
async def get_usage(user: dict = Depends(get_current_user)):
    """Get current resource usage from running workspaces"""
    try:
        # Get workspaces from Coder
        workspaces_data = await coder_api("/api/v2/workspaces")
        
        # Calculate aggregate usage from running workspaces
        total_vcpu = 0
        total_ram = 0
        total_disk = 0
        
        for workspace in workspaces_data.get("workspaces", []):
            if workspace.get("status") == "running":
                # Extract resource specs from workspace
                # Adjust these paths based on your Coder API response structure
                template_id = workspace.get("template_id")
                if template_id:
                    template_data = await coder_api(f"/api/v2/templates/{template_id}")
                    # Map Coder resources to our format
                    total_vcpu += template_data.get("cpu_cores", 0)
                    total_ram += template_data.get("memory_gb", 0)
                    total_disk += template_data.get("disk_gb", 0)
        
        return Usage(
            vcpu=total_vcpu,
            ram_gb=total_ram,
            disk_gb=total_disk
        )
    except Exception as e:
        logger.error(f"Error getting usage: {e}")
        # Return zeros if we can't get real data
        return Usage(vcpu=0, ram_gb=0, disk_gb=0)

@app.get("/workspaces", response_model=dict)
async def get_workspaces(user: dict = Depends(get_current_user)):
    """Get user's workspaces"""
    try:
        workspaces_data = await coder_api("/api/v2/workspaces")
        
        workspaces = []
        for ws in workspaces_data.get("workspaces", []):
            # Map Coder workspace to our format
            workspace = Workspace(
                id=ws.get("id"),
                name=ws.get("name"),
                url=f"vscode--{ws.get('name')}--{user['id']}.dev.fisamy.work",  # Your subdomain pattern
                templateName=ws.get("template_name"),
                status=map_coder_status(ws.get("status"))
            )
            workspaces.append(workspace)
        
        return {"items": workspaces}
    except Exception as e:
        logger.error(f"Error getting workspaces: {e}")
        return {"items": []}

@app.post("/workspaces", response_model=dict)
async def create_workspace(request: CreateWorkspaceRequest, user: dict = Depends(get_current_user)):
    """Create a new workspace from template"""
    try:
        # Create workspace in Coder
        workspace_data = await coder_api(
            "/api/v2/workspaces",
            method="POST",
            data={
                "template_id": request.templateId,
                "name": request.name,
                "owner_id": user["id"]
            }
        )
        
        return {"id": workspace_data.get("id")}
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workspace")

@app.post("/workspaces/{workspace_id}/start")
async def start_workspace(workspace_id: str, user: dict = Depends(get_current_user)):
    """Start a workspace"""
    try:
        await coder_api(f"/api/v2/workspaces/{workspace_id}/start", method="POST")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error starting workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to start workspace")

@app.post("/workspaces/{workspace_id}/stop")
async def stop_workspace(workspace_id: str, user: dict = Depends(get_current_user)):
    """Stop a workspace"""
    try:
        await coder_api(f"/api/v2/workspaces/{workspace_id}/stop", method="POST")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error stopping workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop workspace")

@app.delete("/workspaces/{workspace_id}")
async def delete_workspace(workspace_id: str, user: dict = Depends(get_current_user)):
    """Delete a workspace"""
    try:
        await coder_api(f"/api/v2/workspaces/{workspace_id}", method="DELETE")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workspace")

@app.get("/templates", response_model=dict)
async def get_templates(user: dict = Depends(get_current_user)):
    """Get available templates"""
    try:
        templates_data = await coder_api("/api/v2/templates")
        
        templates = []
        for i, tmpl in enumerate(templates_data.get("templates", [])):
            template = Template(
                id=tmpl.get("id"),
                name=tmpl.get("name"),
                tagline=tmpl.get("description"),
                recommended=(i == 0)  # First template is recommended
            )
            templates.append(template)
        
        return {"items": templates}
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return {"items": []}

@app.get("/domains", response_model=dict)
async def get_domains(user: dict = Depends(get_current_user)):
    """Get user's custom domains"""
    try:
        domains_data = await domain_manager_api(f"/api/domains?user_id={user['id']}")
        
        domains = []
        for domain in domains_data.get("domains", []):
            domain_binding = DomainBinding(
                id=domain.get("id"),
                domain=domain.get("domain"),
                workspaceId=domain.get("workspace_id"),
                status=domain.get("status")
            )
            domains.append(domain_binding)
        
        return {"items": domains}
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        return {"items": []}

@app.post("/domains", response_model=dict)
async def create_domain(request: CreateDomainRequest, user: dict = Depends(get_current_user)):
    """Create a new domain binding"""
    try:
        domain_data = await domain_manager_api(
            "/api/domains",
            method="POST",
            data={
                "domain": request.domain,
                "workspace_id": request.workspaceId,
                "user_id": user["id"]
            }
        )
        
        return {"id": domain_data.get("id")}
    except Exception as e:
        logger.error(f"Error creating domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to create domain")

@app.post("/domains/{domain_id}/verify")
async def verify_domain(domain_id: str, user: dict = Depends(get_current_user)):
    """Verify a domain"""
    try:
        await domain_manager_api(f"/api/domains/{domain_id}/verify", method="POST")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error verifying domain: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify domain")

# Helper function to map Coder statuses to our format
def map_coder_status(coder_status: str) -> str:
    """Map Coder workspace status to our dashboard status"""
    status_mapping = {
        "running": "running",
        "stopped": "stopped",
        "starting": "starting",
        "stopping": "stopping",
        "suspended": "suspended",
        "failed": "stopped",
        "canceled": "stopped"
    }
    return status_mapping.get(coder_status, "stopped")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fisamy-dashboard-bff"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
