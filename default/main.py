#!/usr/bin/python3
import argparse
from argparse import ArgumentTypeError
from colorama import Fore, Style
from pyfiglet import figlet_format
from types import SimpleNamespace
from shutil import which
import json
import os
import shlex
import subprocess
import signal
import re
import importlib.util
import pathlib
import termios, sys, tty

DIR = os.path.dirname(os.path.realpath(__file__))
LIBRARY_DIR = os.path.dirname(os.path.realpath(__file__)) + "/lib"
CONFIG = SimpleNamespace(**json.load(open(f"{DIR}/config.json")))

def info(message, *args):
    """Print an informational message. Will be prefixed with `[*]`"""
    print(f"{Style.RESET_ALL}[{Fore.LIGHTCYAN_EX}*{Style.RESET_ALL}] {message}", *args)

def progress(message, *args):
    """Print a progress message, for telling the user what is happening. Will be prefixed with `[~]`"""
    print(f"{Style.RESET_ALL}[{Fore.LIGHTBLUE_EX}~{Style.RESET_ALL}] {message}", *args)

def success(message, *args):
    """Print a success message, for when something completed or succeeded. Will be prefixed with `[+]`"""
    print(f"{Style.RESET_ALL}[{Fore.LIGHTGREEN_EX}+{Style.RESET_ALL}] {message}", *args)

def warning(message, *args):
    """Print a warning message, for warning the user about something, but not directly exiting. Will be prefixed with `[!]`"""
    print(f"{Style.RESET_ALL}[{Fore.YELLOW}!{Style.RESET_ALL}] {message}", *args)

def error(message, *args):
    """Print an error message, for when something went wrong. Will be prefixed with `[-]` and will **exit the program**."""
    print(f"{Style.RESET_ALL}[{Fore.LIGHTRED_EX}!{Style.RESET_ALL}] {message}", *args)
    exit(1)

def ask(question, default=True):
    """Ask a yes/no question. Will be prefixed with `[?]`. Returns `True` or `False` for yes or no. You can provide a `default=` value for when the user does not provide an answer."""
    y_or_n = "Y/n" if default else "y/N"
    colored_question = f"[{Fore.LIGHTYELLOW_EX}?{Style.RESET_ALL}] {question} [{y_or_n}] "
    print(colored_question, end="", flush=True)  # Print question
    while True:
        choice = input_without_newline(1).lower()
        if choice in ["y", "n", "\r", "\n"]:
            print()
            break
    
    if choice in ["\r", "\n"]:  # Default
        choice = "y" if default else "n"
    
    print(f"\033[F\033[{len(strip_ansi(colored_question))}G {choice}")  # Place default choice in question answer
    
    return choice == "y"  # True if y, False if n

def ask_any(question, default):
    """Ask a question for any input the user needs to type in. Will be prefixed with `[?]`. Returns the raw input. Requires a `default` parameter for when the user does not provide an answer."""
    question = f"[{Fore.LIGHTYELLOW_EX}?{Style.RESET_ALL}] {question} [{default}] "
    choice = input(question)  # Any input
    
    if not choice:  # Default
        choice = default
        print(f"\033[F\033[{len(strip_ansi(question))}G {choice}")  # Place default choice in question answer
        
    return choice

def command(command, *, error_message="Failed to execute command", highlight=False, get_output=False, interact_fg=False, **kwargs):
    if get_output and interact_fg:  # Popen cannot get output
        raise Exception("Cannot get output from a foreground process")
    if interact_fg:  # Highlight automatically if interacting in foreground
        highlight = True
    
    print(Fore.LIGHTBLACK_EX, end="\r")
    command = [os.path.expanduser(str(c)) for c in command]  # Convert to string and expand '~'
    print("$", " ".join(shlex.quote(c) for c in command))
    if highlight:  
        print(Style.RESET_ALL, end="\r")
    
    try:
        if interact_fg:
            returncode = run_as_fg_process(command, **kwargs)
        else:
            p = subprocess.run(command, stdout=subprocess.PIPE if get_output else None, stderr=subprocess.PIPE if get_output else None, 
                           **kwargs)
            returncode = p.returncode
    except FileNotFoundError as e:
        print(e)
        returncode = 1  # Error
    
    if highlight:
        print()
    else:
        print(Style.RESET_ALL, end="")
    
    if returncode not in [0, -2] and error_message is not None:
        error(error_message)
    if get_output:
        return p.stdout
    else:
        return returncode

def detect_wsl():
    """Detect if program is running in Windows Subsystem Linux. Useful for automatically setting certain options in that case. Returns `True` or `False`"""
    try:
        with open("/proc/version") as f:
            return "WSL" in f.read() and which("powershell.exe")  # If WSL in /proc/version and powershell.exe exists
    except FileNotFoundError:
        return False


def strip_ansi(source):
    return re.sub(r'\033\[(\d|;)+?m', '', source)

def input_without_newline(length):
    """Get user input without having to press enter"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        response = sys.stdin.read(length).encode()  # Read `length` bytes
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    if response == b"\x03":  # Ctrl+C
        raise KeyboardInterrupt
    
    return response.decode()

def run_as_fg_process(*args, **kwargs):
    old_pgrp = os.tcgetpgrp(sys.stdin.fileno())
    old_attr = termios.tcgetattr(sys.stdin.fileno())

    user_preexec_fn = kwargs.pop("preexec_fn", None)

    def new_pgid():
        if user_preexec_fn:
            user_preexec_fn()
        
        os.setpgid(os.getpid(), os.getpid())
    try:
        child = subprocess.Popen(*args, preexec_fn=new_pgid,
                                 **kwargs)
        os.tcsetpgrp(sys.stdin.fileno(), child.pid)
        os.kill(child.pid, signal.SIGCONT)
        ret = child.wait()

    finally:
        hdlr = signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        os.tcsetpgrp(sys.stdin.fileno(), old_pgrp)
        signal.signal(signal.SIGTTOU, hdlr)
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_attr)

    return ret

class PathType(object):  # From: https://stackoverflow.com/a/33181083/10508498
    def __init__(self, exists=True, type='file', dash_ok=True):
        '''exists:
                True: a path that does exist
                False: a path that does not exist, in a valid parent directory
                None: don't care
           type: file, dir, symlink, None, or a function returning True for valid paths
                None: don't care
           dash_ok: whether to allow "-" as stdin/stdout'''

        assert exists in (True, False, None)
        assert type in ('file','dir','symlink',None) or hasattr(type,'__call__')

        self._exists = exists
        self._type = type
        self._dash_ok = dash_ok

    def __call__(self, string):
        if string=='-':
            # the special argument "-" means sys.std{in,out}
            if self._type == 'dir':
                raise ArgumentTypeError('standard input/output (-) not allowed as directory path')
            elif self._type == 'symlink':
                raise ArgumentTypeError('standard input/output (-) not allowed as symlink path')
            elif not self._dash_ok:
                raise ArgumentTypeError('standard input/output (-) not allowed')
        else:
            e = os.path.exists(string)
            if self._exists==True:
                if not e:
                    raise ArgumentTypeError("path does not exist: '%s'" % string)

                if self._type is None:
                    pass
                elif self._type=='file':
                    if not os.path.isfile(string):
                        raise ArgumentTypeError("path is not a file: '%s'" % string)
                elif self._type=='symlink':
                    if not os.path.symlink(string):
                        raise ArgumentTypeError("path is not a symlink: '%s'" % string)
                elif self._type=='dir':
                    if not os.path.isdir(string):
                        raise ArgumentTypeError("path is not a directory: '%s'" % string)
                elif not self._type(string):
                    raise ArgumentTypeError("path not valid: '%s'" % string)
            else:
                if self._exists==False and e:
                    raise ArgumentTypeError("path exists: '%s'" % string)

                p = os.path.dirname(os.path.normpath(string)) or '.'
                if not os.path.isdir(p):
                    raise ArgumentTypeError("parent path is not a directory: '%s'" % p)
                elif not os.path.exists(p):
                    raise ArgumentTypeError("parent directory does not exist: '%s'" % p)

        return string


def main():
    parser = argparse.ArgumentParser(description='Run commands with default arguments')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Load modules
    for module in (pathlib.Path(os.path.realpath(__file__)).parent / "commands").glob('*.py'):
        spec = importlib.util.spec_from_file_location(f"{__name__}.imported_{module.stem}" , module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.setup(subparsers)
    
    ARGS = parser.parse_args()
    try:
        # Banner
        command_name = ARGS.command.replace("_", " ").capitalize()
        print(Fore.CYAN + figlet_format("Default", font="standard").rstrip())  # Title
        print(f"{Fore.LIGHTBLACK_EX}{command_name:>34}{Style.RESET_ALL}\n")  # Subtitle
        
        if not CONFIG.completed_setup:
            info("Setup was not done yet. It's recommended to run setup_dependencies.py first to set up all the dependencies and configuration")
            if ask("Do you want to run the setup script now?"):
                print()
                import setup_dependencies
                setup_dependencies.main()
                os.execv(sys.argv[0], sys.argv)  # Run again
                
        ARGS.func(ARGS)  # Execute function for command
    except KeyboardInterrupt:
        print()
        error("Exiting...")

if __name__ == '__main__':
    main()
