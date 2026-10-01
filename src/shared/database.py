import psycopg
from psycopg.rows import dict_row, DictRow
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from .config import get_database_url

url = get_database_url()

checkpoint_conn: psycopg.Connection[DictRow] = psycopg.connect(
    url, autocommit=True, prepare_threshold=0, row_factory=dict_row
)

memory_conn: psycopg.Connection[DictRow] = psycopg.connect(
    url, autocommit=True, prepare_threshold=0, row_factory=dict_row
)

checkpointer = PostgresSaver(checkpoint_conn)
memory_store = PostgresStore(memory_conn)

checkpointer.setup()
memory_store.setup()

def close_database() -> None:
    checkpoint_conn.close()
    memory_conn.close()