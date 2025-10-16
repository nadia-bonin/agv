###Como Executar

1. Executar todos os testes:
bashpytest tests/test_auth_complete.py -v

2. Executar uma classe específica:
bashpytest tests/test_auth_complete.py::TestRegistration -v

3. Executar um teste específico:
bashpytest tests/test_auth_complete.py::TestLogin::test_login_success -v

4. Com cobertura de código:
bashpytest tests/test_auth_complete.py --cov=src --cov-report=html

5. Com output detalhado:
bashpytest tests/test_auth_complete.py -v -s --tb=short

Adicionando Novos Testes

python {
pythonclass TestNewFeature:
    """Testes de nova funcionalidade"""
    
    def test_new_feature(self, auth_service, registered_user):
        """Teste: Nova funcionalidade"""
        # Arrange
        expected_result = "valor_esperado"
        
        # Act
        result = auth_service.new_method()
        
        # Assert
        assert result == expected_result
}
