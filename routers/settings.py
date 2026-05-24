from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gigaam_transcriber.asr_provider import ASRProvider
from gigaam_transcriber.auth import get_current_user
from gigaam_transcriber.database import get_db
from gigaam_transcriber.models import User, UserSettings

router = APIRouter(tags=["settings"])


class ASRProviderRequest(BaseModel):
    provider: str


class ASRProviderResponse(BaseModel):
    provider: str


@router.get("/asr-provider", response_model=ASRProviderResponse)
async def get_asr_provider(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if settings is None:
        return ASRProviderResponse(provider="mistral")

    return ASRProviderResponse(provider=settings.asr_provider)


@router.put("/asr-provider", response_model=ASRProviderResponse)
async def set_asr_provider(
    body: ASRProviderRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        ASRProvider(body.provider)  # noqa: B018
    except ValueError:
        valid = [p.value for p in ASRProvider]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{body.provider}'. Must be one of: {valid}",
        )

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    settings = result.scalar_one_or_none()

    if settings is None:
        settings = UserSettings(user_id=user.id, asr_provider=body.provider)
        db.add(settings)
    else:
        settings.asr_provider = body.provider

    await db.flush()
    await db.commit()

    return ASRProviderResponse(provider=settings.asr_provider)
