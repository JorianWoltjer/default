from default.main import *
from base64 import b64encode, b32encode

    
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
        
        # Base64 encoded
        length = get_encoded_length(prefix, 8, 6)  # Base64 translates 8 bits to 6 bits
        search.append(b64encode(prefix.encode()).decode()[:length])
        info(f"- Base64 {search[-1]!r}")
        # Base32 encoded
        length = get_encoded_length(prefix, 8, 5)  # Base32 translates 8 bits to 5 bits
        search.append(b32encode(prefix.encode()).decode()[:length])
        info(f"- Base32 {search[-1]!r}")
        
        # Do regex search
        grep_args = []
        
        search = '|'.join(re.escape(s) for s in search)

        if ARGS.context is not None:
            grep_args += ["-o"]  # Show match only, and use perl regex
            search = f".{{0,{ARGS.context}}}({search}).{{0,{ARGS.context}}}"
        
        grep_args += ["-a"] if ARGS.all else []  # Match binary (all) files

        command(["grep", "--color=always", "-rE", *grep_args, search], highlight=True, error_message=None)
    
    success("Completed search")


def setup(subparsers):
    parser = subparsers.add_parser('flag', help='Do various simple searches for CTF flags to catch low hanging fruit')
    parser.set_defaults(func=flag)
    
    parser.add_argument('prefix', nargs='?', help=f"Prefix of flag in a CTF{{flag}} format (default: {', '.join(CONFIG.flag_prefixes)})")
    parser.add_argument('--all', '-a', action='store_true', help="Match and print binary files (adds -a to grep)")
    parser.add_argument('--context', '-c', type=int, help="Limit amount of characters to show around match, useful if a file with very long lines matches")
