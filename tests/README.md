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


###Como Testar

pytest tests/test_auth_complete.py -v

def test_password_validation():
    """Testa validação de senha"""
    print_section("1. TESTE DE VALIDAÇÃO DE SENHA")

    from src.utils.password import PasswordManager

    test_cases = [
        ("123", False, "Muito curta"),
        ("senhafraca", False, "Sem maiúscula e números"),
        ("Senha123", False, "Sem caractere especial"),
        ("Senha@123", True, "Válida"),
    ]

    pm = PasswordManager()

    for password, expected_valid, description in test_cases:
        is_valid, message = pm.validate_password_strength(password)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"{status} {description}: {password}")
        print(f"   → {message}")

def test_password_hash_verify():
    """Testa hash e verificação de senha"""
    print_section("2. TESTE DE HASH E VERIFICAÇÃO DE SENHA")

    from src.utils.password import PasswordManager

    pm = PasswordManager()
    password = "Senha@123"

    # Hash
    hashed = pm.hash_password(password)
    print_info(f"Senha original: {password}")
    print_info(f"Hash gerado: {hashed[:50]}...")

    # Verificar correto
    is_correct = pm.verify_password(password, hashed)
    if is_correct:
        print_success("Verificação com senha correta: OK")
    else:
        print_error("Falha na verificação com senha correta")

    # Verificar incorreto
    is_incorrect = pm.verify_password("SenhaErrada@123", hashed)
    if not is_incorrect:
        print_success("Verificação com senha incorreta: OK (corretamente rejeitada)")
    else:
        print_error("Falha ao rejeitar senha incorreta")

def test_jwt_tokens():
    """Testa criação e validação de JWT tokens"""
    print_section("3. TESTE DE JWT TOKENS")

    from src.utils.token import TokenManager

    tm = TokenManager()

    # Criar access token
    access_token = tm.create_access_token(
        user_id=1,
        email="teste@example.com",
        roles=["user", "admin"]
    )
    print_success(f"Access token criado: {access_token[:50]}...")

    # Decodificar
    payload = tm.decode_token(access_token)
    print_success(f"Token decodificado com sucesso")
    print_info(f"  User ID: {payload['sub']}")
    print_info(f"  Email: {payload['email']}")
    print_info(f"  Roles: {payload['roles']}")

    # Criar refresh token
    refresh_token = tm.create_refresh_token(user_id=1)
    print_success(f"Refresh token criado: {refresh_token[:50]}...")

    # Verificar tipo
    verified_access = tm.verify_token(access_token, 'access')
    if verified_access:
        print_success("Verificação de access token: OK")

    verified_refresh = tm.verify_token(refresh_token, 'refresh')
    if verified_refresh:
        print_success("Verificação de refresh token: OK")

def test_registration():
    """Testa registro de usuário"""
    print_section("4. TESTE DE REGISTRO DE USUÁRIO")

    auth_service = AuthService()

    # Teste 1: Registro bem-sucedido
    try:
        result = auth_service.register(
            name="Maria Silva",
            email=f"maria_{datetime.now().timestamp()}@example.com",
            password="Senha@123"
        )
        print_success(f"Usuário registrado: {result['user'].name}")
        print_info(f"  ID: {result['user'].id}")
        print_info(f"  Email: {result['user'].email}")
        print_info(f"  Token type: {result['token_type']}")
        test_registration.user_id = result['user'].id
        test_registration.user_email = result['user'].email
        test_registration.access_token = result['access_token']
        test_registration.refresh_token = result['refresh_token']
    except Exception as e:
        print_error(f"Erro no registro: {e}")

    # Teste 2: Senha fraca
    try:
        auth_service.register(
            name="João",
            email="joao@example.com",
            password="123"
        )
        print_error("Deveria ter rejeitado senha fraca")
    except ValidationError as e:
        print_success(f"Senha fraca corretamente rejeitada: {e}")

    # Teste 3: Email duplicado
    try:
        auth_service.register(
            name="Maria Duplicada",
            email=test_registration.user_email,
            password="Senha@123"
        )
        print_error("Deveria ter rejeitado email duplicado")
    except DuplicateRecordError as e:
        print_success(f"Email duplicado corretamente rejeitado: {e}")

def test_login():
    """Testa login de usuário"""
    print_section("5. TESTE DE LOGIN")

    auth_service = AuthService()

    # Teste 1: Login bem-sucedido
    try:
        result = auth_service.login(
            email=test_registration.user_email,
            password="Senha@123"
        )
        print_success(f"Login realizado: {result['user'].name}")
        print_info(f"  Access token: {result['access_token'][:50]}...")
        print_info(f"  Refresh token: {result['refresh_token'][:50]}...")
    except InvalidCredentialsError as e:
        print_error(f"Erro no login: {e}")

    # Teste 2: Senha incorreta
    try:
        auth_service.login(
            email=test_registration.user_email,
            password="SenhaErrada@123"
        )
        print_error("Deveria ter rejeitado senha incorreta")
    except InvalidCredentialsError as e:
        print_success(f"Senha incorreta corretamente rejeitada: {e}")

    # Teste 3: Email não existe
    try:
        auth_service.login(
            email="naoexiste@example.com",
            password="Senha@123"
        )
        print_error("Deveria ter rejeitado email inexistente")
    except InvalidCredentialsError as e:
        print_success(f"Email inexistente corretamente rejeitado: {e}")

def test_token_refresh():
    """Testa renovação de token"""
    print_section("6. TESTE DE RENOVAÇÃO DE TOKEN")

    auth_service = AuthService()

    # Renovar token
    try:
        result = auth_service.refresh_access_token(test_registration.refresh_token)
        print_success("Token renovado com sucesso")
        print_info(f"  Novo access token: {result['access_token'][:50]}...")
        test_registration.access_token = result['access_token']
    except InvalidCredentialsError as e:
        print_error(f"Erro ao renovar token: {e}")

    # Tentar com token inválido
    try:
        auth_service.refresh_access_token("token_invalido")
        print_error("Deveria ter rejeitado token inválido")
    except InvalidCredentialsError as e:
        print_success(f"Token inválido corretamente rejeitado: {e}")

def test_change_password():
    """Testa alteração de senha"""
    print_section("7. TESTE DE ALTERAÇÃO DE SENHA")

    auth_service = AuthService()

    # Alterar para nova senha válida
    try:
        auth_service.change_password(
            user_id=test_registration.user_id,
            old_password="Senha@123",
            new_password="NovaSenha@456"
        )
        print_success("Senha alterada com sucesso")
    except Exception as e:
        print_error(f"Erro ao alterar senha: {e}")

    # Tentar login com nova senha
    try:
        auth_service.login(
            email=test_registration.user_email,
            password="NovaSenha@456"
        )
        print_success("Login com nova senha bem-sucedido")
    except InvalidCredentialsError as e:
        print_error(f"Falha ao fazer login com nova senha: {e}")

    # Tentar alterar com senha antiga errada
    try:
        auth_service.change_password(
            user_id=test_registration.user_id,
            old_password="SenhaErrada@123",
            new_password="OutraSenha@789"
        )
        print_error("Deveria ter rejeitado senha antiga incorreta")
    except InvalidCredentialsError as e:
        print_success(f"Senha antiga incorreta corretamente rejeitada: {e}")

def test_roles_and_permissions():
    """Testa sistema de roles e permissões"""
    print_section("8. TESTE DE ROLES E PERMISSÕES")

    role_service = RoleService()
    user_repo = UserRepository()
    perm_repo = PermissionRepository()

    # Listar permissões
    try:
        perms = perm_repo.find_all(limit=10)
        print_success(f"Permissões encontradas: {len(perms)}")
        if perms:
            for perm in perms[:3]:
                print_info(f"  - {perm['name']} ({perm['resource']}.{perm['action']})")
    except Exception as e:
        print_error(f"Erro ao listar permissões: {e}")

    # Buscar role
    try:
        user_role = role_service.get_role_by_name('user')
        print_success(f"Role encontrada: {user_role.name}")
        print_info(f"  Descrição: {user_role.description}")
        print_info(f"  Permissões: {len(user_role.permissions)}")
    except RecordNotFoundError as e:
        print_warning(f"Role não encontrada: {e}")
    except Exception as e:
        print_error(f"Erro ao buscar role: {e}")

    # Atribuir role ao usuário
    try:
        admin_role = role_service.get_role_by_name('user')
        user_repo.assign_role(test_registration.user_id, admin_role.id)
        print_success(f"Role 'user' atribuída ao usuário")

        # Verificar permissões do usuário
        user_perms = user_repo.get_user_permissions(test_registration.user_id)
        print_success(f"Permissões do usuário: {len(user_perms)}")
        for perm in user_perms[:3]:
            print_info(f"  - {perm}")
    except Exception as e:
        print_error(f"Erro ao atribuir role: {e}")

def test_user_management():
    """Testa gerenciamento de usuários"""
    print_section("9. TESTE DE GERENCIAMENTO DE USUÁRIOS")

    user_service = UserService()
    user_repo = UserRepository()

    # Listar usuários
    try:
        users = user_repo.find_all(limit=5)
        print_success(f"Usuários encontrados: {len(users)}")
        for user in users:
            print_info(f"  - {user['name']} ({user['email']})")
    except Exception as e:
        print_error(f"Erro ao listar usuários: {e}")

    # Buscar usuário por ID
    try:
        user = user_repo.find_by_id(test_registration.user_id)
        print_success(f"Usuário encontrado: {user['name']}")
        print_info(f"  ID: {user['id']}")
        print_info(f"  Email: {user['email']}")
        print_info(f"  Ativo: {user['is_active']}")
    except RecordNotFoundError as e:
        print_error(f"Usuário não encontrado: {e}")

    # Atualizar usuário
    try:
        user_repo.update(test_registration.user_id, {'name': 'Maria Silva Atualizado'})
        print_success("Usuário atualizado com sucesso")
    except Exception as e:
        print_error(f"Erro ao atualizar usuário: {e}")

    # Contar usuários
    try:
        total = user_repo.count()
        print_success(f"Total de usuários no sistema: {total}")
    except Exception as e:
        print_error(f"Erro ao contar usuários: {e}")

def test_protected_functions():
    """Testa funções protegidas com middleware"""
    print_section("10. TESTE DE FUNÇÕES PROTEGIDAS")

    # Função com autenticação
    @auth_middleware.require_auth
    def funcao_autenticada(user_id: int, user_email: str, **kwargs):
        return f"Função executada para usuário: {user_email}"

    # Teste com token válido
    try:
        result = funcao_autenticada(token=test_registration.access_token)
        print_success(f"Função autenticada: {result}")
    except Exception as e:
        print_error(f"Erro: {e}")

    # Teste sem token
    try:
        funcao_autenticada()
        print_error("Deveria ter exigido autenticação")
    except Exception as e:
        print_success(f"Autenticação corretamente exigida: {type(e).__name__}")

    # Teste com token inválido
    try:
        funcao_autenticada(token="token_invalido")
        print_error("Deveria ter rejeitado token inválido")
    except Exception as e:
        print_success(f"Token inválido corretamente rejeitado: {type(e).__name__}")

    # Função com permissão
    @auth_middleware.require_auth
    @permission_middleware.require_permissions('users.read')
    def funcao_com_permissao(user_id: int, **kwargs):
        return f"Acesso autorizado para usuário {user_id}"

    # Teste com permissão
    try:
        result = funcao_com_permissao(token=test_registration.access_token)
        print_success(f"Função com permissão: {result}")
    except PermissionDeniedError as e:
        print_warning(f"Permissão negada (esperado se usuário não tem a permissão): {e}")
    except Exception as e:
        print_warning(f"Erro: {e}")

def test_error_handling():
    """Testa tratamento de erros"""
    print_section("11. TESTE DE TRATAMENTO DE ERROS")

    user_repo = UserRepository()

    # Buscar ID inexistente
    try:
        user_repo.find_by_id(9999999)
        print_error("Deveria ter lançado exceção")
    except RecordNotFoundError as e:
        print_success(f"RecordNotFoundError corretamente lançado: {e}")

    # Criar registro duplicado (email)
    auth_service = AuthService()
    email_teste = f"duplicado_{datetime.now().timestamp()}@example.com"

    try:
        auth_service.register(
            name="Primeiro",
            email=email_teste,
            password="Senha@123"
        )
        print_success("Primeiro registro criado")

        auth_service.register(
            name="Duplicado",
            email=email_teste,
            password="Senha@123"
        )
        print_error("Deveria ter rejeitado duplicado")
    except DuplicateRecordError as e:
        print_success(f"DuplicateRecordError corretamente lançado: {e}")

def test_token_verification():
    """Testa verificação de tokens"""
    print_section("12. TESTE DE VERIFICAÇÃO DE TOKENS")

    from src.utils.token import TokenManager

    tm = TokenManager()
    auth_service = AuthService()

    # Token válido
    try:
        payload = auth_service.verify_token(test_registration.access_token)
        print_success("Token verificado com sucesso")
        print_info(f"  User ID: {payload['sub']}")
        print_info(f"  Email: {payload['email']}")
        print_info(f"  Roles: {payload['roles']}")
    except Exception as e:
        print_error(f"Erro ao verificar token: {e}")

    # Token inválido
    try:
        auth_service.verify_token("token_invalido")
        print_error("Deveria ter rejeitado token inválido")
    except Exception as e:
        print_success(f"Token inválido corretamente rejeitado: {type(e).__name__}")


## Configuração

def main():
    """Exemplo de uso do sistema de configurações"""
    
    # 1. Inicializar banco
    print("=" * 60)
    print("INICIALIZANDO SISTEMA DE CONFIGURAÇÕES")
    print("=" * 60)
    
    DatabaseManager.initialize_pool(
        host='localhost',
        port=3306,
        user='root',
        password='senha',
        database='config_db'
    )
    
    # 2. Criar tabelas
    ConfigDatabase.create_tables()
    
    # 3. Popular dados iniciais
    print("\n" + "=" * 60)
    print("POPULANDO DADOS INICIAIS")
    print("=" * 60)
    ConfigDatabase.seed_initial_data()
    
    # 4. Usar o gerenciador
    manager = ConfigManager()
    
    print("\n" + "=" * 60)
    print("EXEMPLOS DE USO")
    print("=" * 60)
    
    # Exemplo 1: Configuração Global
    print("\n1. Configuração Global:")
    valor = manager.get_config_value('app_name', 'GERAL', ConfigScope.GLOBAL)
    print(f"   Nome da aplicação: {valor}")
    
    # Exemplo 2: Configuração de Instância
    print("\n2. Configuração de Instância:")
    valor = manager.get_config_value(
        'server_port',
        'SERVIDOR',
        ConfigScope.INSTANCE,
        instance_id='server-001'
    )
    print(f"   Porta do servidor-001: {valor}")
    
    # Exemplo 3: Configuração de Usuário
    print("\n3. Configuração de Usuário:")
    valor = manager.get_config_value(
        'theme',
        'INTERFACE',
        ConfigScope.USER,
        user_id=1
    )
    print(f"   Tema do usuário 1: {valor}")
    
    # Exemplo 4: Atualizar configuração
    print("\n4. Atualizar Configuração:")
    manager.set_config(
        nome='theme',
        tela='INTERFACE',
        valor='light',
        tipo=ConfigType.STRING,
        escopo=ConfigScope.USER,
        user_id=1,
        criado_por='user_1'
    )
    print("   Tema alterado para 'light'")
    
    # Exemplo 5: Buscar por tela
    print("\n5. Todas as configurações da tela INTERFACE:")
    configs = manager.get_configs_by_screen('INTERFACE')
    for config in configs:
        tipo = config['tipo']
        if tipo == 'BOOLEAN':
            valor = config['valor_booleano']
        elif tipo == 'INTEGER':
            valor = config['valor_inteiro']
        elif tipo == 'FLOAT':
            valor = config['valor_real']
        else:
            valor = config['valor_string']
        
        print(f"   - {config['nome']}: {valor} ({config['escopo']})")
    
    # Exemplo 6: Histórico
    print("\n6. Histórico da configuração 'theme':")
    history = manager.get_config_history('theme', 'INTERFACE', limit=5)
    for record in history:
        print(f"   {record['alterado_em']}: {record['valor_antigo']} → {record['valor_novo']} "
              f"(por {record['alterado_por']})")
    
    print("\n" + "=" * 60)
    print("✓ SISTEMA DE CONFIGURAÇÕES FUNCIONANDO")
    print("=" * 60)

