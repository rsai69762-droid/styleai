"""User endpoints: profile, preferences, onboarding."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_current_user
from src.db.engine import get_db
from src.db.models import User, UserProfile
from src.schemas.users import OnboardingIn, UserOut, UserProfileOut, UserProfileUpdate

router = APIRouter()


@router.get("/users/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.get("/users/me/profile", response_model=UserProfileOut)
async def get_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return profile


@router.put("/users/me/profile", response_model=UserProfileOut)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/users/me/onboarding", response_model=UserProfileOut, status_code=201)
async def onboarding(
    data: OnboardingIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))).scalar_one_or_none()
    if existing and existing.onboarding_completed:
        raise HTTPException(status_code=409, detail="Onboarding already completed. Use PUT /profile to update.")

    if existing:
        profile = existing
    else:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    profile.onboarding_completed = True

    await db.commit()
    await db.refresh(profile)
    return profile
