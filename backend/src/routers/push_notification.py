"""
Push Notification Router
Handles Web Push subscription and sending notifications
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from ..database.connection import db
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["Push Notifications"])


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict  # Contains p256dh and auth


@router.post("/subscribe")
async def subscribe_to_push(
    subscription: PushSubscription,
    user: dict = Depends(get_current_user)
):
    """
    Save a student's push subscription to MongoDB
    """
    try:
        # Only students should subscribe to quiz notifications
        if user.get("role") not in ["student"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can subscribe to push notifications"
            )
        
        student_id = user.get("id")
        
        # Check if subscription already exists
        existing = await db.database.push_subscriptions.find_one({
            "studentId": student_id,
            "endpoint": subscription.endpoint
        })
        
        if existing:
            # Update existing subscription
            await db.database.push_subscriptions.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "keys": subscription.keys,
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            return {
                "success": True,
                "message": "Subscription updated",
                "subscriptionId": str(existing["_id"])
            }
        
        # Create new subscription
        doc = {
            "studentId": student_id,
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        result = await db.database.push_subscriptions.insert_one(doc)
        
        return {
            "success": True,
            "message": "Subscription saved",
            "subscriptionId": str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error saving push subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save push subscription"
        )


@router.delete("/unsubscribe")
async def unsubscribe_from_push(
    endpoint: str,
    user: dict = Depends(get_current_user)
):
    """
    Remove a student's push subscription
    """
    try:
        student_id = user.get("id")
        
        result = await db.database.push_subscriptions.delete_one({
            "studentId": student_id,
            "endpoint": endpoint
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )
        
        return {
            "success": True,
            "message": "Subscription removed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing push subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove push subscription"
        )

