import datetime
import enum
import hashlib
import sqlite3
import time
from abc import ABC
from dataclasses import astuple, dataclass
from typing import Any, List, Optional, Sequence, Tuple, Union

DB_NAME = "automsr.sqlite"


# https://stackoverflow.com/questions/60590442
@dataclass
class AbstractDataclass(ABC):
    def __new__(cls, *args, **kwargs):
        if cls == AbstractDataclass or cls.__bases__[0] == AbstractDataclass:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


class State(AbstractDataclass):
    DB_TABLE: str
    DB_SQL_INIT: str
    DB_SQL_INSERT: str
    DB_SQL_QUERY_ALL: str
    DB_SQL_QUERY_EMAIL: str


@dataclass
class PointsState(State):
    # the email of the account owner
    email: str

    # points got at current timestamp
    points: int

    # time.time() casted to int
    # https://www.sqlite.org/datatype3.html#date_and_time_datatype
    timestamp: int

    # points obtained in this run
    points_delta: Optional[int] = None

    # override attributes
    DB_TABLE = "points"
    DB_SQL_INIT = (
        f"create table if not exists {DB_TABLE} "
        "(email text not null, "
        "points int not null, "
        "timestamp integer not null, "
        "points_delta int)"
    )
    DB_SQL_INSERT = f"insert into {DB_TABLE} values (?, ?, ?, ?)"
    DB_SQL_QUERY_ALL = f"select * from {DB_TABLE}"
    DB_SQL_QUERY_EMAIL = f"select * from {DB_TABLE} t where t.email = ?"
    DB_SQL_QUERY_EMAIL_TIMESTAMP = (
        f"select * from {DB_TABLE} t where t.email = ? "
        f"and t.timestamp between ? and ?;"
    )


class ActivityStatusEnum(enum.Enum):
    TODO = "TODO"
    DONE = "DONE"
    INVALID = "INVALID"


@dataclass
class ActivityState(State):
    email: str
    timestamp: int
    daily: bool
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    hash: Optional[str] = None

    def __post_init__(self):
        # raises ValueError if an invalid string is provided
        self.status = self.status.upper()
        ActivityStatusEnum(self.status)

        # create hash with MD5 if not provided
        if not self.hash:
            date = datetime.date.fromtimestamp(self.timestamp)
            attrs = (self.email, date, self.daily, self.title, self.description)
            hashstr = b"".join(bytes(str(x), "utf-8") for x in attrs)
            self.hash = hashlib.md5(hashstr).hexdigest()

    # override attributes
    DB_TABLE = "activity"
    DB_SQL_INIT = (
        f"create table if not exists {DB_TABLE} "
        "(email text not null, "
        "timestamp integer not null, "
        "daily bool not null, "
        "status text not null, "
        "title text, "
        "description text,"
        "hash text)"
    )
    DB_SQL_INSERT = f"insert into {DB_TABLE} values (?, ?, ?, ?, ?, ?, ?)"
    DB_SQL_QUERY_ALL = f"select * from {DB_TABLE}"
    DB_SQL_QUERY_EMAIL = f"select * from {DB_TABLE} t where t.email = ?"
    DB_SQL_QUERY_HASH = f"select * from {DB_TABLE} t where t.hash = ?"
    DB_SQL_UPDATE_HASH = f"update {DB_TABLE} set status = ? where hash = ?"

    DB_SQL_SELECT_TODO_ACTIVITIES = (
        f"select * from {DB_TABLE} t "
        f"where t.email = ? and t.status = 'TODO' "
        f"and t.timestamp between ? and ?;"
    )


@dataclass
class StateFilter:
    query: str
    values: List[Any]

    def execute(self, cursor: sqlite3.Cursor):
        cursor.execute(self.query, self.values)


class StateManager:
    state_classes_map = {
        "points": PointsState,
        "activity": ActivityState,
    }
    state_classes = tuple(state_classes_map.values())

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

        for stateclass in self.state_classes:
            self.cursor.execute(stateclass.DB_SQL_INIT)
            self.conn.commit()

    def insert_state(self, state: State, commit: bool = True):
        self.cursor.execute(state.DB_SQL_INSERT, astuple(state))
        if commit:
            self.conn.commit()

    def insert_states(self, states: Sequence[State], commit: bool = True):
        for state in states:
            self.insert_state(state, commit=False)
        if commit:
            self.conn.commit()

    def update_states_filter_hash(
        self, kind: str, hashstr: str, new_value: str, commit: bool = True
    ):
        kind_cls = self._get_kind_state(kind)
        query = kind_cls.DB_SQL_UPDATE_HASH
        values = [new_value, hashstr]
        self.cursor.execute(query, values)
        if commit:
            self.conn.commit()

    @classmethod
    def _get_kind_state(cls, kind: str):
        kind = kind.lower()
        kind_cls = cls.state_classes_map.get(kind)
        if not kind_cls:
            keys = list(cls.state_classes_map.keys())
            raise ValueError(f"Invalid state kind provided! Availables are: {keys}")
        return kind_cls

    def fetch_states_filter(self, kind: str, sfilter: StateFilter) -> List[State]:
        kind_cls = self._get_kind_state(kind)
        sfilter.execute(cursor=self.cursor)
        return [kind_cls(*t) for t in self.cursor.fetchall()]

    def fetch_states_filter_email(self, kind: str, email: str) -> List[State]:
        kind_cls = self._get_kind_state(kind)
        query = kind_cls.DB_SQL_QUERY_EMAIL
        values = [email]
        sfilter = StateFilter(query, values)
        return self.fetch_states_filter(kind, sfilter)

    def fetch_states_filter_hash(self, kind: str, hashstr: str) -> List[State]:
        kind_cls = self._get_kind_state(kind)
        query = kind_cls.DB_SQL_QUERY_HASH
        values = [hashstr]
        sfilter = StateFilter(query, values)
        return self.fetch_states_filter(kind, sfilter)

    def fetch_states(self, kind: str) -> List[State]:
        kind_cls = self._get_kind_state(kind)
        self.cursor.execute(kind_cls.DB_SQL_QUERY_ALL)
        return [kind_cls(*t) for t in self.cursor.fetchall()]

    @staticmethod
    def _get_timestamp_boundaries(
        date_or_timestamp: Union[int, float, datetime.date]
    ) -> Tuple[float, float]:
        """Get day boundaries (as timestamps) for a given timestamp."""
        if isinstance(date_or_timestamp, (int, float)):
            date = datetime.date.fromtimestamp(date_or_timestamp)
        elif isinstance(date_or_timestamp, datetime.date):
            date = date_or_timestamp
        else:
            raise ValueError(f"Invalid value provided: {date_or_timestamp}")

        min_timestamp = time.mktime(date.timetuple())
        max_timestamp = time.mktime((date + datetime.timedelta(days=1)).timetuple())
        return min_timestamp, max_timestamp

    def get_missing_activities(
        self, email: str, date: datetime.date
    ) -> List[ActivityState]:
        min_timestamp, max_timestamp = self._get_timestamp_boundaries(date)

        sfilter = StateFilter(
            ActivityState.DB_SQL_SELECT_TODO_ACTIVITIES,
            [email, min_timestamp, max_timestamp],
        )
        sfilter.execute(self.cursor)
        return [ActivityState(*t) for t in self.cursor.fetchall()]

    def insert_points(
        self, email: str, points: int, timestamp: int, delta_points: int = None
    ):
        sfilter = StateFilter(
            PointsState.DB_SQL_INSERT, [email, points, timestamp, delta_points]
        )
        sfilter.execute(self.cursor)

    def get_point_states(self, email: str, date: datetime.date) -> List[PointsState]:
        """Get all points state for a given email and date"""
        mint, maxt = self._get_timestamp_boundaries(date)

        query = PointsState.DB_SQL_QUERY_EMAIL_TIMESTAMP
        sfilter = StateFilter(query, [email, mint, maxt])
        sfilter.execute(self.cursor)

        return [PointsState(*t) for t in self.cursor.fetchall()]

    def get_delta_points(self, email: str, date: datetime.date) -> int:
        """Get all obtained points (delta) for a given email and date"""
        points = [p.points for p in self.get_point_states(email, date)]
        return max(points) - min(points)

    def get_final_points(self, email: str, date: datetime.date) -> int:
        """Get final points obtained for a given email and date"""
        return max(p.points for p in self.get_point_states(email, date))

    def _raw_query(self, query: str) -> Any:
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def _quit(self):
        try:
            self.cursor.close()
            self.conn.close()
        except sqlite3.ProgrammingError:
            pass  # already closed

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._quit()

    def __del__(self):
        self._quit()
