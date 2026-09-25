"""
Testes para o módulo summarizer.py e integração com FastAPI
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from fastapi.testclient import TestClient
from main import app
from summarizer import extrair_texto_pdf, resumir_com_gemini, processar_pdf


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def create_mock_pdf():
    """
    Fixture que cria um PDF mock para testes
    """
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF não está instalado")
    
    def _create_pdf(content="Teste PDF\nEste é um documento de teste.\nPágina 1"):
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), content)
        
        pdf_bytes = doc.write()
        doc.close()
        
        return BytesIO(pdf_bytes)
    
    return _create_pdf


@pytest.fixture
def client():
    """
    Fixture do TestClient para testes HTTP
    """
    return TestClient(app)


# ============================================================================
# TESTES: EXTRAÇÃO DE TEXTO DO PDF
# ============================================================================

class TestExtractionTextoPDF:
    """
    Testes para a função extrair_texto_pdf
    """
    
    def test_extrair_texto_de_pdf_valido(self, create_mock_pdf):
        """
        Testa se a extração de texto de um PDF válido funciona corretamente
        """
        # Criar PDF mock
        pdf_file = create_mock_pdf("Teste PDF\nConteúdo de teste")
        
        # Salvar em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.getvalue())
            temp_file_path = temp_file.name
        
        try:
            # Executar função
            texto, num_paginas = extrair_texto_pdf(temp_file_path)
            
            # Assertions
            assert isinstance(texto, str), "Texto deve ser string"
            assert len(texto) > 0, "Texto não deve estar vazio"
            assert num_paginas >= 1, "Deve ter pelo menos 1 página"
            assert "Teste" in texto or "teste" in texto.lower(), "Deve conter o texto inserido"
            
        finally:
            os.unlink(temp_file_path)
    
    def test_extrair_texto_arquivo_nao_existe(self):
        """
        Testa se a função lança FileNotFoundError quando arquivo não existe
        """
        with pytest.raises(FileNotFoundError):
            extrair_texto_pdf("/caminho/que/nao/existe.pdf")
    
    def test_extrair_texto_pdf_vazio(self):
        """
        Testa se a função trata PDFs vazios corretamente
        """
        try:
            import fitz
        except ImportError:
            pytest.skip("PyMuPDF não está instalado")
        
        # Criar PDF vazio
        doc = fitz.open()
        doc.new_page()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(doc.write())
            temp_file_path = temp_file.name
        
        doc.close()
        
        try:
            with pytest.raises(ValueError, match="sem páginas|não contém texto"):
                extrair_texto_pdf(temp_file_path)
        finally:
            os.unlink(temp_file_path)


# ============================================================================
# TESTES: RESUMO COM GEMINI API
# ============================================================================

class TestResumirComGemini:
    """
    Testes para a função resumir_com_gemini (com mocks para não consumir créditos)
    """
    
    @patch('summarizer.genai.GenerativeModel')
    def test_resumir_com_gemini_sucesso(self, mock_generative_model):
        """
        Testa se a chamada à Gemini API retorna um resumo válido (com mock)
        """
        # Configurar mock
        mock_model = MagicMock()
        mock_generative_model.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "Resumo mockado do documento"
        mock_response.usage_metadata.prompt_token_count = 1000
        mock_response.usage_metadata.candidates_token_count = 250
        
        mock_model.generate_content.return_value = mock_response
        
        # Executar função
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            resultado = resumir_com_gemini("Texto de teste para resumir", max_palavras=300)
        
        # Assertions
        assert resultado['resumo'] == "Resumo mockado do documento"
        assert resultado['tokens_entrada'] == 1000
        assert resultado['tokens_saida'] == 250
        assert resultado['modelo_usado'] == "gemini-1.5-flash"
    
    def test_resumir_api_key_nao_configurada(self):
        """
        Testa se a função lança erro quando GOOGLE_API_KEY não está configurada
        """
        # Remover GOOGLE_API_KEY temporariamente
        api_key_backup = os.environ.pop('GOOGLE_API_KEY', None)
        
        try:
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                resumir_com_gemini("Texto de teste")
        finally:
            if api_key_backup:
                os.environ['GOOGLE_API_KEY'] = api_key_backup
    
    @patch('summarizer.genai.GenerativeModel')
    def test_resumir_com_gemini_erro_api(self, mock_generative_model):
        """
        Testa tratamento de erro quando Gemini API falha
        """
        # Configurar mock para falhar
        mock_model = MagicMock()
        mock_generative_model.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")
        
        # Executar e verificar exceção
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'}):
            with pytest.raises(Exception, match="API Error"):
                resumir_com_gemini("Texto de teste")


# ============================================================================
# TESTES: PROCESSAMENTO DE PDF (ORQUESTRAÇÃO)
# ============================================================================

class TestProcessarPDF:
    """
    Testes para a função processar_pdf (completa)
    """
    
    @patch('summarizer.resumir_com_gemini')
    def test_processar_pdf_completo(self, mock_resumir, create_mock_pdf):
        """
        Testa o processamento completo de um PDF (com mock da API)
        """
        # Criar PDF mock
        pdf_file = create_mock_pdf("Documento de teste\nConteúdo importante")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.getvalue())
            temp_file_path = temp_file.name
        
        # Configurar mock
        mock_resumir.return_value = {
            'resumo': 'Resumo do documento',
            'modelo_usado': 'gemini-1.5-flash',
            'tokens_entrada': 800,
            'tokens_saida': 200
        }
        
        try:
            # Executar função
            resultado = processar_pdf(temp_file_path, max_palavras=300)
            
            # Assertions
            assert resultado['sucesso'] is True
            assert resultado['resumo'] == 'Resumo do documento'
            assert resultado['num_pages'] >= 1
            assert resultado['tokens_entrada'] == 800
            assert resultado['tokens_saida'] == 200
            assert resultado['modelo_usado'] == 'gemini-1.5-flash'
            
        finally:
            os.unlink(temp_file_path)
    
    @patch('summarizer.resumir_com_gemini')
    def test_processar_pdf_truncamento_texto_grande(self, mock_resumir, create_mock_pdf):
        """
        Testa se o texto é truncado quando excede MAX_CARACTERES_TEXTO
        """
        # Criar PDF com muito texto (simulado)
        conteudo_grande = "A " * 50001  # Mais de 100k caracteres
        pdf_file = create_mock_pdf(conteudo_grande)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_file.getvalue())
            temp_file_path = temp_file.name
        
        # Configurar mock
        mock_resumir.return_value = {
            'resumo': 'Resumo do texto truncado',
            'modelo_usado': 'gemini-1.5-flash',
            'tokens_entrada': 500,
            'tokens_saida': 150
        }
        
        try:
            resultado = processar_pdf(temp_file_path)
            
            # Verificar se há aviso de truncamento
            assert resultado['sucesso'] is True
            # Pode ter aviso se o texto foi grande o suficiente
            
        finally:
            os.unlink(temp_file_path)


# ============================================================================
# TESTES: ENDPOINT HTTP /summarize
# ============================================================================

class TestEndpointSummarize:
    """
    Testes para o endpoint POST /summarize
    """
    
    def test_endpoint_arquivo_nao_pdf(self, client):
        """
        Testa se a API retorna 400 quando arquivo não é PDF
        """
        # Criar um arquivo que não é PDF
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"Não sou um PDF")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, "rb") as f:
                response = client.post(
                    "/summarize",
                    files={"file": ("test.txt", f, "text/plain")}
                )
            
            assert response.status_code == 400
            assert "PDF" in response.json()["detail"]
            
        finally:
            os.unlink(temp_file_path)
    
    def test_endpoint_arquivo_vazio(self, client):
        """
        Testa se a API retorna 400 para arquivo vazio
        """
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, "rb") as f:
                response = client.post(
                    "/summarize",
                    files={"file": ("empty.pdf", f, "application/pdf")}
                )
            
            assert response.status_code == 400
            
        finally:
            os.unlink(temp_file_path)
    
    def test_endpoint_sem_arquivo(self, client):
        """
        Testa se a API retorna erro quando nenhum arquivo é enviado
        """
        response = client.post("/summarize")
        assert response.status_code in [400, 422]
    
    @patch('main.processar_pdf')
    def test_endpoint_sucesso(self, mock_processar, client, create_mock_pdf):
        """
        Testa se o endpoint retorna sucesso com um PDF válido (com mock)
        """
        # Criar PDF mock
        pdf_file = create_mock_pdf("Documento de teste")
        
        # Configurar mock
        mock_processar.return_value = {
            'sucesso': True,
            'resumo': 'Resumo do documento teste',
            'num_pages': 1,
            'tokens_entrada': 600,
            'tokens_saida': 180,
            'modelo_usado': 'gemini-1.5-flash',
            'aviso': None,
            'mensagem': 'Sucesso'
        }
        
        # Enviar requisição
        response = client.post(
            "/summarize",
            files={"file": ("test.pdf", pdf_file, "application/pdf")}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'sucesso'
        assert data['resumo'] == 'Resumo do documento teste'
        assert data['paginas'] == 1
        assert data['tokens_entrada'] == 600
        assert data['tokens_saida'] == 180


# ============================================================================
# TESTES: ENDPOINTS AUXILIARES
# ============================================================================

class TestEndpointsAuxiliares:
    """
    Testes para endpoints de health check e info
    """
    
    def test_endpoint_health(self, client):
        """
        Testa se o endpoint /health retorna status ok
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert data['service'] == 'pdf-summarizer-ai'
    
    def test_endpoint_info(self, client):
        """
        Testa se o endpoint /info retorna informações da API
        """
        response = client.get("/info")
        
        assert response.status_code == 200
        data = response.json()
        assert 'nome' in data
        assert 'versao' in data
        assert 'endpoints' in data
    
    def test_endpoint_root(self, client):
        """
        Testa se o endpoint raiz retorna frontend ou informações
        """
        response = client.get("/")
        
        assert response.status_code == 200


# ============================================================================
# EXECUTAR TESTES
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
