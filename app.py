"""
BoxFlix - backend de autenticação e catálogo
Framework: Flask
Banco de dados: SQLite (arquivo local boxflix.db)

Rotas principais:
  GET       /               -> tela de login
  GET       /cadastro       -> tela de cadastro
  GET       /dashboard      -> área logada (protegida)
  GET       /busca-avancada -> busca avançada (protegida)
  GET       /logout         -> encerra a sessão
  POST      /api/login      -> login via JS (fetch), retorna JSON
  POST      /api/cadastro   -> cadastro via JS (fetch), retorna JSON
  GET       /api/content    -> conteúdo da home (protegida)
  GET       /api/titulo/id  -> detalhes de um título (protegida)
  GET       /api/buscar     -> busca filtrada no catálogo (protegida)
"""

import os
import re
import sqlite3
from functools import wraps

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

from catalogo import (
    DESTAQUE,
    POPULARES,
    SERIES_EM_ALTA,
    busca_por_id,
    filtra_catalogo,
)
from log import configurar_logger

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")  # necessário para usar session
configurar_logger(app)

DATABASE = "boxflix.db"
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
def get_db():
    """Abre (ou reaproveita) a conexão com o SQLite para esta requisição."""
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria a tabela de usuários caso ainda não exista."""
    with app.app_context():
        db = get_db()
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL
            )
            """
        )
        db.commit()


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)

    return wrapped


def validar_cadastro(nome, email, senha, confirmar_senha):
    if not nome or len(nome.strip()) < 3:
        return "Informe seu nome completo."
    if not email or not EMAIL_REGEX.match(email):
        return "Informe um e-mail válido."
    if not senha or len(senha) < 6:
        return "A senha deve ter pelo menos 6 caracteres."
    if senha != confirmar_senha:
        return "As senhas não coincidem."
    return None


# ---------------------------------------------------------------------------
# Tratamento de erros
# ---------------------------------------------------------------------------
@app.errorhandler(Exception)
def erro_interno(erro):
    """Erros inesperados: registra o detalhe no log e devolve mensagem genérica.

    Nunca expõe stack trace, caminho de arquivo ou mensagem do banco ao cliente.
    Erros HTTP normais (404, 405...) seguem o comportamento padrão do Flask.
    """
    if isinstance(erro, HTTPException):
        return erro
    app.logger.error("Erro interno em %s %s", request.method, request.path, exc_info=erro)
    if request.path.startswith("/api/"):
        return jsonify({"sucesso": False, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}), 500
    return "Erro interno do servidor.", 500


# ---------------------------------------------------------------------------
# Rotas de páginas (HTML)
# ---------------------------------------------------------------------------
@app.route("/")
def login_page():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/cadastro")
def cadastro_page():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("cadastro.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", nome=session.get("usuario_nome"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/busca-avancada")
@login_required
def busca_avancada():
    return render_template(
        "busca.html",
        nome=session.get("usuario_nome"),
        termo_inicial=request.args.get("q", ""),
    )


# ---------------------------------------------------------------------------
# API (chamada pelo JavaScript via fetch)
# ---------------------------------------------------------------------------
@app.route("/api/cadastro", methods=["POST"])
def api_cadastro():
    dados = request.get_json(silent=True) or {}
    nome = (dados.get("nome") or "").strip()
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""
    confirmar_senha = dados.get("confirmarSenha") or ""

    erro = validar_cadastro(nome, email, senha, confirmar_senha)
    if erro:
        return jsonify({"sucesso": False, "mensagem": erro}), 400

    db = get_db()
    existente = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existente:
        return jsonify({"sucesso": False, "mensagem": "Este e-mail já está cadastrado."}), 409

    senha_hash = generate_password_hash(senha)
    db.execute(
        "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
        (nome, email, senha_hash),
    )
    db.commit()

    return jsonify({"sucesso": True, "mensagem": "Conta criada com sucesso! Faça login."})


@app.route("/api/login", methods=["POST"])
def api_login():
    dados = request.get_json(silent=True) or {}
    email = (dados.get("email") or "").strip().lower()
    senha = dados.get("senha") or ""

    if not email or not senha:
        return jsonify({"sucesso": False, "mensagem": "Preencha e-mail e senha."}), 400

    db = get_db()
    usuario = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()

    if usuario is None or not check_password_hash(usuario["senha_hash"], senha):
        return jsonify({"sucesso": False, "mensagem": "E-mail ou senha inválidos."}), 401

    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]

    return jsonify({"sucesso": True, "mensagem": "Login realizado com sucesso!", "redirect": url_for("dashboard")})


@app.route("/api/content")
@login_required
def api_content():
    """Devolve o conteúdo da home (destaque, populares, séries em alta)."""
    return jsonify({
        "destaque": DESTAQUE,
        "populares": POPULARES,
        "series_em_alta": SERIES_EM_ALTA,
    })


@app.route("/api/titulo/<int:item_id>")
@login_required
def api_titulo(item_id):
    """Devolve os detalhes completos de um filme/série (usado pelo modal)."""
    item = busca_por_id(item_id)
    if item is None:
        return jsonify({"mensagem": "Não encontrado."}), 404
    return jsonify(item)


@app.route("/api/buscar")
@login_required
def api_buscar():
    """Busca avançada: filtra o catálogo por título, ano, classificação, nota e qualidade."""
    termo = request.args.get("q", "").strip()
    ano_min = request.args.get("ano_min", 1980, type=int)
    ano_max = request.args.get("ano_max", 2026, type=int)
    nota_min = request.args.get("nota_min", 0, type=float)
    classificacoes = request.args.getlist("classificacao")
    qualidades = request.args.getlist("qualidade")

    resultado = filtra_catalogo(termo, ano_min, ano_max, classificacoes, nota_min, qualidades)
    return jsonify({"total": len(resultado), "filmes": resultado})


if __name__ == "__main__":
    init_db()
    # host 0.0.0.0 é necessário para o container Docker aceitar conexões externas.
    # debug fica desligado (ligue só em desenvolvimento: FLASK_DEBUG=1).
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG") == "1")