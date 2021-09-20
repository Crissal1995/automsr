import sqlite3
from dataclasses import astuple, dataclass
from typing import List, Sequence

DB_NAME = "automsr.sqlite"

DB_TABLE = "states"
DB_SQL_INIT = (
    f"create table if not exists {DB_TABLE} "
    "(email text not null, points int not null, timestamp integer not null)"
)
DB_SQL_INSERT = f"insert into {DB_TABLE} values (?, ?, ?)"
DB_SQL_QUERY_ALL = f"select * from {DB_TABLE}"
DB_SQL_QUERY_EMAIL = f"select * from {DB_TABLE} t where t.email = ?"


@dataclass()
class State:
    # the email of the account owner
    email: str

    # points got at current timestamp
    points: int

    # time.time() casted to int
    # https://www.sqlite.org/datatype3.html#date_and_time_datatype
    timestamp: int


class StateManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

        self.cursor.execute(DB_SQL_INIT)
        self.conn.commit()

    def insert_state(self, state: State, commit: bool = True):
        self.cursor.execute(DB_SQL_INSERT, astuple(state))
        if commit:
            self.conn.commit()

    def insert_states(self, states: Sequence[State]):
        for state in states:
            self.insert_state(state, commit=False)
        self.conn.commit()

    def fetch_states_filtered(self, email: str) -> List[State]:
        self.cursor.execute(DB_SQL_QUERY_EMAIL, (email,))
        return [State(*t) for t in self.cursor.fetchall()]

    def fetch_states(self) -> List[State]:
        self.cursor.execute(DB_SQL_QUERY_ALL)
        return [State(*t) for t in self.cursor.fetchall()]

    def _raw_query(self, query: str):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _quit(self):
        self.cursor.close()
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._quit()

    def __del__(self):
        self._quit()
