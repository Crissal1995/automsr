from automsr.prizes import PrizeKind, PrizeUnit, get_prizes_str

PREFIX = "You can redeem: "
EUR = PrizeUnit.EUR
MONTH = PrizeUnit.MONTH


def get_message(msg):
    return f"{PREFIX}{msg}"


def get_null_message():
    return get_message("NOTHING")


def get_formatted_message(amount, unit, kind, prefix=True):
    if prefix:
        s = get_message(f"{amount} {unit} of {kind}")
    else:
        s = f"{amount} {unit} of {kind}"
    return s


def _(amount, unit, kind, prefix=True):
    return get_formatted_message(amount, unit, kind, prefix=prefix)


def __(values: dict):
    amount = values["amount"]
    unit = values["unit"]
    kind = values["kind"]
    assert isinstance(amount, (list, tuple))
    assert isinstance(unit, (list, tuple))
    assert isinstance(kind, (list, tuple))

    pieces = []
    for i, (a, u, k) in enumerate(zip(amount, unit, kind)):
        prefix = i == 0
        pieces.append(_(a, u, k, prefix=prefix))
    return ", ".join(pieces)


def null():
    return get_null_message()


def test0():
    assert get_prizes_str(1000, prizes_mask=PrizeKind.DONATION) == _(
        1, EUR, PrizeKind.DONATION
    )


def test1():
    assert get_prizes_str(123) == null()


def test2():
    assert get_prizes_str(2000, PrizeKind.GAMEPASS_PC) == null()
    assert get_prizes_str(10_000, PrizeKind.GAMEPASS_PC) == _(
        1, MONTH, PrizeKind.GAMEPASS_PC
    )


def test3():
    assert get_prizes_str(
        10_000,
        [PrizeKind.GAMEPASS_PC, PrizeKind.MICROSOFT_GIFTCARD, PrizeKind.Q8_GIFTCARD],
    ) == __(
        {
            "amount": [1, 10],
            "unit": [MONTH, EUR],
            "kind": [PrizeKind.GAMEPASS_PC, PrizeKind.MICROSOFT_GIFTCARD],
        }
    )


def test4():
    assert get_prizes_str(
        10_000,
        [PrizeKind.GAMEPASS_PC, PrizeKind.MICROSOFT_GIFTCARD, PrizeKind.Q8_GIFTCARD],
        returns_only_collected=False,
    ) == __(
        {
            "amount": [1, 10, 0],
            "unit": [MONTH, EUR, EUR],
            "kind": [
                PrizeKind.GAMEPASS_PC,
                PrizeKind.MICROSOFT_GIFTCARD,
                PrizeKind.Q8_GIFTCARD,
            ],
        }
    )
