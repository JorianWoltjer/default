from main import *
from config import JOHN_RUN_PATH, WORDLIST_PATH, HASHCAT_WINDOWS_PATH
import json
import re
from colorama import Fore, Style
import tempfile

RAW_HASHES_EXT = [".hash", ".txt", ".hashes", ".hashcat", ".john", ""]
NEEDS_CONVERTING = ["7z", "rar", "pkzip", "zip", "11600", "13600", "17200", "17210", "17220", "17225", "17230", "23700", "23800", "12500", "13000"]


# Helper functions
def wslpath(path):
    if path == None:
        return None
    
    return command(["wslpath", "-w", path], get_output=True).strip().decode()

def fix_json_newlines(data):
    """Remove newlines in JSON strings (bug in nth)"""
    return data.replace(b"\n", b"").replace(b"\r", b"")

def strip_john_hash(hashes):
    if type(hashes) is list:
        return [strip_john_hash(h) for h in hashes]
    
    if ":" in hashes:
        return hashes.split(":")[1]
    return hashes


def crack_hashcat(ARGS, hash_type):
    """Crack hashes using hashcat"""
    # Convert hashes to hashcat format
    if hash_type["john"] in NEEDS_CONVERTING or hash_type["hashcat"] in NEEDS_CONVERTING:
        with open(ARGS.file, "r") as f:  # Read
            hashes = f.read().splitlines()
        with open(ARGS.file, "w") as f:  # Write
            f.write("\n".join(strip_john_hash(hashes)))
    
    is_wsl = os.path.exists("/mnt/c/Windows")  # Detect WSL
    
    if ARGS.no_cache:  # Remove already cracked passwords from cache
        try:
            if is_wsl:
                file = f"'{HASHCAT_WINDOWS_PATH}\\hashcat.potfile'"
                command(["powershell.exe", f"if (test-path {file}) {{ rm {file} }}"])
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
    
    return output


def crack_john(ARGS, hash_type):
    """Crack hashes using John the Ripper"""
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
    
    return output


def find_hash_type(file):
    """Detect hash type using Name-That-Hash"""
    name_that_hash = command(['nth', '-g', '-f', file], get_output=True, error_message="Failed to run Name-That-Hash. Is it installed?")
    name_that_hash = json.loads(fix_json_newlines(name_that_hash))
    
    hash_type = None
    for hash in name_that_hash.values():
        for detected in hash:
            if 'hashcat' in detected:
                if hash_type != None and hash_type != detected:  # If not first iteration, and hash type is different from previous
                    error(f"Multiple hash types detected. Please check '{file}' and try cracking them individually.")
                hash_type = detected
                break
            elif 'john' in detected:
                if hash_type != None and hash_type != detected:  # If not first iteration, and hash type is different from previous
                    error(f"Multiple hash types detected. Please check '{file}' and try cracking them individually.")
                hash_type = detected
                if not ARGS.john:  # If only crackable with john, ask to switch to john
                    choice = ask(f"{hash_type['name']} is only crackable with john, want to force john instead of hashcat?")
                    if choice:
                        ARGS.john = True
                    else:
                        exit(1)
                break
        else:
            return None
    
    return hash_type


def crack(ARGS):
    if ARGS.output and os.path.exists(ARGS.output):
        choice = ask(f"Crack output file '{ARGS.output}' already exists, do you want to overwrite it?")
        if choice:
            os.remove(ARGS.output)
        else:
            exit(1)
    
    basename, ext = os.path.splitext(ARGS.file)
    
    # Extract hash automatically
    archive_file = None
    if ext == ".rar":  # RAR archive
        progress("Extracting hash from RAR archive...")
        hash = command([f"{JOHN_RUN_PATH}/rar2john", ARGS.file], get_output=True, error_message="Could not extract hash from RAR archive")
        archive_file = ARGS.file
    elif ext == ".zip":  # ZIP archive
        progress("Extracting hash from ZIP archive...")
        hash = command([f"{JOHN_RUN_PATH}/zip2john", ARGS.file], get_output=True, error_message="Could not extract hash from ZIP archive")
        archive_file = ARGS.file
    elif ext == ".7z":  # 7z archive
        progress("Extracting hash from 7z archive...")
        hash = command([f"{JOHN_RUN_PATH}/7z2john.pl", ARGS.file], get_output=True, error_message="Could not extract hash from 7z archive")
        archive_file = ARGS.file
    elif ext not in RAW_HASHES_EXT:  # Not a raw hash either, so unknown
        error(f"Unknown file type: {ext}. Try making a hash out of it and pass the hash as the argument")
    
    if archive_file:  # If extracted in previous part
        ARGS.file = archive_file + ".hash"
        with open(ARGS.file, "wb") as f:
            f.write(hash)
        
        success(f"Wrote hash to '{ARGS.file}'")
    
    # Get hashes and types
    with open(ARGS.file) as f:  # File must be a raw hash at this point
        hashes = f.read().splitlines()
    
    multiple = '' if len(hashes) == 1 else "es"  # Pluralize
    info(f"Found {len(hashes)} hash{multiple} in '{ARGS.file}'")
    if len(hashes) == 0:
        error("No hashes found in file")
    
    if not ARGS.mode:  # If mode not forced
        progress("Detecting hash type...") 
        hash_type = find_hash_type(ARGS.file)
        if hash_type == None:  # Retry
            info("Hash type was not hashcat format, converting from john and trying again")
            
             # Convert to hashcat format
            with open(ARGS.file, "r") as f:  # Read
                hashes = f.read().splitlines()
                
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write("\n".join(strip_john_hash(hashes)).encode())
                
            hash_type = find_hash_type(tmp.name)
            if hash_type == None:
                if archive_file:
                    error(f"Could not detect hash type of '{ARGS.file}', but it should. Make sure you have the **newest** version of Name-That-Hash installed, I only added these hashes very recently.")
                else:
                    error(f"Could not detect hash type of '{ARGS.file}'. Try manutally setting the hash type with --mode")
            
        success(f"Detected hash type: {hash_type['name']}")
    else:  # Force mode
        hash_type = {
            'hashcat': ARGS.mode,
            'john': ARGS.mode
        }
    
    # Crack hashes
    if ARGS.john:  # John the Ripper
        output = crack_john(ARGS, hash_type)
        
        output_parts = output.split(b"\n\n")
        if len(output_parts) > 1:
            print(f"{Fore.RED}{output_parts[0].decode()}{Style.RESET_ALL}")
        cracked_count = int(re.findall(r"(\d+) password hash(?:es)? cracked, (\d+) left", output_parts[-1].decode())[0][0])
        success(f"Cracked {cracked_count}/{len(hashes)} hashes")
    else:  # Hashcat (default)
        output = crack_hashcat(ARGS, hash_type)
        
        print(f"{Fore.RED}{output.decode()}{Style.RESET_ALL}")
        cracked_count = len(output.split(b"\n")) - 1
        success(f"Cracked {cracked_count}/{len(hashes)} hashes")
    
    # Automatically extract archives with found password
    if ext == ".rar" and cracked_count > 0:
        choice = ask("Found password for RAR archive. Do you want to extract it?")
        if choice:
            progress("Extracting archive with found password...")
            password = output.split(b":")[1].split(b"\n")[0].decode().strip()
            command(["mkdir", "-p", basename])
            command(["unrar", "x", "../"+archive_file, f"-p{password}", "-o+"], cwd=basename, 
                    error_message="Failed to extract archive with password, try extracting manually")
            success(f"Extracted RAR archive to {basename}")
    elif ext == ".zip" and cracked_count > 0:
        choice = ask("Found password for ZIP archive. Do you want to extract it?")
        if choice:
            progress("Extracting archive with found password...")
            password = output.split(b":")[1].split(b"\n")[0].decode().strip()
            command(["7z", "x", archive_file, f"-p{password}", f"-o{basename}", "-aoa"], 
                    error_message="Failed to extract archive with password, try extracting manually")
            success(f"Extracted ZIP archive to {basename}")
    elif ext == ".7z" and cracked_count > 0:
        choice = ask("Found password for 7z archive. Do you want to extract it?")
        if choice:
            progress("Extracting archive with found password...")
            password = output.split(b":")[1].split(b"\n")[0].decode().strip()
            command(["7z", "x", archive_file, f"-p{password}", f"-o{basename}", "-aoa"], 
                    error_message="Failed to extract archive with password, try extracting manually")
            success(f"Extracted 7z archive to {basename}")


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
