from dataclasses import dataclass, field
from enum import Enum, Flag, auto
from typing import Dict, List, Tuple, Union

from .utility import config


class PrizeKind(Enum):
    DONATION = "DONATION"

    MICROSOFT_GIFTCARD = "MICROSOFT_GIFTCARD"
    XBOX_STORE_GIFTCARD = "XBOX_STORE_GIFTCARD"

    XBOX_LIVE_GOLD = "XBOX_LIVE_GOLD"
    GAMEPASS_ULTIMATE = "GAMEPASS_ULTIMATE"
    GAMEPASS_PC = "GAMEPASS_PC"

    ESSELUNGA_GIFTCARD = "ESSELUNGA_GIFTCARD"
    IKEA_GIFTCARD = "IKEA_GIFTCARD"
    OVS_GIFTCARD = "OVS_GIFTCARD"
    Q8_GIFTCARD = "Q8_GIFTCARD"
    ZALANDO_GIFTCARD = "ZALANDO_GIFTCARD"
    DECATHLON_GIFTCARD = "DECATHLON_GIFTCARD"
    FOOT_LOCKER_GIFTCARD = "FOOT_LOCKER_GIFTCARD"
    MANGO_GIFTCARD = "MANGO_GIFTCARD"
    MONDADORI_GIFTCARD = "MONDADORI_GIFTCARD"
    SPOTIFY_GIFTCARD = "SPOTIFY_GIFTCARD"
    VOLAGRATIS_GIFTCARD = "VOLAGRATIS_GIFTCARD"

    THIRD_PARTY_GIFTCARD = "THIRD_PARTY_GIFTCARD"

    def __str__(self):
        return self.name


@dataclass
class PrizeKindGetter:
    get_query: str
    _get_query_parts: List[str] = field(init=False, default_factory=list)

    def __post_init__(self):
        assert self.get_query
        parts = list(map(str.strip, self.get_query.split(",")))
        valid_parts = [p for p in parts if p]
        self._get_query_parts = valid_parts

    @classmethod
    def _check_and_get_prize_kind(cls, prize_kind) -> PrizeKind:
        if isinstance(prize_kind, PrizeKind):
            pk = prize_kind
        elif isinstance(prize_kind, str):
            pk = PrizeKind(prize_kind.upper())
        else:
            raise ValueError(prize_kind)
        return pk

    @classmethod
    def get_mask_from_args(cls, *prize_kinds: Union[str, PrizeKind]) -> List[PrizeKind]:
        buffer = []

        for prize_kind in prize_kinds:
            pk = cls._check_and_get_prize_kind(prize_kind)
            buffer.append(pk)

        return buffer

    def get_mask(self) -> List[PrizeKind]:
        return self.get_mask_from_args(*self._get_query_parts)

    @classmethod
    def get_default_mask(cls) -> List[PrizeKind]:
        return cls.get_mask_from_args(
            PrizeKind.MICROSOFT_GIFTCARD,
            PrizeKind.GAMEPASS_PC,
            PrizeKind.THIRD_PARTY_GIFTCARD,
        )

    @classmethod
    def get_all_mask(cls) -> List[PrizeKind]:
        return list(PrizeKind.__members__.values())


class PrizeUnit(Flag):
    EUR = auto()
    MONTH = auto()

    def __str__(self):
        return self.name


@dataclass
class PrizeAmount:
    price_in_points: int
    amount: int
    unit: PrizeUnit

    def _handle_mul_int(self, other):
        assert isinstance(other, int)
        return PrizeAmount(
            amount=self.amount * other,
            price_in_points=self.price_in_points * other,
            unit=self.unit,
        )

    def _handle_mul(self, other):
        if other is None:
            raise ValueError(other)
        elif isinstance(other, (list, tuple)):
            return [self._handle_mul(integer) for integer in other]
        elif isinstance(other, int):
            return self._handle_mul_int(other)
        else:
            raise ValueError(other)

    def __mul__(self, other):
        return self._handle_mul(other)

    def __le__(self, other):
        assert isinstance(other, PrizeAmount)
        assert self.unit == other.unit
        return self.amount < other.amount

    def __eq__(self, other):
        assert isinstance(other, PrizeAmount)
        assert self.unit == other.unit
        return self.amount == other.amount


@dataclass
class PrizeAmountCollected(PrizeAmount):
    amount_collected: int = 0

    def _handle_mul_int(self, other):
        assert isinstance(other, int)
        return PrizeAmountCollected(
            amount=self.amount * other,
            price_in_points=self.price_in_points * other,
            unit=self.unit,
        )


@dataclass
class Prize:
    kind: PrizeKind
    amounts: List[PrizeAmountCollected]

    def __post_init__(self):
        if isinstance(self.amounts, PrizeAmountCollected):
            self.amounts = [self.amounts]

    def get_sorted_amounts(self, reverse: bool = False) -> List[PrizeAmountCollected]:
        return sorted(self.amounts, reverse=reverse, key=lambda p: p.amount)


PA_DONATION_ONE_EUR = PrizeAmountCollected(
    price_in_points=1000, amount=1, unit=PrizeUnit.EUR
)

PA_MICROSOFT_GIFTCARD_ONE_EUR = PrizeAmountCollected(
    price_in_points=930, amount=1, unit=PrizeUnit.EUR
)

PA_THIRD_PARTY_GIFTCARD_ONE_EUR = PrizeAmountCollected(
    price_in_points=1500, amount=1, unit=PrizeUnit.EUR
)

PA_XBOX_LIVE_GOLD_ONE_MONTH = PrizeAmountCollected(
    price_in_points=6800, amount=1, unit=PrizeUnit.MONTH
)
PA_XBOX_LIVE_GOLD_THREE_MONTHS = PrizeAmountCollected(
    price_in_points=15_000, amount=3, unit=PrizeUnit.MONTH
)

PA_GAMEPASS_ULTIMATE_ONE_MONTH = PrizeAmountCollected(
    price_in_points=12_000, amount=1, unit=PrizeUnit.MONTH
)
PA_GAMEPASS_ULTIMATE_THREE_MONTHS = PrizeAmountCollected(
    price_in_points=35_000, amount=3, unit=PrizeUnit.MONTH
)

PA_GAMEPASS_PC_ONE_MONTH = PrizeAmountCollected(
    price_in_points=7750, amount=1, unit=PrizeUnit.MONTH
)

ALL_PRIZES_LIST = [
    # DONATION
    Prize(kind=PrizeKind.DONATION, amounts=PA_DONATION_ONE_EUR * (1, 3, 5)),
    # MICROSOFT GIFTCARD
    Prize(
        kind=PrizeKind.MICROSOFT_GIFTCARD,
        amounts=PA_MICROSOFT_GIFTCARD_ONE_EUR * (2, 5, 10),
    ),
    Prize(
        kind=PrizeKind.XBOX_STORE_GIFTCARD,
        amounts=PA_MICROSOFT_GIFTCARD_ONE_EUR * (2, 5, 10),
    ),
    # XBOX LIVE GOLD
    Prize(
        kind=PrizeKind.XBOX_LIVE_GOLD,
        amounts=[PA_XBOX_LIVE_GOLD_ONE_MONTH, PA_XBOX_LIVE_GOLD_THREE_MONTHS],
    ),
    # GAMEPASS
    Prize(
        kind=PrizeKind.GAMEPASS_ULTIMATE,
        amounts=[PA_GAMEPASS_ULTIMATE_ONE_MONTH, PA_GAMEPASS_ULTIMATE_THREE_MONTHS],
    ),
    Prize(kind=PrizeKind.GAMEPASS_PC, amounts=[PA_GAMEPASS_PC_ONE_MONTH]),
    # THIRD_PARTY_GIFTCARD
    Prize(
        kind=PrizeKind.ESSELUNGA_GIFTCARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10
    ),
    Prize(kind=PrizeKind.IKEA_GIFTCARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 50),
    Prize(kind=PrizeKind.OVS_GIFTCARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10),
    Prize(kind=PrizeKind.Q8_GIFTCARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10),
    Prize(
        kind=PrizeKind.ZALANDO_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10),
    ),
    Prize(
        kind=PrizeKind.DECATHLON_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10, 25),
    ),
    Prize(
        kind=PrizeKind.FOOT_LOCKER_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (10, 25, 50),
    ),
    Prize(
        kind=PrizeKind.MANGO_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (25, 50, 100),
    ),
    Prize(
        kind=PrizeKind.MONDADORI_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10, 25),
    ),
    Prize(
        kind=PrizeKind.SPOTIFY_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (10, 30, 60),
    ),
    Prize(
        kind=PrizeKind.VOLAGRATIS_GIFTCARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (25, 50, 100),
    ),
    # GENERIC THIRD PARTY
    Prize(
        kind=PrizeKind.THIRD_PARTY_GIFTCARD, amounts=[PA_THIRD_PARTY_GIFTCARD_ONE_EUR]
    ),
]

ALL_PRIZES_DICT = {prize.kind: prize for prize in ALL_PRIZES_LIST}


def get_prizes(
    points: int,
    prizes_mask: Union[None, str, List[str], PrizeKind, List[PrizeKind]] = None,
) -> Dict[PrizeKind, Prize]:
    """
    Returns the dict of prizes that the user can redeem with
    the given points; the AutoMSR level defaults to level 2,
    obtained by reaching a small points threshold every month.

    Prizes Mask is an optional [list of] string[s], that will be used to retrieve
    the desired prizes instead of all prizes. If not provided,
    all prizes will be returned.
    """

    if not prizes_mask:
        prizes_mask = PrizeKindGetter.get_all_mask()
    elif isinstance(prizes_mask, (list, tuple)):
        prizes_mask = PrizeKindGetter.get_mask_from_args(*prizes_mask)
    else:
        prizes_mask = PrizeKindGetter.get_mask_from_args(prizes_mask)

    assert prizes_mask, "At least one prize should be retrieved"

    all_prizes_dict_copy = ALL_PRIZES_DICT.copy()
    prizes = dict()

    for prize_kind in prizes_mask:
        remaining_points = points

        prize: Prize = all_prizes_dict_copy[prize_kind]
        amounts = prize.get_sorted_amounts(reverse=True)

        for amount in amounts:
            amount.amount_collected = remaining_points // amount.price_in_points
            remaining_points %= amount.price_in_points

        # set new amounts
        prize.amounts = amounts
        prizes[prize_kind] = prize

    return prizes


def utility_collection(prize: Prize) -> Tuple[bool, int]:
    """
    Utility method to know if a prize can be collected.
    Returns the tuple (bool, int):
     the first value is the answer to the question;
     the second value is the total amount
    """
    can_collect = any(amount.amount_collected > 0 for amount in prize.amounts)
    if not can_collect:
        return False, 0
    # sum of every pair (amount, amount_collected) where amount is the value
    # of the prize, and amount_collected how many prizes the user can collect with
    # that value [e.g. 2 amount_collected of 5€ (amount) prizes is equal to 10€ total_amount]
    total_amount = sum(
        amount.amount_collected * amount.amount for amount in prize.amounts
    )
    return True, total_amount


def get_prizes_str(
    points: int,
    prizes_mask: Union[None, str, List[str], PrizeKind, List[PrizeKind]] = None,
    returns_only_collected: bool = True,
) -> str:
    """
    Returns a string holding a formatted representation of the prizes
     that the user can redeem.

    Prizes Mask is an optional [list of] string[s], that will be used to retrieve
    the desired prizes instead of all prizes. If not provided,
    all prizes will be returned.
    """
    prizes = get_prizes(points=points, prizes_mask=prizes_mask)

    s = ["You can redeem: "]
    for prize_kind, prize in prizes.items():
        can_collect, total_amount = utility_collection(prize)
        if not can_collect and returns_only_collected:
            continue
        # if I'm here I can redeem at least one prize amount
        s.append(f"{total_amount} {prize.amounts[0].unit} of {prize_kind}")

    # if I have only one element, I cannot redeem anything
    if len(s) == 1:
        s.append("NOTHING")

    return s[0] + ", ".join(s[1:])


def get_prizes_str_from_config(points: int, returns_only_collected: bool = True):
    """
    Returns a string holding a formatted representation of the prizes
     that the user can redeem.
    The mask will be parsed from config.
    """
    mask = config["prize"]["mask"]
    getter = PrizeKindGetter(mask)
    return get_prizes_str(
        points=points,
        prizes_mask=getter.get_mask(),
        returns_only_collected=returns_only_collected,
    )
