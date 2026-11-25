# PDF Summarizer AI

API REST desenvolvida em **Python** e **FastAPI** para extração de texto e sumarização automatizada de documentos PDF utilizando **Google Gemini (`gemini-1.5-flash`)**, com suporte a cache por hash de arquivo, persistência em banco de dados, autenticação JWT e controle de taxa de requisições (rate limiting).

---

## Principais Funcionalidades

- **Extração e Sumarização de PDFs:** leitura de documentos via `PyMuPDF` (`fitz`) e geração de resumos estruturados em português ou inglês.
- **Métricas de Processamento:** retorno de contagem de páginas, tokens de entrada/saída e tempo de execução no cabeçalho `X-Processing-Time`.
- **Cache Inteligente (`Redis` / Fallback Local):** identificação de documentos por hash para evitar reprocessamento e consumo desnecessário de tokens.
- **Autenticação e Histórico (API v2):** endpoints protegidos via JWT (`bcrypt`) com persistência de histórico de resumos em banco de dados (`SQLAlchemy` — SQLite/PostgreSQL).
- **Interface Web Integrada:** frontend leve em HTML/CSS/JS com upload via drag-and-drop e visualização imediata das métricas.

---

## Critérios de Escolha do Modelo (Custo vs. Performance)

A arquitetura utiliza o modelo **`gemini-1.5-flash`** para equilibrar baixa latência em documentos longos e eficiência de custo operacional:

| Critério | LLMs Comerciais Tradicionais (Tier Pago) | Google Gemini 1.5 Flash |
| :--- | :--- | :--- |
| **Custo por Volume** | US$ 3,00 – US$ 15,00 / 1M tokens | Free Tier disponível (até 1.500 req/dia) e baixo custo por milhão de tokens em produção |
| **Janela de Contexto** | 128k – 200k tokens | Até 1M tokens (suporta PDFs extensos sem truncamento agressivo) |
| **Latência Média** | 2 – 5 segundos | 1 – 3 segundos |
| **Rate Limit (Free Tier)** | Restrito a créditos pré-pagos | Até 15 – 60 req/min (adequado para MVPs e cargas moderadas) |

---

## Estrutura do Projeto

```text
pdf-summarizer-ai/
├── main.py                      # Aplicação FastAPI principal (endpoints v1 e inicialização)
├── summarizer.py                # Extração de texto (PyMuPDF) e integração com Gemini
├── advanced_endpoints.py        # Rotas v2 (autenticação, cache e histórico)
├── auth.py                      # Autenticação JWT e hashing de senhas
├── cache.py                     # Camada de cache (Redis com degradação graciosa)
├── database.py                  # Modelos e sessão SQLAlchemy
├── frontend/
│   └── index.html               # Interface web para upload e visualização
├── tests/
│   └── test_summarizer.py       # Suíte de testes automatizados (Pytest + Mocks)
├── docs/                        # Documentação complementar de setup e recursos v2
├── requirements.txt             # Dependências do projeto
└── .env.example                 # Template de variáveis de ambiente
```

---

## Configuração e Execução Local

### 1. Ambiente Virtual e Dependências

```bash
# Criar e ativar ambiente virtual (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env` e configure sua chave de API do [Google AI Studio](https://aistudio.google.com/app/apikey):

```env
GOOGLE_API_KEY=sua_chave_aqui
HOST=0.0.0.0
PORT=8000
DEBUG=false
MAX_FILE_SIZE_MB=10
TIMEOUT_SECONDS=300
IDIOMA_PADRAO=pt
```

### 3. Iniciar o Servidor

```bash
python main.py
```

A aplicação e a interface web ficarão disponíveis em `http://localhost:8000`.

---

## Endpoints Principais

### Sumarização Direta (v1)

- **`POST /summarize`** — Envia um arquivo PDF (`multipart/form-data`) e retorna o resumo estruturado.
  - Query param opcional: `idioma` (`pt` ou `en`).

```bash
curl -X POST "http://localhost:8000/summarize?idioma=pt" \
  -F "file=@documento.pdf" \
  -H "Accept: application/json"
```

**Exemplo de Resposta (`200 OK`):**
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

- **`GET /health`** — Verificação de disponibilidade do serviço.
- **`GET /info`** — Metadados e limites configurados na API.

### Recursos Avançados (v2)

- **`POST /api/v2/auth/cadastro`** e **`POST /api/v2/auth/login`** — Registro e autenticação JWT.
- **`POST /api/v2/summarize-com-cache`** — Sumarização autenticada com verificação de hash em cache e gravação no banco.
- **`GET /api/v2/meus-resumos`** — Listagem paginada do histórico de resumos do usuário.

*(Consulte [`docs/README_ADVANCED_FEATURES.md`](docs/README_ADVANCED_FEATURES.md) para detalhes das rotas v2).*

---

## Testes

A suíte de testes valida a extração de PDF, limites de arquivo, rotas HTTP e utiliza *mocks* para a API do Gemini (sem consumo de cota durante os testes):

```bash
pytest tests/test_summarizer.py -v
```

---

## Autor e Licença

- **Autor:** [Ariston Gomes](https://www.linkedin.com/in/ariston-gomes/)
- **Licença:** Distribuído sob a licença MIT.
