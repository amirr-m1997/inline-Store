# Architecture

The repository separates `backend/` and `frontend/`. Django owns domain rules, persistence, authentication, administration, and the versioned REST API. Next.js owns locale-aware presentation and calls typed service modules rather than embedding backend rules in components.

Core Django apps are `accounts`, `catalog`, `inventory`, `pricing`, `carts`, `dashboard`, and `common`. PostgreSQL is the system of record; Redis is configured as the shared cache/broker endpoint for Celery work added in later phases. No demo catalog data is loaded into the client.

`Category` is an unbounded self-referential tree. Inventory availability is derived as `on_hand_quantity - reserved_quantity`; database constraints prevent invalid quantities. Monetary values use `DecimalField`, and unavailable price/rate data remains null rather than receiving a fallback.

The API is namespaced under `/api/v1/`; `/api/schema/` serves a development OpenAPI schema. The frontend uses `/fa/` by default convention and `/en/`, with `lang` and document direction set at the locale layout boundary.

