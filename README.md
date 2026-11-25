# 📄 PDF Summarizer AI

API REST para resumir documentos PDF automaticamente usando Google Gemini AI (100% GRÁTIS!).

**Versão:** 1.0.0  
**Linguagem:** Python 3.8+  
**Framework:** FastAPI + Uvicorn  
**IA:** Google Gemini-1.5-flash

---

## ⚡ IMPORTANTE: Migração de Claude para Google Gemini

✅ **Este projeto foi migrado de Claude API (pago) para Google Gemini (GRÁTIS!)**

**Mudanças principais:**
- 🆓 **Free tier:** 500.000 tokens/mês (sem cartão de crédito)
- 🚀 **Rápido:** Google Gemini-1.5-flash é muito performático
- 📚 **Fácil setup:** Configure em 2 minutos (veja [GOOGLE_API_KEY_SETUP.md](./GOOGLE_API_KEY_SETUP.md))

**Se você tem uma chave Claude antiga:**
- Ainda funciona! Apenas troque a chave no `.env`
- Recomendamos usar Gemini primeiro (é grátis)

### 📊 Comparação: Claude vs Google Gemini

| Feature | Claude API | Google Gemini |
|---------|-----------|---------------|
| **Custo** | 💰 Pago (3-30$/MTk tokens) | 🆓 Grátis (500k tokens/mês) |
| **Setup** | Necessário cartão de crédito | Email Google apenas |
| **Velocidade** | Muito rápido | 🚀 Relâmpago (Gemini-1.5-flash) |
| **Qualidade** | Excelente | ⭐ Excelente |
| **Rate Limit** | Varável por plano | 60 req/min (grátis) |
| **Contexto** | 200k tokens | 1M tokens (Gemini-1.5-pro) |
| **Latência** | 2-5 segundos | 1-3 segundos |

✅ **Resultado:** Para desenvolvimento e MVP, **Gemini é a melhor escolha!**

---

## 🚀 Quick Start

### 1. Clonar/Preparar Projeto

```bash
cd pdf-summarizer-ai
```

### 2. Criar e Ativar Ambiente Virtual

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env e adicionar sua chave da API Google Gemini
# GOOGLE_API_KEY=AIzaSy_...
```

### 5. Iniciar Servidor

```bash
python main.py
```

A API estará disponível em: **http://localhost:8000**

---

## 📚 Endpoints da API

### GET /
Retorna a interface web (frontend HTML).

```bash
curl http://localhost:8000
```

### POST /summarize
Resumir um arquivo PDF.

**Query Parameters:**
- `idioma` (opcional): `pt` (português, padrão) ou `en` (inglês)

**Request:**
```bash
curl -X POST http://localhost:8000/summarize \
  -F "file=@documento.pdf" \
  -H "Accept: application/json"
```

**Response (200 OK):**
```json
{
  "status": "sucesso",
  "resumo": "Resumo estruturado do documento...",
  "paginas": 10,
  "modelo": "gemini-1.5-flash",
  "tokens_entrada": 1250,
  "tokens_saida": 450,
  "idioma": "pt",
  "aviso": null
}
```

**Headers customizados:**
- `X-Processing-Time`: Tempo de processamento em ms

**Erros (400/500):**
```json
{
  "detail": "Arquivo muito grande. Máximo: 10MB (seu arquivo: 25.5MB)"
}
```

### GET /health
Verificar se a API está online.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "pdf-summarizer-ai",
  "timestamp": "2026-03-26T14:30:45.123456"
}
```

### GET /info
Obter informações sobre a API.

```bash
curl http://localhost:8000/info
```

---

## 🧪 Testes

Executar suite de testes:

```bash
# Todos os testes
pytest test_summarizer.py -v

# Teste específico
pytest test_summarizer.py::TestExtractionTextoPDF::test_extrair_texto_de_pdf_valido -v

# Com coverage
pytest test_summarizer.py --cov=summarizer --cov=main
```

**Testes incluídos:**
- ✅ Extração de texto de PDF
- ✅ Validação de tipo de arquivo
- ✅ Mock da Google Gemini API (sem consumir créditos)
- ✅ Endpoints HTTP
- ✅ Tratamento de erros
- ✅ Health checks

---

## 📋 Estrutura do Projeto

```
pdf-summarizer-ai/
├── main.py                  # Backend FastAPI com endpoints
├── summarizer.py            # Lógica de extração e resumo
├── test_summarizer.py       # Testes pytest
├── requirements.txt         # Dependências Python
├── .env.example             # Variáveis de ambiente (exemplo)
├── .gitignore               # Arquivos a ignorar no git
├── frontend/
│   └── index.html          # Interface web (HTML + CSS + JS)
├── venv/                    # Ambiente virtual (não commit)
└── README.md                # Este arquivo
```

---

## 🔧 Configuração

### Variáveis de Ambiente (.env)

```bash
# OBRIGATÓRIA
GOOGLE_API_KEY=AIzaSy_...         # Chave da API Google Gemini (obtenha em: https://aistudio.google.com/app/apikey)

# OPCIONAIS
HOST=0.0.0.0                      # Host da API (padrão: localhost)
PORT=8000                         # Porta (padrão: 8000)
DEBUG=false                       # Modo debug
MAX_FILE_SIZE_MB=10              # Tamanho máximo de arquivo
TIMEOUT_SECONDS=300              # Timeout de processamento
IDIOMA_PADRAO=pt                 # Idioma padrão (pt/en)
```

Veja `.env.example` para documentação completa.

---

## 📊 Limites e Restrições

| Limite | Valor |
|--------|-------|
| Tamanho máximo de arquivo | 10 MB |
| Timeout de processamento | 300 segundos |
| Máximo de caracteres (truncado) | 100.000 caracteres |
| Modelos suportados | gemini-1.5-flash |

---

## 🎨 Frontend

Interface web moderna com:
- Design dark mode (gradiente azul/roxo)
- Drag-and-drop de arquivos
- Validação de tipo/tamanho
- Spinner de loading
- Exibição de resultados com badges
- Responsivo para mobile
- Mensagens de erro amigáveis

Acesse em: **http://localhost:8000/**

---

## 📦 Dependências Principais

| Lib | Versão | Uso |
|-----|--------|-----|
| fastapi | 0.135.2 | Framework web |
| uvicorn | 0.42.0 | Servidor ASGI |
| PyMuPDF | 1.27.2.2 | Extração de PDF |
| google-generativeai | 0.7.0 | Cliente Google Gemini API |
| pydantic | 2.12.5 | Validação |
| pytest | 9.0.2 | Testes |

Veja `requirements.txt` para a lista completa.

---

## 🐛 Troubleshooting

### "ImportError: No module named 'fitz'"
```bash
pip install PyMuPDF==1.27.2.2
```

### "GOOGLE_API_KEY not found"
- Copiar `.env.example` para `.env`
- Obter chave em: **https://aistudio.google.com/app/apikey**
- Adicionar no .env: `GOOGLE_API_KEY=AIzaSy_...`
- Reiniciar o servidor

📚 **Guia completo:** Veja [GOOGLE_API_KEY_SETUP.md](./GOOGLE_API_KEY_SETUP.md) para instruções detalhadas

### "PDF está vazio" ou "não contém texto"
- Verificar se o PDF tem texto extraível (não apenas imagens)
- Tentar com outro PDF

### Timeout ao processar PDF grande
- Aumentar `TIMEOUT_SECONDS` no `.env`
- Reduzir tamanho do arquivo
- Usar versão mais recente do PyMuPDF

---

## 🚢 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build e run:
```bash
docker build -t pdf-summarizer-ai .
docker run -p 8000:8000 -e GOOGLE_API_KEY=xxx pdf-summarizer-ai
```

### Gunicorn (Produção)

```bash
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Variáveis de Produção

```bash
# .env (produção)
DEBUG=false
CORS_ORIGINS=https://seudominio.com
GOOGLE_API_KEY=AIzaSy_...
HOST=0.0.0.0
PORT=8000
```

---

## 🪲 Logging

Logs são exibidos no stdout com timestamp ISO:

```
[2026-03-26T14:30:45.123456] POST /summarize - Arquivo recebido: documento.pdf
[2026-03-26T14:30:46.456789] POST /summarize - Sucesso em 1234ms: 10 páginas...
```

Para arquivo de log, adicione ao `.env`:
```bash
LOG_FILE=pdf-summarizer.log
```

---

## 📈 Monitoramento

**Health check recomendado:**
```bash
# A cada 30 segundos
while true; do
  curl -s http://localhost:8000/health | jq .
  sleep 30
done
```

**Métricas disponíveis no response:**
- `X-Processing-Time`: Tempo total em ms
- `tokens_entrada`: Tokens de entrada da API
- `tokens_saida`: Tokens de saída da API

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**
- Nunca commit do arquivo `.env` com chave real
- Usar `.gitignore` para proteger `*.env`
- Em produção: desabilitar CORS (* ) 
- Usar HTTPS/SSL
- Restaurar API key se comprometida
- Armazenar chaves em variáveis de ambiente (não hardcoded)

---

## 🤝 Sugestões de Melhorias Futuras

### 🚀 Curto Prazo

1. **Cache de Resumos**
   - Armazenar resumos já gerados
   - Evitar reprocessamento do mesmo PDF
   ```python
   @app.post("/summarize")
   async def summarize(...):
       file_hash = hashlib.md5(content).hexdigest()
       if file_hash in cache:
           return cache[file_hash]
   ```

2. **Fila de Processamento**
   - Usar Celery + Redis para PDFs grandes
   - Retornar job_id para polling assíncrono
   ```python
   result = processar_pdf_async.delay(file_path)
   return {"job_id": result.id, "status": "processing"}
   ```

3. **Banco de Dados**
   - SQLAlchemy + PostgreSQL
   - Armazenar histórico de resumos
   - Rastreamento de uso por usuário

### 🎯 Médio Prazo

4. **Autenticação**
   - JWT tokens
   - Limite de requisições por usuário (rate limiting)
   - Billing/quotas

5. **Múltiplos Idiomas**
   - Suporte a mais idiomas (es, fr, de, ja, zh)
   - Detecção automática de idioma original

6. **Tipos de Resumo**
   - Bullet points
   - Mind map
   - Timeline
   - Índice/TOC

7. **Análise do Documento**
   ```json
   {
     "resumo": "...",
     "sentimento": "positivo",
     "palavras_chave": ["tema1", "tema2"],
     "entidades_nomeadas": ["Empresa X", "Pessoa Y"],
     "perguntas_respondidas": ["P1?", "P2?"]
   }
   ```

### 🌟 Longo Prazo

8. **Interface Web Avançada**
   - Dark/light mode toggle
   - Edição de resumo inline
   - Exportar para PDF/Word/Markdown
   - Histórico de resumos

9. **Integração com Serviços**
   - Webhook para notificações
   - Integração com Slack/Teams
   - Exportar para Google Drive/AWS S3
   - API OpenAI alternativa (GPT-4)

10. **Performance**
    - Processamento paralelo de múltiplos PDFs
    - Compressão de respostas (gzip)
    - CDN para frontend
    - Monitoring com Prometheus/Grafana

11. **Modelos Alternativos**
    ```python
    # Além de Gemini-1.5-flash
    "gemini-1.5-pro": "Modelo mais poderoso (contexto maior, mais tokens)",
    "gemini-2.0-flash": "Versão mais nova (quando disponível)",
    "claude-3": "Integração com Claude (pago)",
    "gpt-4": "Integração com OpenAI (pago)",
    "llama2": "Modelo open-source local (offline)"
    ```

---

## 📝 Notas de Desenvolvimento

### Adicionar Nova Dependência

```bash
# Instalar
pip install nome-da-lib

# Atualizar requirements.txt
pip freeze > requirements.txt
```

### Executar Testes com Coverage

```bash
pytest test_summarizer.py --cov=. --cov-report=html
# Abrir htmlcov/index.html
```

### Debug de Requisição

```python
# Adicione ao main.py:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ou use:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Formatação de Código

```bash
# Black (formatter)
black main.py summarizer.py

# Flake8 (linter)
flake8 main.py summarizer.py

# Ambos (recomendado)
black . && flake8 .
```

---

## 📄 Licença

MIT - Sinta-se livre para usar, modificar e distribuir.

---

## 👨‍💻 Suporte

Para problemas ou sugestões:
1. Verificar arquivo `.env` está configurado
2. Executar testes: `pytest test_summarizer.py -v`
3. Verificar logs no console
4. Testar com `curl` antes de usar frontend
5. Consultar troubleshooting acima

---

## 🔄 Migração de Claude para Google Gemini (Fácil!)

Se você tinha este projeto rodando com **Claude API** antes, aqui estão os passos para migrar:

### 3 passos simples:

**1️⃣ Obter Google API Key:**
```bash
1. Vá para: https://aistudio.google.com/app/apikey
2. Clique em "Create API Key"
3. Copie: AIzaSy_...
```

**2️⃣ Atualizar `.env`:**
```bash
# Remova:
# ANTHROPIC_API_KEY=sk-ant-...

# Adicione:
GOOGLE_API_KEY=AIzaSy_...
```

**3️⃣ Reinstalar dependências:**
```bash
pip install -r requirements.txt
python main.py
```

**Pronto!** Seu projeto já usa Google Gemini automaticamente ✅

### O que mudou internamente?

```python
# ANTES (Claude):
from anthropic import Anthropic
resultado = client.messages.create(model="claude-sonnet-4-20250514")

# DEPOIS (Gemini):
import google.generativeai as genai
model = genai.GenerativeModel("gemini-1.5-flash")
resultado = model.generate_content(prompt)
```

✅ **Resultado:** Mesma funcionalidade, **sem custos!** 🎉

---

## ✨ Resumo das Implementações

✅ **Completo:**
- FastAPI backend com 4 endpoints
- Extração de texto com PyMuPDF
- Integração com Google Gemini API (100% GRÁTIS!)
- Frontend HTML moderno com drag-drop
- Testes pytest com mocks
- Cabeçalho X-Processing-Time
- Parâmetro ?idioma para multi-idioma
- Limite de tamanho (10MB)
- Documentação completa
- requirements.txt com versões fixas
- .env.example bem documentado
- Guia de configuração Google API Key (GOOGLE_API_KEY_SETUP.md)

🎯 **Pronto para Produção:**
- Error handling robusto
- Validações de entrada
- Logging estruturado
- Limpeza de arquivos temporários
- CORS configurável
- Health checks

---

## 🎯 Próximos Passos

1. **Começar agora:** 
   - Obter [Google API Key](https://aistudio.google.com/app/apikey) (2 minutos)
   - Copiar para `.env`
   - Rodar `python main.py`

2. **Teste com seus PDFs:**
   - Acesse http://localhost:8000
   - Upload um PDF
   - Veja o resumo em segundos ⚡

3. **Explore as melhorias** (veja [SUGESTOES.md](./SUGESTOES.md)):
   - Cache de resumos
   - Banco de dados
   - Autenticação
   - Deploy em produção

---

**Autor:** [Ariston Gomes](https://www.linkedin.com/in/ariston-gomes/) • Projeto desenvolvido para aplicação prática de processamento inteligente de documentos.
