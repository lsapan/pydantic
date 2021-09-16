import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional, Type, TypeVar, Union

from .main import BaseModel
from .parse import Protocol, load_file, load_str_bytes
from .types import StrBytes
from .typing import display_as_type

__all__ = ('parse_file_as', 'parse_obj_as', 'parse_raw_as', 'create_partial_model')

NameFactory = Union[str, Callable[[Type[Any]], str]]


def _generate_parsing_type_name(type_: Any) -> str:
    return f'ParsingModel[{display_as_type(type_)}]'


@lru_cache(maxsize=2048)
def _get_parsing_type(type_: Any, *, type_name: Optional[NameFactory] = None) -> Any:
    from pydantic.main import create_model

    if type_name is None:
        type_name = _generate_parsing_type_name
    if not isinstance(type_name, str):
        type_name = type_name(type_)
    return create_model(type_name, __root__=(type_, ...))


T = TypeVar('T')


def parse_obj_as(type_: Type[T], obj: Any, *, type_name: Optional[NameFactory] = None) -> T:
    model_type = _get_parsing_type(type_, type_name=type_name)  # type: ignore[arg-type]
    return model_type(__root__=obj).__root__


def parse_file_as(
    type_: Type[T],
    path: Union[str, Path],
    *,
    content_type: str = None,
    encoding: str = 'utf8',
    proto: Protocol = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
    type_name: Optional[NameFactory] = None,
) -> T:
    obj = load_file(
        path,
        proto=proto,
        content_type=content_type,
        encoding=encoding,
        allow_pickle=allow_pickle,
        json_loads=json_loads,
    )
    return parse_obj_as(type_, obj, type_name=type_name)


def parse_raw_as(
    type_: Type[T],
    b: StrBytes,
    *,
    content_type: str = None,
    encoding: str = 'utf8',
    proto: Protocol = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
    type_name: Optional[NameFactory] = None,
) -> T:
    obj = load_str_bytes(
        b,
        proto=proto,
        content_type=content_type,
        encoding=encoding,
        allow_pickle=allow_pickle,
        json_loads=json_loads,
    )
    return parse_obj_as(type_, obj, type_name=type_name)


def create_partial_model(model: Type[BaseModel]) -> Type[BaseModel]:
    """
    Create a version of the model that is suitable for partial validation.
    Useful when working with CRUD operations, and you need to use an
    existing model for a PATCH operation.
    """

    class PartialModel(model):  # type: ignore
        class Config(model.Config):  # type: ignore
            partial = True

    PartialModel.__name__ = model.__name__
    return PartialModel
