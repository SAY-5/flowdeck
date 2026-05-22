"""Unit tests for JWT decoding and the AuthInterceptor."""

from __future__ import annotations

import grpc
import jwt
import pytest

from flowdeck.auth import (
    METHOD_ROLES,
    AuthInterceptor,
    Principal,
    decode_jwt,
    issue_jwt,
    role_satisfies,
)
from flowdeck.db import Role

SECRET = "test-secret-with-at-least-thirty-two-bytes-please"


class _CallDetails:
    def __init__(self, method: str, metadata: tuple[tuple[str, str], ...] = ()):
        self.method = method
        self.invocation_metadata = metadata


def _continuation_returns_handler(handler):
    def _c(_details):
        return handler

    return _c


def _passthrough_handler():
    return grpc.unary_unary_rpc_method_handler(
        lambda req, ctx: req,
        request_deserializer=None,
        response_serializer=None,
    )


def test_role_satisfies_order():
    assert role_satisfies(Role.SUPERVISOR, Role.VIEWER)
    assert role_satisfies(Role.OPERATOR, Role.OPERATOR)
    assert not role_satisfies(Role.VIEWER, Role.OPERATOR)


def test_jwt_roundtrip():
    token = issue_jwt("u-1", Role.OPERATOR, SECRET)
    principal = decode_jwt(token, SECRET)
    assert principal == Principal(user_id="u-1", role=Role.OPERATOR)


def test_jwt_missing_role_raises():
    bad = jwt.encode({"sub": "u-1"}, SECRET, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_jwt(bad, SECRET)


def test_interceptor_rejects_missing_token():
    interceptor = AuthInterceptor(SECRET)
    handler = interceptor.intercept_service(
        _continuation_returns_handler(_passthrough_handler()),
        _CallDetails("/flowdeck.v1.FlowService/ListRecords"),
    )

    class _Ctx:
        def __init__(self):
            self.code = None
            self.details = None

        def abort(self, code, details):
            self.code = code
            self.details = details

    ctx = _Ctx()
    handler.unary_unary("req", ctx)
    assert ctx.code == grpc.StatusCode.UNAUTHENTICATED


def test_interceptor_rejects_lower_role():
    interceptor = AuthInterceptor(SECRET)
    token = issue_jwt("u-viewer", Role.VIEWER, SECRET)
    handler = interceptor.intercept_service(
        _continuation_returns_handler(_passthrough_handler()),
        _CallDetails(
            "/flowdeck.v1.FlowService/ActOnRecord",
            metadata=(("authorization", f"Bearer {token}"),),
        ),
    )

    class _Ctx:
        def __init__(self):
            self.code = None

        def abort(self, code, details):
            self.code = code

    ctx = _Ctx()
    handler.unary_unary("req", ctx)
    assert ctx.code == grpc.StatusCode.PERMISSION_DENIED


def test_interceptor_accepts_sufficient_role_and_attaches_principal():
    interceptor = AuthInterceptor(SECRET)
    token = issue_jwt("u-op", Role.OPERATOR, SECRET)
    seen = {}

    def behavior(req, ctx):
        seen["principal"] = ctx.principal
        return req

    handler = grpc.unary_unary_rpc_method_handler(
        behavior, request_deserializer=None, response_serializer=None
    )

    wrapped = interceptor.intercept_service(
        _continuation_returns_handler(handler),
        _CallDetails(
            "/flowdeck.v1.FlowService/ActOnRecord",
            metadata=(("authorization", f"Bearer {token}"),),
        ),
    )

    class _Ctx:
        pass

    out = wrapped.unary_unary("req", _Ctx())
    assert out == "req"
    assert seen["principal"].user_id == "u-op"
    assert seen["principal"].role == Role.OPERATOR


def test_method_roles_cover_all_flow_methods():
    expected = {
        "/flowdeck.v1.FlowService/ListRecords",
        "/flowdeck.v1.FlowService/GetRecord",
        "/flowdeck.v1.FlowService/ActOnRecord",
        "/flowdeck.v1.FlowService/GetFacets",
        "/flowdeck.v1.FlowService/ListAuditLog",
    }
    assert expected.issubset(set(METHOD_ROLES))
