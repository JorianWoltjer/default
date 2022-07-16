from main import *
from config import FLAG_PREFIXES
from base64 import b64encode, b32encode


def search(ARGS, value):
    if type(value) == bytes:  # Decode if bytes
        value = value.decode()
        
    grep_args = []

    if ARGS.context != None:
        grep_args += ["-o", "-P"]  # Show match only, and use perl regex
        value = f".{{0,{ARGS.context}}}{re.escape(value)}.{{0,{ARGS.context}}}"
    
    grep_args += ["-a"] if ARGS.all else []  # Match binary (all) files

    command(["grep", "--color=always", "-r", *grep_args, value], highlight=True, error_message=None)
    
def normalize_prefix(prefix):
    if "{" in prefix or "}" in prefix:
        warning("Found { or } in flag prefix, normalizing for search")
        prefix = prefix.split("{")[0]  # Remove {
        prefix = prefix.split("}")[0]  # Remove }
    
    prefix += "{}"
    return prefix


def flag(ARGS):
    global FLAG_PREFIXES
    
    if ARGS.prefix:  # If specified
        FLAG_PREFIXES = [ARGS.prefix]
        
    FLAG_PREFIXES = [normalize_prefix(p) for p in FLAG_PREFIXES]
    
    info(f"Searching for flags with the following formats:", ', '.join(FLAG_PREFIXES))
    
    for prefix in FLAG_PREFIXES:
        prefix = prefix[:-1]  # Remove trailing }
        
        # Plain
        progress(f"Searching for '{prefix}'")
        search(ARGS, prefix)
        # Reversed
        progress(f"Searching for reversed '{prefix}'")
        search(ARGS, prefix[::-1])
        
        # TODO: Find out how many characters we can search max
        # Base64 encoded
        progress(f"Searching for base64 '{prefix}'")
        base64_prefix = b64encode(prefix.encode()).replace(b"=", b"")
        base64_prefix = base64_prefix[:len(base64_prefix) - len(base64_prefix) % 4]  # Cut off last unfinished chunk
        search(ARGS, base64_prefix)
        # Base32 encoded
        progress(f"Searching for base32 '{prefix}'")
        base32_prefix = b32encode(prefix.encode()).replace(b"=", b"")
        base32_prefix = base32_prefix[:len(base32_prefix) - len(base32_prefix) % 7]  # Cut off last unfinished chunk
        if len(prefix) < 5:  # Unsure about last character
            base32_prefix = base32_prefix[:-1]
        search(ARGS, base32_prefix)


def setup(subparsers):
    parser = subparsers.add_parser('flag', help='Do various simple searches for CTF flags to catch low hanging fruit')
    parser.set_defaults(func=flag)
    
    parser.add_argument('prefix', nargs='?', help=f"Prefix of flag in a CTF{{flag}} format (default: {', '.join(FLAG_PREFIXES)})")
    parser.add_argument('--all', '-a', action='store_true', help="Match and print binary files (adds -a to grep)")
    parser.add_argument('--context', '-c', type=int, help="Limit amount of characters to show around match, useful if a file with very long lines matches")
