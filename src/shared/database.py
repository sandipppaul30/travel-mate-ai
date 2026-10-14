
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore

from .config import get_database_url

async def init_database():
    url = get_database_url()

    global checkpoint_conn, memory_conn
    checkpoint_conn = await AsyncConnection.connect(
        url,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    )

    memory_conn = await AsyncConnection.connect(
        url,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    )

    checkpointer = AsyncPostgresSaver(checkpoint_conn)
    memory_store = AsyncPostgresStore(memory_conn)

    await checkpointer.setup()
    await memory_store.setup()

    return checkpointer, memory_store, checkpoint_conn, memory_conn


async def close_database() -> None:
    if checkpoint_conn:
        await checkpoint_conn.close()
    if memory_conn:
        await memory_conn.close()