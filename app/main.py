from grpc import aio
from .servicers import AuthServicer
from gen.sso_pb2_grpc import add_AuthServicer_to_server
from concurrent.futures import ThreadPoolExecutor
import asyncio


async def serve():
    server = aio.server(ThreadPoolExecutor(max_workers=10))
    add_AuthServicer_to_server(AuthServicer(), server)
    server.add_insecure_port("0.0.0.0:50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    asyncio.run(serve())
