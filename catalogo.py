"""
Catálogo em memória do BoxFlix (destaque, filmes e séries).

Separado do app.py para manter o arquivo principal focado nas rotas,
autenticação e acesso ao banco de dados.
"""

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
}

# Cada item tem: id, titulo, tipo (filme/série), genero, ano, nota,
# classificacao, qualidade, poster e descricao (usada no modal de detalhes).
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
    """Retorna o item do catálogo pelo ID, ou None se não existir."""
    return next((item for item in CATALOGO if item["id"] == item_id), None)


def filtra_catalogo(termo, ano_min, ano_max, classificacoes, nota_min, qualidades):
    """Filtra o catálogo por título, faixa de ano, classificação, nota mínima e qualidade."""
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
