"""gRPC server entrypoint."""

from __future__ import annotations

import logging
import signal
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from flowdeck.auth import AuthInterceptor
from flowdeck.config import get_settings
from flowdeck.db import create_all, make_engine, make_session_factory
from flowdeck.gen import flow_pb2 as pb
from flowdeck.gen import flow_pb2_grpc as pb_grpc
from flowdeck.service import FlowServicer

log = logging.getLogger(__name__)


def build_server(settings=None) -> grpc.Server:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    create_all(engine)
    session_factory = make_session_factory(engine)

    interceptors = [AuthInterceptor(secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16), interceptors=interceptors)
    pb_grpc.add_FlowServiceServicer_to_server(
        FlowServicer(
            session_factory,
            page_size_default=settings.default_page_size,
            page_size_max=settings.max_page_size,
        ),
        server,
    )

    if settings.enable_reflection:
        service_names = (
            pb.DESCRIPTOR.services_by_name["FlowService"].full_name,
            reflection.SERVICE_NAME,
        )
        reflection.enable_server_reflection(service_names, server)

    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    server = build_server(settings)
    log.info("flowdeck gRPC server listening on %s:%s", settings.grpc_host, settings.grpc_port)
    server.start()

    def _stop(*_args):
        log.info("stopping server")
        server.stop(grace=5).wait()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    server.wait_for_termination()


if __name__ == "__main__":
    main()
