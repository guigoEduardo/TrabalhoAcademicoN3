# 🛠️ Sistema de Gerenciamento de Prestadores de Serviço (API Rest)

Projeto acadêmico desenvolvido para a Avaliação N3 das disciplinas de **Desenvolvimento Server-Side** e **Banco de Dados**. 

O objetivo é fornecer uma API Rest para gerenciar prestadores de serviços, categorias e serviços, aplicando regras de negócio para cálculo dinâmico de valores e segurança via Token JWT.

## 📋 Funcionalidades

- **CRUD Completo:** Criação, Leitura, Atualização e Remoção de Prestadores.
- **Regra de Negócio:** Cálculo automático do valor da hora do serviço baseado na experiência do prestador (+20%, +40% ou +65%).
- **Autenticação:** Uso de Token JWT para proteger rotas críticas (Cadastro/Edição/Remoção).
- **ORM:** Mapeamento Objeto-Relacional utilizando SQLAlchemy.
- **Banco de Dados:** Persistência em SQLite.

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3
- **Framework Web:** Flask
- **Banco de Dados:** SQLite
- **Bibliotecas Principais:**
  - `Flask-SQLAlchemy` (ORM)
  - `Flask-Marshmallow` (Serialização de JSON)
  - `PyJWT` (Autenticação via Token)

## 📦 Como Rodar o Projeto

### 1. Pré-requisitos
Certifique-se de ter o **Python** instalado em sua máquina.

### 2. Instalação das Dependências
Abra o terminal na pasta do projeto e execute o comando abaixo para instalar as bibliotecas necessárias:

```bash
pip install flask flask-sqlalchemy flask-marshmallow marshmallow-sqlalchemy pyjwt

Obs: Utilize a extensão do Thunder Cliente para gerenciar as requisições e para visualizar o banco de dados visualmente utilize a extensão SQLite Viwer.
