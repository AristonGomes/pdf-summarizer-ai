"""
Módulo com endpoints avançados para PDF Summarizer AI
Integra banco de dados, cache, autenticação e rate limiting
"""

import hashlib
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from summarizer import processar_pdf
from database import get_db, ResumoHistorico, Usuario
from auth import get_current_user, TokenData, create_access_token, hash_password, verify_password, get_token_expire_time
from cache import cache, hash_file_content
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Criar router para novos endpoints
router = APIRouter(prefix="/api/v2", tags=["Advanced Features"])


class LoginRequest(BaseModel):
    """Modelo para requisição de login"""
    email: str
    senha: str


class LoginResponse(BaseModel):
    """Modelo para resposta de login"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ResumoResponse(BaseModel):
    """Modelo para resposta de resumo com histórico"""
    id: Optional[int] = None
    resumo: str
    paginas: int
    tokens_entrada: int
    tokens_saida: int
    modelo: str
    criado_em: Optional[str] = None
    cache_hit: bool = False


class MeusResumosResponse(BaseModel):
    """Modelo para resposta de histórico"""
    total: int
    resumos: list


# ============================================================================
# ENDPOINTS DE AUTENTICAÇÃO
# ============================================================================

@router.post("/auth/cadastro", response_model=LoginResponse)
async def cadastro(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Registrar novo usuário
    
    Args:
        email: Email do usuário
        senha: Senha (será hasheada)
    
    Returns:
        Token JWT de acesso
    """
    # Verificar se usuário já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == request.email).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Criar novo usuário
    novo_usuario = Usuario(
        email=request.email,
        senha_hash=hash_password(request.senha),
        nome_completo=request.email.split("@")[0]
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    # Gerar token JWT
    access_token = create_access_token(
        data={"sub": novo_usuario.id, "email": novo_usuario.email}
    )
    
    logger.info(f"✅ Novo usuário cadastrado: {request.email}")
    
    return LoginResponse(
        access_token=access_token,
        expires_in=get_token_expire_time()
    )


@router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Fazer login com email e senha
    
    Args:
        email: Email do usuário
        senha: Senha em texto plano
    
    Returns:
        Token JWT para usar em requisições autenticadas
    """
    # Buscar usuário
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    
    if not usuario or not verify_password(request.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )
    
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    # Gerar token JWT
    access_token = create_access_token(
        data={"sub": usuario.id, "email": usuario.email}
    )
    
    logger.info(f"✅ Login bem-sucedido: {usuario.email}")
    
    return LoginResponse(
        access_token=access_token,
        expires_in=get_token_expire_time()
    )


# ============================================================================
# ENDPOINTS DE RESUMO COM CACHE E HISTÓRICO
# ============================================================================

@router.post("/summarize-com-cache", response_model=ResumoResponse)
async def summarize_com_cache(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resumir PDF com cache e armazenamento em banco de dados
    
    Funcionalidades:
    - Cacheia resultado por arquivo (hash MD5)
    - Armazena no banco de dados
    - Rastreia uso por usuário
    
    Args:
        file: Arquivo PDF
        current_user: Usuário autenticado (JWT)
    
    Returns:
        Resumo com ID, timestamps e indicação se veio do cache
    """
    import time
    import tempfile
    import os
    
    tempo_inicio = time.time()
    temp_file_path = None
    
    try:
        # Ler conteúdo do arquivo
        file_content = await file.read()
        file_hash = hash_file_content(file_content)
        
        # Verificar cache
        logger.info(f"Verificando cache para arquivo: {file.filename} (hash: {file_hash})")
        cached_result = cache.get(f"pdf:{file_hash}")
        
        if cached_result:
            logger.info(f"✅ Cache HIT para {file.filename}")
            
            # Registrar acesso no histórico
            resumo = db.query(ResumoHistorico).filter_by(arquivo_hash=file_hash).first()
            
            return ResumoResponse(
                id=resumo.id if resumo else None,
                resumo=cached_result["resumo"],
                paginas=cached_result["num_pages"],
                tokens_entrada=cached_result["tokens_entrada"],
                tokens_saida=cached_result["tokens_saida"],
                modelo=cached_result["modelo_usado"],
                cache_hit=True
            )
        
        # Processar novo PDF
        logger.info(f"Cache MISS para {file.filename}. Processando...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_content)
        
        # Processar
        resultado = processar_pdf(temp_file_path)
        
        if not resultado.get("sucesso"):
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar PDF: {resultado.get('mensagem')}"
            )
        
        # Armazenar em cache (24h)
        cache.set(f"pdf:{file_hash}", resultado, ttl=86400)
        
        # Armazenar no banco de dados
        tempo_processamento = int((time.time() - tempo_inicio) * 1000)
        tamanho_arquivo = len(file_content)
        
        resumo_db = ResumoHistorico(
            arquivo_hash=file_hash,
            arquivo_nome=file.filename,
            resumo=resultado.get("resumo", ""),
            num_paginas=resultado.get("num_pages", 0),
            tokens_entrada=resultado.get("tokens_entrada", 0),
            tokens_saida=resultado.get("tokens_saida", 0),
            modelo_usado=resultado.get("modelo_usado", ""),
            tempo_processamento_ms=tempo_processamento,
            tamanho_arquivo_bytes=tamanho_arquivo
        )
        
        db.add(resumo_db)
        db.commit()
        db.refresh(resumo_db)
        
        # Atualizar estatísticas do usuário
        usuario = db.query(Usuario).filter_by(id=current_user.usuario_id).first()
        if usuario:
            usuario.resumos_processados += 1
            usuario.tokens_usados_total += resultado.get("tokens_entrada", 0) + resultado.get("tokens_saida", 0)
            db.commit()
        
        logger.info(f"✅ PDF processado e armazenado: {file.filename}")
        
        return ResumoResponse(
            id=resumo_db.id,
            resumo=resultado.get("resumo", ""),
            paginas=resultado.get("num_pages", 0),
            tokens_entrada=resultado.get("tokens_entrada", 0),
            tokens_saida=resultado.get("tokens_saida", 0),
            modelo=resultado.get("modelo_usado", ""),
            criado_em=resumo_db.criado_em.isoformat() if resumo_db.criado_em else None,
            cache_hit=False
        )
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass


# ============================================================================
# ENDPOINTS DE HISTÓRICO
# ============================================================================

@router.get("/meus-resumos", response_model=MeusResumosResponse)
async def meus_resumos(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    limite: int = 10
):
    """
    Obter histórico de resumos do usuário autenticado
    
    Args:
        limit: Número máximo de resumos a retornar (padrão: 10)
    
    Returns:
        Lista de resumos processados com metadados
    """
    resumos = db.query(ResumoHistorico).order_by(
        ResumoHistorico.criado_em.desc()
    ).limit(limite).all()
    
    return MeusResumosResponse(
        total=len(resumos),
        resumos=[r.to_dict() for r in resumos]
    )


@router.get("/resumo/{resumo_id}")
async def get_resumo(
    resumo_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obter um resumo específico pelo ID
    
    Args:
        resumo_id: ID do resumo no banco de dados
    
    Returns:
        Dados completos do resumo
    """
    resumo = db.query(ResumoHistorico).filter_by(id=resumo_id).first()
    
    if not resumo:
        raise HTTPException(
            status_code=404,
            detail="Resumo não encontrado"
        )
    
    return resumo.to_dict()


# ============================================================================
# ENDPOINTS DE ADMINISTRAÇÃO
# ============================================================================

@router.post("/admin/cache-flush")
async def cache_flush(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Limpar cache Redis (apenas para admins)
    
    ⚠️ USE COM CUIDADO! Isso apagará todos os resumos cacheados.
    """
    # Verificar se é admin
    usuario = db.query(Usuario).filter_by(id=current_user.usuario_id).first()
    if not usuario or usuario.email != "admin@example.com":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas administradores."
        )
    
    cache.flush_all()
    logger.warning(f"🔴 Cache limpo por: {usuario.email}")
    
    return {"status": "success", "mensagem": "Cache limpo completamente"}


@router.get("/admin/estatisticas")
async def estatisticas(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obter estatísticas de uso (apenas admins)
    
    Returns:
        Dados de uso geral da plataforma
    """
    # Verificar se é admin
    usuario = db.query(Usuario).filter_by(id=current_user.usuario_id).first()
    if not usuario or usuario.email != "admin@example.com":
        raise HTTPException(
            status_code=403,
            detail="Acesso negado"
        )
    
    total_resumos = db.query(ResumoHistorico).count()
    total_usuarios = db.query(Usuario).count()
    total_tokens = db.query(Usuario).with_entities(
        db.func.sum(Usuario.tokens_usados_total)
    ).scalar() or 0
    
    return {
        "total_resumos": total_resumos,
        "total_usuarios": total_usuarios,
        "total_tokens_usados": total_tokens,
        "cache_enabled": cache.enabled
    }
