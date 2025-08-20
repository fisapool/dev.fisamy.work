<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Code.fisamy.work - VS Code Hosting Platform

A modern, scalable platform for hosting VS Code workspaces in the cloud.

##  Choose Your Path

This project offers two deployment approaches:

### **Option 1: Coder (Enterprise-Grade)**
- Full Coder platform with advanced features
- Multi-tenant workspace management
- Professional templates and quotas
- **Status**: Templates need to be created (no-gpu/gpu missing)
- **Best for**: Production deployments, teams, enterprise use

### **Option 2: Coder-lite (Simple & Fast)**
- OpenVSCode + Caddy bundle
- Per-user limits and quotas
- Idle reaper and Python devctl CLI
- **Status**: Ready to deploy
- **Best for**: Quick setup, small teams, MVP deployments

## 📁 Project Structure

- `frontend/` - React SPA (Vite 6, React 19)
- `back-end/` - FastAPI BFF with Coder integration
- `coder-lite/` - OpenVSCode + Caddy deployment
- `coder-templates/` - Coder workspace templates

##  Quick Start

1. **Frontend**: `npm install && npm run build`
2. **Backend**: Choose your path above
3. **Deploy**: Follow the [DEPLOYMENT.md](DEPLOYMENT.md) guide

##  Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Project Status](PROJECT_STATUS.md)
- [Deliverables Summary](DELIVERABLES_SUMMARY.md)

## 🔒 Security Notes

- Frontend only exposes `VITE_*` environment variables
- Backend CORS configured for localhost:5173 (Vite dev)
- Secrets should be stored in `/etc/fisamy/*.env` (not in repo)
- Rotate `CODER_API_TOKEN` before production use
