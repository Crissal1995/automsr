import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import yaml
from email_validator import (
    ValidatedEmail as _ValidatedEmail,
)
from email_validator import (
    validate_email as _validate_email,
)
from pydantic import AfterValidator, BaseModel, ConfigDict, SecretStr
from typing_extensions import Annotated

from automsr.datatypes import RewardsType


def validate_version(value: str) -> str:
    if value != "v1":
        raise ValueError("Version unsupported")
    return value


def validate_url(value: str) -> str:
    result = urlparse(value)
    assert all(field for field in (result.scheme, result.netloc, result.path))
    return value


def validate_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    validated_email: _ValidatedEmail = _validate_email(value)
    return validated_email.normalized


ValidatedVersion = Annotated[str, AfterValidator(validate_version)]
ValidatedURL = Annotated[str, AfterValidator(validate_url)]
ValidatedEmail = Annotated[str, AfterValidator(validate_email)]


class SingleCredentials(BaseModel):
    email: ValidatedEmail
    password: SecretStr


class MultipleCredentials(BaseModel):
    credentials: List[SingleCredentials]


def validate_credentials_path(value: Path) -> Path:
    content = open(value).read()
    if value.suffix == ".json":
        data = json.loads(content)
    elif value.suffix in (".yml", ".yaml"):
        data = yaml.safe_load(content)
    else:
        raise ValueError(f"Expecting a json or yaml file, received: {value!s}")

    # check that the data is pydantic-complaint
    if isinstance(data, list):
        raise TypeError("Expecting a dictionary, found a list!")
    elif isinstance(data, dict):
        _credentials = MultipleCredentials(**data)

    return value


ValidatedCredentialsPath = Annotated[Path, AfterValidator(validate_credentials_path)]


class AutomsrConfig(BaseModel):
    """
    >>> from unittest.mock import patch, mock_open
    >>> from unittest import TestCase
    >>> from pydantic import ValidationError
    >>> path = Path("credentials.json")
    >>> content = '{"credentials": [{"email": "mario@outlook.com", "password": "secretValue"}]}'
    >>> wrong_content_list = '[{"email": "mario@outlook.com", "password": "secretValue"}]'
    >>> wrong_content_fields = '{"credentials": [{"foo": "baz"}]}'
    >>> with patch("builtins.open", mock_open(read_data=content)):
    ...     _ = AutomsrConfig(credentials=path)
    >>> with patch("builtins.open", mock_open(read_data=wrong_content_list)):
    ...     with TestCase().assertRaises(TypeError):
    ...         _ = AutomsrConfig(credentials=path)
    >>> with patch("builtins.open", mock_open(read_data=wrong_content_fields)):
    ...     with TestCase().assertRaises(ValidationError):
    ...         _ = AutomsrConfig(credentials=path)
    """

    credentials: ValidatedCredentialsPath
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

    version: ValidatedVersion = "v1"
    automsr: AutomsrConfig
    email: EmailConfig
    selenium: SeleniumConfig

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
          Value error, Version unsupported [type=value_error, input_value='v2', input_type=str]
        ...
        """

        return cls(**data)


if __name__ == "__main__":
    import doctest

    failures, _all_tests = doctest.testmod()
    assert not failures
