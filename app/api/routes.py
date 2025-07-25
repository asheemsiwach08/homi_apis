from fastapi import APIRouter
from app.api.endpoints import (
    leads, health, otp, whatsapp_webhook, 
    historical_disbursements, live_disbursements,
    detail_leads
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router)
api_router.include_router(leads.router) 
api_router.include_router(otp.router)
api_router.include_router(whatsapp_webhook.router)
api_router.include_router(historical_disbursements.router)
api_router.include_router(live_disbursements.router) 
api_router.include_router(detail_leads.router)
