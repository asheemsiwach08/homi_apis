import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import BasicVerifyApprovalRequest, BasicVerifyApprovalResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["basicverify_approval"])

@router.post("/basicverify_approval", response_model=BasicVerifyApprovalResponse)
def basicverify_approval(request: BasicVerifyApprovalRequest):
    logger.info(f"Basic Verify Approval request received: {request}")

    if not request.basicVerifyData:
        raise HTTPException(status_code=400, detail="Basic Verify Data is required")

    if request.basicVerifyStatus == "RejectedByBasic":
        logger.info(f"Basic Verify Status is Rejected with comments: {request.rejectionComments}")

        # Update the database with the rejection comments
        from app.services.database_service import database_service

        db_result = database_service.update_basic_verify_status(
            verification_id=request.basicVerifyData.get("ai_disbursement_id"),
            verification_status="RejectedByBasic",
            comments=request.rejectionComments
        )

        if db_result:
            logger.info(f"Disbursement status updated to RejectedByBasic for AI Disbursement ID: {request.basicVerifyData.get('ai_disbursement_id')}")
        else:
            logger.error(f"Failed to update disbursement status for AI Disbursement ID: {request.basicVerifyData.get('ai_disbursement_id')}")

        return BasicVerifyApprovalResponse(
            success=False,
            message="Basic verification was rejected",
            data={
                "status": "RejectedByBasic",
                "ai_disbursement_id": request.basicVerifyData.get("ai_disbursement_id"),
                "basicVerifyData": request.basicVerifyData,
                "comments": request.rejectionComments,
                "message": "Verification process completed with rejection"
            }
        )
    elif request.basicVerifyStatus == "VerifiedByBasic":
        logger.info(f"Basic Verify Status is Verified with comments: {request.rejectionComments}")

        # Update the database with the acceptance comments
        from app.services.database_service import database_service

        db_result = database_service.update_basic_verify_status(
            verification_id=request.basicVerifyData.get("ai_disbursement_id"),
            verification_status="VerifiedByBasic",
            comments=request.rejectionComments
        )

        if db_result:
            logger.info(f"Disbursement status updated to VerifiedByBasic for AI Disbursement ID: {request.basicVerifyData.get('ai_disbursement_id')}")
        else:
            logger.error(f"Failed to update disbursement status for AI Disbursement ID: {request.basicVerifyData.get('ai_disbursement_id')}")

        return BasicVerifyApprovalResponse(
            success=True,
            message="Basic verification was accepted",
            data={
                "status": "VerifiedByBasic",
                "ai_disbursement_id": request.basicVerifyData.get("ai_disbursement_id"),
                "comments": request.rejectionComments,
                "message": "Verification process completed with acceptance"
            }
        )

    