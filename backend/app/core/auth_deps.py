from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.funcionario import Funcionario, FuncionarioRole, role_at_least
from app.models.token_blacklist import TokenBlacklist

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Funcionario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        funcionario_id = payload.get("sub")
        jti = payload.get("jti")
        if funcionario_id is None or jti is None:
            raise credentials_exception
        if db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
            raise credentials_exception
    except Exception:
        raise credentials_exception

    funcionario = db.get(Funcionario, funcionario_id)
    if funcionario is None or not funcionario.is_active:
        raise credentials_exception
    return funcionario


def require_role(minimum: FuncionarioRole):
    def _dep(
        current_user: Funcionario = Depends(get_current_user),
    ) -> Funcionario:
        if not role_at_least(current_user.role, minimum):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permisos insuficientes",
            )
        return current_user

    return _dep
