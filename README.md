# BOXFLIX

*BoxFlix é um sistema em que as pessoas podem assistir aos seus filmes, séries favoritas com um ambiente acolhedor e simples.*

## Como executar

```bash
pip install -r requirements.txt
python app.py            # http://127.0.0.1:5000
```

Com Docker:

```bash
docker build -t boxflix .
docker run -p 5000:5000 boxflix
```

## Como executar os testes

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

Os testes (`tests/test_api.py`) implementam todos os cenários descritos abaixo. Cada teste usa um banco SQLite temporário, então o `boxflix.db` real não é alterado.

---

## Cenários de teste das APIs

### Endpoints da aplicação

| Método | Endpoint | Descrição | Exige login |
|---|---|---|---|
| POST | `/api/cadastro` | Cria uma conta de usuário | Não |
| POST | `/api/login` | Autentica o usuário e abre a sessão | Não |
| GET | `/api/content` | Conteúdo da home (destaque, populares, séries em alta) | Sim |
| GET | `/api/titulo/<id>` | Detalhes de um filme/série | Sim |
| GET | `/api/buscar` | Busca avançada (`q`, `ano_min`, `ano_max`, `nota_min`, `classificacao`, `qualidade`) | Sim |

> **Sobre o 201:** o `POST /api/cadastro` cria um recurso, mas a API foi implementada para responder **200** (e não 201). Os cenários seguem o comportamento real da API.
>
> **Sobre endpoints protegidos:** sem sessão ativa, eles respondem **302** (redirecionamento para `/`), e não 401.

### 1. POST `/api/cadastro`

| ID | Cenário | Dados enviados (JSON) | Status esperado | Resposta esperada |
|---|---|---|---|---|
| CAD-01 | **200 – Sucesso:** cadastro válido | `{"nome":"Maria Silva","email":"maria@email.com","senha":"123456","confirmarSenha":"123456"}` | 200 | `{"sucesso": true, "mensagem": "Conta criada com sucesso! Faça login."}` |
| CAD-02 | **400** – nome muito curto | mesmo corpo, com `"nome":"Ma"` | 400 | `{"sucesso": false, "mensagem": "Informe seu nome completo."}` |
| CAD-03 | **400** – nome vazio | mesmo corpo, com `"nome":""` | 400 | `{"sucesso": false, "mensagem": "Informe seu nome completo."}` |
| CAD-04 | **400** – e-mail inválido | mesmo corpo, com `"email":"email-invalido"` | 400 | `{"sucesso": false, "mensagem": "Informe um e-mail válido."}` |
| CAD-05 | **400** – campo obrigatório omitido (sem `email`) | `{"nome":"Maria Silva","senha":"123456","confirmarSenha":"123456"}` | 400 | `{"sucesso": false, "mensagem": "Informe um e-mail válido."}` |
| CAD-06 | **400** – senha com menos de 6 caracteres | mesmo corpo, com `"senha":"123"` | 400 | `{"sucesso": false, "mensagem": "A senha deve ter pelo menos 6 caracteres."}` |
| CAD-07 | **400** – senhas diferentes | mesmo corpo, com `"confirmarSenha":"999999"` | 400 | `{"sucesso": false, "mensagem": "As senhas não coincidem."}` |
| CAD-08 | **400** – requisição sem corpo | *(nenhum)* | 400 | `{"sucesso": false, "mensagem": ...}` |
| CAD-09 | **409** – e-mail já cadastrado | mesmo corpo de CAD-01, enviado duas vezes | 409 | `{"sucesso": false, "mensagem": "Este e-mail já está cadastrado."}` |
| CAD-10 | **500** – falha no banco (simulada com `monkeypatch`: `get_db` levanta `sqlite3.OperationalError`) | corpo válido de CAD-01 | 500 | `{"sucesso": false, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}` — sem *traceback*, nome de exceção, caminho de arquivo ou mensagem do banco |

### 2. POST `/api/login`

| ID | Cenário | Dados enviados (JSON) | Status esperado | Resposta esperada |
|---|---|---|---|---|
| LOG-01 | **200 – Sucesso:** credenciais corretas de usuário cadastrado | `{"email":"maria@email.com","senha":"123456"}` | 200 | `{"sucesso": true, "mensagem": "Login realizado com sucesso!", "redirect": "/dashboard"}` + cookie de sessão |
| LOG-02 | **400** – senha omitida | `{"email":"maria@email.com"}` | 400 | `{"sucesso": false, "mensagem": "Preencha e-mail e senha."}` |
| LOG-03 | **400** – e-mail omitido | `{"senha":"123456"}` | 400 | `{"sucesso": false, "mensagem": "Preencha e-mail e senha."}` |
| LOG-04 | **400** – corpo vazio | `{}` | 400 | `{"sucesso": false, "mensagem": "Preencha e-mail e senha."}` |
| LOG-05 | **401** – senha incorreta | `{"email":"maria@email.com","senha":"errada!"}` | 401 | `{"sucesso": false, "mensagem": "E-mail ou senha inválidos."}` |
| LOG-06 | **401** – usuário inexistente | `{"email":"naoexiste@email.com","senha":"123456"}` | 401 | `{"sucesso": false, "mensagem": "E-mail ou senha inválidos."}` |
| LOG-07 | **500** – falha no banco (simulada: `get_db` levanta `sqlite3.OperationalError`) | `{"email":"a@a.com","senha":"123456"}` | 500 | `{"sucesso": false, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}` — sem detalhes técnicos |

### 3. GET `/api/content` (requer login)

| ID | Cenário | Dados enviados | Status esperado | Resposta esperada |
|---|---|---|---|---|
| CON-01 | **200 – Sucesso:** usuário logado | *(nenhum)* | 200 | JSON com `destaque` (título "Vingadores: Guerra Infinita"), `populares` (5 filmes, cada um com `id`, `titulo`, `poster`) e `series_em_alta` (Teen Wolf, Diários de Vampiros, Naruto, Barbie) |
| CON-02 | Sem login | *(nenhum)* | 302 | Redireciona para `/` |
| CON-03 | **500** – dado interno corrompido (simulado: `POPULARES` com valor não serializável em JSON) | *(nenhum)* | 500 | `{"sucesso": false, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}` — sem detalhes técnicos |

### 4. GET `/api/titulo/<id>` (requer login)

| ID | Cenário | Dados enviados | Status esperado | Resposta esperada |
|---|---|---|---|---|
| TIT-01 | **200 – Sucesso:** id existente | `GET /api/titulo/5` | 200 | Objeto com `id: 5`, `titulo: "Homem de Ferro"`, `tipo: "filme"`, `genero: "Ação"`, `ano: 2008`, `nota: 9.1`, além de `classificacao`, `qualidade`, `descricao` e `poster` |
| TIT-02 | **404** – id inexistente | `GET /api/titulo/999` | 404 | `{"mensagem": "Não encontrado."}` |
| TIT-03 | **400/404** – id não numérico (a rota só aceita `int`, então o Flask responde 404) | `GET /api/titulo/abc` | 404 | Página de erro 404 padrão do Flask |
| TIT-04 | **500** – falha interna (simulada: `busca_por_id` levanta `RuntimeError`) | `GET /api/titulo/1` | 500 | `{"sucesso": false, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}` — sem detalhes técnicos |

### 5. GET `/api/buscar` (requer login)

| ID | Cenário | Dados enviados (query string) | Status esperado | Resposta esperada |
|---|---|---|---|---|
| BUS-01 | **200 – Sucesso:** sem filtros | *(nenhum)* | 200 | `{"total": 9, "filmes": [...]}` com os 9 títulos do catálogo |
| BUS-02 | **200** – busca por título | `?q=homem` | 200 | `total: 2`; títulos "Homem-Aranha 2" e "Homem de Ferro" |
| BUS-03 | **200** – filtros combinados | `?nota_min=9&ano_min=2010` | 200 | `total: 1`; título "Vingadores: Guerra Infinita" |
| BUS-04 | **200** – filtro por classificação | `?classificacao=L` | 200 | `total: 3`; ids 3, 4 e 9 |
| BUS-05 | **200** – nenhum resultado | `?q=zzzinexistente` | 200 | `{"total": 0, "filmes": []}` |
| BUS-06 | **400 (não aplicável hoje)** – parâmetro numérico inválido | `?ano_min=abc` | 200 | A API **ignora** o valor inválido e usa o padrão: retorna os 9 títulos. Não há validação que resulte em 400 *(ver "Observações")* |
| BUS-07 | Sem login | `?q=x` | 302 | Redireciona para `/` |
| BUS-08 | **500** – falha interna (simulada: `filtra_catalogo` levanta `RuntimeError`) | `?q=x` | 500 | `{"sucesso": false, "mensagem": "Erro interno do servidor. Tente novamente mais tarde."}` — sem detalhes técnicos |

### Como o erro 500 é tratado e testado

- A aplicação possui um *error handler* global (`erro_interno` em `app.py`) que registra o erro completo apenas no **log do servidor** e devolve ao cliente uma mensagem genérica em JSON.
- Nos testes, a falha é provocada de forma controlada com `monkeypatch`, substituindo uma função interna por outra que levanta uma exceção com texto "sensível" (ex.: `unable to open database file /var/secret/boxflix.db`). O teste confere, além do status 500, que o corpo da resposta é exatamente a mensagem genérica e **não contém** `Traceback`, `sqlite3`, `OperationalError`, nem caminhos de arquivo.

### Observações

- `/api/buscar` não responde 400 para parâmetros inválidos; ele usa os valores padrão. Se o grupo preferir, é possível alterar a API para validar e retornar 400, e atualizar o cenário BUS-06.
- `POST /api/cadastro` retorna 200 ao criar o usuário. Se o grupo quiser seguir a convenção REST, basta mudar para 201 e ajustar CAD-01 e o teste.
- Em produção, o servidor **não** deve rodar com `debug=True`, pois o modo debug exibe *tracebacks* no navegador.
