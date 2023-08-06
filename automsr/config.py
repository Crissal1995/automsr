import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from typing_extensions import Annotated
from urllib.parse import urlparse

import yaml
from email_validator import ValidatedEmail as _ValidatedEmail, validate_email as _validate_email
from pydantic import BaseModel, ConfigDict, field_validator, AfterValidator

from automsr.datatypes import RewardsType


def validate_url(value: str) -> str:
    result = urlparse(value)
    assert all(field for field in (result.scheme, result.netloc, result.path))
    return value


def validate_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    validated_email: _ValidatedEmail = _validate_email(value)
    return validated_email.normalized


ValidatedURL = Annotated[str, AfterValidator(validate_url)]
ValidatedEmail = Annotated[str, AfterValidator(validate_email)]


class AutomsrConfig(BaseModel):
    credentials: Path
    skip: Union[None, RewardsType, List[RewardsType]] = None

    rewards_homepage: ValidatedURL = "https://rewards.bing.com/"


class EmailConfig(BaseModel):
    enable: bool = False
    sender: Optional[ValidatedEmail] = None
    recipient: Optional[ValidatedEmail] = None


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
        >>> _data["email"]["sender"] = "invalid-email"
        >>> Config.from_dict(_data)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: 1 validation error for Config
        email.sender
          Value error, The email address is not valid...
        ...
        >>> del _data["email"]["sender"]
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
