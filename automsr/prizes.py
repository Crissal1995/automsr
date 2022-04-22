from dataclasses import dataclass
from enum import Flag, auto
from typing import List


class PrizeKind(Flag):
    DONATION = auto()

    MICROSOFT_GIFTCARD = auto()
    XBOX_STORE_GIFTCARD = auto()

    XBOX_LIVE_GOLD = auto()
    GAMEPASS_ULTIMATE = auto()
    GAMEPASS_PC = auto()

    ESSELUNGA_GIFT_CARD = auto()
    IKEA_GIFT_CARD = auto()
    OVS_GIFT_CARD = auto()
    Q8_GIFT_CARD = auto()
    ZALANDO_GIFT_CARD = auto()
    DECATHLON_GIFT_CARD = auto()
    FOOT_LOCKER_GIFT_CARD = auto()
    MANGO_GIFT_CARD = auto()
    MONDADORI_GIFT_CARD = auto()
    SPOTIFY_GIFT_CARD = auto()
    VOLAGRATIS_GIFT_CARD = auto()

    THIRD_PARTY_GIFTCARD = (
        ESSELUNGA_GIFT_CARD
        | IKEA_GIFT_CARD
        | OVS_GIFT_CARD
        | Q8_GIFT_CARD
        | ZALANDO_GIFT_CARD
        | DECATHLON_GIFT_CARD
        | FOOT_LOCKER_GIFT_CARD
        | MANGO_GIFT_CARD
        | MONDADORI_GIFT_CARD
        | SPOTIFY_GIFT_CARD
        | VOLAGRATIS_GIFT_CARD
    )


class PrizeUnit(Flag):
    EUR = auto()
    MONTH = auto()


@dataclass
class PrizeAmount:
    price_in_points: int
    amount: int
    unit: PrizeUnit

    def _handle_mul(self, other):
        if other is None:
            raise ValueError(other)
        elif isinstance(other, (list, tuple)):
            return [self._handle_mul(integer) for integer in other]
        elif isinstance(other, int):
            return PrizeAmount(
                amount=self.amount * other,
                price_in_points=self.price_in_points * other,
                unit=self.unit,
            )
        else:
            raise ValueError(other)

    def __mul__(self, other):
        return self._handle_mul(other)


@dataclass
class Prize:
    kind: PrizeKind
    amounts: List[PrizeAmount]

    def __post_init__(self):
        if isinstance(self.amounts, PrizeAmount):
            self.amounts = [self.amounts]


PA_DONATION_ONE_EUR = PrizeAmount(price_in_points=1000, amount=1, unit=PrizeUnit.EUR)

PA_MICROSOFT_GIFTCARD_ONE_EUR = PrizeAmount(
    price_in_points=930, amount=1, unit=PrizeUnit.EUR
)

PA_THIRD_PARTY_GIFTCARD_ONE_EUR = PrizeAmount(
    price_in_points=1500, amount=1, unit=PrizeUnit.EUR
)

PA_XBOX_LIVE_GOLD_ONE_MONTH = PrizeAmount(
    price_in_points=6800, amount=1, unit=PrizeUnit.MONTH
)
PA_XBOX_LIVE_GOLD_THREE_MONTHS = PrizeAmount(
    price_in_points=15_000, amount=3, unit=PrizeUnit.MONTH
)

PA_GAMEPASS_ULTIMATE_ONE_MONTH = PrizeAmount(
    price_in_points=12_000, amount=1, unit=PrizeUnit.MONTH
)
PA_GAMEPASS_ULTIMATE_THREE_MONTHS = PrizeAmount(
    price_in_points=35_000, amount=3, unit=PrizeUnit.MONTH
)

PA_GAMEPASS_PC_ONE_MONTH = PrizeAmount(
    price_in_points=7750, amount=1, unit=PrizeUnit.MONTH
)

ALL_PRIZES = [
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
        kind=PrizeKind.ESSELUNGA_GIFT_CARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10
    ),
    Prize(kind=PrizeKind.IKEA_GIFT_CARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 50),
    Prize(kind=PrizeKind.OVS_GIFT_CARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10),
    Prize(kind=PrizeKind.Q8_GIFT_CARD, amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * 10),
    Prize(
        kind=PrizeKind.ZALANDO_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10),
    ),
    Prize(
        kind=PrizeKind.DECATHLON_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10, 25),
    ),
    Prize(
        kind=PrizeKind.FOOT_LOCKER_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (10, 25, 50),
    ),
    Prize(
        kind=PrizeKind.MANGO_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (25, 50, 100),
    ),
    Prize(
        kind=PrizeKind.MONDADORI_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (5, 10, 25),
    ),
    Prize(
        kind=PrizeKind.SPOTIFY_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (10, 30, 60),
    ),
    Prize(
        kind=PrizeKind.VOLAGRATIS_GIFT_CARD,
        amounts=PA_THIRD_PARTY_GIFTCARD_ONE_EUR * (25, 50, 100),
    ),
    # GENERIC THIRD PARTY
    Prize(
        kind=PrizeKind.THIRD_PARTY_GIFTCARD, amounts=[PA_THIRD_PARTY_GIFTCARD_ONE_EUR]
    ),
]

"""
def get_prizes(points: int) -> List[Prize]:
    \"""
    Returns the list of prizes that the user can redeem with
    the given points; the AutoMSR level defaults to level 2,
    obtained by reaching a small points threshold every month.

    Returns a dictionary (key: string, value: int) where
    each key is a prize, and the value returned is the amount
    of prizes the user can get.
    \"""

    prizes_collected = prizes.copy()

    for prize in prizes_collected.values():
        one_amount = prize[PrizeKeys.POINTS_PER_ONE_AMOUNT]
        minimum_amount = prize[PrizeKeys.MINIMUM_AMOUNT]
        collected = points // one_amount
        prize[PrizeKeys.AMOUNT_COLLECTED] = (
            collected if collected >= minimum_amount else 0
        )

    return prizes_collected



def get_prizes_str(points: int, level: int = 2) -> str:
    \"""
    Returns a string holding a formatted representation of the prizes
     that the user can redeem.
    \"""
    prizes_collected = get_prizes(points=points, level=level)

    if not any(
        prize[PrizeKeys.AMOUNT_COLLECTED] for prize in prizes_collected.values()
    ):
        return "You cannot redeem anything!"

    # here at least one prize can be collected
    msg_list = ["You can redeem: "]
    for prize_key, prize in prizes_collected.items():
        amount = prize[PrizeKeys.AMOUNT_COLLECTED]
        if not amount:
            continue

        value = amount * prize[PrizeKeys.MINIMUM_AMOUNT]

        unit = "€"
        if prize_key in (PrizeKind.GAMEPASS_PC, PrizeKind.GAMEPASS_ULTIMATE):
            unit = " month"
            if amount > 1:
                unit += "s"

        msg_list += [f"{amount} {prize_key.name} [{value}{unit}]"]

    msg = msg_list[0] + ", ".join(msg_list[1:])
    return msg
"""
