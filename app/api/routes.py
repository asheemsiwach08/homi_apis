from fastapi import APIRouter
from app.api.endpoints import (
    track_leads, otp, whatsapp_webhook, 
    historical_disbursements, live_disbursements,
    leads, basicverify_approval
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
# api_router.include_router(health.router)
api_router.include_router(otp.router)
api_router.include_router(leads.router)
api_router.include_router(track_leads.router) 
api_router.include_router(whatsapp_webhook.router)
api_router.include_router(live_disbursements.router) 
api_router.include_router(basicverify_approval.router)
api_router.include_router(historical_disbursements.router)