import json
from pathlib import Path
from typing import Any, Collection, Dict, Union

import yaml
from email_validator import validate_email, ValidatedEmail
from pydantic import BaseModel, ConfigDict, field_validator

from automsr.datatypes import RewardsType


class AutomsrConfig(BaseModel):
    credentials: Path
    skip: Union[RewardsType, Collection[RewardsType]]


class EmailConfig(BaseModel):
    enable: bool
    sender: str
    recipient: str

    @field_validator("sender", "recipient")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        validated_email: ValidatedEmail = validate_email(value)
        return validated_email.normalized


class SeleniumConfig(BaseModel):
    chromedriver_path: Path
    chrome_binary_path: Path


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "v1"
    automsr: AutomsrConfig
    selenium: SeleniumConfig

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """
        Load config from a yaml filepath.
        """

        data = yaml.safe_load(open(path))
        return cls(**data)

    @classmethod
    def from_json(cls, path: Path) -> "Config":
        """
        Load config from a json filepath.
        """

        data = json.load(open(path))
        return cls(**data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Load config from an in-memory mapping.

        >>> _data = {"automsr": {}, "selenium": {"foo": "bar"}}
        >>> Config.from_dict(_data)  # doctest: +ELLIPSIS
        Config(version='v1', automsr=..., selenium=...)
        """

        return cls(**data)


if __name__ == "__main__":
    import doctest

    failures, _all_tests = doctest.testmod()
    assert not failures
