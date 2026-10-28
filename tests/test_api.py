"""Testes da API BoxFlix (cenários 200, 400, 500 e complementares).

Executar na raiz do projeto:  python -m pytest tests -v
"""
import os
import sqlite3
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as boxflix  # noqa: E402

CADASTRO = {"nome": "Maria Silva", "email": "Maria@Teste.com",
            "senha": "senha123", "confirmarSenha": "senha123"}
TERMOS_PROIBIDOS = ["Traceback", "sqlite3", "unable to open database", "falha interna simulada", "app.py", "SELECT "]


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(boxflix, "DATABASE", str(tmp_path / "teste.db"))
    boxflix.init_db()
    boxflix.app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    return boxflix.app.test_client()


@pytest.fixture
def logado(client):
    client.post("/api/cadastro", json=CADASTRO)
    r = client.post("/api/login", json={"email": "maria@teste.com", "senha": "senha123"})
    assert r.status_code == 200
    return client


def titulos(r):
    return [i["titulo"] for i in r.get_json()["filmes"]]


# ------------------------------- 200 / 201 ---------------------------------
def test_ct01_cadastro_valido(client):
    r = client.post("/api/cadastro", json=CADASTRO)
    assert r.status_code == 201
    assert r.get_json() == {"sucesso": True, "mensagem": "Conta criada com sucesso! Faça login."}
    with sqlite3.connect(boxflix.DATABASE) as db:
        email, hash_ = db.execute("SELECT email, senha_hash FROM usuarios").fetchone()
    assert email == "maria@teste.com" and hash_ != "senha123"


def test_ct02_login_valido(client):
    client.post("/api/cadastro", json=CADASTRO)
    r = client.post("/api/login", json={"email": " MARIA@teste.com ", "senha": "senha123"})
    assert r.status_code == 200
    assert r.get_json() == {"sucesso": True, "mensagem": "Login realizado com sucesso!", "redirect": "/dashboard"}
    assert "session=" in r.headers["Set-Cookie"]
    assert client.get("/dashboard").status_code == 200


def test_ct03_content(logado):
    r = logado.get("/api/content")
    j = r.get_json()
    assert r.status_code == 200 and set(j) == {"destaque", "populares", "series_em_alta"}
    assert j["destaque"]["id"] == 2
    assert [i["id"] for i in j["populares"]] == [1, 2, 3, 4, 5]
    assert [i["id"] for i in j["series_em_alta"]] == [6, 7, 8, 9]


def test_ct04_titulo(logado):
    r = logado.get("/api/titulo/1")
    j = r.get_json()
    assert r.status_code == 200
    assert set(j) == {"id", "titulo", "tipo", "genero", "ano", "nota", "classificacao", "qualidade", "poster", "descricao"}
    assert (j["titulo"], j["tipo"], j["ano"], j["nota"]) == ("Homem-Aranha 2", "filme", 2004, 8.9)


def test_ct05_buscar_sem_filtros(logado):
    j = logado.get("/api/buscar").get_json()
    assert j["total"] == 9 == len(j["filmes"])


def test_ct06_buscar_titulo(logado):
    r = logado.get("/api/buscar?q=homem")
    assert r.status_code == 200 and r.get_json()["total"] == 2
    assert set(titulos(r)) == {"Homem-Aranha 2", "Homem de Ferro"}


def test_ct07_buscar_classificacao_e_nota(logado):
    assert titulos(logado.get("/api/buscar?classificacao=L&nota_min=8")) == ["Divertida Mente 2"]


def test_ct08_buscar_qualidade_e_periodo(logado):
    r = logado.get("/api/buscar", query_string={"qualidade": "4K HDR", "ano_min": 2010, "ano_max": 2024})
    assert set(titulos(r)) == {"Vingadores: Guerra Infinita", "Divertida Mente 2", "Barbie"}


def test_ct09_buscar_sem_resultado(logado):
    r = logado.get("/api/buscar?q=zzzz")
    assert r.status_code == 200 and r.get_json() == {"total": 0, "filmes": []}


# ---------------------------------- 400 ------------------------------------
@pytest.mark.parametrize("campos,mensagem", [
    ({"nome": ""}, "Informe seu nome completo."),
    ({"nome": "Jo"}, "Informe seu nome completo."),
    ({"email": "maria.teste.com"}, "Informe um e-mail válido."),
    ({"senha": "123", "confirmarSenha": "123"}, "A senha deve ter pelo menos 6 caracteres."),
    ({"confirmarSenha": "outra123"}, "As senhas não coincidem."),
    ({"__vazio__": True}, "Informe seu nome completo."),
])
def test_ct10_a_15_cadastro_invalido(client, campos, mensagem):
    corpo = {} if "__vazio__" in campos else {**CADASTRO, **campos}
    r = client.post("/api/cadastro", json=corpo)
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": mensagem}
    with sqlite3.connect(boxflix.DATABASE) as db:
        assert db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0


@pytest.mark.parametrize("tipo", ["application/json", "text/plain"])
def test_ct16_cadastro_corpo_nao_json(client, tipo):
    r = client.post("/api/cadastro", data="{nome:", content_type=tipo)
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": boxflix.MSG_CORPO_INVALIDO}


def test_ct17_login_sem_senha(client):
    r = client.post("/api/login", json={"email": "maria@teste.com"})
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": "Preencha e-mail e senha."}
    assert "Set-Cookie" not in r.headers


def test_ct18_login_corpo_vazio(client):
    r = client.post("/api/login", json={})
    assert r.status_code == 400
    assert r.get_json() == {"sucesso": False, "mensagem": "Preencha e-mail e senha."}


# ---------------------------------- 500 ------------------------------------
def confere_500(r):
    assert r.status_code == 500
    assert r.get_json() == {"sucesso": False, "mensagem": "Erro interno. Tente novamente mais tarde."}
    corpo = r.get_data(as_text=True)
    for termo in TERMOS_PROIBIDOS:
        assert termo not in corpo


def falha_db():
    return mock.patch.object(boxflix, "get_db", side_effect=sqlite3.OperationalError("unable to open database file"))


def test_ct19_500_login(client):
    with falha_db():
        r = client.post("/api/login", json={"email": "maria@teste.com", "senha": "senha123"})
    confere_500(r)
    assert "Set-Cookie" not in r.headers


def test_ct20_500_cadastro(client):
    with falha_db():
        r = client.post("/api/cadastro", json=CADASTRO)
    confere_500(r)
    with sqlite3.connect(boxflix.DATABASE) as db:
        assert db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0


def test_ct21_500_buscar(logado):
    with mock.patch.object(boxflix, "filtra_catalogo", side_effect=RuntimeError("falha interna simulada")):
        confere_500(logado.get("/api/buscar?q=x"))


def test_ct22_500_titulo(logado):
    with mock.patch.object(boxflix, "busca_por_id", side_effect=RuntimeError("falha interna simulada")):
        confere_500(logado.get("/api/titulo/1"))


# ------------------------------ complementares -----------------------------
@pytest.mark.parametrize("corpo", [
    {"email": "maria@teste.com", "senha": "errada1"},
    {"email": "x@y.com", "senha": "abcdef"},
])
def test_ct23_login_invalido(client, corpo):
    client.post("/api/cadastro", json=CADASTRO)
    r = client.post("/api/login", json=corpo)
    assert r.status_code == 401
    assert r.get_json() == {"sucesso": False, "mensagem": "E-mail ou senha inválidos."}


def test_ct24_email_duplicado(client):
    client.post("/api/cadastro", json=CADASTRO)
    r = client.post("/api/cadastro", json=CADASTRO)
    assert r.status_code == 409
    assert r.get_json() == {"sucesso": False, "mensagem": "Este e-mail já está cadastrado."}


def test_ct25_titulo_inexistente(logado):
    r = logado.get("/api/titulo/999")
    assert r.status_code == 404 and r.get_json() == {"sucesso": False, "mensagem": "Não encontrado."}
    r = logado.get("/api/titulo/abc")
    assert r.status_code == 404 and r.get_json()["sucesso"] is False


@pytest.mark.parametrize("rota", ["/api/content", "/api/titulo/1", "/api/buscar"])
def test_ct26_api_sem_sessao_401(client, rota):
    r = client.get(rota)
    assert r.status_code == 401
    assert r.get_json()["sucesso"] is False


@pytest.mark.parametrize("rota", ["/dashboard", "/busca-avancada"])
def test_ct26_paginas_sem_sessao_redirecionam(client, rota):
    r = client.get(rota)
    assert r.status_code == 302 and r.headers["Location"] == "/"


def test_metodo_nao_permitido_em_api(client):
    r = client.get("/api/cadastro")
    assert r.status_code == 405 and r.get_json()["sucesso"] is False


@pytest.mark.parametrize("qs", ["ano_min=abc", "ano_max=x", "nota_min=abc", "nota_min=nan", "nota_min=-5", "nota_min=11"])
def test_ct27_buscar_parametro_invalido(logado, qs):
    r = logado.get(f"/api/buscar?{qs}")
    assert r.status_code == 400 and r.get_json()["sucesso"] is False


def test_buscar_intervalo_invertido_e_200_vazio(logado):
    r = logado.get("/api/buscar?ano_min=2030&ano_max=2020")
    assert r.status_code == 200 and r.get_json() == {"total": 0, "filmes": []}
