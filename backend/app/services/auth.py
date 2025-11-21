"""
Authentication and Authorization Service (Phase 4)
JWT-based authentication with user management
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# JWT settings
SECRET_KEY = settings.secret_key  # Must be set in .env - no default for security
ALGORITHM = settings.algorithm if hasattr(settings, 'algorithm') else "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes if hasattr(settings, 'access_token_expire_minutes') else 30


class AuthService:
    """Authentication service for user management and JWT tokens"""

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and verify a JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        full_name: str,
        organization: Optional[str] = None,
    ) -> User:
        """Create a new user"""
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create user
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            organization=organization,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Use this in route dependencies: user: User = Depends(get_current_user)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = AuthService.decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (convenience wrapper)"""
    return current_user


def verify_project_access(
    project_id: int,
    user: User,
    db: Session,
    require_owner: bool = False
) -> bool:
    """
    Verify that a user has access to a project.

    Args:
        project_id: Project ID
        user: Current user
        db: Database session
        require_owner: If True, require user to be the owner

    Returns:
        True if access granted

    Raises:
        HTTPException if access denied
    """
    from ..models import Project, ProjectShare

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check if user is owner
    is_owner = project.owner_id == user.id

    if require_owner and not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owner can perform this action"
        )

    if is_owner:
        return True

    # Check if project is shared with user
    share = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id,
        ProjectShare.user_id == user.id,
        ProjectShare.is_active == True
    ).first()

    if share:
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this project"
    )
