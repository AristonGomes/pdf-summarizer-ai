"""
FastAPI backend para PDF Summarizer AI
Endpoint para receber arquivos PDF e gerar resumos usando Google Gemini AI
"""

import os
import logging
import tempfile
import time
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

# Tentar importar módulos avançados (opcionais)
try:
    from advanced_endpoints import router as advanced_router
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False
    advanced_router = None

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    limiter = None

from summarizer import processar_pdf

# Constantes
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar FastAPI
app = FastAPI(
    title="PDF Summarizer AI",
    description="API para resumir PDFs usando Google Gemini AI",
    version="1.1.0"
)

# Adicionar rate limiting se disponível
if RATE_LIMITING_AVAILABLE:
    app.state.limiter = limiter
    print("[INFO] Rate limiting ativado (Slowapi)")
else:
    print("[WARNING] Rate limiting desativado (instale: pip install slowapi)")

# Configurar CORS para localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*"  # Em desenvolvimento; remover em produção
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verificar se a pasta frontend existe
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """
    Endpoint raiz que serve o arquivo index.html
    """
    frontend_file = Path(__file__).parent / "frontend" / "index.html"
    if frontend_file.exists():
        print(f"[{datetime.now().isoformat()}] GET / - Servindo frontend (index.html)")
        return FileResponse(frontend_file, media_type="text/html")
    else:
        print(f"[{datetime.now().isoformat()}] GET / - Frontend não encontrado")
        return {
            "message": "PDF Summarizer AI API",
            "version": "1.0.0",
            "endpoints": {
                "summarize": "POST /summarize",
                "health": "GET /health"
            }
        }


@app.post("/summarize")
async def summarize(
    file: UploadFile = File(...),
    idioma: str = Query("pt", description="Idioma do resumo: 'pt' (português) ou 'en' (inglês)")
):
    """
    Endpoint para resumir um arquivo PDF
    
    - Recebe arquivo via multipart/form-data
    - Valida se é PDF pelo content_type
    - Valida tamanho máximo (10MB)
    - Salva temporariamente, processa e deleta
    - Retorna resumo com metadados
    
    Query Parameters:
        idioma: 'pt' para português (padrão) ou 'en' para inglês
    
    Args:
        file: Arquivo PDF enviado pelo cliente
    
    Returns:
        JSON com:
        - resumo: Texto do resumo gerado
        - paginas: Número de páginas do PDF
        - modelo: Modelo Claude utilizado
        - tokens_entrada: Tokens consumidos na entrada
        - tokens_saida: Tokens consumidos na saída
        - idioma: Idioma do resumo
        - status: "sucesso" ou "erro"
    
    Raises:
        HTTPException 400: Se não for um PDF válido ou muito grande
        HTTPException 500: Se houver erro no processamento
    """
    tempo_inicio = time.time()
    
    print(f"[{datetime.now().isoformat()}] POST /summarize - Arquivo recebido: {file.filename} (idioma: {idioma})")
    
    # Validar idioma
    if idioma not in ["pt", "en"]:
        print(f"[{datetime.now().isoformat()}] POST /summarize - Erro: idioma inválido ({idioma})")
        raise HTTPException(
            status_code=400,
            detail="Idioma deve ser 'pt' (português) ou 'en' (inglês)"
        )
    
    # Validar content_type
    if file.content_type not in ["application/pdf", "application/x-pdf"]:
        print(f"[{datetime.now().isoformat()}] POST /summarize - Erro: content_type inválido ({file.content_type})")
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo deve ser PDF. Recebido: {file.content_type}"
        )
    
    # Validar extensão do arquivo
    if not file.filename.lower().endswith(".pdf"):
        print(f"[{datetime.now().isoformat()}] POST /summarize - Erro: extensão inválida ({file.filename})")
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ter extensão .pdf"
        )
    
    temp_file_path = None
    
    try:
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file_path = temp_file.name
            conteudo = await file.read()
            temp_file.write(conteudo)
        
        # Validar tamanho do arquivo
        tamanho_arquivo = os.path.getsize(temp_file_path)
        if tamanho_arquivo > MAX_FILE_SIZE_BYTES:
            tamanho_mb = tamanho_arquivo / (1024 * 1024)
            print(f"[{datetime.now().isoformat()}] POST /summarize - Erro: arquivo muito grande ({tamanho_mb:.1f}MB)")
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE_MB}MB (seu arquivo: {tamanho_mb:.1f}MB)"
            )
        
        print(f"[{datetime.now().isoformat()}] POST /summarize - Arquivo salvo temporariamente: {temp_file_path} ({tamanho_arquivo} bytes)")
        
        # Validar se o arquivo não está vazio
        if tamanho_arquivo == 0:
            print(f"[{datetime.now().isoformat()}] POST /summarize - Erro: arquivo vazio")
            raise HTTPException(
                status_code=400,
                detail="Arquivo PDF está vazio"
            )
        
        # Processar PDF
        print(f"[{datetime.now().isoformat()}] POST /summarize - Iniciando processamento do PDF (idioma: {idioma})...")
        resultado = processar_pdf(temp_file_path, max_palavras=300)
        
        # Verificar se houve sucesso
        if not resultado.get("sucesso", False):
            print(f"[{datetime.now().isoformat()}] POST /summarize - Erro no processamento: {resultado.get('mensagem')}")
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar PDF: {resultado.get('mensagem')}"
            )
        
        # Calcular tempo de processamento
        tempo_total_ms = int((time.time() - tempo_inicio) * 1000)
        
        # Preparar resposta
        resposta = {
            "status": "sucesso",
            "resumo": resultado.get("resumo", ""),
            "paginas": resultado.get("num_pages", 0),
            "modelo": resultado.get("modelo_usado", ""),
            "tokens_entrada": resultado.get("tokens_entrada", 0),
            "tokens_saida": resultado.get("tokens_saida", 0),
            "idioma": idioma,
            "aviso": resultado.get("aviso")
        }
        
        print(f"[{datetime.now().isoformat()}] POST /summarize - Sucesso em {tempo_total_ms}ms: {resultado['num_pages']} páginas, {resultado['tokens_entrada']} tokens entrada, {resultado['tokens_saida']} tokens saída")
        
        # Retornar com header X-Processing-Time
        return JSONResponse(
            status_code=200,
            content=resposta,
            headers={"X-Processing-Time": str(tempo_total_ms)}
        )
        
    except HTTPException:
        raise
    
    except Exception as e:
        error_msg = f"Erro inesperado ao processar PDF: {str(e)}"
        print(f"[{datetime.now().isoformat()}] POST /summarize - {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # Limpar arquivo temporário
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"[{datetime.now().isoformat()}] POST /summarize - Arquivo temporário deletado: {temp_file_path}")
            except Exception as e:
                print(f"[{datetime.now().isoformat()}] POST /summarize - Aviso: Não foi possível deletar arquivo temporário: {e}")


@app.get("/health")
async def health_check():
    """
    Endpoint para verificar se a API está funcionando
    """
    print(f"[{datetime.now().isoformat()}] GET /health - API está online")
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "pdf-summarizer-ai",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.get("/info")
async def info():
    """
    Endpoint para retornar informações da API
    """
    print(f"[{datetime.now().isoformat()}] GET /info - Retornando informações da API")
    return {
        "nome": "PDF Summarizer AI",
        "versao": "1.0.0",
        "descricao": "API para resumir PDFs usando Claude AI",
        "endpoints": {
            "GET /": "Retorna a interface web (frontend)",
            "GET /health": "Verifica se a API está online",
            "GET /info": "Retorna informações da API",
            "POST /summarize": "Resumir um arquivo PDF",
            "POST /api/v2/summarize-com-cache": "Resumir com cache e histórico (autenticado)",
            "GET /api/v2/meus-resumos": "Ver histórico de resumos (autenticado)"
        }
    }


# Integrar endpoints avançados
if ADVANCED_FEATURES_AVAILABLE:
    app.include_router(advanced_router)
    print("[INFO] ✅ Endpoints avançados (autenticação, cache, BD) ativados!")
    print("       API v2 disponível em: /api/v2/")
else:
    print("[WARNING] Endpoints avançados desativados.")
    print("       Para ativar: pip install sqlalchemy redis python-jose passlib cryptography")


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("PDF SUMMARIZER AI - Iniciando servidor...")
    print("="*60)
    print("🚀 API disponível em: http://localhost:8000")
    print("📄 Frontend em: http://localhost:8000/")
    print("🏥 Health check em: http://localhost:8000/health")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

