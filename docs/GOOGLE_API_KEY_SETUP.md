# 🔑 Configuração da Google Gemini API Key

Seu projeto foi migrado de **Claude API** para **Google Gemini API**, que é **completamente grátis**!

## ⚡ Como Obter a API Key

### 1. **Acesse o Google AI Studio**
   - Vá para: https://aistudio.google.com/app/apikey
   - Se não estiver logado, faça login com sua conta Google (é grátis!)

### 2. **Crie uma API Key**
   - Clique no botão **"Create API Key"** ou **"+ Criar chave de API"**
   - Selecione o projeto padrão
   - A chave será gerada automaticamente (formato: `AIzaSy...`)

### 3. **Configure no Projeto**
   - Copie a chave gerada
   - Crie/abra o arquivo `.env` na raiz do projeto
   - Cole a seguinte linha:
   ```env
   GOOGLE_API_KEY=AIzaSy_sua_chave_aqui
   ```

## 📝 Exemplo de .env

```env
# Chave da API Google Gemini
GOOGLE_API_KEY=AIzaSy_suaChaveAquiAquiAquiAquiAqui

# Configurações opcionais
HOST=127.0.0.1
PORT=8000
DEBUG=true
```

## ✅ Verificar se Está Funcionando

Depois de configurar a chave, execute:

```bash
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Rodar o servidor
python main.py
```

Acesse http://localhost:8000 e teste enviar um PDF!

## 🎯 Limites da API Gratuita

- **500.000 tokens/mês** (grátis)
- **60 requisições/minuto** (limite de rate)
- **32k tokens** por requisição (máximo de contexto)

Isso é **mais que suficiente** para desenvolvimento e uso pessoal!

## 🚀 Mudanças Realizadas

As seguintes mudanças foram feitas automaticamente:

| Arquivo | Mudança |
|---------|---------|
| `summarizer.py` | Trocar `Anthropic` por `google.generativeai` |
| `requirements.txt` | Remover `anthropic`, adicionar `google-generativeai` |
| `.env.example` | Trocar `ANTHROPIC_API_KEY` por `GOOGLE_API_KEY` |
| `main.py` | Atualizar descrição para "Gemini AI" |
| `test_summarizer.py` | Atualizar mocks para Gemini API |

## ⚠️ Notas Importantes

1. **Não exponha sua chave**: Nunca commit o arquivo `.env`
2. **Rotação de chefs**: Para segurança, revogue chaves antigas em https://aistudio.google.com/app/apikey
3. **Monitoramento**: Acompanhe o uso em https://console.cloud.google.com/

## 🆘 Problemas?

Se receber erro `GOOGLE_API_KEY não configurada`:
1. Verifique se o arquivo `.env` existe e está na raiz do projeto
2. Verifique se a variável está formatada corretamente: `GOOGLE_API_KEY=AIzaSy_...`
3. Certifique-se que não há espaços antes ou depois do valor
4. Reinicie o servidor (kill Python e execute `python main.py` novamente)

## 📚 Referências

- **Google AI Studio**: https://aistudio.google.com/
- **Documentação Gemini**: https://ai.google.dev/docs
- **SDK Python**: https://github.com/google/generative-ai-python

---

**Pronto para começar? Configure a chave e execute `python main.py`!** 🎉
