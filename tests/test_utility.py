from automsr.utility import activity_skip, get_value_from_dictionary


def test0():
    d = {"foo": 1, "bar": 2}

    assert get_value_from_dictionary(d, "foo") == 1
    assert get_value_from_dictionary(d, "bar") == 2
    assert get_value_from_dictionary(d, "baz") is None


def test1():
    d = {"a": "", "b": False, "c": 0}

    assert get_value_from_dictionary(d, "a") == ""
    assert get_value_from_dictionary(d, "b") is False
    assert get_value_from_dictionary(d, "c") == 0

    assert get_value_from_dictionary(d, "a", strict_non_false_value=True) is None
    assert get_value_from_dictionary(d, "b", strict_non_false_value=True) is None
    assert get_value_from_dictionary(d, "c", strict_non_false_value=True) is None


def test2():
    d = {"profile": "path"}
    kws = ["profile_dir", "profiles", "profile"]
    assert get_value_from_dictionary(d, kws) == "path"


def test3():
    SKIP_NOTHING = (False, False, False)
    SKIP_ALL = (True, True, True)
    NO_ACTIVITY = (True, False, False)
    NO_PUNCHCARD = (False, True, False)
    NO_SEARCH = (False, False, True)

    assert activity_skip("") == SKIP_NOTHING
    assert activity_skip("no") == SKIP_NOTHING
    assert activity_skip("false") == SKIP_NOTHING

    assert activity_skip("all") == SKIP_ALL
    assert activity_skip("yes") == SKIP_ALL
    assert activity_skip("true") == SKIP_ALL

    assert activity_skip("activity") == NO_ACTIVITY
    assert activity_skip("activities") == NO_ACTIVITY

    assert activity_skip("punchcard") == NO_PUNCHCARD
    assert activity_skip("punchcards") == NO_PUNCHCARD

    assert activity_skip("search") == NO_SEARCH
    assert activity_skip("searches") == NO_SEARCH


def test4():
    NO_ACTIVITY_PUNCHCARD = (True, True, False)
    NO_PUNCHCARD_SEARCH = (False, True, True)
    NO_ACTIVITY_SEARCH = (True, False, True)
    SKIP_ALL = (True, True, True)

    assert activity_skip("activity,punchcard") == NO_ACTIVITY_PUNCHCARD
    assert activity_skip("activity, search") == NO_ACTIVITY_SEARCH
    assert activity_skip(" punchcard, search ") == NO_PUNCHCARD_SEARCH
    assert activity_skip(" punchcard, search ,   activity    ") == SKIP_ALL
