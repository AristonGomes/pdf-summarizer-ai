"""
Módulo de autenticação com JWT (JSON Web Tokens)
Permite que apenas usuários autenticados usem a API
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import Depends, HTTPException, status, Header

# Configurações
SECRET_KEY = os.getenv("SECRET_KEY", "seu-secret-key-super-secreto-mude-em-producao")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Dados contidos no JWT"""
    usuario_id: Optional[int] = None
    email: Optional[str] = None


class Token(BaseModel):
    """Resposta de login"""
    access_token: str
    token_type: str
    expires_in: int


def hash_password(password: str) -> str:
    """
    Gerar hash bcrypt da senha
    
    Args:
        password: Senha em texto plano
    
    Returns:
        Hash seguro da senha
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verificar se a senha corresponde ao hash
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash armazenado no banco
    
    Returns:
        True se corresponde, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Criar JWT token
    
    Args:
        data: Dados a incluir no token (ex: {"sub": "user_id"})
        expires_delta: Tempo de expiração (padrão: 7 dias)
    
    Returns:
        JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verificar e decodificar JWT token
    
    Args:
        token: Token JWT
    
    Returns:
        Dados contidos no token
    
    Raises:
        HTTPException: Se token for inválido ou expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        usuario_id: int = payload.get("sub")
        email: str = payload.get("email")
        
        if usuario_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(usuario_id=usuario_id, email=email)
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado ou inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(authorization: Optional[str] = Header(None)) -> TokenData:
    """
    Dependência FastAPI para validar token em requisições
    
    Usa header Authorization: Bearer {token}
    
    Uso em endpoints:
    @app.get("/minhas-resumos")
    async def meus_resumos(current_user: TokenData = Depends(get_current_user)):
        return {"usuario_id": current_user.usuario_id}
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido ou inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ")[1]
    return verify_token(token)


def get_token_expire_time() -> int:
    """Retorna tempo de expiração em segundos"""
    return ACCESS_TOKEN_EXPIRE_DAYS * 24 * 3600
