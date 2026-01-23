from fastapi import Depends, HTTPException, status, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from app.connectors.database_connector import get_db
from app.entities.user import User

# ======================================================
# ENV & CONSTANTS
# ======================================================
load_dotenv()

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "LYSw3EDblwQMxzu5gdgK97gidtSIx0f8JvAjEvINQXuM8Tk-fkZq1tuvpEemI88FmNQTyNi9NaHW2hrQZNLw3w",
)
ALGORITHM = "HS256"

security = HTTPBearer()


# ======================================================
# INTERNAL JWT DECODE HELPER
# ======================================================
def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ======================================================
# HTTP AUTH (USED BY NORMAL APIs)
# ======================================================
async def verify_auth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Verify JWT for HTTP routes and return User"""

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing",
        )

    payload = decode_jwt_token(credentials.credentials)

    user_id: str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


# ======================================================
# WEBSOCKET AUTH (USED BY GROUP CHAT)
# ======================================================
async def get_user_from_ws_token(
    websocket: WebSocket,
    db: Session,
) -> User:
    """
    Extract JWT from query param:
    ws://host/ws/groups/{group_id}?token=JWT
    """

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        raise RuntimeError("WebSocket authentication failed")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if not user_id:
            await websocket.close(code=4401)
            raise RuntimeError("Invalid token payload")

        user = db.get(User, user_id)
        if not user or not user.is_active:
            await websocket.close(code=4403)
            raise RuntimeError("User not authorized")

        return user

    except JWTError:
        await websocket.close(code=4401)
        raise RuntimeError("Invalid or expired token")
