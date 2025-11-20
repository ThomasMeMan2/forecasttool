"""
Project Sharing and Collaboration endpoints (Phase 4)
Share projects with other users with granular permissions
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from ..database import get_db
from ..services.auth import get_current_user, verify_project_access
from ..models import User, Project, ProjectShare

router = APIRouter()


# ============= Schemas =============

class ShareCreate(BaseModel):
    email: EmailStr
    can_view: bool = True
    can_edit: bool = False
    can_delete: bool = False
    can_share: bool = False


class ShareUpdate(BaseModel):
    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None
    can_share: Optional[bool] = None
    is_active: Optional[bool] = None


class ShareResponse(BaseModel):
    id: int
    project_id: int
    user_email: str
    user_name: Optional[str]
    can_view: bool
    can_edit: bool
    can_delete: bool
    can_share: bool
    is_active: bool
    shared_at: str
    shared_by_email: Optional[str]

    class Config:
        from_attributes = True


# ============= Endpoints =============

@router.post("/{project_id}/shares", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def share_project(
    project_id: int,
    share_data: ShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a project with another user.

    Only project owner can share (or users with can_share permission).
    """
    # Verify project access
    verify_project_access(project_id, current_user, db, require_owner=False)

    # Check if current user has share permission
    project = db.query(Project).filter(Project.id == project_id).first()
    is_owner = project.user_id == current_user.id

    if not is_owner:
        # Check if user has share permission
        share = db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id,
            ProjectShare.user_id == current_user.id,
            ProjectShare.can_share == True,
            ProjectShare.is_active == True
        ).first()

        if not share:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to share this project"
            )

    # Find user to share with
    target_user = db.query(User).filter(User.email == share_data.email).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {share_data.email} not found"
        )

    if target_user.id == project.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share project with owner"
        )

    # Check if already shared
    existing_share = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id,
        ProjectShare.user_id == target_user.id
    ).first()

    if existing_share:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project already shared with this user"
        )

    # Create share
    new_share = ProjectShare(
        project_id=project_id,
        user_id=target_user.id,
        can_view=share_data.can_view,
        can_edit=share_data.can_edit,
        can_delete=share_data.can_delete,
        can_share=share_data.can_share,
        shared_by=current_user.id
    )

    db.add(new_share)
    db.commit()
    db.refresh(new_share)

    return ShareResponse(
        id=new_share.id,
        project_id=new_share.project_id,
        user_email=target_user.email,
        user_name=target_user.full_name,
        can_view=new_share.can_view,
        can_edit=new_share.can_edit,
        can_delete=new_share.can_delete,
        can_share=new_share.can_share,
        is_active=new_share.is_active,
        shared_at=new_share.shared_at.isoformat(),
        shared_by_email=current_user.email
    )


@router.get("/{project_id}/shares", response_model=List[ShareResponse])
async def list_project_shares(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all users who have access to a project.

    Only accessible by project owner or users with share permission.
    """
    verify_project_access(project_id, current_user, db)

    shares = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id
    ).all()

    result = []
    for share in shares:
        user = db.query(User).filter(User.id == share.user_id).first()
        shared_by_user = db.query(User).filter(User.id == share.shared_by).first()

        result.append(ShareResponse(
            id=share.id,
            project_id=share.project_id,
            user_email=user.email if user else "unknown",
            user_name=user.full_name if user else None,
            can_view=share.can_view,
            can_edit=share.can_edit,
            can_delete=share.can_delete,
            can_share=share.can_share,
            is_active=share.is_active,
            shared_at=share.shared_at.isoformat(),
            shared_by_email=shared_by_user.email if shared_by_user else None
        ))

    return result


@router.put("/{project_id}/shares/{share_id}", response_model=ShareResponse)
async def update_share_permissions(
    project_id: int,
    share_id: int,
    share_update: ShareUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update permissions for a shared project.

    Only project owner can update permissions.
    """
    verify_project_access(project_id, current_user, db, require_owner=True)

    share = db.query(ProjectShare).filter(
        ProjectShare.id == share_id,
        ProjectShare.project_id == project_id
    ).first()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )

    # Update permissions
    if share_update.can_view is not None:
        share.can_view = share_update.can_view
    if share_update.can_edit is not None:
        share.can_edit = share_update.can_edit
    if share_update.can_delete is not None:
        share.can_delete = share_update.can_delete
    if share_update.can_share is not None:
        share.can_share = share_update.can_share
    if share_update.is_active is not None:
        share.is_active = share_update.is_active

    db.commit()
    db.refresh(share)

    user = db.query(User).filter(User.id == share.user_id).first()

    return ShareResponse(
        id=share.id,
        project_id=share.project_id,
        user_email=user.email if user else "unknown",
        user_name=user.full_name if user else None,
        can_view=share.can_view,
        can_edit=share.can_edit,
        can_delete=share.can_delete,
        can_share=share.can_share,
        is_active=share.is_active,
        shared_at=share.shared_at.isoformat(),
        shared_by_email=None
    )


@router.delete("/{project_id}/shares/{share_id}")
async def revoke_share(
    project_id: int,
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke project access for a user.

    Only project owner can revoke access.
    """
    verify_project_access(project_id, current_user, db, require_owner=True)

    share = db.query(ProjectShare).filter(
        ProjectShare.id == share_id,
        ProjectShare.project_id == project_id
    ).first()

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )

    db.delete(share)
    db.commit()

    return {"message": "Access revoked successfully"}


@router.get("/shared-with-me", response_model=List[dict])
async def list_shared_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all projects shared with the current user.
    """
    shares = db.query(ProjectShare).filter(
        ProjectShare.user_id == current_user.id,
        ProjectShare.is_active == True
    ).all()

    result = []
    for share in shares:
        project = db.query(Project).filter(Project.id == share.project_id).first()
        if project:
            owner = db.query(User).filter(User.id == project.user_id).first()
            result.append({
                "share_id": share.id,
                "project_id": project.id,
                "project_name": project.name,
                "project_description": project.description,
                "owner_email": owner.email if owner else "unknown",
                "owner_name": owner.full_name if owner else None,
                "can_view": share.can_view,
                "can_edit": share.can_edit,
                "can_delete": share.can_delete,
                "can_share": share.can_share,
                "shared_at": share.shared_at.isoformat()
            })

    return result
