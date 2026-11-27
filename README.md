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

---

## Pipeline de CI (GitHub Actions → Docker Hub)

Arquivo: `.github/workflows/argoPipeline.yaml`. A cada push em `develop`/`main`:

1. **test** – instala dependências e roda `pytest -v`.
2. **docker** – só se os testes passarem: faz login no Docker Hub, builda a imagem e publica `usuario/boxflix:latest` e `usuario/boxflix:<sha do commit>`.

Configure em *Settings → Secrets and variables → Actions* do repositório:

| Secret | Valor |
|---|---|
| `DOCKERHUB_USERNAME` | seu usuário do Docker Hub |
| `DOCKERHUB_TOKEN` | token de acesso criado em Docker Hub → Account Settings → Security |

Rodar a imagem publicada: `docker run -p 5000:5000 SEU_USUARIO/boxflix:latest`

---

## Observabilidade

### O que é observabilidade e por que ela importa

Observabilidade é a capacidade de compreender o **estado interno** de um sistema a partir dos dados que ele expõe — sem precisar adivinhar o que está acontecendo ou acessar o servidor manualmente para investigar.

Enquanto o **monitoramento tradicional** é reativo (alerta quando algo já quebrou), a observabilidade é **proativa**: ela permite antecipar problemas, entender comportamentos inesperados e responder perguntas que nem foram previstas no momento da instrumentação.

Em uma aplicação como a BoxFlix — com autenticação de usuários, catálogo de conteúdo e busca avançada — a observabilidade é essencial para garantir que a experiência dos usuários se mantenha fluida e que falhas sejam identificadas antes de impactarem um grande número de pessoas.

### Os três pilares: métricas, logs e traces

A observabilidade se apoia em três tipos de dados complementares, conhecidos como os **três pilares da observabilidade**:

#### 1. Métricas

Métricas são **valores numéricos agregados ao longo do tempo** que representam o comportamento do sistema em alto nível. Elas respondem à pergunta: *"O sistema está saudável agora?"*

Exemplos de métricas relevantes para a BoxFlix:

| Métrica | Tipo | O que mede | Por que importa |
|---|---|---|---|
| `http_requests_total` | Contador | Total de requisições recebidas, por rota e status HTTP | Detectar picos de tráfego ou aumento repentino de erros |
| `http_request_duration_seconds` | Histograma | Tempo de resposta de cada endpoint | Identificar lentidão em rotas como `/api/buscar` |
| `login_failures_total` | Contador | Quantidade de tentativas de login que falharam (401) | Detectar possíveis ataques de força bruta |
| `cadastro_sucesso_total` | Contador | Novos cadastros realizados com sucesso | Acompanhar o crescimento da base de usuários |
| `db_errors_total` | Contador | Erros ao acessar o banco SQLite | Antecipar problemas de infraestrutura antes de uma queda total |

**Exemplo prático:** se a métrica `http_request_duration_seconds` do endpoint `/api/buscar` começa a subir gradualmente ao longo de semanas, isso pode indicar que o catálogo está crescendo e a busca sequencial está ficando lenta — sinalizando a necessidade de otimização antes que os usuários percebam.

#### 2. Logs

Logs são **registros textuais de eventos** que acontecem durante a execução da aplicação. Eles respondem à pergunta: *"O que aconteceu em determinado momento?"*

A BoxFlix já possui um logging básico no error handler (linha 270 do `app.py`):

```python
app.logger.error("Erro interno em %s %s", request.method, request.path, exc_info=erro)
```

Para uma observabilidade mais completa, os logs seriam expandidos com diferentes níveis de severidade:

| Nível | Quando usar | Exemplo na BoxFlix |
|---|---|---|
| `DEBUG` | Detalhes úteis em desenvolvimento | `"Busca avançada: q='homem', ano_min=2010 → 2 resultados em 3ms"` |
| `INFO` | Eventos normais relevantes | `"Usuário id=42 (maria@email.com) logou com sucesso"` |
| `WARNING` | Situações suspeitas que merecem atenção | `"3 tentativas de login falhas para naoexiste@email.com em 1 minuto"` |
| `ERROR` | Falhas que impactam uma requisição | `"Erro 500 em POST /api/cadastro: sqlite3.OperationalError"` |
| `CRITICAL` | Falhas que comprometem todo o sistema | `"Banco de dados inacessível após 5 tentativas de reconexão"` |

**Logs estruturados (JSON)** facilitam a análise automatizada. Em vez de texto livre, cada entrada teria campos padronizados:

```json
{
  "timestamp": "2026-11-28T14:30:00Z",
  "level": "WARNING",
  "event": "login_falho",
  "email": "atacante@email.com",
  "ip": "192.168.1.100",
  "motivo": "senha_incorreta",
  "tentativas_recentes": 5,
  "rota": "POST /api/login"
}
```

Isso permitiria, por exemplo, buscar todos os logins falhos de um mesmo IP nas últimas 24 horas — algo difícil com logs em texto simples.

#### 3. Traces (rastreamento distribuído)

Traces acompanham o **caminho completo de uma requisição** através de todos os componentes do sistema, dividindo-a em **spans** (etapas). Eles respondem à pergunta: *"Onde exatamente a requisição ficou lenta ou falhou?"*

Exemplo de trace para uma busca na BoxFlix:

```
Trace ID: abc-123-def
│
├─ Span 1: Flask recebe GET /api/buscar?q=homem         [2ms]
│   ├─ Atributos: método=GET, rota=/api/buscar, usuario_id=42
│
├─ Span 2: Validar e extrair parâmetros da query string  [1ms]
│   ├─ Atributos: q="homem", ano_min=1980, ano_max=2026
│
├─ Span 3: filtra_catalogo() — percorrer e filtrar itens  [4ms]
│   ├─ Atributos: itens_avaliados=9, resultados=2
│
├─ Span 4: Serializar resposta JSON                       [1ms]
│
└─ Total: 8ms | Status: OK
```

Se a BoxFlix evoluísse para uma arquitetura com microsserviços (por exemplo, um serviço de autenticação separado do serviço de catálogo), os traces seriam ainda mais valiosos para rastrear uma requisição que atravessa múltiplos serviços.

### Telemetria: identificação e antecipação de falhas

**Telemetria** é o processo de coletar, transmitir e analisar automaticamente os dados de observabilidade (métricas, logs e traces). Na BoxFlix, a telemetria contribuiria para:

**Identificação rápida de falhas:**
- Se a taxa de respostas 500 no `/api/login` subir de 0% para 10% em 5 minutos, um alerta automático notificaria a equipe imediatamente, sem esperar que os usuários reclamem.
- Cruzando logs e traces, seria possível descobrir que o erro ocorre especificamente quando o banco de dados atinge um limite de conexões simultâneas.

**Antecipação de problemas:**
- Se o tempo médio de resposta do `/api/buscar` cresce 50ms por semana, a telemetria permite projetar que em 2 meses a experiência ficará inaceitável — dando tempo para otimizar a busca.
- Se o número de tentativas de login falhas para um mesmo IP excede um limiar, o sistema pode bloquear o IP automaticamente antes que um ataque de força bruta tenha sucesso.

**Melhoria contínua:**
- Dados de telemetria alimentam decisões de evolução do software: quais funcionalidades são mais usadas (priorizar melhorias), quais rotas são mais lentas (priorizar otimizações), quais erros são mais frequentes (priorizar correções).
- Comparar métricas antes e depois de um deploy permite avaliar objetivamente se uma mudança melhorou ou piorou a aplicação.

### Ferramentas de telemetria e monitoramento

#### Prometheus

**O que é:** banco de dados de séries temporais que coleta e armazena métricas, usando um modelo de *pull* (ele consulta a aplicação periodicamente em um endpoint `/metrics`).

**Como seria usado na BoxFlix:**
- A biblioteca `prometheus_flask_instrumentator` exporia automaticamente métricas HTTP (contagem de requisições, tempo de resposta, tamanho da resposta) no endpoint `/metrics`.
- Métricas de negócio personalizadas (logins falhos, cadastros) seriam registradas manualmente com contadores do Prometheus.
- Regras de alerta seriam configuradas: por exemplo, `rate(http_requests_total{status="500"}[5m]) > 0.05` dispara um alerta se mais de 5% das requisições resultam em erro 500.

```python
# Exemplo conceitual de instrumentação com Prometheus
from prometheus_flask_instrumentator import Instrumentator
from prometheus_client import Counter

login_falhos = Counter('login_failures_total', 'Tentativas de login que falharam')

Instrumentator().instrument(app).expose(app)  # expõe /metrics automaticamente

# No endpoint de login, ao falhar:
login_falhos.inc()
```

#### Grafana

**O que é:** plataforma de visualização que cria dashboards interativos a partir de diversas fontes de dados (Prometheus, Elasticsearch, etc.).

**Como seria usado na BoxFlix:**
- **Dashboard de saúde geral:** gráficos de requisições por segundo, taxa de erros, tempo de resposta (p50, p95, p99).
- **Dashboard de autenticação:** logins bem-sucedidos vs. falhos por hora, novos cadastros por dia, IPs com mais tentativas falhas.
- **Dashboard de busca:** termos mais buscados, tempo de resposta da busca, proporção de buscas sem resultado.
- Alertas visuais: painéis que mudam de verde para vermelho quando uma métrica ultrapassa o limiar definido.

#### Elastic Stack (ELK)

**O que é:** conjunto de três ferramentas — **Elasticsearch** (indexação e busca), **Logstash** (coleta e processamento de logs) e **Kibana** (visualização) — para centralizar e analisar logs.

**Como seria usado na BoxFlix:**
- **Logstash** coletaria os logs JSON estruturados da aplicação Flask e os enviaria ao Elasticsearch.
- **Elasticsearch** indexaria os logs, permitindo buscas como: "todos os erros 500 das últimas 24h na rota /api/cadastro" ou "todos os warnings de login falho do IP 192.168.1.100".
- **Kibana** exibiria dashboards de logs: volume de logs por nível (INFO, WARNING, ERROR), linha do tempo de erros, e filtros por rota, usuário ou IP.

Essa centralização seria especialmente útil se a BoxFlix rodasse em múltiplos containers Docker — sem o ELK, seria necessário acessar cada container individualmente para ver os logs.

#### OpenTelemetry

**O que é:** framework open-source e vendor-neutral que padroniza a coleta dos três pilares (métricas, logs e traces) em uma única API, permitindo enviar dados para qualquer backend (Prometheus, Jaeger, Elastic, Grafana Cloud, etc.).

**Como seria usado na BoxFlix:**
- A biblioteca `opentelemetry-instrumentation-flask` geraria automaticamente spans para cada requisição HTTP, sem alterar o código da aplicação.
- Spans personalizados poderiam ser adicionados para funções internas como `filtra_catalogo()` e `validar_cadastro()`.
- Os dados seriam exportados via OTLP (OpenTelemetry Protocol) para um coletor central, que redistribuiria para Prometheus (métricas), Jaeger (traces) e Elasticsearch (logs).

```python
# Exemplo conceitual de instrumentação com OpenTelemetry
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry import trace

FlaskInstrumentor().instrument_app(app)
tracer = trace.get_tracer("boxflix")

# Dentro de uma função, criar um span personalizado:
def filtra_catalogo(termo, ano_min, ano_max, classificacoes, nota_min, qualidades):
    with tracer.start_as_current_span("filtra_catalogo") as span:
        span.set_attribute("busca.termo", termo)
        span.set_attribute("busca.ano_min", ano_min)
        # ... lógica de filtro ...
        span.set_attribute("busca.resultados", len(resultado))
        return resultado
```

### Arquitetura de observabilidade proposta para a BoxFlix

O diagrama abaixo ilustra como as ferramentas de observabilidade se integrariam à arquitetura da BoxFlix:

```
┌──────────────────────────────────────────────────────────────────┐
│                        BoxFlix (Flask)                           │
│                                                                  │
│  ┌────────────┐   ┌────────────┐   ┌────────────────────────┐   │
│  │  Métricas  │   │    Logs    │   │        Traces          │   │
│  │ Prometheus │   │  JSON p/   │   │   OpenTelemetry SDK    │   │
│  │  Client    │   │  stdout    │   │   (Flask Instrumentor) │   │
│  └─────┬──────┘   └─────┬──────┘   └───────────┬────────────┘   │
│        │                │                       │                │
└────────┼────────────────┼───────────────────────┼────────────────┘
         │                │                       │
         ▼                ▼                       ▼
   ┌───────────┐   ┌───────────┐          ┌─────────────┐
   │Prometheus │   │ Logstash  │          │ OTel        │
   │  Server   │   │           │          │ Collector   │
   └─────┬─────┘   └─────┬─────┘         └──────┬──────┘
         │                │                      │
         ▼                ▼                      ▼
   ┌───────────┐   ┌──────────────┐       ┌───────────┐
   │  Grafana  │   │Elasticsearch │       │  Jaeger   │
   │(dashboards│   │   + Kibana   │       │ (traces)  │
   │ e alertas)│   │   (logs)     │       │           │
   └───────────┘   └──────────────┘       └───────────┘
```

**Fluxo:**
1. A aplicação Flask, instrumentada com OpenTelemetry e Prometheus Client, gera métricas, logs estruturados e traces durante cada requisição.
2. O Prometheus Server coleta as métricas periodicamente consultando o endpoint `/metrics`.
3. Os logs são coletados pelo Logstash e enviados ao Elasticsearch para indexação.
4. Os traces são enviados via OTLP para o OpenTelemetry Collector, que os encaminha ao Jaeger.
5. O Grafana conecta-se ao Prometheus para exibir dashboards de métricas e configurar alertas.
6. O Kibana conecta-se ao Elasticsearch para visualização e busca de logs.