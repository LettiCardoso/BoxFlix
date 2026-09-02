from flask import Flask, render_template

app = Flask(__name__)

# Lista de itens salvos pelo usuário (em um projeto real, isso viria de um banco de dados)
minha_lista = [
    {
        "titulo": "O Horizonte de Marte",
        "tipo": "Série",
        "classificacao": "16",
        "info_extra": "2 Temporadas",
        "destaque": True,           # item grande em destaque
        "novo_episodio": True,
        "cor": "#1b2a4a"
    },
    {
        "titulo": "Night Shadows",
        "tipo": "Filme",
        "classificacao": "14",
        "info_extra": "2h 05min",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#20242c"
    },
    {
        "titulo": "Lumina",
        "tipo": "Filme",
        "classificacao": "12",
        "info_extra": "1h 48min",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#123524"
    },
    {
        "titulo": "Rota de Fogo",
        "tipo": "Filme",
        "classificacao": "16",
        "info_extra": "1h 55min",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#3a1010"
    },
    {
        "titulo": "A Casa na Névoa",
        "tipo": "Série",
        "classificacao": "16",
        "info_extra": "1 Temporada",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#1c1c1c"
    },
    {
        "titulo": "Abismo Luminoso",
        "tipo": "Filme",
        "classificacao": "10",
        "info_extra": "1h 32min",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#0f2b3a"
    },
    {
        "titulo": "A Herança Perdida",
        "tipo": "Série",
        "classificacao": "14",
        "info_extra": "3 Temporadas",
        "destaque": False,
        "novo_episodio": False,
        "cor": "#2a2013"
    },
]


@app.route("/")
def minha_lista_view():
    # Separa o item em destaque (o primeiro card grande) do restante da grade
    item_destaque = next((item for item in minha_lista if item["destaque"]), None)
    outros_itens = [item for item in minha_lista if not item["destaque"]]

    return render_template(
        "minha_lista.html",
        item_destaque=item_destaque,
        outros_itens=outros_itens
    )


if __name__ == "__main__":
    app.run(debug=True)
