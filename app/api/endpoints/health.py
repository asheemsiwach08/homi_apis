"""
Health Check API Endpoint

Comprehensive health check for the entire API including:
- Database service (Supabase)
- Live disbursements service and dependencies
- General API status
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Response

from app.services.database_service import database_service
from app.api.endpoints.live_disbursements import check_live_disbursements_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api_v1", tags=["health"])


@router.get("/health")
async def health_check(response: Response) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint for the entire API.
    
    Checks:
    - Database service (Supabase) - Orbit and Homfinity environments
    - Live disbursements service and all dependencies
    - General API status
    
    Returns:
        Dict containing health status of all components
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "HOM-i WhatsApp OTP, Lead Creation & Status API",
        "version": "1.0.0"
    }
    
    # 1. Check Database Environments
    try:
        db_environments = {
            "orbit": {
                "available": bool(database_service.client_orbit),
                "error": None
            },
            "homfinity": {
                "available": bool(database_service.client_homfinity),
                "error": None
            }
        }
        
        # Check if at least one environment is available
        db_healthy = db_environments["orbit"]["available"] or db_environments["homfinity"]["available"]
        
        health_status["database_environments"] = db_environments
        
        # Environment configuration details
        health_status["environment_config"] = {
            "default_environment": database_service.environment,
            "orbit_configured": bool(database_service.supabase_orbit_url and database_service.supabase_orbit_service_role_key),
            "homfinity_configured": bool(database_service.supabase_homfinity_url and database_service.supabase_homfinity_service_role_key),
            "orbit_client_initialized": bool(database_service.client_orbit),
            "homfinity_client_initialized": bool(database_service.client_homfinity),
            "table_environment_mapping": {
                "leads": "orbit",
                "appointments": "orbit",
                "disbursements": "orbit",
                "whatsapp_messages": "orbit",
                "otp_storage": "homfinity"
            }
        }
        
        if not db_healthy:
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["database_environments"] = {
            "orbit": {"available": False, "error": str(e)},
            "homfinity": {"available": False, "error": str(e)}
        }
        health_status["status"] = "unhealthy"
    
    # 2. Check Live Disbursements Service
    try:
        live_disbursements_health = check_live_disbursements_health()
        health_status["live_disbursements"] = live_disbursements_health
        
        # Update overall status based on live disbursements health
        if live_disbursements_health["overall_status"] == "unhealthy":
            health_status["status"] = "unhealthy"
        elif live_disbursements_health["overall_status"] == "degraded" and health_status["status"] == "healthy":
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["live_disbursements"] = {
            "overall_status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Set HTTP status code based on overall health
    if health_status["status"] == "unhealthy":
        response.status_code = 503  # Service Unavailable
    elif health_status["status"] == "degraded":
        response.status_code = 200  # Still OK but degraded
    else:
        response.status_code = 200  # Healthy
    
    return health_status
