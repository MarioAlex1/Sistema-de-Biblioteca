from flask import Flask, request, redirect, render_template_string, flash, url_for, session
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'biblioteca_secreta_2024'

def conectar():
    """Abre conexão com o banco de dados SQLite"""
    conn = sqlite3.connect("biblioteca.db")
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabelas():
    """Função para criar todas as tabelas necessárias"""
    conn = conectar()
    cursor = conn.cursor()

    # Tabela de livros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            isbn TEXT UNIQUE,
            ano INTEGER,
            quantidade INTEGER DEFAULT 1
        )
    ''')

    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            curso TEXT
        )
    ''')

    # Tabela de empréstimos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emprestimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            livro_id INTEGER NOT NULL,
            data_emprestimo DATE NOT NULL,
            data_prevista DATE NOT NULL,
            data_devolucao DATE,
            status TEXT DEFAULT 'emprestado',
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            FOREIGN KEY (livro_id) REFERENCES livros(id)
        )
    ''')

    # Tabela de administradores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

def criar_admin_padrao():
    """Cria um administrador padrão se não existir"""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM administradores")
    if cursor.fetchone()['total'] == 0:
        cursor.execute("""
            INSERT INTO administradores (nome, usuario, senha)
            VALUES ('Administrador', 'admin', 'admin123')
        """)
        conn.commit()

    conn.close()

def verificar_admin():
    """Verifica se o usuário é admin"""
    return session.get('tipo_usuario') == 'admin'

def verificar_aluno():
    """Verifica se o usuário é aluno"""
    return session.get('tipo_usuario') == 'aluno'

def login_requerido(f):
    """Decorator para páginas que requerem login"""
    def decorated_function(*args, **kwargs):
        if 'tipo_usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_requerido(f):
    """Decorator para páginas que requerem acesso de admin"""
    def decorated_function(*args, **kwargs):
        if not verificar_admin():
            flash("Acesso negado! Apenas administradores podem acessar esta página.")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Template HTML principal
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titulo }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
            position: relative;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }
        .user-info {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .nav {
            background: rgba(255,255,255,0.9);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        .nav a {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 25px;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        .nav a:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .nav a.disabled {
            background: #ccc;
            cursor: not-allowed;
            pointer-events: none;
        }
        .content {
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
            box-sizing: border-box;
        }
        .form-group input:focus, .form-group select:focus {
            border-color: #667eea;
            outline: none;
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #764ba2;
            transform: translateY(-2px);
        }
        .btn-secondary {
            background: #6c757d;
        }
        .btn-secondary:hover {
            background: #5a6268;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table th {
            background: #667eea;
            color: white;
        }
        .table tr:hover {
            background: #f5f5f5;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 8px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .login-form {
            max-width: 400px;
            margin: 50px auto;
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        .user-type-selector {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            justify-content: center;
        }
        .user-type-option {
            background: #f8f9fa;
            border: 2px solid #ddd;
            padding: 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
            flex: 1;
        }
        .user-type-option.selected {
            border-color: #667eea;
            background: #e7f1ff;
        }
        .user-type-option:hover {
            border-color: #667eea;
        }
    </style>
</head>
<body>
    <div class="container">
        {% if session.get('tipo_usuario') %}
        <div class="header">
            <div class="user-info">
                {% if session.get('tipo_usuario') == 'admin' %}
                    👨‍💼 Admin: {{ session.get('nome_usuario') }}
                {% else %}
                    👨‍🎓 Aluno: {{ session.get('matricula_usuario') }}
                {% endif %}
                | <a href="/logout" style="color: white; text-decoration: underline;">Sair</a>
            </div>
            <h1>📚 Sistema de Gestão de Biblioteca</h1>
            <p>Biblioteca</p>
        </div>

        <div class="nav">
            <a href="/">🏠 Início</a>
            <a href="/livros" {% if not session.get('tipo_usuario') %}class="disabled"{% endif %}>📖 Livros</a>
            {% if session.get('tipo_usuario') == 'admin' %}
            <a href="/usuarios">👥 Usuários</a>
            <a href="/emprestimos">📋 Empréstimos</a>
            {% else %}
            <a href="/meus_emprestimos">📋 Meus Empréstimos</a>
            {% endif %}
            <a href="/relatorios">📊 Relatórios</a>
        </div>
        {% endif %}

        <div class="content">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert alert-success">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {{ conteudo|safe }}
        </div>
    </div>
</body>
</html>
'''

@app.route("/")
def home():
    """Página inicial - redireciona para login se não autenticado"""
    if 'tipo_usuario' not in session:
        return redirect(url_for('login'))

    """Página inicial com estatísticas"""
    conn = conectar()
    cursor = conn.cursor()

    # Buscar estatísticas
    cursor.execute("SELECT COUNT(*) as total FROM livros")
    total_livros = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM usuarios")
    total_usuarios = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM emprestimos WHERE status = 'emprestado'")
    total_emprestados = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) as total FROM emprestimos 
        WHERE status = 'emprestado' AND data_prevista < DATE('now')
    """)
    total_atrasados = cursor.fetchone()['total']

    conn.close()

    # Conteúdo diferente para admin e aluno
    if verificar_admin():
        conteudo = f'''
        <h2>📊 Central de Administração</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_livros}</div>
                <div>Total de Livros</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_usuarios}</div>
                <div>Usuários Cadastrados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_emprestados}</div>
                <div>Livros Emprestados</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_atrasados}</div>
                <div>Empréstimos Atrasados</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <h3>👨‍💼 Área do Administrador</h3>
            <p>Você tem acesso completo ao sistema. Use o menu acima para gerenciar livros, usuários e empréstimos.</p>
        </div>
        '''
    else:
        # Buscar empréstimos do aluno
        cursor = conectar().cursor()
        cursor.execute("""
            SELECT COUNT(*) as total FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE u.matricula = ? AND e.status = 'emprestado'
        """, (session.get('matricula_usuario'),))
        meus_emprestimos = cursor.fetchone()['total']

        conteudo = f'''
        <h2>📚 Portal do Aluno</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_livros}</div>
                <div>Total de Livros</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_livros - total_emprestados}</div>
                <div>Livros Disponíveis</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{meus_emprestimos}</div>
                <div>Meus Empréstimos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">3</div>
                <div>Limite de Empréstimos</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <h3>👨‍🎓 Bem-vindo, {session.get('nome_usuario')}!</h3>
            <p>Você pode consultar livros disponíveis e acompanhar seus empréstimos.</p>
        </div>
        '''

    return render_template_string(HTML_TEMPLATE, titulo="Sistema de Biblioteca", conteudo=conteudo)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Página de login"""
    if request.method == "POST":
        tipo_usuario = request.form.get('tipo_usuario')

        if tipo_usuario == 'admin':
            usuario = request.form.get('usuario')
            senha = request.form.get('senha')

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM administradores 
                WHERE usuario = ? AND senha = ?
            """, (usuario, senha))
            admin = cursor.fetchone()
            conn.close()

            if admin:
                session['tipo_usuario'] = 'admin'
                session['nome_usuario'] = admin['nome']
                session['usuario_id'] = admin['id']
                flash("Login de administrador realizado com sucesso!")
                return redirect(url_for('home'))
            else:
                flash("Usuário ou senha de administrador incorretos!")

        elif tipo_usuario == 'aluno':
            matricula = request.form.get('matricula')

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE matricula = ?", (matricula,))
            usuario = cursor.fetchone()
            conn.close()

            if usuario:
                session['tipo_usuario'] = 'aluno'
                session['nome_usuario'] = usuario['nome']
                session['matricula_usuario'] = usuario['matricula']
                session['usuario_id'] = usuario['id']
                flash(f"Bem-vindo, {usuario['nome']}!")
                return redirect(url_for('home'))
            else:
                flash("Matrícula não encontrada! Procure um administrador para se cadastrar.")

    conteudo = '''
    <div class="login-form">
        <h2 style="text-align: center; margin-bottom: 30px;">🔐 Acesso ao Sistema</h2>

        <div class="user-type-selector">
            <div class="user-type-option" onclick="selectUserType('admin')" id="admin-option">
                <h3>👨‍💼 Administrador</h3>
                <p>Gerenciar sistema</p>
            </div>
            <div class="user-type-option" onclick="selectUserType('aluno')" id="aluno-option">
                <h3>👨‍🎓 Aluno</h3>
                <p>Consultar livros</p>
            </div>
        </div>

        <form method="POST" id="login-form">
            <input type="hidden" name="tipo_usuario" id="tipo_usuario" value="">

            <div id="admin-fields" style="display: none;">
                <div class="form-group">
                    <label for="usuario">Usuário:</label>
                    <input type="text" id="usuario" name="usuario">
                </div>
                <div class="form-group">
                    <label for="senha">Senha:</label>
                    <input type="password" id="senha" name="senha">
                </div>
            </div>

            <div id="aluno-fields" style="display: none;">
                <div class="form-group">
                    <label for="matricula">Matrícula:</label>
                    <input type="text" id="matricula" name="matricula" placeholder="Digite sua matrícula">
                </div>
            </div>

            <button type="submit" class="btn" id="login-btn" style="width: 100%; display: none;">Entrar</button>
        </form>

        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <a href="/cadastro" style="color: #667eea; text-decoration: none; font-weight: bold;">
                ➕ Primeiro acesso? Cadastre-se como administrador
            </a>
        </div>

        <div style="text-align: center; margin-top: 15px;">
            <small>
                <strong>Dados de teste:</strong><br>
                Admin - Usuário: admin / Senha: admin123<br>
                Aluno - Use uma matrícula já cadastrada (ex: 2024001)
            </small>
        </div>
    </div>

    <script>
        function selectUserType(type) {
            // Reset selections
            document.getElementById('admin-option').classList.remove('selected');
            document.getElementById('aluno-option').classList.remove('selected');
            document.getElementById('admin-fields').style.display = 'none';
            document.getElementById('aluno-fields').style.display = 'none';

            // Set new selection
            document.getElementById(type + '-option').classList.add('selected');
            document.getElementById(type + '-fields').style.display = 'block';
            document.getElementById('tipo_usuario').value = type;
            document.getElementById('login-btn').style.display = 'block';
        }
    </script>
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Login", conteudo=conteudo)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    """Página de cadastro de administradores"""
    if request.method == "POST":
        nome = request.form.get('nome')
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        confirmar_senha = request.form.get('confirmar_senha')

        # Validações
        if not nome or not usuario or not senha:
            flash("Todos os campos são obrigatórios!")
        elif senha != confirmar_senha:
            flash("As senhas não coincidem!")
        elif len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres!")
        else:
            conn = conectar()
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    INSERT INTO administradores (nome, usuario, senha)
                    VALUES (?, ?, ?)
                """, (nome, usuario, senha))
                conn.commit()
                flash("Administrador cadastrado com sucesso! Faça login agora.")
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash("Nome de usuário já existe! Escolha outro.")
            except Exception as e:
                flash(f"Erro ao cadastrar administrador: {str(e)}")
            finally:
                conn.close()

    conteudo = '''
    <div class="login-form">
        <h2 style="text-align: center; margin-bottom: 30px;">📝 Cadastro de Administrador</h2>

        <form method="POST">
            <div class="form-group">
                <label for="nome">Nome Completo:</label>
                <input type="text" id="nome" name="nome" required placeholder="Digite seu nome completo">
            </div>
            <div class="form-group">
                <label for="usuario">Nome de Usuário:</label>
                <input type="text" id="usuario" name="usuario" required placeholder="Escolha um nome de usuário">
            </div>
            <div class="form-group">
                <label for="senha">Senha:</label>
                <input type="password" id="senha" name="senha" required placeholder="Mínimo 6 caracteres">
            </div>
            <div class="form-group">
                <label for="confirmar_senha">Confirmar Senha:</label>
                <input type="password" id="confirmar_senha" name="confirmar_senha" required placeholder="Digite a senha novamente">
            </div>

            <button type="submit" class="btn" style="width: 100%;">Cadastrar Administrador</button>
        </form>

        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
            <a href="/login" style="color: #667eea; text-decoration: none; font-weight: bold;">
                ← Voltar para Login
            </a>
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 20px;">
            <h4 style="margin-top: 0;">ℹ️ Informações Importantes:</h4>
            <ul style="margin-bottom: 0; text-align: left;">
                <li>Apenas administradores podem cadastrar outros administradores e alunos</li>
                <li>Alunos são cadastrados pelos administradores no sistema</li>
                <li>Administradores têm acesso completo ao sistema de biblioteca</li>
            </ul>
        </div>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Cadastro", conteudo=conteudo)

@app.route("/logout")
def logout():
    """Logout do sistema"""
    session.clear()
    flash("Logout realizado com sucesso!")
    return redirect(url_for('login'))

# ROTAS PARA LIVROS
@app.route("/livros")
@login_requerido
def listar_livros():
    """Lista todos os livros cadastrados"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM livros ORDER BY titulo")
    livros = cursor.fetchall()
    conn.close()

    tabela_livros = ""
    if livros:
        tabela_livros = '''
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Título</th>
                    <th>Autor</th>
                    <th>ISBN</th>
                    <th>Ano</th>
                    <th>Quantidade</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        '''
        for livro in livros:
            status = "✅ Disponível" if livro['quantidade'] > 0 else "❌ Indisponível"
            status_color = "green" if livro['quantidade'] > 0 else "red"

            tabela_livros += f'''
                <tr>
                    <td>{livro['id']}</td>
                    <td>{livro['titulo']}</td>
                    <td>{livro['autor']}</td>
                    <td>{livro['isbn'] or 'N/A'}</td>
                    <td>{livro['ano'] or 'N/A'}</td>
                    <td>{livro['quantidade']}</td>
                    <td style="color: {status_color}; font-weight: bold;">{status}</td>
                </tr>
            '''
        tabela_livros += "</tbody></table>"
    else:
        tabela_livros = "<p>Nenhum livro cadastrado ainda.</p>"

    # Formulário de cadastro apenas para admins
    form_cadastro = ""
    if verificar_admin():
        form_cadastro = '''
        <h3>➕ Cadastrar Novo Livro</h3>
        <form method="POST" action="/cadastrar_livro">
            <div class="form-group">
                <label for="titulo">Título:</label>
                <input type="text" id="titulo" name="titulo" required>
            </div>
            <div class="form-group">
                <label for="autor">Autor:</label>
                <input type="text" id="autor" name="autor" required>
            </div>
            <div class="form-group">
                <label for="isbn">ISBN:</label>
                <input type="text" id="isbn" name="isbn">
            </div>
            <div class="form-group">
                <label for="ano">Ano de Publicação:</label>
                <input type="number" id="ano" name="ano" min="1900" max="2024">
            </div>
            <div class="form-group">
                <label for="quantidade">Quantidade:</label>
                <input type="number" id="quantidade" name="quantidade" min="1" value="1" required>
            </div>
            <button type="submit" class="btn">Cadastrar Livro</button>
        </form>
        '''

    titulo_secao = "📖 Livros Cadastrados" if verificar_aluno() else "📖 Gerenciar Livros"

    conteudo = f'''
    <h2>{titulo_secao}</h2>

    {form_cadastro}

    <h3>📚 Acervo da Biblioteca</h3>
    {tabela_livros}
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Livros", conteudo=conteudo)

@app.route("/cadastrar_livro", methods=["POST"])
@admin_requerido
def cadastrar_livro():
    """Cadastra um novo livro - apenas admins"""
    titulo = request.form.get('titulo')
    autor = request.form.get('autor')
    isbn = request.form.get('isbn') or None
    ano = request.form.get('ano') or None
    quantidade = request.form.get('quantidade', 1)

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO livros (titulo, autor, isbn, ano, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, autor, isbn, ano, quantidade))
        conn.commit()
        flash(f"Livro '{titulo}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        flash("Erro: ISBN já existe no sistema!")
    except Exception as e:
        flash(f"Erro ao cadastrar livro: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('listar_livros'))

# ROTAS PARA USUÁRIOS (apenas admins)
@app.route("/usuarios")
@admin_requerido
def listar_usuarios():
    """Lista todos os usuários cadastrados - apenas admins"""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()
    conn.close()

    tabela_usuarios = ""
    if usuarios:
        tabela_usuarios = '''
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Matrícula</th>
                    <th>Curso</th>
                </tr>
            </thead>
            <tbody>
        '''
        for usuario in usuarios:
            tabela_usuarios += f'''
                <tr>
                    <td>{usuario['id']}</td>
                    <td>{usuario['nome']}</td>
                    <td>{usuario['matricula']}</td>
                    <td>{usuario['curso'] or 'N/A'}</td>
                </tr>
            '''
        tabela_usuarios += "</tbody></table>"
    else:
        tabela_usuarios = "<p>Nenhum usuário cadastrado ainda.</p>"

    conteudo = f'''
    <h2>👥 Gerenciar Usuários</h2>

    <h3>➕ Cadastrar Novo Usuário</h3>
    <form method="POST" action="/cadastrar_usuario">
        <div class="form-group">
            <label for="nome">Nome Completo:</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div class="form-group">
            <label for="matricula">Matrícula:</label>
            <input type="text" id="matricula" name="matricula" required>
        </div>
        <div class="form-group">
            <label for="curso">Curso:</label>
            <input type="text" id="curso" name="curso">
        </div>
        <button type="submit" class="btn">Cadastrar Usuário</button>
    </form>

    <h3>👥 Usuários Cadastrados</h3>
    {tabela_usuarios}
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Usuários", conteudo=conteudo)

@app.route("/cadastrar_usuario", methods=["POST"])
@admin_requerido
def cadastrar_usuario():
    """Cadastra um novo usuário - apenas admins"""
    nome = request.form.get('nome')
    matricula = request.form.get('matricula')
    curso = request.form.get('curso') or None

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, matricula, curso)
            VALUES (?, ?, ?)
        """, (nome, matricula, curso))
        conn.commit()
        flash(f"Usuário '{nome}' cadastrado com sucesso!")
    except sqlite3.IntegrityError:
        flash("Erro: Matrícula já existe no sistema!")
    except Exception as e:
        flash(f"Erro ao cadastrar usuário: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('listar_usuarios'))

# ROTAS PARA EMPRÉSTIMOS
@app.route("/emprestimos")
@admin_requerido
def gerenciar_emprestimos():
    """Página para gerenciar empréstimos - apenas admins"""
    conn = conectar()
    cursor = conn.cursor()

    # Buscar usuários para select
    cursor.execute("SELECT * FROM usuarios ORDER BY nome")
    usuarios = cursor.fetchall()

    # Buscar livros disponíveis
    cursor.execute("SELECT * FROM livros WHERE quantidade > 0 ORDER BY titulo")
    livros = cursor.fetchall()

    # Buscar empréstimos ativos
    cursor.execute("""
        SELECT e.*, u.nome as usuario_nome, u.matricula, l.titulo as livro_titulo
        FROM emprestimos e
        JOIN usuarios u ON e.usuario_id = u.id
        JOIN livros l ON e.livro_id = l.id
        WHERE e.status = 'emprestado'
        ORDER BY e.data_emprestimo DESC
    """)
    emprestimos = cursor.fetchall()

    conn.close()

    # Gerar opções para selects
    opcoes_usuarios = ""
    for usuario in usuarios:
        opcoes_usuarios += f'<option value="{usuario["id"]}">{usuario["nome"]} ({usuario["matricula"]})</option>'

    opcoes_livros = ""
    for livro in livros:
        opcoes_livros += f'<option value="{livro["id"]}">{livro["titulo"]} - {livro["autor"]} (Qtd: {livro["quantidade"]})</option>'

    # Gerar tabela de empréstimos
    tabela_emprestimos = ""
    if emprestimos:
        tabela_emprestimos = '''
        <table class="table">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Usuário</th>
                    <th>Livro</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                    <th>Status</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in emprestimos:
            data_prevista = datetime.strptime(emp['data_prevista'], '%Y-%m-%d')
            hoje = datetime.now()
            status_cor = "red" if data_prevista < hoje else "green"
            status_texto = "ATRASADO" if data_prevista < hoje else "No prazo"

            tabela_emprestimos += f'''
                <tr>
                    <td>{emp['id']}</td>
                    <td>{emp['usuario_nome']} ({emp['matricula']})</td>
                    <td>{emp['livro_titulo']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{data_prevista.strftime('%d/%m/%Y')}</td>
                    <td style="color: {status_cor}; font-weight: bold;">{status_texto}</td>
                    <td>
                        <form method="POST" action="/devolver_livro" style="display: inline;">
                            <input type="hidden" name="emprestimo_id" value="{emp['id']}">
                            <button type="submit" class="btn" style="padding: 5px 10px; font-size: 12px;">Devolver</button>
                        </form>
                    </td>
                </tr>
            '''
        tabela_emprestimos += "</tbody></table>"
    else:
        tabela_emprestimos = "<p>Nenhum empréstimo ativo no momento.</p>"

    conteudo = f'''
    <h2>📋 Gerenciar Empréstimos</h2>

    <h3>➕ Realizar Novo Empréstimo</h3>
    <form method="POST" action="/realizar_emprestimo">
        <div class="form-group">
            <label for="usuario_id">Usuário:</label>
            <select id="usuario_id" name="usuario_id" required>
                <option value="">Selecione um usuário</option>
                {opcoes_usuarios}
            </select>
        </div>
        <div class="form-group">
            <label for="livro_id">Livro:</label>
            <select id="livro_id" name="livro_id" required>
                <option value="">Selecione um livro</option>
                {opcoes_livros}
            </select>
        </div>
        <button type="submit" class="btn">Realizar Empréstimo</button>
    </form>

    <h3>📚 Empréstimos Ativos</h3>
    {tabela_emprestimos}
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Empréstimos", conteudo=conteudo)

@app.route("/meus_emprestimos")
@login_requerido
def meus_emprestimos():
    """Página para alunos visualizarem seus empréstimos"""
    if not verificar_aluno():
        return redirect(url_for('gerenciar_emprestimos'))

    conn = conectar()
    cursor = conn.cursor()

    # Buscar empréstimos do aluno logado
    cursor.execute("""
        SELECT e.*, l.titulo as livro_titulo, l.autor
        FROM emprestimos e
        JOIN livros l ON e.livro_id = l.id
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE u.matricula = ? AND e.status = 'emprestado'
        ORDER BY e.data_emprestimo DESC
    """, (session.get('matricula_usuario'),))
    emprestimos = cursor.fetchall()

    # Buscar histórico de empréstimos
    cursor.execute("""
        SELECT e.*, l.titulo as livro_titulo, l.autor
        FROM emprestimos e
        JOIN livros l ON e.livro_id = l.id
        JOIN usuarios u ON e.usuario_id = u.id
        WHERE u.matricula = ? AND e.status = 'devolvido'
        ORDER BY e.data_devolucao DESC
        LIMIT 10
    """, (session.get('matricula_usuario'),))
    historico = cursor.fetchall()

    conn.close()

    # Gerar tabela de empréstimos ativos
    tabela_emprestimos = ""
    if emprestimos:
        tabela_emprestimos = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in emprestimos:
            data_prevista = datetime.strptime(emp['data_prevista'], '%Y-%m-%d')
            hoje = datetime.now()
            status_cor = "red" if data_prevista < hoje else "green"
            status_texto = "ATRASADO" if data_prevista < hoje else "No prazo"

            tabela_emprestimos += f'''
                <tr>
                    <td>{emp['livro_titulo']}</td>
                    <td>{emp['autor']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{data_prevista.strftime('%d/%m/%Y')}</td>
                    <td style="color: {status_cor}; font-weight: bold;">{status_texto}</td>
                </tr>
            '''
        tabela_emprestimos += "</tbody></table>"
    else:
        tabela_emprestimos = "<p>Você não possui empréstimos ativos no momento.</p>"

    # Gerar tabela de histórico
    tabela_historico = ""
    if historico:
        tabela_historico = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Data Empréstimo</th>
                    <th>Data Devolução</th>
                </tr>
            </thead>
            <tbody>
        '''
        for emp in historico:
            tabela_historico += f'''
                <tr>
                    <td>{emp['livro_titulo']}</td>
                    <td>{emp['autor']}</td>
                    <td>{datetime.strptime(emp['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{datetime.strptime(emp['data_devolucao'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                </tr>
            '''
        tabela_historico += "</tbody></table>"
    else:
        tabela_historico = "<p>Nenhum histórico de empréstimos encontrado.</p>"

    conteudo = f'''
    <h2>📋 Meus Empréstimos</h2>

    <h3>📚 Empréstimos Ativos</h3>
    {tabela_emprestimos}

    <div style="margin-top: 40px;">
        <h3>📜 Histórico de Empréstimos</h3>
        {tabela_historico}
    </div>

    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px;">
        <h4>ℹ️ Informações Importantes:</h4>
        <ul>
            <li>Você pode ter até 3 livros emprestados simultaneamente</li>
            <li>O prazo de devolução é de 7 dias</li>
            <li>Para renovar um empréstimo, procure um administrador</li>
            <li>Empréstimos em atraso podem impedir novos empréstimos</li>
        </ul>
    </div>
    '''

    return render_template_string(HTML_TEMPLATE, titulo="Meus Empréstimos", conteudo=conteudo)

@app.route("/realizar_emprestimo", methods=["POST"])
@admin_requerido
def realizar_emprestimo():
    """Realiza um novo empréstimo - apenas admins"""
    usuario_id = request.form.get('usuario_id')
    livro_id = request.form.get('livro_id')

    conn = conectar()
    cursor = conn.cursor()

    try:
        # Verificar se usuário não tem mais que 3 livros emprestados
        cursor.execute("""
            SELECT COUNT(*) as total FROM emprestimos 
            WHERE usuario_id = ? AND status = 'emprestado'
        """, (usuario_id,))
        total_emprestimos = cursor.fetchone()['total']

        if total_emprestimos >= 3:
            flash("Erro: Usuário já possui 3 livros emprestados (limite máximo)!")
            conn.close()
            return redirect(url_for('gerenciar_emprestimos'))

        # Verificar se livro está disponível
        cursor.execute("SELECT quantidade FROM livros WHERE id = ?", (livro_id,))
        livro = cursor.fetchone()

        if not livro or livro['quantidade'] <= 0:
            flash("Erro: Livro não disponível para empréstimo!")
            conn.close()
            return redirect(url_for('gerenciar_emprestimos'))

        # Realizar empréstimo
        data_emprestimo = datetime.now().strftime('%Y-%m-%d')
        data_prevista = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, livro_id, data_emprestimo, data_prevista))

        # Diminuir quantidade disponível do livro
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?
        """, (livro_id,))

        conn.commit()
        flash("Empréstimo realizado com sucesso!")

    except Exception as e:
        flash(f"Erro ao realizar empréstimo: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('gerenciar_emprestimos'))

@app.route("/devolver_livro", methods=["POST"])
@admin_requerido
def devolver_livro():
    """Realiza a devolução de um livro - apenas admins"""
    emprestimo_id = request.form.get('emprestimo_id')

    conn = conectar()
    cursor = conn.cursor()

    try:
        # Buscar dados do empréstimo
        cursor.execute("""
            SELECT e.*, l.titulo FROM emprestimos e
            JOIN livros l ON e.livro_id = l.id
            WHERE e.id = ?
        """, (emprestimo_id,))
        emprestimo = cursor.fetchone()

        if not emprestimo:
            flash("Erro: Empréstimo não encontrado!")
            conn.close()
            return redirect(url_for('gerenciar_emprestimos'))

        # Marcar como devolvido
        data_devolucao = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            UPDATE emprestimos 
            SET data_devolucao = ?, status = 'devolvido'
            WHERE id = ?
        """, (data_devolucao, emprestimo_id))

        # Aumentar quantidade disponível do livro
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade + 1 WHERE id = ?
        """, (emprestimo['livro_id'],))

        conn.commit()
        flash(f"Livro '{emprestimo['titulo']}' devolvido com sucesso!")

    except Exception as e:
        flash(f"Erro ao devolver livro: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('gerenciar_emprestimos'))

# ROTAS PARA RELATÓRIOS
@app.route("/relatorios")
@login_requerido
def relatorios():
    """Página de relatórios"""
    conn = conectar()
    cursor = conn.cursor()

    if verificar_admin():
        # Relatórios completos para admins

        # Relatório de livros emprestados
        cursor.execute("""
            SELECT l.titulo, l.autor, u.nome as usuario_nome, u.matricula,
                   e.data_emprestimo, e.data_prevista
            FROM emprestimos e
            JOIN livros l ON e.livro_id = l.id
            JOIN usuarios u ON e.usuario_id = u.id
            WHERE e.status = 'emprestado'
            ORDER BY e.data_emprestimo DESC
        """)
        livros_emprestados = cursor.fetchall()

        # Relatório de usuários com empréstimos atrasados
        cursor.execute("""
            SELECT u.nome, u.matricula, u.curso, l.titulo, 
                   e.data_emprestimo, e.data_prevista,
                   julianday('now') - julianday(e.data_prevista) as dias_atraso
            FROM emprestimos e
            JOIN usuarios u ON e.usuario_id = u.id
            JOIN livros l ON e.livro_id = l.id
            WHERE e.status = 'emprestado' AND e.data_prevista < DATE('now')
            ORDER BY dias_atraso DESC
        """)
        emprestimos_atrasados = cursor.fetchall()

        # Relatório de livros disponíveis
        cursor.execute("""
            SELECT titulo, autor, isbn, ano, quantidade
            FROM livros
            WHERE quantidade > 0
            ORDER BY titulo
        """)
        livros_disponiveis = cursor.fetchall()

    else:
        # Relatórios limitados para alunos
        livros_emprestados = []
        emprestimos_atrasados = []

        # Apenas livros disponíveis
        cursor.execute("""
            SELECT titulo, autor, isbn, ano, quantidade
            FROM livros
            WHERE quantidade > 0
            ORDER BY titulo
        """)
        livros_disponiveis = cursor.fetchall()

    conn.close()

    # Gerar tabelas HTML
    def gerar_tabela_emprestados():
        if not livros_emprestados:
            return "<p>Nenhum livro emprestado no momento.</p>"

        html = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Livro</th>
                    <th>Autor</th>
                    <th>Usuário</th>
                    <th>Matrícula</th>
                    <th>Data Empréstimo</th>
                    <th>Data Prevista</th>
                </tr>
            </thead>
            <tbody>
        '''
        for item in livros_emprestados:
            html += f'''
                <tr>
                    <td>{item['titulo']}</td>
                    <td>{item['autor']}</td>
                    <td>{item['usuario_nome']}</td>
                    <td>{item['matricula']}</td>
                    <td>{datetime.strptime(item['data_emprestimo'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td>{datetime.strptime(item['data_prevista'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    def gerar_tabela_atrasados():
        if not emprestimos_atrasados:
            return "<p>Nenhum empréstimo em atraso! 🎉</p>"

        html = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Usuário</th>
                    <th>Matrícula</th>
                    <th>Curso</th>
                    <th>Livro</th>
                    <th>Data Prevista</th>
                    <th>Dias de Atraso</th>
                </tr>
            </thead>
            <tbody>
        '''
        for item in emprestimos_atrasados:
            dias_atraso = int(item['dias_atraso'])
            html += f'''
                <tr style="background-color: #ffebee;">
                    <td>{item['nome']}</td>
                    <td>{item['matricula']}</td>
                    <td>{item['curso'] or 'N/A'}</td>
                    <td>{item['titulo']}</td>
                    <td>{datetime.strptime(item['data_prevista'], '%Y-%m-%d').strftime('%d/%m/%Y')}</td>
                    <td style="color: red; font-weight: bold;">{dias_atraso} dias</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    def gerar_tabela_disponiveis():
        if not livros_disponiveis:
            return "<p>Nenhum livro disponível no momento.</p>"

        html = '''
        <table class="table">
            <thead>
                <tr>
                    <th>Título</th>
                    <th>Autor</th>
                    <th>ISBN</th>
                    <th>Ano</th>
                    <th>Quantidade Disponível</th>
                </tr>
            </thead>
            <tbody>
        '''
        for livro in livros_disponiveis:
            html += f'''
                <tr>
                    <td>{livro['titulo']}</td>
                    <td>{livro['autor']}</td>
                    <td>{livro['isbn'] or 'N/A'}</td>
                    <td>{livro['ano'] or 'N/A'}</td>
                    <td style="color: green; font-weight: bold;">{livro['quantidade']}</td>
                </tr>
            '''
        html += "</tbody></table>"
        return html

    # Conteúdo diferente para admin e aluno
    if verificar_admin():
        conteudo = f'''
        <h2>📊 Relatórios da Biblioteca</h2>

        <div style="margin-bottom: 40px;">
            <h3>📚 Livros Atualmente Emprestados</h3>
            {gerar_tabela_emprestados()}
        </div>

        <div style="margin-bottom: 40px;">
            <h3>⚠️ Usuários com Empréstimos Atrasados</h3>
            {gerar_tabela_atrasados()}
        </div>

        <div style="margin-bottom: 40px;">
            <h3>✅ Livros Disponíveis para Empréstimo</h3>
            {gerar_tabela_disponiveis()}
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.print()" class="btn">🖨️ Imprimir Relatórios</button>
        </div>
        '''
    else:
        conteudo = f'''
        <h2>📊 Consulta de Livros</h2>

        <div style="margin-bottom: 40px;">
            <h3>✅ Livros Disponíveis para Empréstimo</h3>
            {gerar_tabela_disponiveis()}
        </div>

        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 30px;">
            <h4>ℹ️ Como fazer um empréstimo:</h4>
            <p>Para emprestar um livro, procure um administrador da biblioteca com sua matrícula e o nome do livro desejado.</p>
        </div>
        '''

    return render_template_string(HTML_TEMPLATE, titulo="Relatórios", conteudo=conteudo)

def inserir_dados_exemplo():
    """Insere alguns dados de exemplo para demonstração"""
    conn = conectar()
    cursor = conn.cursor()

    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) as total FROM livros")
    if cursor.fetchone()['total'] > 0:
        conn.close()
        return

    # Inserir livros de exemplo
    livros_exemplo = [
        ("Dom Casmurro", "Machado de Assis", "978-85-359-0277-5", 1899, 2),
        ("O Cortiço", "Aluísio Azevedo", "978-85-260-1631-8", 1890, 1),
        ("Capitães da Areia", "Jorge Amado", "978-85-254-0024-7", 1937, 3),
        ("Python para Iniciantes", "Eric Matthes", "978-85-7522-718-3", 2019, 2),
        ("Algoritmos e Estruturas de Dados", "Thomas Cormen", "978-85-352-8913-9", 2012, 1),
        ("História do Brasil", "Boris Fausto", "978-85-314-0556-2", 2013, 2)
    ]

    for livro in livros_exemplo:
        cursor.execute("""
            INSERT INTO livros (titulo, autor, isbn, ano, quantidade)
            VALUES (?, ?, ?, ?, ?)
        """, livro)

    # Inserir usuários de exemplo
    usuarios_exemplo = [
        ("João Silva Santos", "2024001", "Análises e Desenvolvimento de Sistemas"),
        ("Maria Oliveira Lima", "2024002", "Engenharia de Software"),
        ("Pedro Costa Ferreira", "2024003", "Sistemas de Informação"),
        ("Leticia Rodrigues", "2024004", "Química"),
        ("Carlos Eduardo Souza", "2024005", "Zootecnia")
    ]

    for usuario in usuarios_exemplo:
        cursor.execute("""
            INSERT INTO usuarios (nome, matricula, curso)
            VALUES (?, ?, ?)
        """, usuario)

    # Inserir alguns empréstimos de exemplo
    emprestimos_exemplo = [
        (1, 1, "2024-05-20", "2024-05-27"),  # João emprestou Dom Casmurro
        (2, 4, "2024-05-22", "2024-05-29"),  # Maria emprestou Python para Iniciantes
        (3, 5, "2024-05-15", "2024-05-22"),  # Pedro emprestou Algoritmos (atrasado)
    ]

    for emp in emprestimos_exemplo:
        cursor.execute("""
            INSERT INTO emprestimos (usuario_id, livro_id, data_emprestimo, data_prevista)
            VALUES (?, ?, ?, ?)
        """, emp)

        # Diminuir quantidade do livro emprestado
        cursor.execute("""
            UPDATE livros SET quantidade = quantidade - 1 WHERE id = ?
        """, (emp[1],))

    conn.commit()
    conn.close()
    print("Dados de exemplo inseridos com sucesso!")

if __name__ == "__main__":
    criar_tabelas()
    criar_admin_padrao()
    inserir_dados_exemplo()
    print("=" * 50)
    print("🚀 SISTEMA DE BIBLIOTECA INICIADO!")
    print("=" * 50)
    print("📍 Acesse: http://0.0.0.0:5000")
    print("📚 Sistema pronto para uso!")
    print("👨‍💼 Admin padrão: admin / admin123")
    print("👨‍🎓 Alunos de teste: matrículas 2024001 a 2024005")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)