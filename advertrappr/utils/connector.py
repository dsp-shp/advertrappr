import duckdb

from advertrappr.settings import DATABASE_PATH, MODELS, getCreateSQL


class connect(duckdb.DuckDBPyConnection):
    def __new__(
        cls,
        database: str = str(DATABASE_PATH),
        read_only: bool = False,
        **kwargs
    ) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(database=database, read_only=read_only)
