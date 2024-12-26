import os
from flask import Flask, render_template, request, redirect, flash, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from functools import wraps
from urllib.parse import quote

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir,"BancoDeDados_Cinema.db"))

app = Flask(__name__)
app.config.from_object('config.Config')
app.config["SQLALCHEMY_DATABASE_URI"] = database_file

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


#Sistema de Cadastro e Login
class Usuario(db.Model, UserMixin):
    Id = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(150), unique=True, nullable=False)
    Nome = db.Column(db.String(150), nullable=False)
    Senha = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    def get_id(self):
        return str(self.Id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

#Classes 
class Diretor(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    Nome = db.Column(db.String(100), nullable=False)
    Nacionalidade = db.Column(db.String(50))
    Filmes_dirigidos = db.Column(db.Integer, default=0)
    Data_nascimento = db.Column(db.String(10))

class Filme(db.Model):
    Titulo = db.Column(db.String(100), nullable = False, primary_key = True)
    Autor = db.Column(db.String(80), nullable = False)
    Genero = db.Column(db.String(30), nullable = False)
    Duracao = db.Column(db.String(30), nullable = False)
    DataLancamento = db.Column(db.String(100), nullable = False)
    Orcamento = db.Column(db.String(100), nullable = False)
    Descricao = db.Column(db.String(200), nullable = False)

class Comentario(db.Model):
    __tablename__ = 'comentarios'

    Id = db.Column(db.Integer, primary_key=True)
    Usuario = db.Column(db.String(80), nullable=False)
    Data = db.Column(db.String(100), nullable=False)
    Descricao = db.Column(db.String(200), nullable=False)

#Comandos do ADM
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)  
        return f(*args, **kwargs)
    return decorated_function

#Rotas
@app.route('/criar_admin', methods=["GET", "POST"])
def criar_admin():
    # Verifica se já existe um administrador
    admin_existente = Usuario.query.filter_by(role='admin').first()
    
    if admin_existente:
        flash('Já existe um administrador no sistema!', 'warning')
        return redirect(url_for('Home'))
    
    if request.method == 'POST':
        # Cria um novo administrador
        nome = request.form['Nome']
        email = request.form['Email']
        senha = bcrypt.generate_password_hash(request.form['Senha']).decode('utf-8')

        # Cria o usuário administrador
        usuario_admin = Usuario(Nome=nome, Email=email, Senha=senha, role='admin')
        db.session.add(usuario_admin)
        db.session.commit()

        flash('Administrador criado com sucesso! Agora faça login.', 'success')
        return redirect(url_for('Entrar'))  # Redireciona para a página de login

    return render_template('criar_admin.html')

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@app.route('/') #Rota para pagina inicial (index.html)
def Home():
    return render_template('index.html')

@app.route('/Usuario/Filmes/Listar', methods=["GET", "POST"]) #rota para lista de filmes (ListarFilmes.html)
def ListarFilmesUsuario():
    Filmes = Filme.query.all()

    return render_template('ListaFilmes.html', filmes = Filmes)

@app.route('/CadastrarAdmin', methods=["GET", "POST"])  # Rota para cadastrar administrador
def CadastrarAdmin():
    if current_user.is_authenticated and current_user.role == 'admin':  # Apenas admins podem cadastrar outro admin
        if request.method == 'POST':
            nome = request.form['Nome']
            email = request.form['Email']
            senha = bcrypt.generate_password_hash(request.form['Senha']).decode('utf-8')
            user = Usuario(Nome=nome, Email=email, Senha=senha, role='admin')  # Define o papel como 'admin'
            db.session.add(user)
            db.session.commit()
            flash('Administrador criado com sucesso!', 'success')
            return redirect(url_for('Home'))
        return render_template('CadastrarAdmin.html')
    else:
        flash('Acesso negado!', 'danger')
        return redirect(url_for('Home'))

@app.route('/Usuario/Entrar', methods=["GET", "POST"])  # Rota para login (Entrar.html)
def Entrar():
    if current_user.is_authenticated:
        return redirect(url_for('Home'))
    
    if request.method == 'POST':
        email = request.form['Email']
        senha = request.form['Senha']
        
        user = Usuario.query.filter_by(Email=email).first()
        
        if user and bcrypt.check_password_hash(user.Senha, senha):
            login_user(user, remember=True)
            flash('Login realizado com sucesso!', 'success')
            
            next_page = request.args.get('next')


            return redirect(next_page) if next_page else redirect(url_for('Home'))
        else:
            flash('Falha no login. Verifique suas credenciais.', 'danger')
    
    return render_template('Entrar.html')

@app.route('/Cadastrar', methods=["GET", "POST"])  # Rota para cadastrar usuário (Cadastrar.html)
def Cadastrar():
    if current_user.is_authenticated:
        return redirect(url_for('Home'))
    
    if request.method == 'POST':
        nome = request.form['Nome']
        email = request.form['Email']
        senha = bcrypt.generate_password_hash(request.form['Senha']).decode('utf-8')
        
        user_exists = Usuario.query.filter_by(Email=email).first()
        if user_exists:
            flash('Este email já está cadastrado. Tente fazer login.', 'warning')
            return redirect(url_for('Entrar'))
        
        user = Usuario(Nome=nome, Email=email, Senha=senha)
        db.session.add(user)
        db.session.commit()
        flash('Sua conta foi criada! Agora você pode fazer login.', 'success')
        
        return redirect(url_for('Entrar'))  # Redirecionando para a página de login
    
    return render_template('Cadastrar.html')

@app.route('/Usuario/Cadastrado/Blog/Inicio', methods=["GET", "POST"]) #rota para redirecionar para blog (BlogInicio.html)
def BlogInicio():
    return render_template('BlogInicio.html')

@app.route('/Coment', methods=["GET", "POST"])
def Coment1():
    return render_template('Coment1.html')

@app.route('/Coment2', methods=["GET", "POST"])
def Coment2():
    return render_template('Coment2.html')

@app.route('/Coment3', methods=["GET", "POST"])
def Coment3():
    return render_template('Coment3.html')

@app.route('/Coment4', methods=["GET", "POST"])
def Coment4():
    return render_template('Coment4.html')

@app.route('/Coment5', methods=["GET", "POST"])
def Coment5():
    return render_template('Coment5.html')

@app.route('/ADM/Cadastrado/Filmes/Cadastrar', methods=["GET", "POST"])
def FilmeCadastro():
    if request.method == "POST":
        titulo = request.form.get("TituloFilme")
        autor = request.form.get("AutorFilme")
        genero = request.form.get("GeneroFilme")
        duracao = request.form.get("DuracaoFilme")
        datalancamento = request.form.get("DataLancamentoFilme")
        orcamento = request.form.get("OrcamentoFilme")
        descricao = request.form.get("DescricaoFilme")
        
        novo_filme = Filme(Titulo = titulo, Autor = autor, Genero = genero, Duracao = duracao, DataLancamento = datalancamento, Orcamento = orcamento, Descricao = descricao)
        db.session.add(novo_filme)
        db.session.commit()
        return redirect('/Usuario/Filmes/Listar')

    filmes = Filme.query.all()
    return render_template('FilmeCadastro.html', Filmes = filmes)

@app.route('/editar/<titulo>', methods=['GET', 'POST'])
def editar_filme(titulo):
    filme = Filme.query.get_or_404(titulo)  # Busca o filme pelo título

    if request.method == 'POST':
        # Captura os dados do formulário
        filme.autor = request.form['autor']
        filme.genero = request.form['genero']
        filme.duracao = int(request.form['duracao'])  # Conversão para inteiro
        filme.data_lancamento = datetime.strptime(request.form['data_lancamento'], '%Y-%m-%d')  # Formato de data
        filme.orcamento = float(request.form['orcamento'])  # Conversão para float
        filme.descricao = request.form['descricao']

        db.session.commit()  # Salva as alterações no banco de dados
        return redirect(url_for('listar_filmes'))  # Redireciona para a lista de filmes

    return render_template('Crud.html', filme=filme)

@app.route('/filme/<string:Titulo>/excluir', methods=['POST'])
def excluir_filme(Titulo):
    filme = Filme.query.get_or_404(Titulo)
    db.session.delete(filme)
    db.session.commit()
    flash('Filme excluído com sucesso!', 'success')
    return redirect(url_for('Usuario/Filmes/Listar'))

@app.route('/Usuario/Cadastrado/Blog/Comentar', methods=["GET", "POST"])
def ComentCadastro():
    if request.method == 'POST':
        descricao = request.form['descricao']

        # Verifica se a descrição não está vazia
        if not descricao:
            flash('A descrição do comentário não pode estar vazia.', 'danger')
            return redirect(url_for('ComentCadastro'))  # Redireciona para a mesma página

        usuario = current_user.Nome  # Obtendo o nome do usuário logado
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Obtendo a data e hora atual

        # Criação de um novo comentário
        novo_comentario = Comentario(Usuario=usuario, Data=data, Descricao=descricao)

        try:
            # Salvando no banco de dados
            db.session.add(novo_comentario)
            db.session.commit()
            flash('Comentário adicionado com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()  # Caso ocorra algum erro, realiza o rollback
            flash(f'Ocorreu um erro ao adicionar o comentário: {e}', 'danger')

        # Recuperando todos os comentários
        comentarios = Comentario.query.all()

        return render_template('Comentarios.html', Comentarios=comentarios)
    
    # Se o método for GET, apenas renderiza o template
    return render_template('Coment1.html')

@app.route('/Painel', methods = ["GET", "POST"])
def Painel():
    return render_template('ADM.html')

@app.route('/limpar_comentarios', methods=["GET", "POST"])
def limpar_comentarios():
    try:
        # Deletar todos os comentários
        Comentario.query.delete()
        db.session.commit()
        flash('Todos os comentários foram removidos com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao limpar os comentários: {e}', 'danger')

    return redirect('/Painel') 

@app.route('/Coments/Visualizar/Comentar', methods=["GET", "POST"])
def Coment():
    comentarios = Comentario.query.all()

    return render_template('Comentarios.html', Comentarios = comentarios)

@app.route('/Nos', methods=["GET", "POST"])
def Nos():
    return render_template('Nos.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template('Entrar.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('ADM.html')

#Comandos do Banco de Dados
with app.app_context():
    db.create_all()

#Inicializador
if __name__ == '__main__':
    app.run(debug=True)