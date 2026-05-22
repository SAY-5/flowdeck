"""JWT decoding plus a gRPC interceptor that enforces method-level RBAC."""

from __future__ import annotations

from dataclasses import dataclass

import grpc
import jwt

from flowdeck.db import Role


@dataclass(frozen=True)
class Principal:
    user_id: str
    role: Role


# Method full name -> minimum required role.
# RBAC matrix lives here so it can be unit-tested without spinning up a server.
METHOD_ROLES: dict[str, Role] = {
    "/flowdeck.v1.FlowService/ListRecords": Role.VIEWER,
    "/flowdeck.v1.FlowService/GetRecord": Role.VIEWER,
    "/flowdeck.v1.FlowService/GetFacets": Role.VIEWER,
    "/flowdeck.v1.FlowService/ListAuditLog": Role.VIEWER,
    "/flowdeck.v1.FlowService/ActOnRecord": Role.OPERATOR,
}

# Some action types require an even higher role on top of the method floor.
# Checked inside the service implementation.
ACTION_ROLE_OVERRIDES: dict[str, Role] = {
    "ACTION_TYPE_REOPEN": Role.SUPERVISOR,
}


ROLE_ORDER = {Role.VIEWER: 0, Role.OPERATOR: 1, Role.SUPERVISOR: 2}


def role_satisfies(actual: Role, required: Role) -> bool:
    return ROLE_ORDER[actual] >= ROLE_ORDER[required]


def decode_jwt(token: str, secret: str, algorithm: str = "HS256") -> Principal:
    payload = jwt.decode(token, secret, algorithms=[algorithm])
    try:
        return Principal(user_id=payload["sub"], role=Role(payload["role"]))
    except (KeyError, ValueError) as exc:
        raise jwt.InvalidTokenError(f"missing or invalid claim: {exc}") from exc


def issue_jwt(user_id: str, role: Role, secret: str, algorithm: str = "HS256") -> str:
    """Test-only helper for issuing demo tokens."""
    return jwt.encode({"sub": user_id, "role": role.value}, secret, algorithm=algorithm)


class AuthInterceptor(grpc.ServerInterceptor):
    """Decodes the JWT, attaches the Principal, enforces the method RBAC floor."""

    def __init__(self, secret: str, algorithm: str = "HS256") -> None:
        self._secret = secret
        self._algorithm = algorithm

    def intercept_service(self, continuation, handler_call_details):  # type: ignore[override]
        method = handler_call_details.method
        metadata = dict(handler_call_details.invocation_metadata or ())
        auth_header = metadata.get("authorization", "")

        if not auth_header.lower().startswith("bearer "):
            return _abort_handler(grpc.StatusCode.UNAUTHENTICATED, "missing bearer token")

        token = auth_header.split(" ", 1)[1].strip()
        try:
            principal = decode_jwt(token, self._secret, self._algorithm)
        except jwt.InvalidTokenError as exc:
            return _abort_handler(grpc.StatusCode.UNAUTHENTICATED, f"invalid token: {exc}")

        required = METHOD_ROLES.get(method)
        if required is None:
            return _abort_handler(
                grpc.StatusCode.PERMISSION_DENIED, f"method not allowlisted: {method}"
            )
        if not role_satisfies(principal.role, required):
            return _abort_handler(
                grpc.StatusCode.PERMISSION_DENIED,
                f"role {principal.role.value} cannot call {method} (need {required.value})",
            )

        handler = continuation(handler_call_details)
        if handler is None:
            return None
        return _wrap_with_principal(handler, principal)


def _wrap_with_principal(
    handler: grpc.RpcMethodHandler, principal: Principal
) -> grpc.RpcMethodHandler:
    """Re-pack the handler so the service sees `context.principal`."""

    def _attach(behavior):
        def wrapped(request, context):
            context.principal = principal  # type: ignore[attr-defined]
            return behavior(request, context)

        return wrapped

    if handler.unary_unary:
        return grpc.unary_unary_rpc_method_handler(
            _attach(handler.unary_unary),
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
    if handler.unary_stream:
        return grpc.unary_stream_rpc_method_handler(
            _attach(handler.unary_stream),
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
    # Bidi / client streaming not used in FlowService; pass through unchanged.
    return handler


def _abort_handler(code: grpc.StatusCode, detail: str) -> grpc.RpcMethodHandler:
    def behavior(_request, context):
        context.abort(code, detail)

    return grpc.unary_unary_rpc_method_handler(behavior)
