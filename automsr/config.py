import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from email_validator import ValidatedEmail, validate_email
from pydantic import BaseModel, ConfigDict, field_validator

from automsr.datatypes import RewardsType


class AutomsrConfig(BaseModel):
    credentials: Path
    skip: Union[None, RewardsType, List[RewardsType]] = None


class EmailConfig(BaseModel):
    enable: bool = False
    sender: Optional[str] = None
    recipient: Optional[str] = None

    @field_validator("sender", "recipient")
    @classmethod
    def _validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        validated_email: ValidatedEmail = validate_email(value)
        return validated_email.normalized


class SeleniumConfig(BaseModel):
    chrome_path: Path
    chromedriver_path: Path


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "v1"
    automsr: AutomsrConfig
    email: EmailConfig
    selenium: SeleniumConfig

    @field_validator("version")
    @classmethod
    def _assert_version(cls, value: str) -> str:
        if value != "v1":
            raise ValueError("Only version 'v1' is supported!")
        return value

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """
        Load config from a yaml filepath.
        """

        data = yaml.safe_load(open(path))
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, path: Path) -> "Config":
        """
        Load config from a json filepath.
        """

        data = json.load(open(path))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Load config from an in-memory mapping.

        >>> _data = {
        ...     "automsr": {"credentials": Path("creds.json")},
        ...     "email": {},
        ...     "selenium": {"chrome_path": Path("chrome.exe"), "chromedriver_path": Path("chromedriver.exe")},
        ... }
        >>> Config.from_dict(_data)  # doctest: +ELLIPSIS
        Config(version='v1', automsr=..., email=..., selenium=...)
        >>> _data["version"] = "v2"
        >>> Config.from_dict(_data)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: 1 validation error for Config
        version
          Value error, Only version 'v1' is supported! [type=value_error, input_value='v2', input_type=str]
        ...
        """

        return cls(**data)


if __name__ == "__main__":
    import doctest

    failures, _all_tests = doctest.testmod()
    assert not failures
