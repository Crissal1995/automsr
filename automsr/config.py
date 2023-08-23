import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml
from attr import define
from email_validator import (
    ValidatedEmail as _ValidatedEmail,
)
from email_validator import (
    validate_email as _validate_email,
)
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr
from typing_extensions import Annotated


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
    validated_email: _ValidatedEmail = _validate_email(
        value, check_deliverability=False
    )
    return validated_email.normalized


ValidatedVersion = Annotated[str, AfterValidator(validate_version)]
ValidatedURL = Annotated[str, AfterValidator(validate_url)]
ValidatedEmail = Annotated[str, AfterValidator(validate_email)]


@define(frozen=True)
class Defaults:
    desktop_useragent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188"
    )
    mobile_useragent = (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.3"
    )

    rewards_homepage = "https://rewards.bing.com/"
    bing_homepage = "https://www.bing.com/?scope=web"


class Profile(BaseModel):
    email: ValidatedEmail
    profile: str
    skip: bool = False


class AutomsrConfig(BaseModel):
    """
    >>> profiles = [{"email": "1@gmail.com", "profile": "p1"}, {"email": "2@gmail.com", "profile": "p2"}]
    >>> _ = AutomsrConfig(profiles=profiles)
    """

    profiles: List[Profile] = Field(..., min_length=1)

    rewards_homepage: ValidatedURL = Defaults.rewards_homepage
    bing_homepage: ValidatedURL = Defaults.bing_homepage

    desktop_useragent: str = Defaults.desktop_useragent
    mobile_useragent: str = Defaults.mobile_useragent


class EmailConfig(BaseModel):
    enable: bool = False
    recipient: Optional[ValidatedEmail] = None
    sender: Optional[ValidatedEmail] = None
    sender_password: Optional[SecretStr] = None
    host: Optional[str] = None
    port: Optional[int] = None
    tls: Optional[bool] = False


class SeleniumConfig(BaseModel):
    profiles_root: Path
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

        >>> profiles = [{"email": "1@gmail.com", "profile": "p1"}]
        >>> _data = {
        ...     "automsr": {"profiles": profiles},
        ...     "email": {},
        ...     "selenium": {"profiles_root": Path("profiles"), "chromedriver_path": Path("chromedriver.exe")},
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
