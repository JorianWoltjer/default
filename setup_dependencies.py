#!/bin/python3
from default.main import *
from shutil import which
from urllib.parse import urlparse
import json
import glob
import os


def save_config(key, value):
    config = json.load(open(f"{DIR}/config.json"))
    config[key] = value
    json.dump(config, open(f"{DIR}/config.json", "w"), indent=4)


def install_nth():
    progress("Installing name-that-hash from custom fork...")
    command(["pip", "install", "git+https://github.com/JorianWoltjer/Name-That-Hash.git"], highlight=True)
    success("Installed name-that-hash")


def is_valid_john(path):
    """Checks if a path is a valid John the Ripper Jumbo clone, and returns the path to the root folder"""
    if path is None:  # If not set
        return False

    if os.path.exists(f"{path}/run/zip2john"):
        return path.rstrip("/")  # Remove trailing slashes

    for sub in ["run", "src", "doc"]:  # If specified a subdirectory or path
        split = path.split(f"/{sub}")
        if len(split) > 1:
            return split[0]

    return False


def main():
    apt_dependencies = {
        # which        apt
        "procyon":   "procyon-decompiler",
        "apktool":   "apktool",
        "apksigner": "apksigner",
        "zipalign":  "zipalign",
        "nmap":      "nmap",
        "masscan":   "masscan",
        "unzip":     "unzip",
        "hashcat":   "hashcat",
    }

    progress("Checking installed apt packages...")
    not_installed = []
    for tool in apt_dependencies.keys():
        if which(tool):
            success(f"{tool} is already installed")
        else:
            warning(f"{tool} is not yet installed")
            not_installed.append(apt_dependencies[tool])

    if not_installed:  # If any dependencies missing
        progress("Some packages missing, installing with apt...")
        command(["sudo", "apt", "install", *not_installed], highlight=True,
                error_message="Failed to install packages")

        success("Installed required packages")

    if which("ffuf") is None:  # ffuf
        warning("ffuf is not yet installed")
        if which("go") is None:
            warning("go is not yet installed. Install the latest version manually following the instructions on https://go.dev/doc/install. Make sure 'go' is in the PATH and run this setup again")
        else:
            progress("Installing ffuf with go...")
            command(["go", "install", "github.com/ffuf/ffuf@latest"],
                    error_message="Failed to install ffuf using go, check if go is updated or try it manually")
            success("Installed ffuf")
    else:
        success("ffuf is already installed")
        
    if which("x8") is None:  # x8
        warning("x8 is not yet installed")
        if which("cargo") is None:
            warning("cargo is not yet installed. Install the latest version manually following the instructions on https://doc.rust-lang.org/cargo/getting-started/installation.html. Make sure 'cargo' is in the PATH and run this setup again")
        else:
            progress("Installing x8 with cargo...")
            command(["cargo", "install", "x8"],
                    error_message="Failed to install x8 using cargo, check if cargo is updated or try it manually")
            success("Installed x8")
    else:
        success("x8 is already installed")

    print()
    progress("Checking other dependencies")
    if which("nth") is None:  # Name That Hash
        warning("name-that-hash is not yet installed")
        install_nth()
    else:
        success("name-that-hash is already installed")
        progress("Checking if the custom fork of name-that-hash is installed...")
        test_hash = "$RAR3$*0*45109af8ab5f297a*adbf6c5385d7a40373e8f77d7b89d317"  # Test if this RAR hash gets recognized (only custom fork does)
        output = command(["nth", "-g", "-t", test_hash], get_output=True)
        output = json.loads(output)
        if output[test_hash]:
            success("Verified custom fork is already installed")
        else:
            warning("Normal version of name-that-hash installed, but custom fork is required")
            progress("Removing normal version...")
            command(["pip", "uninstall", "name-that-hash"], highlight=True)
            success("Successfully removed normal version of name-that-hash")
            install_nth()

    if glob.glob(f"{LIBRARY_DIR}/dex*"):
        success("dex2jar is already installed")
    else:
        warning("dex2jar is not yet installed")
        progress("Installing latest release of dex2jar...")
        output = command(["curl", "-s", "https://api.github.com/repos/pxb1988/dex2jar/releases/latest"], get_output=True)
        output = json.loads(output)
        latest_release = output["assets"][0]["browser_download_url"]
        filename = os.path.basename(urlparse(latest_release).path)
        command(["wget", "-q", "--show-progress", latest_release, "-O", f"{LIBRARY_DIR}/{filename}"])  # Download
        command(["unzip", "-q", f"{LIBRARY_DIR}/{filename}", "-d", LIBRARY_DIR])  # Unzip
        unzipped = glob.glob(f"{LIBRARY_DIR}/dex-tools*")[0]
        command(["mv", unzipped, f"{LIBRARY_DIR}/dex-tools"])  # Remove version number
        os.remove(f"{LIBRARY_DIR}/{filename}")
        success("Successfully installed dex2jar")

    print()
    progress("Checking if config.json is set correctly...")

    valid_path = is_valid_john(CONFIG.john_path)
    if valid_path:  # Test if zip2john is found
        success("john is already installed and configured")
        if valid_path != CONFIG.john_path:
            warning(f"Config path was not the root path to john, updating to {valid_path}")
            save_config("john_path", valid_path)
    else:
        directory = ask_any("John the Ripper Jumbo is not yet configured. Enter the directory of john or where it should be installed", default="~/john")
        directory = os.path.expanduser(directory)
        valid_path = is_valid_john(directory)
        if valid_path:  # Test if already cloned
            success("john is already installed in this directory, updated config")
            save_config("john_path", valid_path)
        else:
            info("john is not yet installed in this directory")
            progress(f"Cloning John the Ripper Jumbo to {directory}...")
            # Clone
            command(["git", "clone", "https://github.com/openwall/john.git", directory])
            progress("Building John the Ripper Jumbo...")
            # Build
            command(["./configure"], cwd=f"{directory}/src")
            command(["make", "-s", "clean"], cwd=f"{directory}/src")
            command(["make", "-sj4"], cwd=f"{directory}/src")

            save_config("john_path", directory)
            success("Successfully cloned and configured john")

    is_wsl = detect_wsl()
    if is_wsl:
        progress("Detected Windows Subsystem Linux (WSL), checking if hashcat is found...")
        output = command(["powershell.exe", "where.exe hashcat"], get_output=True, error_message=None).strip().decode()
        if output:
            success(f"Found hashcat at {output}")
            hashcat_dir = os.path.dirname(output.replace("\\", "/")).replace("/", "\\")
            if CONFIG.hashcat_windows_path is None:  # If null
                progress(f"hashcat Windows directory was not configured yet, setting to {hashcat_dir}")
                save_config("hashcat_windows_path", hashcat_dir)
                success("Updated config with hashcat path")
            elif CONFIG.hashcat_windows_path != hashcat_dir:  # If doesn't match config
                if ask(f"Found hashcat directory does not match with config, do you want to replace '{CONFIG.hashcat_windows_path}' with '{hashcat_dir}'?"):
                    save_config("hashcat_windows_path", hashcat_dir)
                    success("Updated config with hashcat path")
            else:  # If same as config
                success("hashcat path in config is already set correctly")
        else:  # which.exe hashcat not found
            warning("hashcat command was not found in PowerShell")
            warning("This script won't install hashcat on Windows automatically. If you want to use this feature download and extract the latest release on GitHub from https://github.com/hashcat/hashcat/releases")
            warning("Make sure to also add the hashcat folder to your Windows PATH variable, so you can access it via the 'hashcat' command")

    if CONFIG.password_list is not None and os.path.exists(CONFIG.password_list):
        success("Password list for cracking is already set")
    else:
        warning("Password list is not yet configured")
        location = ""
        while True:  # Repeat until valid path
            location = ask_any("Enter the default wordlist to be used for cracking passwords", default="/usr/share/wordlists/rockyou.txt")
            if os.path.exists(location):
                break
            else:
                warning(f"Path '{location}' does not exist")

        save_config("password_list", location)
        success(f"Successfully set default wordlist to '{location}'")

    print()
    success("Completed setup")

    if not CONFIG.completed_setup:
        save_config("completed_setup", True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        error("Exiting...")
