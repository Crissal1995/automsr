import sqlite3

import pytest

import msrewards.state
from msrewards.state import State, StateManager

# mock DB_NAME to create an in-memory database
msrewards.state.DB_NAME = ":memory:"


def test0():
    sm = StateManager()
    db_table = msrewards.state.DB_TABLE

    with pytest.raises(sqlite3.OperationalError):
        sm._raw_query(f"create table {db_table} (foo text, bar int)")


def test1():
    sm = StateManager()

    state = State("foo@bar.com", 42, 999)
    sm.insert_state(state)

    states = sm.fetch_states()
    assert len(states) == 1
    assert states[0] == state


def test2():
    sm = StateManager()

    email = "hello@world.it"
    state = State(email, 42, 999)
    sm.insert_state(state)

    states = sm.fetch_states_filtered(email=email)
    assert len(states) == 1
    assert states[0] == state


def test3():
    sm = StateManager()

    state1 = State("foo", 42, 999)
    state2 = State("bar", 42, 999)
    sm.insert_state(state1)
    sm.insert_state(state2)

    states = sm.fetch_states()
    assert len(states) == 2

    states = sm.fetch_states_filtered(email="foo")
    assert len(states) == 1
    assert states[0] == state1
