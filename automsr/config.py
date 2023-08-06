import json
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, ConfigDict


class AutomsrConfig(BaseModel):
    credentials: Path


class EmailConfig(BaseModel):
    pass


class SeleniumConfig(BaseModel):
    pass


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
