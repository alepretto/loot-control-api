from enum import StrEnum


class AccountType(StrEnum):
    bank = "bank"
    wallet = "wallet"
    digital = "digital"
    benefits = "benefits"