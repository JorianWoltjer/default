from default.main import *
import json
import re
from colorama import Fore, Style
import tempfile
from time import sleep

RAW_HASHES_EXT = [".hash", ".txt", ".hashes", ".hashcat", ".john", ""]
NEEDS_CONVERTING = ["7z", "rar", "pkzip", "zip", "office", "oldoffice"
                    "11600", "13600", "17200", "17210", "17220", "17225", "17230", "23700", "23800", "12500", "13000", 
                    "9400", "9500", "9600", "9700", "9710", "9800", "9810", "9820"]
FORCE_NEEDS_CONVERTING = False  # Special for when cracking shadow hash with hashcat


# Helper functions
def wslpath(path):
    if path is None:
        return None
    
    return command(["wslpath", "-w", path], get_output=True).strip().decode()

def fix_json_newlines(data):
    """Remove newlines in JSON strings (bug in nth)"""
    return data.replace(b"\n", b"").replace(b"\r", b"")

def strip_john_hash(hash):
    if type(hash) is list:
        return [strip_john_hash(h) for h in hash]
    
    if ":" in hash:
        hash = hash.split(":")[1]
        if len(hash) <= 4:  # Sanity check
            return ""

    return hash


def crack_hashcat(ARGS, hash_type):
    """Crack hashes using hashcat"""
    # Convert hashes to hashcat format
    if hash_type["john"] in NEEDS_CONVERTING or hash_type["hashcat"] in NEEDS_CONVERTING or FORCE_NEEDS_CONVERTING:
        with open(ARGS.file, "r") as f:  # Read
            hashes = f.read().splitlines()
        with open(ARGS.file, "w") as f:  # Write
            f.write("\n".join(strip_john_hash(hashes)))
    
    windows_hashcat = detect_wsl() and not ARGS.no_wsl and CONFIG.hashcat_windows_path is not None  # Detect WSL
    
    if ARGS.no_cache:  # Remove already cracked passwords from cache
        try:
            if windows_hashcat:
                file = f"'{CONFIG.hashcat_windows_path}\\hashcat.potfile'"
                command(["powershell.exe", f"if (test-path {file}) {{ rm {file} }}"])
            else:
                os.remove(os.path.expanduser("~/.hashcat/hashcat.potfile"))
            success("Removed hashcat.potfile cache")
        except FileNotFoundError:
            pass
    
    if windows_hashcat:
        info("Detected WSL, using powershell.exe to crack hashes for GPU acceleration")
        ARGS.file = wslpath(ARGS.file)
        ARGS.wordlist = wslpath(ARGS.wordlist)
        ARGS.output = wslpath(ARGS.output)
        output_args = f"--outfile {ARGS.output}" if ARGS.output else ""
        progress("Cracking hashes...")
        command(["powershell.exe", "-c", f"cd '{CONFIG.hashcat_windows_path}'; hashcat -m {hash_type['hashcat']} '{ARGS.file}' '{ARGS.wordlist}' {output_args}"], 
                highlight=True, error_message=None)
    else:
        output_args = ["--outfile", ARGS.output] if ARGS.output else []
        progress("Cracking hashes...")
        command(["hashcat", "--force", "-m", str(hash_type['hashcat']), *output_args, ARGS.file, ARGS.wordlist], 
                highlight=True, error_message=None)
    
    success("Finished cracking hashes. Results:")
    if windows_hashcat:
        output = command(["powershell.exe", "-c", f"cd '{CONFIG.hashcat_windows_path}'; hashcat --show -m {hash_type['hashcat']} '{ARGS.file}'"], 
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
            os.remove(os.path.expanduser(f"{CONFIG.john_path}/run/john.pot"))
            success("Removed john.pot cache")
        except FileNotFoundError:
            pass
    
    john_args = [] if hash_type["john"] == "auto" else [f"--format={hash_type['john']}"]
    
    progress("Cracking hashes...")
    command([f'{CONFIG.john_path}/run/john', f"--wordlist={ARGS.wordlist}", *john_args, ARGS.file], highlight=True)

    success("Finished cracking hashes. Results:")
    output = command([f'{CONFIG.john_path}/run/john', '--show', *john_args, ARGS.file], get_output=True)
    if ARGS.output:
        with open(ARGS.output, "wb") as f:
            f.write(output)
    
    return output


def find_hash_type(ARGS, file):
    """Detect hash type using Name-That-Hash"""
    name_that_hash = command(['nth', '-g', '-f', file], get_output=True, error_message="Failed to run Name-That-Hash. Is it installed?")
    name_that_hash = json.loads(fix_json_newlines(name_that_hash))
    
    # If no results
    if not name_that_hash:
        error(f"No hashes found in '{file}'")
    
    # Check if all types are the same
    hash_type = list(name_that_hash.values())[0]
    if not all(value == hash_type for value in name_that_hash.values()):
        error(f"Different hash types detected. Please check '{file}' and try cracking them individually.")
        
    # Filter out hashes that don't have hashcat or john modes
    hash_type = list(filter(lambda d: (not ARGS.john and d['hashcat'] is not None) or (ARGS.john and d['john'] is not None), 
                       hash_type))
        
    if len(hash_type) > 1:
        info("Multiple compatible hash types found, choose a type to use for cracking.")
        for i, detected in enumerate(hash_type):
            padding = 2 - len(str(i+1))
            print(" "*padding + f"{i+1}. {detected['name']}")
        
        types_lower = [detected['name'].lower() for detected in hash_type]
        while True:
            choice = ask_any("What type do you want to use?", default="1")
            if choice.isnumeric() and int(choice) in range(1, len(hash_type)+1):
                choice = int(choice)
                break
            elif choice.lower() in types_lower:
                choice = types_lower.index(choice.lower()) + 1
                break
        
        hash_type = hash_type[choice-1]
    elif len(hash_type) == 1:  # If only one possible hash type
        hash_type = hash_type[0]
    else:  # None found
        return None
    
    return hash_type

def find_shadow_hashes(file):
    with open(file) as f:
        data = f.read()
        
    print(data)
    
    exit()


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
        hash = command([f"{CONFIG.john_path}/run/rar2john", ARGS.file], get_output=True, error_message="Could not extract hash from RAR archive")
        archive_file = ARGS.file
    elif ext == ".zip":  # ZIP archive
        progress("Extracting hash from ZIP archive...")
        hash = command([f"{CONFIG.john_path}/run/zip2john", ARGS.file], get_output=True, error_message="Could not extract hash from ZIP archive")
        archive_file = ARGS.file
    elif ext == ".7z":  # 7z archive
        progress("Extracting hash from 7z archive...")
        hash = command([f"{CONFIG.john_path}/run/7z2john.pl", ARGS.file], get_output=True, error_message="Could not extract hash from 7z archive")
        archive_file = ARGS.file
    elif ext in [".docx", ".docm", ".doc", ".xlsx", ".xlsm", ".xls", ".xlm", ".pptx", ".pptm", ".ppt"]:  # Office document
        progress("Extracting hash from office document...")
        hash = command([f"{CONFIG.john_path}/run/office2john.py", ARGS.file], get_output=True, error_message="Could not extract hash from office document")
        archive_file = ARGS.file
    elif not ARGS.mode and (ext == ".shadow" or basename == "shadow"):  # Linux shadow hashes
        if ARGS.john:  # John the Ripper
            ARGS.mode = "auto"  # John can find the correct hash itself
        else:  # Hashcat
            global FORCE_NEEDS_CONVERTING
            FORCE_NEEDS_CONVERTING = True  # Shadow hash file needs to be converted from john
    elif ext not in RAW_HASHES_EXT:  # Not a raw hash either, so unknown
        error(f"Unknown file type: {ext}. Try making a hash out of it and pass the hash as the argument")
    
    if archive_file:  # If extracted in previous part
        ARGS.file = archive_file + ".hash"
        with open(ARGS.file, "wb") as f:
            f.write(hash)
        
        success(f"Wrote hash to '{ARGS.file}'")
    
    # Get hashes and types
    with open(ARGS.file) as f:  # File must be a raw hash at this point
        hashes = [l for l in f.read().splitlines() if l]  # Read non-empty lines
    
    multiple = '' if len(hashes) == 1 else "es"  # Pluralize
    info(f"Found {len(hashes)} hash{multiple} in '{ARGS.file}'")
    if len(hashes) == 0:
        error("No hashes found in file")
    
    if not ARGS.mode:  # If mode not forced
        progress("Detecting hash type...") 
        hash_type = find_hash_type(ARGS, ARGS.file)
        if hash_type is None:  # Retry
            info("Hash type was not hashcat format, converting from john and trying again")
            
             # Convert to hashcat format
            with open(ARGS.file, "r") as f:  # Read
                hashes = f.read().splitlines()
                
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write("\n".join(strip_john_hash(hashes)).encode())
                
            hash_type = find_hash_type(ARGS, tmp.name)
            if hash_type is None:
                if archive_file:
                    error(f"Could not detect hash type of '{ARGS.file}', but it should. Make sure you have the **newest** version of Name-That-Hash installed, I only added these hashes very recently.")
                else:
                    error(f"Could not detect hash type of '{ARGS.file}'. Try manually setting the hash type with --mode")
            
        success(f"Detected hash type: {hash_type['name']}")
        sleep(1)  # Wait a second to show hash type
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


def setup(subparsers):
    parser = subparsers.add_parser('crack', help='Crack a password hash')
    parser.set_defaults(func=crack)
    
    parser.add_argument('file', type=PathType(), help='File with the hash to crack (.txt or .hash for raw hashes)')
    parser.add_argument('-w', '--wordlist', type=PathType(), help='Wordlist to use', default=CONFIG.password_list)
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('-m', '--mode', help='Force hash mode/format for hashcat or john')
    parser.add_argument('-j', '--john', help='Use John the Ripper for cracking instead of hashcat', action='store_true')
    parser.add_argument('-n', '--no-cache', help='Remove any cache files before running (mostly used for testing)', action='store_true')
    parser.add_argument('-W', '--no-wsl', help='Disable automatic Windows Subsystem Linux detection, force linux hashcat', action='store_true')
