# FlowDeck

Internal operations console for triaging high-volume operational records. TypeScript + React frontend over a Python gRPC backend, with faceted filtering, optimistic action updates, and role-based access control.

## Stack

- **Backend:** Python 3.12, `grpcio` + `grpcio-tools` + `grpcio-reflection`, SQLAlchemy + Postgres, Pydantic, pytest
- **Frontend:** React 18, TypeScript 5, Vite, TanStack Query, ConnectRPC (`@bufbuild/protobuf` + `@connectrpc/connect-web`)
- **Bridge:** Envoy `grpc_web` filter, so the browser talks gRPC-web while the backend stays pure gRPC
- **Auth:** JWT for the demo (see [`docs/rbac.md`](docs/rbac.md) for the OIDC swap path)
- **Tests:** pytest + `grpcio-testing` + testcontainers (backend), Vitest + React Testing Library (frontend), Playwright (e2e)

## Repo layout

```
flowdeck/
├── apps/
│   ├── web/                  # Vite + React + TS + ConnectRPC client
│   └── api/                  # Python gRPC server + SQLAlchemy
├── proto/                    # flow.proto + buf codegen config
├── infra/envoy/              # gRPC-web bridge config
├── docker-compose.yml        # api + web + postgres + envoy
└── docs/                     # rbac, optimistic-updates, facets, grpc-web-bridge
```

## Quick start

```bash
# Generate proto stubs (requires buf)
make proto

# Run the full stack
docker compose up --build

# Web: http://localhost:5173
# Envoy (gRPC-web): http://localhost:8080
# API (native gRPC): localhost:50051
# Postgres: localhost:5432
```

## Development

```bash
# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest

# Frontend
cd apps/web
npm install
npm run dev
npm run test
```

## Key concepts

- [Optimistic updates](docs/optimistic-updates.md) — how `ActOnRecord` mutates the cache before the server replies, and rolls back on failure
- [Faceted filtering](docs/facets.md) — server returns `FacetCounts` next to every page of records
- [RBAC](docs/rbac.md) — viewer / operator / supervisor, enforced by a gRPC interceptor
- [gRPC-web bridge](docs/grpc-web-bridge.md) — Envoy config + ConnectRPC transport choice

## License

MIT
