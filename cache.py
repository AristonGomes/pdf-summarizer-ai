"""
Módulo de cache com Redis
Evita reprocessamento de PDFs já resumidos
"""

import os
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Tentar importar redis, mas permitir operação sem ele
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis não instalado. Cache desabilitado. Para ativar: pip install redis")


class Cache:
    """
    Gerenciador de cache com Redis
    Se Redis não estiver disponível, funciona sem cache (graceful degradation)
    """
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        """
        Inicializar conexão com Redis
        
        Args:
            host: Host do Redis (padrão: localhost)
            port: Porta do Redis (padrão: 6379)
            db: Banco de dados Redis (padrão: 0)
        """
        self.host = os.getenv("REDIS_HOST", host)
        self.port = int(os.getenv("REDIS_PORT", port))
        self.db = int(os.getenv("REDIS_DB", db))
        self.redis_client = None
        self.enabled = REDIS_AVAILABLE
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                # Testa conexão
                self.redis_client.ping()
                logger.info(f"✅ Redis conectado em {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"⚠️  Redis indisponível: {str(e)}. Operando sem cache.")
                self.enabled = False
                self.redis_client = None
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Obter valor do cache
        
        Args:
            key: Chave do cache
        
        Returns:
            Valor em cache ou None se não encontrado
        """
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit: {key}")
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao ler cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Armazenar valor em cache
        
        Args:
            key: Chave do cache
            value: Valor a armazenar (será serializado para JSON)
            ttl: Time-to-live em segundos (padrão: 24h)
        
        Returns:
            True se sucesso, False caso contrário
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Erro ao escrever cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Deletar chave do cache
        
        Args:
            key: Chave do cache
        
        Returns:
            True se deletado, False caso contrário
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache: {str(e)}")
            return False
    
    def flush_all(self) -> bool:
        """
        Limpar todo o cache (USE COM CUIDADO!)
        
        Returns:
            True se sucesso
        """
        if not self.enabled:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Cache limpo completamente!")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False


# Instância global do cache
cache = Cache()


def hash_file_content(content: bytes) -> str:
    """
    Gerar hash MD5 do conteúdo do arquivo
    Útil para identificar PDFs duplicados
    
    Args:
        content: Bytes do arquivo
    
    Returns:
        Hash MD5 em hexadecimal
    """
    return hashlib.md5(content).hexdigest()


def cache_resultado(ttl: int = 86400):
    """
    Decorator para cachear resultados de funções
    
    Args:
        ttl: Time-to-live em segundos
    
    Exemplo:
        @cache_resultado(ttl=3600)
        def funcao_cara():
            return resultado
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave baseada em função e argumentos
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Tentar obter do cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.info(f"Usando resultado cacheado para {func.__name__}")
                return cached
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


# Dicas de uso em main.py:
"""
# Importar cache e função hash
from cache import cache, hash_file_content

# No endpoint:
@app.post("/summarize")
async def summarize(file: UploadFile):
    # Ler conteúdo do arquivo
    file_content = await file.read()
    file_hash = hash_file_content(file_content)
    
    # Verificar se já foi processado
    cached = cache.get(f"pdf:{file_hash}")
    if cached:
        return cached
    
    # Processar PDF
    resultado = processar_pdf(temp_file_path)
    
    # Armazenar em cache por 24h
    cache.set(f"pdf:{file_hash}", resultado, ttl=86400)
    
    return resultado

# Limpar cache manualmente:
@app.post("/admin/cache-flush")
async def cache_flush(current_user: TokenData = Depends(get_current_user)):
    if current_user.email != "admin@example.com":  # Apenas admin
        raise HTTPException(status_code=403)
    
    cache.flush_all()
    return {"status": "Cache limpo"}
"""
