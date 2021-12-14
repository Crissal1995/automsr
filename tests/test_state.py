import datetime
import random
import sqlite3
import time

import pytest

import automsr.state
from automsr.state import ActivityState, PointsState, StateManager

# mock DB_NAME to create an in-memory database
automsr.state.DB_NAME = ":memory:"


def test0():
    sm = StateManager()
    db_table = PointsState.DB_TABLE

    with pytest.raises(sqlite3.OperationalError):
        sm._raw_query(f"create table {db_table} (foo text, bar int)")


def test1():
    sm = StateManager()

    state = PointsState("foo@bar.com", 42, 1, 999)
    sm.insert_state(state)

    states = sm.fetch_states(kind="points")
    assert len(states) == 1
    assert states[0] == state


def test2():
    sm = StateManager()

    email = "hello@world.it"
    state = PointsState(email, 42, 22, 999)
    sm.insert_state(state)

    states = sm.fetch_states_filter_email(kind="points", email=email)
    assert len(states) == 1
    assert states[0] == state


def test3():
    sm = StateManager()

    state1 = PointsState("foo", 42, 34, 999)
    state2 = PointsState("bar", 42, 0, 999)
    sm.insert_state(state1)
    sm.insert_state(state2)

    states = sm.fetch_states(kind="points")
    assert len(states) == 2

    states = sm.fetch_states_filter_email(kind="points", email="foo")
    assert len(states) == 1
    assert states[0] == state1


def test5():
    sm = StateManager()

    email = "foo@bar.com"
    timestamp = int(time.time())
    s1 = ActivityState(email, timestamp, True, "TODO")
    s2 = ActivityState(email, timestamp, False, "DONE")
    s3 = ActivityState(
        email, timestamp, False, "INVALID", "The title", "The description"
    )
    local_states = [s1, s2, s3]

    sm.insert_states(local_states)
    fetch_states = sm.fetch_states("activity")
    assert len(local_states) == len(fetch_states)
    assert all(s1 == s2 for (s1, s2) in zip(local_states, fetch_states))


def test6():
    email = "foo@bar.com"
    timestamp = int(time.time())
    with pytest.raises(ValueError):
        ActivityState(email, timestamp, True, "Invalid Status")


def test7():
    sm = StateManager()

    email = "foo@bar.com"
    day_in_s = 60 * 60 * 24
    timestamp = int(time.time())

    n = 10
    timestamps = [timestamp - (i + 1) * day_in_s for i in range(n)]
    points = [random.randint(100, 1000) for _ in range(n)]

    states = [PointsState(email, points[i], timestamps[i]) for i in range(n)]
    sm.insert_states(states)

    fetch_states = sm.fetch_states("points")
    assert len(fetch_states) == len(states) == n
    assert fetch_states == states
    assert all(fs == s for (fs, s) in zip(fetch_states, states))


def test8():
    sm = StateManager()

    email = "foo@bar.com"
    timestamp = int(time.time())
    a = ActivityState(email, timestamp, True, "DONE")
    assert a.hash

    sm.insert_state(a)
    s1 = sm.fetch_states("activity")
    s2 = sm.fetch_states_filter_hash("activity", a.hash)

    assert len(s1) == 1
    s1 = s1[0]
    assert s1 == a

    assert len(s2) == 1
    s2 = s2[0]
    assert s2 == a


def test9():
    sm = StateManager()

    email = "foo@bar.com"
    timestamp = int(time.time())
    a = ActivityState(email, timestamp, True, "DONE")

    sm.insert_state(a)

    new_status = "TODO"
    a.status = new_status
    sm.update_states_filter_hash("activity", a.hash, new_status)

    s = sm.fetch_states_filter_hash("activity", a.hash)

    assert len(s) == 1
    s = s[0]
    assert s == a


def test10():
    sm = StateManager()

    timestamp = int(time.time())
    thedate = datetime.date.fromtimestamp(timestamp)

    names = ["foo", "bar", "baz", "pippo"]
    emails = [f"{x}@example.org" for x in names]
    states = [ActivityState(email, timestamp, True, "TODO") for email in emails]
    sm.insert_states(states)

    for email, state in zip(emails, states):
        activities = sm.get_missing_activities(email, thedate)
        assert len(activities) == 1
        activity = activities.pop()
        assert activity == state

    NEW_VALUE = "DONE"
    state = states[0]
    state.status = NEW_VALUE
    sm.update_states_filter_hash("activity", state.hash, NEW_VALUE)

    fetch_states = sm.get_missing_activities(state.email, thedate)
    assert len(fetch_states) == 0

    fetch_states = sm.fetch_states_filter_hash("activity", state.hash)
    assert len(fetch_states) == 1
    assert fetch_states[0] == state


def test11():
    sm = StateManager()

    timestamp = int(time.time())
    today = datetime.date.fromtimestamp(timestamp)

    email = "foo@bar.com"
    points = 42

    state = PointsState(email, points, timestamp)

    sm.insert_points(email, points, timestamp)
    s = sm.get_point_states(email, today)

    assert len(s) == 1
    assert s[0] == state


def test12():
    sm = StateManager()

    timestamp = int(time.time())
    today = datetime.date.fromtimestamp(timestamp)

    email = "foo@bar.com"
    points = 42
    delta = 111

    state = PointsState(email, points, timestamp, delta)

    sm.insert_points(email, points, timestamp, delta)
    s = sm.get_point_states(email, today)

    assert len(s) == 1
    assert s[0] == state


def test13():
    sm = StateManager()

    timestamp = int(time.time())
    today = datetime.date.fromtimestamp(timestamp)

    email = "foo@bar.com"
    points = 42

    sm.insert_points(email, points, timestamp)
    delta = sm.get_delta_points(email, today)
    assert delta == 0


def test14():
    sm = StateManager()

    timestamp = int(time.time())
    today = datetime.date.fromtimestamp(timestamp)

    email = "foo@bar.com"
    points_list = list(range(100, 300, 10))
    org_delta = points_list[-1] - points_list[0]

    for points in points_list:
        sm.insert_points(email, points, timestamp)
    delta = sm.get_delta_points(email, today)

    assert org_delta == delta


def test15():
    sm = StateManager()

    timestamp = int(time.time())
    today = datetime.date.fromtimestamp(timestamp)

    email = "foo@bar.com"
    points = list(range(100, 300, 10))

    for point in points:
        sm.insert_points(email, point, timestamp)
    final_points = sm.get_final_points(email, today)

    assert max(points) == final_points
