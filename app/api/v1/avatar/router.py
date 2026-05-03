"""
Avatar router
"""

import uuid
from typing import Dict
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.core.exceptions import ServiceUnavailableException
from app.core.logging import get_logger
from app.middleware.middleware import get_current_user_id
from app.models.models import AvatarResponse, TryOnRequest
from app.services.avatar_service import avatar_service

logger = get_logger(__name__)
router = APIRouter()

# In-memory job store: job_id → {status, result, error}
# "processing" | "completed" | "failed"
_jobs: Dict[str, dict] = {}


async def _run_try_on_job(job_id: str, request: TryOnRequest, user_id: str):
    """Background task that runs the Replicate call and updates _jobs."""
    try:
        result = await avatar_service.perform_virtual_try_on(request, user_id)
        _jobs[job_id] = {"status": "completed", "result": result}
        logger.info(f"✅ Try-on job {job_id} completed")
    except Exception as e:
        logger.error(f"❌ Try-on job {job_id} failed: {e}")
        _jobs[job_id] = {"status": "failed", "error": str(e)}


@router.post("/upload", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user_id)
):
    """Upload and process user avatar for digital twin creation"""
    try:
        if not avatar_service.is_available():
            raise ServiceUnavailableException(
                "Avatar service not available. Please install MediaPipe: pip install mediapipe"
            )
        result = await avatar_service.process_avatar_upload(file, current_user_id)
        return AvatarResponse(
            success=True,
            data=result["avatar"],
            message=f"Avatar created successfully with quality score: {result['quality_score']:.2f}"
        )
    except ServiceUnavailableException:
        raise
    except Exception as e:
        logger.error(f"Error uploading avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=AvatarResponse)
async def get_user_avatar(current_user_id: str = Depends(get_current_user_id)):
    """Get user's current avatar"""
    try:
        from app.services.database_service import DatabaseService
        avatar = await DatabaseService.get_user_avatar(current_user_id)
        if not avatar:
            raise HTTPException(status_code=404, detail="No avatar found for user")
        return AvatarResponse(success=True, data=avatar, message="Avatar retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user avatar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/try-on")
async def virtual_try_on(
    request: TryOnRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Start a virtual try-on job. Returns immediately with a job_id.
    Poll GET /avatar/try-on/status/{job_id} for the result.
    """
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "processing"}
    background_tasks.add_task(_run_try_on_job, job_id, request, current_user_id)
    logger.info(f"🚀 Try-on job {job_id} queued for user {current_user_id}")
    return {"success": True, "job_id": job_id, "status": "processing"}


@router.get("/try-on/status/{job_id}")
async def get_tryon_status(
    job_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Poll the status of an async try-on job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] == "completed":
        # Clean up after delivering the result
        _jobs.pop(job_id, None)
        return {"success": True, "status": "completed", "data": job["result"]}

    if job["status"] == "failed":
        _jobs.pop(job_id, None)
        return {"success": False, "status": "failed", "error": job.get("error")}

    return {"success": True, "status": "processing"}


@router.get("/try-on/history")
async def get_tryon_history(
    limit: int = 20,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get user's virtual try-on history"""
    try:
        from app.services.database_service import DatabaseService
        results = await DatabaseService.get_user_tryon_results(current_user_id, limit)
        return {"success": True, "data": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error getting try-on history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/service/status")
async def get_avatar_service_status():
    """Get avatar service status and capabilities"""
    try:
        status = avatar_service.get_service_status()
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting avatar service status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{avatar_id}", response_model=AvatarResponse)
async def get_avatar_by_id(
    avatar_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get avatar by ID (must belong to current user)"""
    try:
        from app.services.database_service import DatabaseService
        avatar = await DatabaseService.get_avatar_by_id(avatar_id)
        if not avatar:
            raise HTTPException(status_code=404, detail="Avatar not found")
        if avatar.user_id != current_user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        return AvatarResponse(success=True, data=avatar, message="Avatar retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting avatar by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
