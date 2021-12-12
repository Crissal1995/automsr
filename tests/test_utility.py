from automsr.utility import get_value_from_dictionary


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
