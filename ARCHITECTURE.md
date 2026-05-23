# Architecture

## Shape

```
   browser                  Envoy (or built-in Connect)         Python gRPC
   ----------               -----------------------------       ---------------
   React + TS    --HTTP-->  gRPC-web bridge   --gRPC-->         FlowService
   ConnectRPC               (also serves /api)                    + RBAC intercep
                                                                  + SQLAlchemy
                                                                       |
                                                                       v
                                                                  Postgres
```

## Why ConnectRPC

The browser cannot speak gRPC natively. Three transport options exist:
gRPC-web with an Envoy proxy, Connect protocol (which is gRPC-compatible
on the wire but JSON-friendly on the client), or REST translation. We
picked **Connect** because:

- One protocol covers both browser and server-to-server calls.
- The client library `@connectrpc/connect-web` is small and works with
  TanStack Query without ceremony.
- The Python server runs on `grpcio` (the standard gRPC stack). A
  ConnectRPC server library is not strictly required — clients can speak
  the gRPC-web subset of Connect to the Python gRPC server directly via
  Envoy.

We document Envoy as the canonical bridge in `infra/envoy/`.

## Optimistic updates

When an operator marks a record as `resolved` the UI updates immediately
via TanStack Query's `useMutation` with `onMutate`:

1. `onMutate` snapshots the current cache and applies the optimistic
   write to the cached page.
2. `mutationFn` calls the gRPC `ActOnRecord` method.
3. On success the cache is invalidated and refetched (or the server's
   final value is merged).
4. On error the snapshot is restored and a toast is shown.

The e2e test exercises the rollback path explicitly: the mock server is
configured to NACK; the test asserts the UI shows the action, then
reverts, then surfaces the toast.

## Faceted filtering

`ListRecords(filter) -> { records[], facets, next_cursor }`. The
response carries facet counts under the current filter so the UI does
not have to make a second round-trip. The cursor encodes `(sort_key,
id)` and is stable under inserts.

## RBAC

Three roles: `viewer`, `operator`, `supervisor`. A server-side gRPC
interceptor reads the JWT claim and checks against the method's
`required_role` annotation (declared in the proto via a custom option).
A `viewer` calling a write method gets `PERMISSION_DENIED` at the
interceptor before the handler runs.

## What is deliberately not here

- Real OIDC (local JWT only; swap path is documented)
- Live event streaming (`SAY-5/live-events-spa` is that study)
- Multi-tenant (single team)
- Approval workflows beyond accept/reject/needs-info
- Mobile-native client
