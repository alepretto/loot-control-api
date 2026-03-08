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

| Variável             | Descrição                              |
|----------------------|----------------------------------------|
| `DATABASE_URL`       | URL de conexão via PgBouncer (pooled)  |
| `DIRECT_URL`         | URL de conexão direta (para migrations)|
| `SUPABASE_URL`       | URL do projeto Supabase                |
| `SUPABASE_JWT_SECRET`| JWT secret do Supabase                 |
| `ENVIRONMENT`        | `development` ou `production`          |

## Instalação

```bash
uv sync
```

## Desenvolvimento

```bash
uv run uvicorn app.main:app --reload
```

API disponível em `http://localhost:8000`. Documentação em `/docs`.

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

Os testes sobem um container PostgreSQL via **testcontainers** — Docker é necessário.

```bash
uv run pytest -v
```

Nenhuma variável de ambiente é necessária para rodar os testes.

## Jobs agendados

| Job                  | Horário (UTC) | Fonte          | Tabela                     |
|----------------------|---------------|----------------|----------------------------|
| Cotações de moedas   | 21:00         | AwesomeAPI     | `finance.exchange_rates`   |
| Preços de ativos     | 21:30         | CoinGecko / brapi.dev | `finance.asset_prices` |

## Modelo de dados

```
public.users
└── finance.categories  (outcome | income)
    └── finance.tags
        └── finance.transactions

finance.exchange_rates   — cotações diárias BRL/USD/EUR
finance.asset_prices     — preços diários de crypto e ações
```

## CI

Testes rodam automaticamente via **GitHub Actions** em todo push e pull request para `main`.
