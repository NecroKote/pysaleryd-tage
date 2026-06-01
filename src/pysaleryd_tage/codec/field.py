from dataclasses import dataclass
from enum import StrEnum
from typing import Callable


class FieldType(StrEnum):
    INT = "int"
    STRING = "string"
    ARRAY = "array"


@dataclass
class FieldDescriptor:
    start_bit: int
    length: int
    signed: bool
    type: FieldType
    length_per_element: int | None = None


class FieldMapBuilder:
    def __init__(self):
        self.field_map: dict[str, FieldDescriptor] = {}
        self._offset = 0

    def add_field(
        self,
        name: str,
        length: int,
        signed: bool = False,
        type: FieldType = FieldType.INT,
        length_per_item: int | None = None,
    ):
        descriptor = FieldDescriptor(
            self._offset, length, signed, type, length_per_item
        )
        self.field_map[name] = descriptor
        self._offset += length
        return self

    def add_stub(self, length: int):
        self._offset += length
        return self

    def apply(self, func: Callable[["FieldMapBuilder"], None]):
        func(self)
        return self

    @property
    def offset(self):
        return self._offset

    def offset_to(self, offset: int):
        self._offset = offset
        return self

    def build(self):
        return self.field_map

    def __enter__(self):
        return self
