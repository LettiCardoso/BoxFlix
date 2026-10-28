"""Testes automatizados das APIs do BoxFlix (cenários 200/201, 400 e 500).

Execução:  pytest -v
Cada teste usa um banco SQLite temporário, sem tocar no boxflix.db real.
"""
import sqlite3

import pytest

import app as boxflix

USUARIO = {
    "nome": "Maria Silva",
    "email": "maria@email.com",
    "senha": "123456",
    "confirmarSenha": "123456",
}
MSG_ERRO_500 = "Erro interno do servidor. Tente novamente mais tarde."


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(boxflix, "DATABASE", str(tmp_path / "teste.db"))
    boxflix.init_db()
    boxflix.app.config["TESTING"] = True
    with boxflix.app.test_client() as c:
        yield c


@pytest.fixture
def logado(client):
    client.post("/api/cadastro", json=USUARIO)
    client.post("/api/login", json={"email": USUARIO["email"], "senha": USUARIO["senha"]})
    return client


def quebrar_banco(monkeypatch):
    """Simula falha interna controlada: o banco levanta erro com detalhe sensível."""
    def falha():
        raise sqlite3.OperationalError("unable to open database file /var/secret/boxflix.db")
    monkeypatch.setattr(boxflix, "get_db", falha)


def assert_500_sem_detalhes(resp):
    assert resp.status_code == 500
    corpo = resp.get_data(as_text=True)
    assert resp.get_json() == {"sucesso": False, "mensagem": MSG_ERRO_500}
    for vazado in ("Traceback", "sqlite3", "OperationalError", "secret", "app.py"):
        assert vazado not in corpo


# ------------------------------ POST /api/cadastro ------------------------------
def test_cadastro_200_sucesso(client):
    r = client.post("/api/cadastro", json=USUARIO)
    assert r.status_code == 200
    assert r.get_json() == {"sucesso": True, "mensagem": "Conta criada com sucesso! Faça login."}


@pytest.mark.parametrize("campo,valor,mensagem", [
    ("nome", "Ma", "Informe seu nome completo."),
    ("nome", "", "Informe seu nome completo."),
    ("email", "email-invalido", "Informe um e-mail válido."),
    ("senha", "123", "A senha deve ter pelo menos 6 caracteres."),
    ("confirmarSenha", "999999", "As senhas não coincidem."),
])
def test_cadastro_400_dados_invalidos(client, campo, valor, mensagem):
    r = client.post("/api/cadastro", json={**USUARIO, campo: valor})
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": mensagem}


def test_cadastro_400_campo_omitido(client):
    dados = {k: v for k, v in USUARIO.items() if k != "email"}
    r = client.post("/api/cadastro", json=dados)
    assert r.status_code == 400
    assert r.get_json()["mensagem"] == "Informe um e-mail válido."


def test_cadastro_400_corpo_vazio(client):
    r = client.post("/api/cadastro")
    assert r.status_code == 400
    assert r.get_json()["sucesso"] is False


def test_cadastro_409_email_duplicado(client):
    client.post("/api/cadastro", json=USUARIO)
    r = client.post("/api/cadastro", json=USUARIO)
    assert r.status_code == 409
    assert r.get_json() == {"sucesso": False, "mensagem": "Este e-mail já está cadastrado."}


def test_cadastro_500_falha_no_banco(client, monkeypatch):
    quebrar_banco(monkeypatch)
    assert_500_sem_detalhes(client.post("/api/cadastro", json=USUARIO))


# -------------------------------- POST /api/login --------------------------------
def test_login_200_sucesso(client):
    client.post("/api/cadastro", json=USUARIO)
    r = client.post("/api/login", json={"email": USUARIO["email"], "senha": USUARIO["senha"]})
    assert r.status_code == 200
    assert r.get_json() == {"sucesso": True, "mensagem": "Login realizado com sucesso!", "redirect": "/dashboard"}


@pytest.mark.parametrize("dados", [{"senha": "123456"}, {"email": "maria@email.com"}, {}])
def test_login_400_campo_omitido(client, dados):
    r = client.post("/api/login", json=dados)
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": "Preencha e-mail e senha."}


def test_login_401_senha_incorreta(client):
    client.post("/api/cadastro", json=USUARIO)
    r = client.post("/api/login", json={"email": USUARIO["email"], "senha": "errada!"})
    assert r.status_code == 401
    assert r.get_json() == {"sucesso": False, "mensagem": "E-mail ou senha inválidos."}


def test_login_401_usuario_inexistente(client):
    r = client.post("/api/login", json={"email": "naoexiste@email.com", "senha": "123456"})
    assert r.status_code == 401
    assert r.get_json()["mensagem"] == "E-mail ou senha inválidos."


def test_login_500_falha_no_banco(client, monkeypatch):
    quebrar_banco(monkeypatch)
    assert_500_sem_detalhes(client.post("/api/login", json={"email": "a@a.com", "senha": "123456"}))


# -------------------------------- GET /api/content --------------------------------
def test_content_200_sucesso(logado):
    r = logado.get("/api/content")
    assert r.status_code == 200
    d = r.get_json()
    assert d["destaque"]["titulo"] == "Vingadores: Guerra Infinita"
    assert len(d["populares"]) == 5 and all(i["id"] for i in d["populares"])
    assert [s["titulo"] for s in d["series_em_alta"]] == ["Teen Wolf", "Diários de Vampiros", "Naruto", "Barbie"]


def test_content_sem_login_redireciona(client):
    r = client.get("/api/content")
    assert r.status_code == 302 and r.headers["Location"] == "/"


def test_content_500_falha_interna(logado, monkeypatch):
    # Dado corrompido (não serializável em JSON) provoca falha interna ao montar a resposta
    monkeypatch.setattr(boxflix, "POPULARES", {object()})
    assert_500_sem_detalhes(logado.get("/api/content"))


# ------------------------------ GET /api/titulo/<id> ------------------------------
def test_titulo_200_sucesso(logado):
    r = logado.get("/api/titulo/5")
    assert r.status_code == 200
    d = r.get_json()
    assert (d["id"], d["titulo"], d["tipo"], d["ano"], d["nota"]) == (5, "Homem de Ferro", "filme", 2008, 9.1)


def test_titulo_404_inexistente(logado):
    r = logado.get("/api/titulo/999")
    assert r.status_code == 404
    assert r.get_json() == {"mensagem": "Não encontrado."}


def test_titulo_id_nao_numerico_404(logado):
    assert logado.get("/api/titulo/abc").status_code == 404


def test_titulo_500_falha_interna(logado, monkeypatch):
    def falha(_):
        raise RuntimeError("falha simulada /home/app/segredo.py")
    monkeypatch.setattr(boxflix, "busca_por_id", falha)
    assert_500_sem_detalhes(logado.get("/api/titulo/1"))


# ------------------------------- GET /api/buscar -------------------------------
def test_buscar_200_sem_filtros_retorna_catalogo(logado):
    d = logado.get("/api/buscar").get_json()
    assert d["total"] == 9 and len(d["filmes"]) == 9


def test_buscar_200_por_titulo(logado):
    r = logado.get("/api/buscar?q=homem")
    assert r.status_code == 200
    d = r.get_json()
    assert d["total"] == 2
    assert {f["titulo"] for f in d["filmes"]} == {"Homem-Aranha 2", "Homem de Ferro"}


def test_buscar_200_filtros_combinados(logado):
    d = logado.get("/api/buscar?nota_min=9&ano_min=2010").get_json()
    assert d["total"] == 1 and d["filmes"][0]["titulo"] == "Vingadores: Guerra Infinita"


def test_buscar_200_por_classificacao(logado):
    d = logado.get("/api/buscar?classificacao=L").get_json()
    assert sorted(f["id"] for f in d["filmes"]) == [3, 4, 9]


def test_buscar_200_sem_resultados(logado):
    r = logado.get("/api/buscar?q=zzzinexistente")
    assert r.status_code == 200
    assert r.get_json() == {"total": 0, "filmes": []}


def test_buscar_parametro_invalido_usa_padrao(logado):
    """Comportamento atual: ano_min não numérico é ignorado (não gera 400)."""
    r = logado.get("/api/buscar?ano_min=abc")
    assert r.status_code == 200 and r.get_json()["total"] == 9


def test_buscar_sem_login_redireciona(client):
    assert client.get("/api/buscar").status_code == 302


def test_buscar_500_falha_interna(logado, monkeypatch):
    def falha(*a, **k):
        raise RuntimeError("falha simulada /home/app/segredo.py")
    monkeypatch.setattr(boxflix, "filtra_catalogo", falha)
    assert_500_sem_detalhes(logado.get("/api/buscar?q=x"))
