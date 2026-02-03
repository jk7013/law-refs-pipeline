import os
from dataclasses import dataclass


@dataclass
class DbConfig:
    host: str
    port: str
    dbname: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "DbConfig":
        return cls(
            host=os.getenv("PGHOST", "localhost"),
            port=os.getenv("PGPORT", "5432"),
            dbname=os.getenv("PGDATABASE", ""),
            user=os.getenv("PGUSER", ""),
            password=os.getenv("PGPASSWORD", ""),
        )

