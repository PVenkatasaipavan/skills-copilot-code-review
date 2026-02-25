"""
Endpoints for announcements in the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements(active_only: Optional[bool] = Query(False)) -> List[Dict[str, Any]]:
    """
    Get all announcements, optionally filtering for active ones only

    - active_only: If True, only return announcements marked as active
    """
    query = {}
    if active_only:
        query["is_active"] = True

    announcements = []
    for announcement in announcements_collection.find(query).sort("created_at", -1):
        announcement.pop("_id", None)
        announcements.append(announcement)

    return announcements


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    title: str,
    message: str,
    teacher_username: Optional[str] = Query(None),
    is_active: bool = Query(True)
) -> Dict[str, Any]:
    """
    Create a new announcement - requires teacher authentication

    - title: The announcement title
    - message: The announcement message content
    - teacher_username: The username of the teacher posting the announcement (required)
    - is_active: Whether the announcement is active (default: True)
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required to post announcements")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Create the announcement
    announcement = {
        "title": title,
        "message": message,
        "created_by": teacher["display_name"],
        "created_at": datetime.utcnow().isoformat(),
        "is_active": is_active
    }

    result = announcements_collection.insert_one(announcement)

    announcement["_id"] = str(result.inserted_id)
    return announcement


@router.patch("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    title: Optional[str] = Query(None),
    message: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Update an announcement - requires teacher authentication

    - announcement_id: The ID of the announcement to update
    - teacher_username: The username of the teacher (required)
    - is_active: Update the active status
    - title: Update the title
    - message: Update the message
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Build update document
    update_doc = {}
    if is_active is not None:
        update_doc["is_active"] = is_active
    if title is not None:
        update_doc["title"] = title
    if message is not None:
        update_doc["message"] = message

    if not update_doc:
        raise HTTPException(
            status_code=400, detail="No fields to update")

    result = announcements_collection.update_one(
        {"_id": announcement_id},
        {"$set": update_doc}
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404, detail="Announcement not found")

    # Return the updated announcement
    updated = announcements_collection.find_one({"_id": announcement_id})
    updated.pop("_id", None)
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """
    Delete an announcement - requires teacher authentication

    - announcement_id: The ID of the announcement to delete
    - teacher_username: The username of the teacher (required)
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    result = announcements_collection.delete_one({"_id": announcement_id})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
