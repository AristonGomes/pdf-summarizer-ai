"""
Módulo de banco de dados para histórico de resumos
Usa SQLAlchemy ORM com SQLite (fácil, sem servidor)
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configurar banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pdf_summarizer.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ResumoHistorico(Base):
    """
    Modelo para armazenar histórico de resumos processados
    """
    __tablename__ = "resumos_historico"

    id = Column(Integer, primary_key=True, index=True)
    arquivo_hash = Column(String(32), unique=True, index=True, nullable=False)
    arquivo_nome = Column(String(255), nullable=False)
    resumo = Column(Text, nullable=False)
    num_paginas = Column(Integer, nullable=False)
    tokens_entrada = Column(Integer, default=0)
    tokens_saida = Column(Integer, default=0)
    modelo_usado = Column(String(100), nullable=False)
    idioma = Column(String(5), default="pt")
    tempo_processamento_ms = Column(Integer, default=0)
    tamanho_arquivo_bytes = Column(Integer, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ResumoHistorico {self.id}: {self.arquivo_nome}>"

    def to_dict(self):
        """Converter para dicionário"""
        return {
            "id": self.id,
            "arquivo_nome": self.arquivo_nome,
            "resumo": self.resumo,
            "num_paginas": self.num_paginas,
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "modelo_usado": self.modelo_usado,
            "idioma": self.idioma,
            "tempo_processamento_ms": self.tempo_processamento_ms,
            "tamanho_arquivo_bytes": self.tamanho_arquivo_bytes,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }


class Usuario(Base):
    """
    Modelo para usuários da API (autenticação)
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(255), nullable=True)
    ativo = Column(Integer, default=1)
    resumos_processados = Column(Integer, default=0)
    tokens_usados_total = Column(Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
    ultimo_acesso = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Usuario {self.email}>"

    def to_dict(self):
        """Converter para dicionário"""
        return {
            "id": self.id,
            "email": self.email,
            "nome_completo": self.nome_completo,
            "resumos_processados": self.resumos_processados,
            "tokens_usados_total": self.tokens_usados_total,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None
        }


# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependência para injetar sessão do banco de dados
    Uso em endpoints FastAPI:
    
    @app.get("/")
    async def exemplo(db: Session = Depends(get_db)):
        resumos = db.query(ResumoHistorico).all()
        return resumos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
