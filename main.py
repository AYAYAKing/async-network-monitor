# Heorhii Yaroshenko

import argparse
import asyncio
import platform
import time

from sqlalchemy import Column, Integer, String, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite+aiosqlite:///network.db"

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

DEFAULT_HOSTS = [
    "127.0.0.1",
    "192.168.56.101",
    "192.168.56.102",
]


class Node(Base):
    """A monitored network node."""

    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    ip_address = Column(String, unique=True, nullable=False)
    status = Column(String, default="unknown")


async def create_tables():
    """Create database tables if they do not exist."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_nodes():
    """Clear the nodes table before a new monitoring run."""

    async with AsyncSessionLocal() as session:
        await session.execute(text("DELETE FROM nodes"))
        await session.commit()


async def add_nodes(hosts):
    """Add hosts to the database with an initial unknown status."""

    async with AsyncSessionLocal() as session:
        nodes = [Node(ip_address=host, status="unknown") for host in hosts]
        session.add_all(nodes)
        await session.commit()

    print(f"[System] Added {len(hosts)} node(s) with status 'unknown'.")


async def get_nodes(label=""):
    """Display nodes currently stored in the database."""

    print(f"\n--- {label} ---")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Node).order_by(Node.id))
        nodes = result.scalars().all()

        for node in nodes:
            print(
                f"ID: {node.id:<3} | "
                f"IP/Host: {node.ip_address:<20} | "
                f"Status: {node.status}"
            )


async def ping_host(host, timeout=1.0):
    """
    Check host reachability with the operating system's ping command.

    Returns:
        tuple[str, float | None]:
            ("active", latency_ms) if reachable,
            ("offline", None) otherwise.
    """

    system = platform.system().lower()

    if system == "windows":
        command = [
            "ping",
            "-n",
            "1",
            "-w",
            str(int(timeout * 1000)),
            host,
        ]
    else:
        command = [
            "ping",
            "-c",
            "1",
            "-W",
            str(max(1, int(timeout))),
            host,
        ]

    start = time.perf_counter()

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            return_code = await asyncio.wait_for(
                process.wait(),
                timeout=timeout + 1,
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return "offline", None

    except FileNotFoundError:
        raise RuntimeError(
            "The system 'ping' command was not found. "
            "Install/enable ping and try again."
        )

    latency_ms = (time.perf_counter() - start) * 1000

    if return_code == 0:
        return "active", latency_ms

    return "offline", None


async def monitor_nodes(timeout=1.0):
    """Check all nodes concurrently and save their reachability status."""

    print("\n[Monitoring] Starting asynchronous reachability checks...")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Node).order_by(Node.id))
        nodes = result.scalars().all()

        checks = [
            ping_host(node.ip_address, timeout=timeout)
            for node in nodes
        ]

        results = await asyncio.gather(*checks)

        for node, (status, latency_ms) in zip(nodes, results):
            node.status = status

            if latency_ms is None:
                print(
                    f"[OFFLINE] {node.ip_address:<20} "
                    f"| no response"
                )
            else:
                print(
                    f"[ACTIVE ] {node.ip_address:<20} "
                    f"| {latency_ms:.1f} ms"
                )

        await session.commit()

    print("[Monitoring] Statuses saved to the database.")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Asynchronous network reachability monitor "
            "with SQLAlchemy and SQLite."
        )
    )

    parser.add_argument(
        "hosts",
        nargs="*",
        help=(
            "IP addresses or hostnames to monitor. "
            "If omitted, home-lab defaults are used."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Ping timeout in seconds (default: 1.0).",
    )

    return parser.parse_args()


async def main():
    args = parse_arguments()
    hosts = args.hosts or DEFAULT_HOSTS

    await create_tables()
    await reset_nodes()
    await add_nodes(hosts)

    await get_nodes("Node list BEFORE monitoring")
    await monitor_nodes(timeout=args.timeout)
    await get_nodes("Node list AFTER monitoring")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
