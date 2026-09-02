"""
BoxFlix - backend de autenticação
Framework: Flask
Banco de dados: SQLite (arquivo local boxflix.db)

Rotas principais:
  GET/POST  /              -> tela de login
  GET/POST  /cadastro      -> tela de cadastro
  GET       /dashboard     -> área logada (protegida)
  GET       /logout        -> encerra a sessão
  POST      /api/login     -> login via JS (fetch), retorna JSON
  POST      /api/cadastro  -> cadastro via JS (fetch), retorna JSON
"""

import re
import sqlite3
from functools import wraps

from flask import Flask, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-chave-em-producao"  # necessário para usar session
DATABASE = "boxflix.db"

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Conteúdo da home (área logada) — "banco de dados" em memória.
# Troque por uma tabela real (ex.: filmes/series no SQLite) quando quiser.
# Itens sem "poster" aparecem como espaço reservado no front-end.
# ---------------------------------------------------------------------------
DESTAQUE = {
    "tipo": "FILME",
    "tag": "Destaque da Semana",
    "titulo": "A Fronteira do Silêncio",
    "descricao": (
        "Em um futuro onde a comunicação falhou, um grupo de exploradores "
        "precisa cruzar uma zona de distorção temporal para salvar a "
        "humanidade. Uma jornada épica sobre sacrifício e esperança na "
        "vastidão silenciosa do cosmos."
    ),
    "poster": None,
}

POPULARES = [
    {"id": 1, "titulo": "", "poster": None},
    {"id": 2, "titulo": "", "poster": None},
    {"id": 3, "titulo": "", "poster": None},
    {"id": 4, "titulo": "", "poster": None},
    {"id": 5, "titulo": "", "poster": None},
]

SERIES_EM_ALTA = [
    {"id": 1, "titulo": "", "poster": None},
    {"id": 2, "titulo": "", "poster": None},
    {"id": 3, "titulo": "", "poster": None},
    {"id": 4, "titulo": "", "poster": None},
]


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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
