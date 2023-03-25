import re

BASE64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def to_binary(s):
    return ''.join(f"{c:08b}" for c in s)


def fill_possible_ends(binary):
    if len(binary) == 6:
        yield binary
    else:
        yield from fill_possible_ends(binary + "0")
        yield from fill_possible_ends(binary + "1")


def fill_possible_starts(binary):
    if len(binary) == 6:
        yield binary
    else:
        yield from fill_possible_starts("0" + binary)
        yield from fill_possible_starts("1" + binary)


def create_one_base64_regex(binary):
    result = r''
    for i in range(0, len(binary), 6):
        chunk = binary[i:i + 6]

        if len(chunk) < 6:
            return result, len(chunk)
        else:
            result += BASE64[int(chunk, 2)]

    return result, 0


def create_base64_regex(s):
    """Create a strict regex for finding `s` encoded in base64"""
    binary = to_binary(s)

    before = {
        0: 0,
        2: 2,
        4: 1,
    }

    matchers = []
    for shift in [0, 2, 4]:
        shifted = binary[shift:]

        if shift > 0:
            prefix = fill_possible_starts(binary[:shift])
            prefix = ''.join(re.escape(BASE64[int(c, 2)]) for c in prefix)

            regex = f'[A-z0-9+/]{{{before[shift]}}}[{prefix}]'
        else:
            regex = ''

        one, leftover = create_one_base64_regex(shifted)
        regex += one

        if leftover > 0:
            suffix = fill_possible_ends(binary[-leftover:])
            suffix = ''.join(re.escape(BASE64[int(c, 2)]) for c in suffix)
            regex += f'[{suffix}]'

        matchers.append(regex)

    return f'({"|".join(matchers)})[A-z0-9+/]*'


if __name__ == "__main__":
    print(create_base64_regex(b"CTF{"))
    # (Q1RGe[wxyz0123456789\+/]|[A-z0-9+/]{2}[AgQw]DVEZ7|[A-z0-9+/]{1}[AgQwIoY4EkU0Msc8]NURn[stuv])[A-z0-9+/]*
