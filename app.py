"""
CineFlix — backend Flask
-------------------------
Serve o layout da página inicial e uma API simples que entrega os dados
(destaque, filmes populares e séries em alta) para o front-end montar os
cartões. Os "posters" ficam como espaços reservados (placeholders) — basta
trocar o campo "poster" por uma URL de imagem real quando você tiver a arte
de cada filme/série.

Rodar:
    pip install flask
    python app.py
Depois acesse http://localhost:5000
"""

from flask import Flask, jsonify, render_template

app = Flask(__name__)

# ---------------------------------------------------------------------------
# "Banco de dados" em memória — troque por um banco real (SQLite/Postgres)
# quando quiser. Cada item sem "poster" definido renderiza como um espaço
# reservado no front-end, pronto para receber a arte do filme/série.
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
    "poster": None,   # coloque aqui a URL da arte de fundo do herói
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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/content")
def content():
    """Devolve todo o conteúdo da home em um único payload."""
    return jsonify({
        "destaque": DESTAQUE,
        "populares": POPULARES,
        "series_em_alta": SERIES_EM_ALTA,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
