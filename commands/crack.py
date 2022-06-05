from main import *
from config import JOHN_RUN_PATH, WORDLIST_PATH, HASHCAT_WINDOWS_PATH
import json
import re
from colorama import Fore, Style


def wslpath(path):
    if path == None:
        return None
    
    return command(["wslpath", "-w", path], get_output=True).strip().decode()

def fix_json_newlines(data):
    """Remove newlines in JSON strings (bug in nth)"""
    prev = b""
    while True:  # Remove one at a time
        data = re.sub(rb'("[^"\n]*)\r?\n(?!(([^"]*"){2})*[^"]*$)', rb'\1', data)
        if data == prev:
            return data
        prev = data

def crack(ARGS):
    if ARGS.output and os.path.exists(ARGS.output):
        choice = ask(f"Crack output file '{ARGS.output}' already exists, do you want to overwrite it?")
        if choice:
            os.remove(ARGS.output)
        else:
            exit(1)
    
    # Get hashes
    basename, ext = os.path.splitext(ARGS.file)
    if ext == ".txt" or ext == ".hash":  # Raw hashes
        with open(ARGS.file) as f:
            hashes = f.read().splitlines()
            hashes_count = len(hashes)
        
        multiple = 'es' if len(hashes) > 1 else ""
        info(f"Found {len(hashes)} hash{multiple} in '{ARGS.file}'")
        
        if not ARGS.mode:
            # Detect hash type
            progress("Detecting hash type...") 
            name_that_hash = command(['nth', '-g', '-f', ARGS.file], get_output=True, error_message="Could not detect hash type. Is name-that-hash installed and updated?")
            name_that_hash = json.loads(fix_json_newlines(name_that_hash))
            first = name_that_hash[hashes[0]]
            for detected in first:
                if 'hashcat' in detected:
                    hash_type = detected
                    break
                elif 'john' in detected:
                    hash_type = detected
                    ARGS.john = True
                    info(f"Hash only crackable with john")
                    break
            else:
                error("Could not detect hash type")
            
            success(f"Detected hash type: {hash_type['name']}")
        else:  # Force mode
            hash_type = {
                'hashcat': ARGS.mode,
                'john': ARGS.mode
            }
    else:
        if ext == ".rar":  # RAR archive
            progress("Extracting hash from RAR archive...")
            hash = command([f"{JOHN_RUN_PATH}/rar2john", ARGS.file], get_output=True, error_message="Could not extract hash from rar archive")
            if not ARGS.john:
                hash = hash.split(b":")[1]  # Convert john to hashcat (remove filename)
            
            ARGS.original_file = ARGS.file
            ARGS.file += ".hash"
            with open(ARGS.file, "wb") as f:
                f.write(hash)
                hashes_count = 1
            
            success(f"Wrote hash to '{ARGS.file}'")
            hash_type = {
                'hashcat': 13000,
                'john': 'rar5'
            }
        elif ext == ".zip":
            info("Note: This is a temporary workaround for detecting zip files, if you have problems try using the --mode option to force a hash type")
            # https://hashcat.net/wiki/doku.php?id=example_hashes
            zip_types = {  # TODO: Will add these to Name-That-Hash later
                b"$zip2$": {"hashcat": 13600, "john": "zip"},
                b"$pkzip2$": {"hashcat": 17200, "john": "zip"},  #! Not always correct, only for normal compressed zip
            }
            progress("Extracting hash from ZIP archive...")
            hash = command([f"{JOHN_RUN_PATH}/zip2john", ARGS.file], get_output=True, error_message="Could not extract hash from zip archive")
            
            #! Temporary, until Name-That-Hash supports zip types
            if not ARGS.mode:
                for zip_type in zip_types:
                    if hash.split(b":")[1].startswith(zip_type):
                        hash_type = zip_types[zip_type]
                        break
                else:
                    error("Could not detect hash type")
            
            if not ARGS.john:
                hash = hash.split(b":")[1]  # Convert john to hashcat (remove filename)
                
            ARGS.original_file = ARGS.file
            ARGS.file += ".hash"
            with open(ARGS.file, "wb") as f:
                f.write(hash)
                hashes_count = 1
            
            success(f"Wrote hash to '{ARGS.file}'")
    
    # Crack hashes
    if ARGS.john:  # John the Ripper
        if ARGS.no_cache:  # Remove already cracked passwords from cache
            try:
                os.remove(os.path.expanduser(f"{JOHN_RUN_PATH}/john.pot"))
                success("Removed john.pot")
            except FileNotFoundError:
                pass
        
        progress("Cracking hashes...")
        command([f'{JOHN_RUN_PATH}/john', f"--wordlist={ARGS.wordlist}", f"--format={hash_type['john']}", ARGS.file], highlight=True)

        success("Finished cracking hashes. Results:")
        output = command([f'{JOHN_RUN_PATH}/john', '--show', f"--format={hash_type['john']}", ARGS.file], get_output=True)
        if ARGS.output:
            with open(ARGS.output, "wb") as f:
                f.write(output)
        
        output_parts = output.split(b"\n\n")
        if len(output_parts) > 1:
            print(f"{Fore.RED}{output_parts[0].decode()}{Style.RESET_ALL}")
        cracked_count = int(re.findall(r"(\d+) password hash(?:es)? cracked, (\d+) left", output_parts[-1].decode())[0][0])
        success(f"Cracked {cracked_count}/{hashes_count} hashes")
    else:  # Hashcat (default)
        is_wsl = os.path.exists("/mnt/c/Windows")  # Detect WSL
        
        if ARGS.no_cache:  # Remove already cracked passwords from cache
            try:
                if is_wsl:
                    command(["powershell.exe", f"rm '{HASHCAT_WINDOWS_PATH}\\hashcat.potfile'"])
                else:
                    os.remove(os.path.expanduser("~/.hashcat/hashcat.potfile"))
                success("Removed hashcat.potfile")
            except FileNotFoundError:
                pass
        
        if is_wsl:
            info("Detected WSL, using powershell.exe to crack hashes for GPU acceleration")
            ARGS.file = wslpath(ARGS.file)
            ARGS.wordlist = wslpath(ARGS.wordlist)
            ARGS.output = wslpath(ARGS.output)
            output_args = f"--outfile {ARGS.output}" if ARGS.output else ""
            progress("Cracking hashes...")
            command(["powershell.exe", "-c", f"cd '{HASHCAT_WINDOWS_PATH}'; hashcat -m {hash_type['hashcat']} '{ARGS.file}' '{ARGS.wordlist}' {output_args}"], 
                    highlight=True, error_message=None)
        else:
            output_args = ["--outfile", ARGS.output] if ARGS.output else []
            progress("Cracking hashes...")
            command(["hashcat", "--force", "-m", str(hash_type['hashcat']), *output_args, ARGS.file, ARGS.wordlist], 
                    highlight=True, error_message=None)
        
        success("Finished cracking hashes. Results:")
        if is_wsl:
            output = command(["powershell.exe", "-c", f"cd '{HASHCAT_WINDOWS_PATH}'; hashcat --show -m {hash_type['hashcat']} '{ARGS.file}'"], 
                    get_output=True, error_message="Failed to crack hashes")
        else:
            output = command(["hashcat", "--show", "-m", str(hash_type['hashcat']), ARGS.file], 
                    get_output=True, error_message="Failed to crack hashes")
        
        if ARGS.output:
            with open(ARGS.output, "wb") as f:
                f.write(output)
        
        print(f"{Fore.RED}{output.decode()}{Style.RESET_ALL}")
        cracked_count = len(output.split(b"\n")) - 1
        success(f"Cracked {cracked_count}/{hashes_count} hashes")
    
    # Automatically extract archives with password
    if ext == ".rar" and cracked_count > 0:
        choice = ask("Found password for RAR archive. Do you want to extract it?")
        if choice:
            progress("Extracting archive with found password...")
            password = output.split(b":")[1].split(b"\n")[0].decode().strip()
            command(["mkdir", "-p", basename])
            command(["unrar", "x", "../"+ARGS.original_file, f"-p{password}", "-o+"], cwd=basename, 
                    error_message="Failed to extract archive with password, try extracting manually")
            success(f"Extracted RAR archive to {basename}")
    elif ext == ".zip" and cracked_count > 0:
        choice = ask("Found password for ZIP archive. Do you want to extract it?")
        if choice:
            progress("Extracting archive with found password...")
            password = output.split(b":")[1].split(b"\n")[0].decode().strip()
            command(["7z", "x", ARGS.original_file, f"-p{password}", f"-o{basename}", "-aoa"], 
                    error_message="Failed to extract archive with password, try extracting manually")
            success(f"Extracted ZIP archive to {basename}")


import sys  # Import live values from main.py
__main__ = sys.modules['__main__']

parser_crack = __main__.subparsers.add_parser('crack', help='Crack a password hash')
parser_crack.set_defaults(func=crack)
parser_crack.add_argument('file', type=PathType(), help='File with the hash to crack (.txt or .hash for raw hashes)')
parser_crack.add_argument('-w', '--wordlist', type=PathType(), help='Wordlist to use', default=f"{WORDLIST_PATH}/rockyou.txt")
parser_crack.add_argument('-o', '--output', help='Output file')
parser_crack.add_argument('-m', '--mode', help='Force hash mode/format for hashcat or john')
parser_crack.add_argument('-j', '--john', help='Use John the Ripper for cracking instead of hashcat', action='store_true')
parser_crack.add_argument('-n', '--no-cache', help='Remove any cache files before running (mostly used for testing)', action='store_true')
