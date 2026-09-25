"""
Módulo para extração de texto de PDFs e geração de resumos usando Claude API
"""

import os
import logging
from typing import Dict, Tuple
import fitz  # PyMuPDF
from anthropic import Anthropic
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
MAX_CARACTERES_TEXTO = 100_000
MODELO_CLAUDE = "claude-sonnet-4-20250514"
TAMANHO_RESUMO_PADRAO = 300


def extrair_texto_pdf(caminho_arquivo: str) -> Tuple[str, int]:
    """
    Extrair texto de um arquivo PDF usando PyMuPDF (fitz)
    
    Args:
        caminho_arquivo: Caminho para o arquivo PDF
    
    Returns:
        Tupla contendo:
        - texto_extraido (str): Texto completo extraído do PDF
        - numero_paginas (int): Número total de páginas
    
    Raises:
        FileNotFoundError: Se o arquivo não existe
        ValueError: Se não for um PDF válido ou estiver corrompido
    """
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
        # Abrir o PDF
        documento = fitz.open(caminho_arquivo)
        
        # Verificar se o PDF tem páginas
        numero_paginas = documento.page_count
        if numero_paginas == 0:
            raise ValueError("PDF está vazio (sem páginas)")
        
        logger.info(f"PDF aberto com sucesso: {numero_paginas} páginas")
        
        # Extrair texto de todas as páginas
        texto_completo = []
        for num_pagina in range(numero_paginas):
            try:
                pagina = documento[num_pagina]
                texto_pagina = pagina.get_text()
                texto_completo.append(texto_pagina)
            except Exception as e:
                logger.warning(f"Erro ao extrair texto da página {num_pagina + 1}: {str(e)}")
                continue
        
        # Fechar o documento
        documento.close()
        
        # Juntar todo o texto
        texto_extraido = "\n".join(texto_completo)
        
        if not texto_extraido.strip():
            raise ValueError("PDF não contém texto extraível")
        
        logger.info(f"Texto extraído com sucesso: {len(texto_extraido)} caracteres")
        
        return texto_extraido, numero_paginas
        
    except fitz.FileError as e:
        raise ValueError(f"PDF corrompido ou inválido: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
        raise


def resumir_com_gemini(texto: str, max_palavras: int = TAMANHO_RESUMO_PADRAO) -> Dict:
    """
    Gerar resumo do texto usando Google Gemini API
    
    Args:
        texto: Texto a ser resumido
        max_palavras: Número máximo de palavras no resumo (padrão: 300)
    
    Returns:
        Dicionário contendo:
        - resumo (str): Resumo estruturado gerado
        - modelo_usado (str): Nome do modelo Gemini utilizado
        - tokens_entrada (int): Tokens consumidos de entrada
        - tokens_saida (int): Tokens consumidos de saída
    
    Raises:
        ValueError: Se a chave da API não estiver configurada
        Exception: Se houver erro na chamada da API
    """
    # Validar chave da API
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não está configurada no arquivo .env")
    
    # Configurar o cliente Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODELO_GEMINI)
    
    # Preparar o prompt em português
    prompt = f"""Você é um assistente especializado em resumir documentos de forma estruturada.

Leia o texto a seguir e gere um resumo estruturado com:
1. **Tema Principal**: Uma frase resumindo o principal assunto
2. **Pontos-Chave**: Máximo 5 pontos principais (use bullets)
3. **Conclusão**: 2 linhas resumindo a ideia central

Mantenha o resumo em torno de {max_palavras} palavras.
Responda em português do Brasil.

---
TEXTO PARA RESUMIR:
{texto}
---

Gere o resumo estruturado agora:"""

    try:
        logger.info("Chamando Google Gemini API para gerar resumo...")
        
        # Chamar a API Gemini
        resposta = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=1024,
            )
        )
        
        # Extrair informações da resposta
        resumo = resposta.text
        # Gemini retorna usage_metadata com prompt_token_count e candidates_token_count
        tokens_entrada = resposta.usage_metadata.prompt_token_count
        tokens_saida = resposta.usage_metadata.candidates_token_count
        modelo_usado = MODELO_GEMINI
        
        logger.info(f"Resumo gerado com sucesso. Tokens - Entrada: {tokens_entrada}, Saída: {tokens_saida}")
        
        return {
            "resumo": resumo,
            "modelo_usado": modelo_usado,
            "tokens_entrada": tokens_entrada,
            "tokens_saida": tokens_saida
        }
        
    except Exception as e:
        logger.error(f"Erro ao chamar Google Gemini API: {str(e)}")
        raise


def processar_pdf(caminho_arquivo: str, max_palavras: int = TAMANHO_RESUMO_PADRAO) -> Dict:
    """
    Processo completo: extrair texto do PDF e gerar resumo com Gemini
    
    Orquestra as funções extrair_texto_pdf e resumir_com_gemini.
    Se o texto for maior que 100k caracteres, trunca com aviso.
    
    Args:
        caminho_arquivo: Caminho para o arquivo PDF
        max_palavras: Número máximo de palavras no resumo
    
    Returns:
        Dicionário com:
        - sucesso (bool): Se o processamento foi bem-sucedido
        - resumo (str): Texto do resumo gerado
        - num_pages (int): Número de páginas do PDF
        - tokens_entrada (int): Tokens consumidos de entrada
        - tokens_saida (int): Tokens consumidos de saída
        - modelo_usado (str): Modelo Gemini utilizado
        - aviso (str): Mensagem de aviso se houver (ex: texto truncado)
        - mensagem (str): Mensagem descritiva ou de erro
    """
    
    resultado_base = {
        "sucesso": False,
        "resumo": "",
        "num_pages": 0,
        "tokens_entrada": 0,
        "tokens_saida": 0,
        "modelo_usado": "",
        "aviso": None,
        "mensagem": ""
    }
    
    try:
        logger.info(f"Iniciando processamento do PDF: {caminho_arquivo}")
        
        # Etapa 1: Extrair texto do PDF
        logger.info("Etapa 1: Extração de texto do PDF...")
        texto_extraido, numero_paginas = extrair_texto_pdf(caminho_arquivo)
        
        # Etapa 2: Verificar tamanho do texto
        tamanho_texto = len(texto_extraido)
        logger.info(f"Tamanho do texto extraído: {tamanho_texto} caracteres")
        
        aviso = None
        if tamanho_texto > MAX_CARACTERES_TEXTO:
            aviso = f"Atenção: Texto truncado de {tamanho_texto} para {MAX_CARACTERES_TEXTO} caracteres"
            texto_extraido = texto_extraido[:MAX_CARACTERES_TEXTO]
            logger.warning(aviso)
        
        # Etapa 3: Gerar resumo com Gemini
        logger.info("Etapa 2: Geração do resumo com Google Gemini API...")
        resultado_resumo = resumir_com_gemini(texto_extraido, max_palavras)
        
        # Etapa 4: Montar resultado final
        resultado_base.update({
            "sucesso": True,
            "resumo": resultado_resumo["resumo"],
            "num_pages": numero_paginas,
            "tokens_entrada": resultado_resumo["tokens_entrada"],
            "tokens_saida": resultado_resumo["tokens_saida"],
            "modelo_usado": resultado_resumo["modelo_usado"],
            "aviso": aviso,
            "mensagem": f"PDF processado com sucesso: {numero_paginas} páginas, {tamanho_texto} caracteres"
        })
        
        logger.info("Processamento concluído com sucesso")
        return resultado_base
        
    except FileNotFoundError as e:
        resultado_base["mensagem"] = f"Erro: Arquivo não encontrado - {str(e)}"
        logger.error(resultado_base["mensagem"])
        return resultado_base
        
    except ValueError as e:
        resultado_base["mensagem"] = f"Erro: {str(e)}"
        logger.error(resultado_base["mensagem"])
        return resultado_base
        
    except Exception as e:
        resultado_base["mensagem"] = f"Erro inesperado ao processar PDF: {str(e)}"
        logger.error(resultado_base["mensagem"])
        return resultado_base


def get_summarizer() -> "PDFSummarizerSimples":
    """
    Factory function para obter instância compatível (interface simplificada)
    
    Returns:
        Objeto com método process_pdf para compatibilidade com código existente
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não está configurada no arquivo .env")
    
    return PDFSummarizerSimples()


class PDFSummarizerSimples:
    """
    Classe wrapper para interface compatível com código existente
    """
    
    def process_pdf(self, file_path: str, tamanho_resumo: str = "medium") -> Dict:
        """
        Método compatível que chama a função processar_pdf
        
        Args:
            file_path: Caminho do arquivo PDF
            tamanho_resumo: 'short' (150), 'medium' (300), 'long' (500)
        
        Returns:
            Dicionário com resultado do processamento
        """
        # Mapear tamanho_resumo para max_palavras
        tamanhos = {
            "short": 150,
            "medium": 300,
            "long": 500
        }
        max_palavras = tamanhos.get(tamanho_resumo, 300)
        
        return processar_pdf(file_path, max_palavras)
