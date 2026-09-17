# Architecture

The repository separates `backend/` and `frontend/`. Django owns domain rules, persistence, authentication, administration, and the versioned REST API. Next.js owns locale-aware presentation and calls typed service modules rather than embedding backend rules in components.

Core Django apps are `accounts`, `catalog`, `inventory`, `pricing`, `carts`, `orders`, `dashboard`, `company`, `website`, `content`, `search`, `rfq`, `common`, and `notifications`. PostgreSQL is the system of record; Redis is configured as the shared cache/broker endpoint for Celery work added in later phases. No demo catalog data is loaded into the client.

Canonical data source: `کالاها_با_دسته_بندی_کامل.xlsx` (sheet «ساختار دسته‌بندی») is the single source of truth for the category tree `(t, g, z)`. `LOCAL_SHOP/local_shop.html` and `MehrAsl_Store_Preview/` are frozen UX/behavior references only and must not be copied into production code or data.

`Category` is an unbounded self-referential tree. Inventory availability is derived as `on_hand_quantity - reserved_quantity`; database constraints prevent invalid quantities. Monetary values use `DecimalField`, and unavailable price/rate data remains null rather than receiving a fallback.

The API is namespaced under `/api/v1/`; `/api/schema/` serves a development OpenAPI schema. The frontend uses `/fa/` by default convention and `/en/`, with `lang` and document direction set at the locale layout boundary.

