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
def _poster(seed, largura=500, altura=750):
    """Gera uma URL de pôster de placeholder, estável por 'seed' (mesmo id = mesma imagem)."""
    return f"https://picsum.photos/seed/{seed}/{largura}/{altura}"


DESTAQUE = {
    "id": 2,
    "tipo": "FILME",
    "tag": "Destaque da Semana",
    "titulo": "Vingadores: Guerra Infinita",
    "descricao": (
        "Um grupo de heróis se une para enfrentar a maior ameaça já vista, "
        "numa corrida contra o tempo para impedir a destruição de metade "
        "do universo."
    ),
    "poster": _poster("destaque-vingadores", 1600, 900),
}

# ---------------------------------------------------------------------------
# Catálogo usado pela Home e pela Busca Avançada — "banco de dados" em memória.
# Troque por uma tabela real (ex.: filmes/series no SQLite) quando quiser.
# Cada item tem: id, titulo, tipo (filme/série), genero, ano, nota,
# classificacao, qualidade, poster e descricao (usada no modal de detalhes).
# ---------------------------------------------------------------------------
CATALOGO = [
    {
        "id": 1, "titulo": "Homem-Aranha 2", "tipo": "filme", "genero": "Ação",
        "ano": 2004, "nota": 8.9, "classificacao": 12, "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Dividido entre a vida pessoal e o dever de proteger a cidade, o herói "
            "aracnídeo enfrenta um cientista transformado em vilão após um "
            "experimento que sai do controle."
        ),
    },
    {
        "id": 2, "titulo": "Vingadores: Guerra Infinita", "tipo": "filme", "genero": "Ação",
        "ano": 2018, "nota": 9.0, "classificacao": 12, "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Um grupo de heróis se une para enfrentar a maior ameaça já vista, "
            "numa corrida contra o tempo para impedir a destruição de metade "
            "do universo."
        ),
    },
    {
        "id": 3, "titulo": "Divertida Mente 2", "tipo": "filme", "genero": "Animação",
        "ano": 2024, "nota": 8.6, "classificacao": "L", "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Na cabeça de uma adolescente, novas emoções chegam para bagunçar o "
            "equilíbrio que já existia, obrigando os sentimentos antigos a se "
            "reorganizarem para lidar com essa nova fase."
        ),
    },
    {
        "id": 4, "titulo": "Branca de Neve", "tipo": "filme", "genero": "Fantasia",
        "ano": 2025, "nota": 6.8, "classificacao": "L", "qualidade": ["HD 1080p"],
        "descricao": (
            "Uma jovem princesa foge para a floresta para escapar de uma rainha "
            "cruel e encontra, no caminho, aliados inesperados dispostos a "
            "ajudá-la a recuperar seu lugar."
        ),
    },
    {
        "id": 5, "titulo": "Homem de Ferro", "tipo": "filme", "genero": "Ação",
        "ano": 2008, "nota": 9.1, "classificacao": 12, "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Um bilionário e inventor cria uma armadura de alta tecnologia após "
            "escapar do cativeiro, e passa a usá-la para corrigir os erros do "
            "próprio passado."
        ),
    },
    {
        "id": 6, "titulo": "Teen Wolf", "tipo": "série", "genero": "Terror",
        "ano": 2011, "nota": 8.0, "classificacao": 14, "qualidade": ["HD 1080p"],
        "descricao": (
            "Um adolescente comum é mordido por uma criatura misteriosa e passa a "
            "desenvolver habilidades sobrenaturais, tendo que equilibrar a vida "
            "escolar com os perigos de seu novo lado selvagem."
        ),
    },
    {
        "id": 7, "titulo": "Diários de Vampiros", "tipo": "série", "genero": "Drama",
        "ano": 2009, "nota": 8.1, "classificacao": 16, "qualidade": ["HD 1080p"],
        "descricao": (
            "Numa pequena cidade cheia de segredos, uma jovem se apaixona por um "
            "vampiro centenário, dando início a um triângulo amoroso marcado por "
            "mistérios sobrenaturais."
        ),
    },
    {
        "id": 8, "titulo": "Naruto", "tipo": "série", "genero": "Aventura",
        "ano": 2002, "nota": 8.4, "classificacao": 12, "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Um jovem ninja sonha em se tornar o líder de sua vila e treina "
            "incansavelmente para provar seu valor, enfrentando rivais e "
            "organizações que ameaçam a paz entre as nações."
        ),
    },
    {
        "id": 9, "titulo": "Barbie", "tipo": "série", "genero": "Família",
        "ano": 2023, "nota": 7.5, "classificacao": "L", "qualidade": ["4K HDR", "HD 1080p"],
        "descricao": (
            "Depois de viver anos num mundo perfeito e colorido, a boneca mais "
            "famosa do mundo parte para o mundo real e descobre que a vida por "
            "lá é bem mais complicada do que imaginava."
        ),
    },
]

# Nome do arquivo de imagem de cada item, dentro de static/img/.
# Baixe o pôster oficial de cada título e salve na pasta static/img
# com o nome de arquivo indicado abaixo (o modelo mais fácil: buscar
# "nome do filme poster" no Google Imagens, salvar como .jpg).
POSTERS_ARQUIVOS = {
    1: "homem-aranha-2.jpg",
    2: "vingadores-guerra-infinita.jpg",
    3: "divertida-mente-2.jpg",
    4: "branca-de-neve.jpg",
    5: "homem-de-ferro.jpg",
    6: "teen-wolf.jpg",
    7: "diarios-de-vampiros.jpg",
    8: "naruto.jpg",
    9: "barbie.jpg",
}

for _item in CATALOGO:
    _item["poster"] = f"/static/img/{POSTERS_ARQUIVOS[_item['id']]}"

DESTAQUE["poster"] = f"/static/img/{POSTERS_ARQUIVOS[DESTAQUE['id']]}"

POPULARES = [
    {"id": item["id"], "titulo": item["titulo"], "poster": item["poster"]}
    for item in CATALOGO if item["tipo"] == "filme"
][:5]

SERIES_EM_ALTA = [
    {"id": item["id"], "titulo": item["titulo"], "poster": item["poster"]}
    for item in CATALOGO if item["tipo"] == "série"
]


def busca_por_id(item_id):
    return next((item for item in CATALOGO if item["id"] == item_id), None)


def filtra_catalogo(termo, ano_min, ano_max, classificacoes, nota_min, qualidades):
    resultado = []
    for item in CATALOGO:
        if termo and termo.lower() not in item["titulo"].lower():
            continue
        if not (ano_min <= item["ano"] <= ano_max):
            continue
        if classificacoes and str(item["classificacao"]) not in classificacoes:
            continue
        if item["nota"] < nota_min:
            continue
        if qualidades and not any(q in item["qualidade"] for q in qualidades):
            continue
        resultado.append(item)
    return resultado


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
    app.run(debug=True)
