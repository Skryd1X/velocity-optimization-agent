# Databases, APIs and caches

## Database diagnosis

Inspect actual query count per journey, resolved SQL/ORM paths, predicates/order, plans, row counts, selected columns and data volume. Look for N+1, full scans where selective access matters, unnecessary joins, repeated aggregates, deep offset pagination, expensive sorts and overfetching. A scan is not automatically a bug: table size and selectivity matter.

Use the database's supported plan/statistics tools. EXPLAIN ANALYZE actually executes the statement; a rollback does not undo every external effect or avoid production load. Prefer read-only analysis and synthetic/staging datasets. The bundled SQLite adapter uses a read-only connection, an authorizer, row/time bounds and plan capture; other databases require their own tools and permissions.

Add indexes matched to observed predicates/order, then measure read/write costs, lock behavior, space and deployment effects. Do not create every suggested index. Preserve query result ordering, pagination, ownership and transaction semantics. Changes to concurrency, isolation or pooling must not produce races or data corruption.

## Services and API paths

Separate network/queue wait, connection acquisition, computation, data access and serialization. Remove verified serial waterfalls, duplicate work and blocking I/O; use bounded concurrency and cancellation. Apply timeouts/retry budgets and idempotency where needed. Do not parallelize dependent financial/state transitions or enlarge pools beyond backend capacity.

Review payload size/fields, pagination, compression, streaming where appropriate, image/document processing and background work. Keep useful UI states responsive, but do not use a loading placeholder to disguise a still-broken data path. Inspect external provider latency separately; missing live provider access remains a gap.

## Cache correctness

Define ownership-aware keys, freshness, invalidation, cold/warm behavior, eviction and stampede handling. Public cache must not include private user/tenant responses. Prices, balances, stock, authorization and payment state need explicit freshness/consistency semantics. Verify changes, logout/role changes and cross-tenant requests. Route suspected leaks or unsafe shortcuts to Aegis.

## Infrastructure

Inspect actual saturation, worker/thread/event-loop behavior, limits, storage/network latency and deployed configuration when available. Tune the limiting resource based on evidence. CDN/cache and origin changes need representative geography and cache-state measurements. Prepare deployment/rollback consequences; local improvement is not proof of production capacity.
