import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml
from attr import define
from email_validator import EmailNotValidError
from email_validator import (
    ValidatedEmail as _ValidatedEmail,
)
from email_validator import validate_email as _validate_email
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


def validate_email(
    value: Optional[str], *, raise_on_error: bool = True
) -> Optional[str]:
    if value is None:
        return None
    try:
        validated_email: _ValidatedEmail = _validate_email(
            value, check_deliverability=False
        )
        return validated_email.normalized
    except EmailNotValidError as e:
        if raise_on_error:
            raise e
        else:
            return None


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

    def store(
        self, path: Optional[Path] = None, *, optional_keys: bool = False
    ) -> Optional[str]:
        """
        Write the config file to a specified path.
        If the path is None, then it will be dumped to the stdout.

        The format used is YAML.

        If `optional_keys` is True, then also optional keys will be added to the
        resulting config file.

        >>> _config = Config.from_dict({
        ...     "automsr": {"profiles": [{"email": "foo@gmail.com", "profile": "my-profile"}]},
        ...     "email": {
        ...         "enable": True,
        ...         "recipient": "foo@gmail.com",
        ...         "sender": "bar@gmail.com",
        ...         "sender_password": "abcd",
        ...     },
        ...     "selenium": {
        ...         "profiles_root": "profiles_root",
        ...         "chromedriver_path": "chromedriver",
        ...     }
        ... })

        Dump to stdout
        >>> _config.store()
        '---\\nversion: v1\\nautomsr:\\n  profiles:\\n  - email: foo@gmail.com\\n    profile: my-profile\\n    skip: false\\nselenium:\\n  profiles_root: profiles_root\\n  chromedriver_path: chromedriver\\nemail:\\n  enable: true\\n  recipient: foo@gmail.com\\n  sender: bar@gmail.com\\n  sender_password: abcd\\n'

        Dump to a file
        >>> import tempfile
        >>> f = tempfile.NamedTemporaryFile(mode="w", delete=False)
        >>> _path = Path(f.name)
        >>> _config.store(path=_path)
        >>> f.close()
        >>> assert _path.is_file()
        >>> assert Config.from_yaml(_path) is not None
        >>> _path.unlink()
        """  # noqa: E501

        data = self.get_dict(optional_keys=optional_keys)
        output: Optional[str] = yaml.dump(
            data=data,
            stream=path.open(mode="w") if path is not None else None,
            indent=2,
            sort_keys=False,
            explicit_start=True,
        )
        return output

    def get_dict(self, optional_keys: bool = False) -> Dict[str, Any]:
        """
        Get a dictionary of the current config.

        If `optional_keys` is False, non required keys
        will be filtered out from the final config.
        """

        data = self.model_dump()
        if isinstance(data["email"]["sender_password"], SecretStr):
            data["email"]["sender_password"] = data["email"][
                "sender_password"
            ].get_secret_value()
        if optional_keys:
            return data

        version = data["version"]
        automsr_data = dict(profiles=data["automsr"]["profiles"])
        selenium_data = dict(
            profiles_root=str(data["selenium"]["profiles_root"]),
            chromedriver_path=str(data["selenium"]["chromedriver_path"]),
        )
        email_data = dict(
            enable=data["email"]["enable"],
            # also the following keys are optional,
            # however they are mandatory if `email/enable` is true
            recipient=data["email"]["recipient"],
            sender=data["email"]["sender"],
            sender_password=data["email"]["sender_password"],
        )

        return {
            "version": version,
            "automsr": automsr_data,
            "selenium": selenium_data,
            "email": email_data,
        }


if __name__ == "__main__":
    import doctest

    failures, _all_tests = doctest.testmod()
    assert not failures
