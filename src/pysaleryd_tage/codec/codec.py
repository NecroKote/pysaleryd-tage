from typing import Any, Dict, MutableMapping, cast

from .field import FieldDescriptor, FieldType


def data_decode(
    data: bytes,
    type_map: Dict[str, FieldDescriptor],
    destination: MutableMapping[str, Any],
):
    for key, descriptor in type_map.items():
        end_bit = descriptor.start_bit + descriptor.length

        try:
            match descriptor.type:
                case FieldType.INT:
                    value = 0
                    for i in range(end_bit - 1, descriptor.start_bit - 1, -1):
                        byte_index = i // 8
                        bit_index = i % 8
                        value = (value << 1) | ((data[byte_index] >> bit_index) & 1)

                    if descriptor.signed and (value & (1 << (descriptor.length - 1))):
                        value -= 1 << descriptor.length

                    destination[key] = value

                case FieldType.STRING:
                    byte_start = descriptor.start_bit // 8
                    byte_end = end_bit // 8
                    destination[key] = (
                        data[byte_start:byte_end].decode("utf-8").replace("\0", "")
                    )

                case FieldType.ARRAY:
                    length_per_element = cast(int, descriptor.length_per_element)
                    items = []
                    num_elements = descriptor.length // length_per_element

                    # take subarray from data, that has only bits for this array
                    byte_start, byte_end = descriptor.start_bit // 8, end_bit // 8
                    bit_offset = descriptor.start_bit % 8
                    end_bit_offset = end_bit % 8
                    if end_bit_offset != 0:
                        byte_end += 1

                    array_data = data[byte_start:byte_end]

                    # Saleryd's code has a weird bug where advertised DeviceHeader size is
                    # smaller than actual size, so sometimes we get less data than expected.
                    # HACK: so we fill in the missing rest with zeroes
                    expected_byte_size = byte_end - byte_start
                    if len(array_data) < expected_byte_size:
                        array_data += b"\x00" * (expected_byte_size - len(array_data))

                    # combine bits into elements
                    for i in range(num_elements):
                        element = 0
                        for j in range(length_per_element):
                            bit_index = bit_offset + i * length_per_element + j
                            byte_index = bit_index // 8
                            bit_position = 7 - (bit_index % 8)
                            element = (element << 1) | (
                                (array_data[byte_index] >> bit_position) & 1
                            )

                        if descriptor.signed and (
                            element & (1 << (length_per_element - 1))
                        ):
                            element -= 1 << length_per_element

                        items.append(element)

                    destination[key] = items
        except Exception as e:
            raise RuntimeError(f"Error decoding {key}: {e}. {descriptor!r}") from e


def data_encode(
    type_map: Dict[str, FieldDescriptor],
    source: Dict[str, Any],
) -> bytes:
    # find final length of data
    bit_length = sum(x.length for x in type_map.values())
    result = bytearray(bit_length // 8)

    global_bit_pos = 0
    for key, descriptor in type_map.items():
        if (value := source.get(key)) is None:
            global_bit_pos += descriptor.length
            continue

        byte_pos = global_bit_pos // 8
        local_bit_pos = global_bit_pos % 8

        try:
            match descriptor.type:
                case FieldType.INT:
                    e = 0
                    for t in range(descriptor.length):
                        i = (value >> t) & 1
                        result[byte_pos] |= i << local_bit_pos + e
                        e += 1
                        if e >= 8:
                            e = 0
                            byte_pos += 1

                        global_bit_pos += 1

                case FieldType.STRING:
                    byte_start = descriptor.start_bit // 8
                    byte_end = (descriptor.start_bit + descriptor.length) // 8
                    data = value.encode("utf-8")
                    for i, pos in enumerate(range(byte_start, byte_end)):
                        if i >= len(data):
                            break
                        result[pos] = data[i]
                    global_bit_pos += descriptor.length

                case FieldType.ARRAY:
                    length_per_element = cast(int, descriptor.length_per_element)
                    num_elements = descriptor.length // length_per_element

                    for i in range(num_elements):
                        result[byte_pos] = value[i]
                        byte_pos += 1
                        global_bit_pos += length_per_element

        except Exception as e:
            raise RuntimeError(f"Error encoding {key}: {e}. {descriptor!r}") from e

    return bytes(result)
