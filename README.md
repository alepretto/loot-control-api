# Loot Control API

Backend do **Loot Control** — sistema de acompanhamento de gastos, receitas e investimentos.

## Stack

- **Python 3.12** gerenciado com [uv](https://docs.astral.sh/uv/)
- **FastAPI** — framework HTTP assíncrono
- **SQLModel + SQLAlchemy** — ORM async com suporte a Pydantic
- **asyncpg** — driver PostgreSQL assíncrono
- **Alembic** — migrations assíncronas
- **APScheduler** — jobs agendados para cotações e preços de ativos
- **Supabase** — banco de dados PostgreSQL + autenticação JWT (python-jose)

## Arquitetura

```
app/
├── core/           # Configurações, banco de dados, segurança JWT
├── models/         # Modelos SQLModel (tabelas)
│   └── finance/
├── schemas/        # Schemas Pydantic (request/response)
│   └── finance/
├── repositories/   # Acesso ao banco de dados (queries SQL puras)
│   └── finance/
├── services/       # Regras de negócio (orquestra repositórios)
│   └── finance/
├── routers/        # Endpoints HTTP
│   └── finance/
└── jobs/           # Workers agendados (cotações, preços de ativos)
```

Padrão: **Router → Service → Repository** — cada camada tem responsabilidade única.

## Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) instalado
- Docker (para rodar os testes)
- Conta no [Supabase](https://supabase.com/)

## Configuração

Copie `.env.example` para `.env` e preencha as variáveis:

```bash
cp .env.example .env
```

| Variável               | Descrição                                                      |
|------------------------|----------------------------------------------------------------|
| `DATABASE_URL`         | URL de conexão via PgBouncer (pooled)                          |
| `DIRECT_URL`           | URL de conexão direta (para migrations)                        |
| `SUPABASE_URL`         | URL do projeto Supabase                                        |
| `SUPABASE_JWT_SECRET`  | JWT secret do Supabase                                         |
| `ENVIRONMENT`          | `development` ou `production`                                  |
| `ALLOWED_ORIGINS`      | Origens CORS permitidas (separadas por vírgula)                |
| `COINGECKO_API_KEY`    | Chave Demo gratuita do CoinGecko — melhora rate limits         |

> A `COINGECKO_API_KEY` é opcional mas recomendada. Cadastre em [coingecko.com/api](https://www.coingecko.com/en/api) (plano Demo é gratuito).

## Instalação

```bash
uv sync
```

## Desenvolvimento

```bash
uv run uvicorn app.main:app --reload
```

API disponível em `http://localhost:8000`. Documentação interativa em `/docs`.

## Migrations

```bash
# Gerar migration após alterar models
uv run alembic revision --autogenerate -m "descrição"

# Aplicar migrations pendentes
uv run alembic upgrade head

# Reverter última migration
uv run alembic downgrade -1
```

> As migrations usam a `DIRECT_URL` (conexão direta, sem PgBouncer) para evitar problemas com prepared statements. Migrations novas devem ser idempotentes — checar existência antes de criar via `sa.inspect`.

## Testes

Os testes sobem um container PostgreSQL via **testcontainers** — Docker é necessário, nenhuma variável de ambiente precisa ser configurada.

```bash
uv run pytest -v
```

### Cobertura de testes

| Arquivo de teste        | O que cobre                                                        |
|-------------------------|--------------------------------------------------------------------|
| `test_tag_families.py`  | CRUD completo de famílias, cascade delete em categorias/tags       |
| `test_categories.py`    | CRUD, criação com/sem família, reatribuição de família via PATCH   |
| `test_tags.py`          | CRUD, prevenção de duplicatas (409), mesmo nome em cats diferentes |
| `test_transactions.py`  | CRUD, transações de investimento, paginação, filtros               |

## Endpoints

### Hierarquia financeira

| Método  | Rota                             | Descrição                           |
|---------|----------------------------------|-------------------------------------|
| `GET`   | `/finance/tag-families/`         | Listar famílias                     |
| `POST`  | `/finance/tag-families/`         | Criar família                       |
| `GET`   | `/finance/tag-families/{id}`     | Buscar família                      |
| `PATCH` | `/finance/tag-families/{id}`     | Atualizar família                   |
| `DELETE`| `/finance/tag-families/{id}`     | Excluir família (cascade)           |
| `GET`   | `/finance/categories/`           | Listar categorias                   |
| `POST`  | `/finance/categories/`           | Criar categoria                     |
| `PATCH` | `/finance/categories/{id}`       | Atualizar categoria                 |
| `DELETE`| `/finance/categories/{id}`       | Excluir categoria (cascade)         |
| `GET`   | `/finance/tags/`                 | Listar tags                         |
| `POST`  | `/finance/tags/`                 | Criar tag (409 se duplicada)        |
| `PATCH` | `/finance/tags/{id}`             | Atualizar tag                       |
| `DELETE`| `/finance/tags/{id}`             | Excluir tag (cascade)               |
| `GET`   | `/finance/transactions/`         | Listar transações (paginado)        |
| `POST`  | `/finance/transactions/`         | Criar transação                     |
| `PATCH` | `/finance/transactions/{id}`     | Atualizar transação                 |
| `DELETE`| `/finance/transactions/{id}`     | Excluir transação                   |

### Market data

| Método | Rota                                           | Descrição                          |
|--------|------------------------------------------------|------------------------------------|
| `GET`  | `/finance/market-data/exchange-rates/latest`   | Última cotação USD e EUR           |
| `GET`  | `/finance/market-data/exchange-rates/history`  | Histórico de cotações              |
| `GET`  | `/finance/market-data/asset-prices/latest`     | Último preço por símbolo           |
| `GET`  | `/finance/market-data/asset-prices/history`    | Histórico de preços por símbolo    |
| `GET`  | `/finance/market-data/cdi/history`             | Taxas CDI diárias (BCB)            |

Todos os endpoints requerem autenticação via `Bearer <supabase_jwt>`.

## Jobs agendados

Rodam **3x/dia** no horário de Brasília (`America/Sao_Paulo`). A cada execução os registros do dia são substituídos pelos valores mais recentes.

| Job                | Horários (BRT)    | Fonte                              | Tabela                     |
|--------------------|-------------------|------------------------------------|----------------------------|
| Cotações de moedas | 09:00, 15:00, 18:00 | AwesomeAPI                       | `finance.exchange_rates`   |
| Preços de ativos   | 09:30, 15:30, 18:30 | CoinGecko / brapi.dev / Yahoo Finance | `finance.asset_prices` |

### Classificação automática de ativos

| Tipo         | Critério                                  | Fonte           |
|--------------|-------------------------------------------|-----------------|
| Crypto       | Símbolo no mapeamento `CRYPTO_ID_MAP`     | CoinGecko       |
| Ação BR      | Símbolo termina em dígito (ex: `PETR4`)   | brapi.dev       |
| Ação US      | Demais símbolos sem `index`               | Yahoo Finance   |
| Renda Fixa   | Transação com campo `index` preenchido    | — (cálculo local) |

## Modelo de dados

```
public.users
└── finance.tag_families              — nível 1: família (ex: Moradia, Lazer)
    │   unique: (user_id, name)
    └── finance.categories            — nível 2: categoria (ex: Alimentação)
        │   family_id FK ON DELETE CASCADE
        └── finance.tags              — nível 3: tag (ex: Restaurante)
            │   type: outcome | income   ← tipo está aqui, não na categoria
            │   is_active: bool
            │   unique: (user_id, category_id, name)
            │   category_id FK ON DELETE CASCADE
            └── finance.transactions
                  tag_id FK ON DELETE CASCADE
                  date_transaction  TIMESTAMPTZ
                  value             float
                  currency          BRL | USD | EUR
                  quantity          float nullable   — investimentos
                  symbol            varchar nullable  — ex: BTC, PETR4
                  index_rate        float nullable    — ex: 12.5
                  index             varchar nullable  — ex: CDI, IPCA

finance.exchange_rates   — cotação diária em BRL (USD, EUR)
finance.asset_prices     — preço diário por símbolo (crypto em USD, ações BR em BRL)
```

**Regras importantes:**
- **Tipo está na Tag** — `outcome`/`income` é campo de `Tag`, não de `Category`. Uma mesma categoria pode ter tags de tipos diferentes.
- **Cascade deletes** — excluir Família apaga Categorias → Tags → Transações em cascata.
- Tags com mesmo nome na mesma categoria retornam HTTP 409.
- Famílias com mesmo nome para o mesmo usuário retornam HTTP 409.

## CI

Testes rodam automaticamente via **GitHub Actions** em todo push e pull request para `main`.
