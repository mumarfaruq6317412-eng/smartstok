from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2 = OAuth2PasswordBearer(tokenUrl='/api/auth/login')

def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def create_token(user):
    payload={'sub':str(user.id),'username':user.username,'role':user.role,'exp':datetime.now(timezone.utc)+timedelta(hours=12)}
    return jwt.encode(payload, settings.jwt_secret, algorithm='HS256')

def current_user(token: str=Depends(oauth2), db: Session=Depends(get_db)):
    try:
        data=jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
        uid=int(data['sub'])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token tidak valid')
    user=db.get(User, uid)
    if not user or not user.is_active: raise HTTPException(401,'Pengguna tidak aktif')
    return user

def require_roles(*roles):
    def dep(user=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403,'Anda tidak memiliki hak akses')
        return user
    return dep
