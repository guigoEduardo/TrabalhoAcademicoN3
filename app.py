# SEÇÃO 1: IMPORTAÇÕES E CONFIGURAÇÕES

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
import jwt
import datetime
from functools import wraps
import os

app = Flask(__name__)

# Configuração do caminho do banco de dados (SQLite)
# Garante que o banco seja criado na mesma pasta do arquivo app.py
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'banco.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' # Chave usada para assinar o Token JWT

# Inicialização das bibliotecas
db = SQLAlchemy(app)      # ORM (Banco de Dados)
ma = Marshmallow(app)     # Serialização (Transformar Objetos em JSON)

# SEÇÃO 2: MODELOS DE DADOS (ORM)

class Categoria(db.Model):
    """ Tabela que armazena as categorias (Ex: Eletricista, Encanador) """
    id_categoria = db.Column(db.Integer, primary_key=True)
    nome_categoria = db.Column(db.String(100), nullable=False)
    
    # Relacionamento: Permite acessar os prestadores desta categoria
    prestadores = db.relationship('Prestador', backref='categoria', lazy=True)

class Prestador(db.Model):
    """ Tabela principal dos Prestadores de Serviço """
    codigo_prestador = db.Column(db.Integer, primary_key=True)
    nome_prestador = db.Column(db.String(100), nullable=False)
    tempo_experiencia = db.Column(db.Integer, nullable=False) # Armazenado em anos
    
    # Chave Estrangeira ligando à Categoria
    id_categoria = db.Column(db.Integer, db.ForeignKey('categoria.id_categoria'), nullable=False)
    
    # Relacionamento: Um prestador pode ter vários serviços realizados
    servicos = db.relationship('Servico', backref='prestador', lazy=True)

class Servico(db.Model):
    """ Tabela de Serviços realizados """
    id_servico = db.Column(db.Integer, primary_key=True)
    nome_servico = db.Column(db.String(100), nullable=False)
    
    # Armazena o valor base (R$ 50.00) no banco de dados
    _vlr_servico = db.Column("vlr_servico", db.Float, default=50.00)
    
    # Chave Estrangeira ligando ao Prestador
    codigo_prestador = db.Column(db.Integer, db.ForeignKey('prestador.codigo_prestador'), nullable=False)

    # REGRA DE NEGÓCIO (CAMPO CALCULADO)
    @property
    def vlr_servico(self):
        """
        Calcula o valor final do serviço dinamicamente.
        Base R$ 50 + % de acréscimo dependendo da experiência do prestador.
        """
        base = 50.00
        # Busca a experiência do prestador dono deste serviço
        experiencia = self.prestador.tempo_experiencia
        
        if experiencia == 2:
            return base * 1.20 # +20%
        elif 2 < experiencia <= 5:
            return base * 1.40 # +40%
        elif experiencia > 5:
            return base * 1.65 # +65%
        return base # Caso padrão

    @vlr_servico.setter
    def vlr_servico(self, value):
        self._vlr_servico = value

# SEÇÃO 3: SCHEMAS (SERIALIZAÇÃO JSON)

class CategoriaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Categoria
        load_instance = True

class ServicoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Servico
        include_fk = True # Inclui as chaves estrangeiras no JSON
        load_instance = True
    
    # Força a exibição do valor calculado (@property), e não do valor do banco
    vlr_servico = fields.Float(dump_only=True)

class PrestadorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Prestador
        include_fk = True
        load_instance = True
    
    # Opcional: Mostra os serviços e categoria aninhados no JSON do prestador
    servicos = ma.Nested(ServicoSchema, many=True)
    categoria = ma.Nested(CategoriaSchema)

# Instâncias dos schemas para uso nas rotas
prestador_schema = PrestadorSchema()
prestadores_schema = PrestadorSchema(many=True)
categoria_schema = CategoriaSchema()
servico_schema = ServicoSchema()

# SEÇÃO 4: AUTENTICAÇÃO E SEGURANÇA (JWT)

def token_required(f):
    """ Decorador para proteger rotas que exigem login """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token') # Busca token na URL
        if not token:
            return jsonify({'message': 'Token ausente!'}), 403
        try:
            # Tenta decodificar o token usando nossa chave secreta
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token inválido!'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    """ Rota para gerar o Token de acesso """
    auth = request.json
    # Validação simples (Login fixo para teste)
    if auth and auth['user'] == 'admin' and auth['password'] == '1234':
        # Gera token com validade de 30 minutos
        token = jwt.encode({
            'user': auth['user'], 
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'message': 'Login falhou'}), 401

# SEÇÃO 5: ROTAS DA API (CONTROLLERS)

# SETUP INICIAL
@app.route('/setup', methods=['GET'])
def setup():
    """ Cria o banco de dados e popula categorias iniciais """
    with app.app_context():
        db.create_all()
        if not Categoria.query.first():
            db.session.add_all([
                Categoria(nome_categoria="Carpintaria"),
                Categoria(nome_categoria="Eletricista"),
                Categoria(nome_categoria="Encanador")
            ])
            db.session.commit()
    return "Banco recriado com tabelas e dados iniciais!"

# ROTAS DE PRESTADOR (CRUD)

@app.route('/prestador', methods=['POST'])
@token_required # Rota Protegida
def add_prestador():
    """ CREATE: Adiciona novo prestador """
    try:
        nome = request.json['nome_prestador']
        exp = int(request.json['tempo_experiencia'])
        cat_id = int(request.json['id_categoria'])
        
        novo_prestador = Prestador(nome_prestador=nome, tempo_experiencia=exp, id_categoria=cat_id)
        db.session.add(novo_prestador)
        db.session.commit()
        return prestador_schema.jsonify(novo_prestador)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/prestador', methods=['GET'])
def get_prestadores():
    """ READ: Lista todos os prestadores """
    all_prestadores = Prestador.query.all()
    return prestadores_schema.jsonify(all_prestadores)

@app.route('/prestador/<int:id>', methods=['PUT'])
@token_required # Rota Protegida
def update_prestador(id):
    """ UPDATE: Atualiza dados de um prestador """
    prestador = Prestador.query.get(id)
    if not prestador: return jsonify({'message': 'Não encontrado!'}), 404
    
    try:
        data = request.json
        if 'nome_prestador' in data: prestador.nome_prestador = data['nome_prestador']
        if 'tempo_experiencia' in data: prestador.tempo_experiencia = int(data['tempo_experiencia'])
        if 'id_categoria' in data: prestador.id_categoria = int(data['id_categoria'])
        
        db.session.commit()
        return prestador_schema.jsonify(prestador)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/prestador/<int:id>', methods=['DELETE'])
@token_required # Rota Protegida
def delete_prestador(id):
    """ DELETE: Remove prestador e seus serviços """
    prestador = Prestador.query.get(id)
    if not prestador: return jsonify({'message': 'Não encontrado!'}), 404
    
    try:
        Servico.query.filter_by(codigo_prestador=id).delete() # Limpa serviços antes
        db.session.delete(prestador)
        db.session.commit()
        return jsonify({'message': 'Prestador deletado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 400

# ROTAS DE CONSULTA ESPECÍFICAS

@app.route('/prestador/categoria/<id>', methods=['GET'])
def get_prestador_by_cat(id):
    """ Busca prestadores por ID da categoria """
    prestadores = Prestador.query.filter_by(id_categoria=id).all()
    return prestadores_schema.jsonify(prestadores)

@app.route('/prestador/servico/<nome_servico>', methods=['GET'])
def get_prestador_by_servico(nome_servico):
    """ Busca prestadores filtrando pelo nome do serviço principal """
    prestadores = Prestador.query.join(Servico).filter(Servico.nome_servico.like(f"%{nome_servico}%")).all()
    return prestadores_schema.jsonify(prestadores)

# ROTAS DE SERVIÇO E CATEGORIA

@app.route('/servico', methods=['POST'])
def add_servico():
    """ Adiciona um serviço a um prestador existente """
    try:
        nome = request.json['nome_servico']
        cod_prestador = int(request.json['codigo_prestador'])
        
        novo_servico = Servico(nome_servico=nome, codigo_prestador=cod_prestador)
        db.session.add(novo_servico)
        db.session.commit()
        return servico_schema.jsonify(novo_servico)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/servico/<int:id>', methods=['DELETE'])
@token_required # Rota Protegida
def delete_servico(id):
    """ DELETE: Remove apenas um serviço específico """
    servico = Servico.query.get(id)
    if not servico: return jsonify({'message': 'Não encontrado!'}), 404
    
    try:
        db.session.delete(servico)
        db.session.commit()
        return jsonify({'message': f'Serviço {id} removido com sucesso!'})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/categoria', methods=['POST'])
def add_categoria():
    """ Adiciona nova categoria """
    try:
        nome = request.json['nome_categoria']
        nova_categoria = Categoria(nome_categoria=nome)
        db.session.add(nova_categoria)
        db.session.commit()
        return categoria_schema.jsonify(nova_categoria)
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@app.route('/categoria', methods=['GET'])
def get_categorias():
    """ Lista todas as categorias """
    todas = Categoria.query.all()
    result = [{"id_categoria": c.id_categoria, "nome_categoria": c.nome_categoria} for c in todas]
    return jsonify(result)

@app.route('/categoria/<int:id>', methods=['DELETE'])
@token_required # Rota Protegida
def delete_categoria(id):
    """ DELETE: Remove categoria (se não houver prestadores vinculados) """
    categoria = Categoria.query.get(id)
    if not categoria: return jsonify({'message': 'Não encontrada!'}), 404

    # Verifica integridade antes de deletar
    if categoria.prestadores:
        return jsonify({'erro': 'Não é possível deletar! Existem prestadores nesta categoria.'}), 400

    try:
        db.session.delete(categoria)
        db.session.commit()
        return jsonify({'message': f'Categoria {id} deletada com sucesso!'})
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

# SEÇÃO 6: EXECUÇÃO

if __name__ == '__main__':
    app.run(debug=True)
