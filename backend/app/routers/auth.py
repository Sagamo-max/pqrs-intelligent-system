import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, oauth2_scheme, require_role
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.funcionario import Funcionario, FuncionarioRole
from app.models.login_attempt import LoginAttempt
from app.models.refresh_token import RefreshToken
from app.models.token_blacklist import TokenBlacklist
from app.schemas.auth import (
    FuncionarioCreate,
    FuncionarioOut,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Auth"])
logger = logging.getLogger(__name__)


def _issue_token_pair(
    funcionario: Funcionario,
    db: Session,
    family_id: UUID | None = None,
) -> TokenResponse:
    family_id = family_id or uuid4()
    access_token = create_access_token(
        {"sub": str(funcionario.id), "role": funcionario.role.value}
    )
    refresh_token = create_refresh_token(
        {
            "sub": str(funcionario.id),
            "role": funcionario.role.value,
            "family_id": str(family_id),
        }
    )
    refresh_payload = decode_refresh_token(refresh_token)
    db.add(
        RefreshToken(
            funcionario_id=funcionario.id,
            token_hash=hash_refresh_token(refresh_token),
            family_id=family_id,
            expires_at=datetime.fromtimestamp(
                refresh_payload["exp"],
                tz=timezone.utc,
            ),
        )
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=funcionario.role,
    )


def _record_login_attempt(
    db: Session,
    username: str,
    request: Request,
    success: bool,
) -> None:
    db.add(
        LoginAttempt(
            username=username,
            ip_address=request.client.host if request.client else None,
            success=success,
        )
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    failed_attempts = db.scalar(
        select(func.count())
        .select_from(LoginAttempt)
        .where(
            LoginAttempt.username == payload.username,
            LoginAttempt.success.is_(False),
            LoginAttempt.created_at >= cutoff,
        )
    ) or 0
    if failed_attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Intente más tarde.",
        )

    funcionario = db.scalar(
        select(Funcionario).where(Funcionario.username == payload.username)
    )
    if not funcionario or not verify_password(
        payload.password, funcionario.hashed_password
    ):
        _record_login_attempt(db, payload.username, request, False)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    if not funcionario.is_active:
        _record_login_attempt(db, payload.username, request, False)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    _record_login_attempt(db, payload.username, request, True)
    token_pair = _issue_token_pair(funcionario, db)
    db.commit()
    return token_pair


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido",
    )
    try:
        refresh_payload = decode_refresh_token(payload.refresh_token)
        funcionario_id = UUID(refresh_payload["sub"])
        family_id = UUID(refresh_payload["family_id"])
    except Exception:
        raise credentials_exception

    stored = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token))
        .with_for_update()
    )
    if stored is None or stored.funcionario_id != funcionario_id:
        raise credentials_exception
    if stored.used:
        db.query(RefreshToken).filter(
            RefreshToken.family_id == stored.family_id
        ).delete(synchronize_session=False)
        db.commit()
        raise credentials_exception
    now = datetime.now(timezone.utc)
    if stored.expires_at <= now or family_id != stored.family_id:
        raise credentials_exception

    funcionario = db.get(Funcionario, stored.funcionario_id)
    if funcionario is None or not funcionario.is_active:
        raise credentials_exception

    stored.used = True
    token_pair = _issue_token_pair(funcionario, db, stored.family_id)
    db.commit()
    return token_pair


@router.post("/logout")
def logout(
    payload: RefreshRequest,
    token: str = Depends(oauth2_scheme),
    current_user: Funcionario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        access_payload = decode_access_token(token)
        access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        if not db.scalar(
            select(TokenBlacklist).where(TokenBlacklist.jti == access_payload["jti"])
        ):
            db.add(
                TokenBlacklist(
                    jti=access_payload["jti"],
                    expires_at=access_exp,
                )
            )
    except Exception:
        logger.exception("Failed to blacklist access token during logout")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    refresh_hash = hash_refresh_token(payload.refresh_token)
    stored = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == refresh_hash,
            RefreshToken.funcionario_id == current_user.id,
        )
    )
    if stored:
        stored.used = True
    db.commit()
    return {"message": "Sesión cerrada"}


@router.get("/me", response_model=FuncionarioOut)
def me(current_user: Funcionario = Depends(get_current_user)):
    return current_user


@router.post(
    "/funcionarios",
    response_model=FuncionarioOut,
    status_code=status.HTTP_201_CREATED,
)
def create_funcionario(
    payload: FuncionarioCreate,
    db: Session = Depends(get_db),
    _: Funcionario = Depends(require_role(FuncionarioRole.MASTER)),
):
    if payload.role == FuncionarioRole.ANALISTA and payload.area_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un ANALISTA debe tener un area_id asignado",
        )
    if (
        payload.role in (FuncionarioRole.SUPERVISOR, FuncionarioRole.MASTER)
        and payload.area_id is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SUPERVISOR y MASTER no deben tener area_id",
        )
    if db.scalar(select(Funcionario).where(Funcionario.username == payload.username)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El username ya existe",
        )

    funcionario = Funcionario(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        area_id=payload.area_id,
    )
    db.add(funcionario)
    db.commit()
    db.refresh(funcionario)
    return funcionario
