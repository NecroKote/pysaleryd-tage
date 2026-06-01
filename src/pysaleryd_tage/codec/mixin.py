from .codec import data_decode, data_encode
from .field import FieldDescriptor


class DecodeableFieldsObject:
    decode_field_map: dict[str, FieldDescriptor]

    @classmethod
    def get_decode_field_map(cls) -> dict[str, FieldDescriptor]:
        return cls.decode_field_map

    @classmethod
    def decode(cls, data: bytes) -> dict[str, int | str | list[int]]:
        state = {}
        data_decode(data, cls.get_decode_field_map(), state)
        return state


class EncodeableFieldsObject:
    encode_field_map: dict[str, FieldDescriptor]

    @classmethod
    def get_encode_field_map(cls) -> dict[str, FieldDescriptor]:
        return cls.encode_field_map

    @classmethod
    def encode(cls, state: dict[str, int | str | list[int]]) -> bytes:
        return data_encode(cls.get_encode_field_map(), state)
