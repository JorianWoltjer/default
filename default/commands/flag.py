from default.main import *
from base64 import b32encode
from default.lib.base64_search import create_base64_regex


def normalize_prefix(prefix):
    if "{" in prefix or "}" in prefix:
        warning("Found { or } in flag prefix, normalizing for search")
        prefix = prefix.split("{")[0]  # Remove {
        prefix = prefix.split("}")[0]  # Remove }

    prefix += "{}"
    return prefix


def get_encoded_length(s, in_bits, out_bits):
    """Get the length of the encoded value that can be used (last few characters may vary, this function solves that)"""
    s_bits = len(s) * in_bits  # 8 bits per character
    encoded_len = s_bits // out_bits  # Split into 5/6 bit per character
    return encoded_len


def xor(s, key):
    return bytes([c ^ key for c in s])


def rot(s, key):
    """Rotate every byte of s by key, modulo 256"""
    return bytes((c + key) % 256 for c in s)


def chunks(s, length):
    return [s[i:i+length] for i in range(0, len(s), length)]


def to_grep_hex(s):
    """Convert bytes to regex hex format (b"A" -> '\x41')"""
    return ''.join('\\x' + c for c in chunks(s.hex(), 2))


def grep(regex, grep_args=[]):
    if which("rg"):
        command(["rg", "--color=always", *grep_args, regex], highlight=True, error_message=None)
    else:
        command(["grep", "--color=always", "-rE", *grep_args, regex], highlight=True, error_message=None)


def flag(ARGS):
    if ARGS.prefix:  # If specified
        flag_prefixes = [ARGS.prefix]
    else:
        flag_prefixes = CONFIG.flag_prefixes

    flag_prefixes = [normalize_prefix(p) for p in flag_prefixes]

    for prefix in flag_prefixes:
        progress(f"Searching for flags with {prefix} format")

        prefix = prefix[:-1]  # Remove trailing }
        search = []

        # Plain
        search.append(prefix)
        info(f"- {search[-1]!r}")
        # Reversed
        search.append(prefix[::-1])
        info(f"- Reversed {search[-1]!r}")
        # Hex encoded
        search.append(prefix.encode().hex())
        info(f"- Hex {search[-1]!r}")
        # Base32 encoded
        length = get_encoded_length(prefix, 8, 5)  # Base32 translates 8 bits to 5 bits
        search.append(b32encode(prefix.encode()).decode()[:length])
        info(f"- Base32 {search[-1]!r}")

        # Do regex search
        grep_args = []

        regex = '|'.join(re.escape(s) for s in search)

        if ARGS.context is not None:
            grep_args += ["-o"]  # Show match only
            regex = f".{{0,{ARGS.context}}}({regex}).{{0,{ARGS.context}}}"

        grep_args += ["-a"] if ARGS.all else []  # Match binary (all) files

        grep(regex, grep_args)

        # Base64 encoded
        regex = create_base64_regex(prefix.encode())
        info(f"- Base64 (all offsets)")

        if "-o" not in grep_args:
            grep_args += ["-o"]
        grep(regex, grep_args)

    success("Completed search")

    if ARGS.brute_force:
        for prefix in flag_prefixes:
            progress(f"Searching 256 possible keys with {prefix} format")

            prefix = prefix.encode()[:-1]  # To bytes and remove trailing }
            search = []

            # XOR
            for key in range(1, 256):
                search.append(xor(prefix, key))
            info("- XOR")

            # ROT
            for key in range(1, 256):
                search.append(rot(prefix, key))
            info("- ROT")

            search = [to_grep_hex(s) for s in search]
            # Grep with recursive, binary, Perl regex, byte offset and match only
            command(["grep", "--color=always", "-raPbo", '|'.join(search)],  # env=dict(os.environ, LANG="C"),
                    highlight=True, error_message=None)

        success("Completed brute-force search")
        info("Tip: Use `xxd -s +[offset] -l 32 [file]` to see full data from matches")


def setup(subparsers):
    parser = subparsers.add_parser('flag', help='Do various simple searches for CTF flags to catch low hanging fruit')
    parser.set_defaults(func=flag)

    parser.add_argument('prefix', nargs='?', help=f"Prefix of flag in a CTF{{flag}} format (default: {', '.join(CONFIG.flag_prefixes)})")
    parser.add_argument('-a', '--all', action='store_true', help="Match and print binary files (adds -a to grep)")
    parser.add_argument('-b', '--brute-force', action='store_true',
                        help="Try to brute-force XOR and ROT encodings with 256 attempts (may take some time)")
    parser.add_argument('-c', '--context', type=int,
                        help="Limit amount of characters to show around match, useful if a file with very long lines matches")
