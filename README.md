# Loot Control API

Backend do **Loot Control** — sistema de acompanhamento de gastos, receitas e investimentos.

## Stack

- **Python 3.12** gerenciado com [uv](https://docs.astral.sh/uv/)
- **FastAPI** — framework HTTP assíncrono
- **SQLModel + SQLAlchemy** — ORM async com suporte a Pydantic
- **asyncpg** — driver PostgreSQL assíncrono
- **Alembic** — migrations assíncronas
- **APScheduler** — jobs agendados para cotações e preços de ativos
- **Supabase** — banco de dados PostgreSQL + autenticação JWT

## Arquitetura

```
app/
├── core/           # Configurações, banco de dados, segurança JWT
├── models/         # Modelos SQLModel (tabelas)
│   └── finance/
├── schemas/        # Schemas Pydantic (request/response)
│   └── finance/
├── repositories/   # Acesso ao banco de dados (queries SQL)
│   └── finance/
├── services/       # Regras de negócio (orquestra repositórios)
│   └── finance/
├── routers/        # Endpoints HTTP
│   └── finance/
└── jobs/           # Workers agendados (cotações, preços)
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

| Variável              | Descrição                               |
|-----------------------|-----------------------------------------|
| `DATABASE_URL`        | URL de conexão via PgBouncer (pooled)   |
| `DIRECT_URL`          | URL de conexão direta (para migrations) |
| `SUPABASE_URL`        | URL do projeto Supabase                 |
| `SUPABASE_JWT_SECRET` | JWT secret do Supabase                  |
| `ENVIRONMENT`         | `development` ou `production`           |

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

> As migrations usam a `DIRECT_URL` (conexão direta, sem PgBouncer) para evitar problemas com prepared statements.

## Testes

Os testes sobem um container PostgreSQL via **testcontainers** — Docker é necessário, nenhuma variável de ambiente é necessária.

```bash
uv run pytest -v
```

### Cobertura de testes

| Arquivo de teste            | O que cobre                                                       |
|-----------------------------|-------------------------------------------------------------------|
| `test_tag_families.py`      | CRUD completo de famílias, ON DELETE SET NULL em categorias       |
| `test_categories.py`        | CRUD, criação com/sem família, reatribuição de família via PATCH  |
| `test_tags.py`              | CRUD, prevenção de duplicatas (409), mesmo nome em cats diferentes|
| `test_transactions.py`      | CRUD, transações de investimento, paginação, filtros              |

## Endpoints

| Método   | Rota                             | Descrição                      |
|----------|----------------------------------|--------------------------------|
| `GET`    | `/finance/tag-families/`         | Listar famílias                |
| `POST`   | `/finance/tag-families/`         | Criar família                  |
| `GET`    | `/finance/tag-families/{id}`     | Buscar família                 |
| `PATCH`  | `/finance/tag-families/{id}`     | Atualizar família              |
| `DELETE` | `/finance/tag-families/{id}`     | Excluir família (nullifica FKs)|
| `GET`    | `/finance/categories/`           | Listar categorias              |
| `POST`   | `/finance/categories/`           | Criar categoria                |
| `PATCH`  | `/finance/categories/{id}`       | Atualizar categoria            |
| `DELETE` | `/finance/categories/{id}`       | Excluir categoria              |
| `GET`    | `/finance/tags/`                 | Listar tags                    |
| `POST`   | `/finance/tags/`                 | Criar tag (409 se duplicada)   |
| `PATCH`  | `/finance/tags/{id}`             | Atualizar tag                  |
| `DELETE` | `/finance/tags/{id}`             | Excluir tag                    |
| `GET`    | `/finance/transactions/`         | Listar transações (paginado)   |
| `POST`   | `/finance/transactions/`         | Criar transação                |
| `PATCH`  | `/finance/transactions/{id}`     | Atualizar transação            |
| `DELETE` | `/finance/transactions/{id}`     | Excluir transação              |

Todos os endpoints requerem autenticação via `Bearer <supabase_jwt>`.

## Jobs agendados

| Job                | Horário (UTC) | Fonte                 | Tabela                      |
|--------------------|---------------|-----------------------|-----------------------------|
| Cotações de moedas | 21:00         | AwesomeAPI            | `finance.exchange_rates`    |
| Preços de ativos   | 21:30         | CoinGecko / brapi.dev | `finance.asset_prices`      |

## Modelo de dados

```
public.users
└── finance.tag_families          — agrupamento de categorias (ex: Gastos de Casa)
    └── finance.categories        — tipo: outcome | income
        └── finance.tags          — is_active: bool
            │                     — unique: (user_id, category_id, name)
            └── finance.transactions
                  date_transaction  TIMESTAMPTZ
                  value             float
                  currency          BRL | USD | EUR
                  quantity          float nullable   — investimentos
                  symbol            varchar nullable  — ex: BTC, PETR4
                  index_rate        float nullable
                  index             varchar nullable

finance.exchange_rates   — cotação diária em BRL (BRL/USD/EUR)
finance.asset_prices     — preço diário por símbolo
```

**Regras importantes:**
- `family_id` em `categories` é nullable — categorias sem família são válidas
- Excluir uma família define `family_id = NULL` nas categorias vinculadas (ON DELETE SET NULL)
- Tags com mesmo nome na mesma categoria retornam 409

## CI

Testes rodam automaticamente via **GitHub Actions** em todo push e pull request para `main`.
