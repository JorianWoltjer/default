#!/usr/bin/python3
import argparse
from argparse import ArgumentTypeError
from colorama import Fore, Style
import os
import shlex
import subprocess
import re
import importlib.util
import pathlib

LIBRARY_DIR = os.path.dirname(os.path.realpath(__file__)) + "/lib"

def info(message):
    """Print an informational message. Will be prefixed with `[*]`"""
    print(f"[{Fore.LIGHTCYAN_EX}*{Style.RESET_ALL}] {message}")

def progress(message):
    """Print a progress message, for telling the user what is happening. Will be prefixed with `[~]`"""
    print(f"[{Fore.LIGHTBLUE_EX}~{Style.RESET_ALL}] {message}")

def success(message):
    """Print a success message, for when something completed or succeeded. Will be prefixed with `[+]`"""
    print(f"[{Fore.LIGHTGREEN_EX}+{Style.RESET_ALL}] {message}")

def error(message):
    """Print an error message, for when something went wrong. Will be prefixed with `[-]` and will **exit the program**."""
    print(f"[{Fore.LIGHTRED_EX}!{Style.RESET_ALL}] {message}")
    exit(1)
    
def ask(question, default=True):
    """Ask a yes/no question. Will be prefixed with `[?]`. Returns `True` or `False` for yes or no. You can provide a `default=` value for when the user does not provide an answer."""
    while True:
        question = f"[{Fore.LIGHTYELLOW_EX}?{Style.RESET_ALL}] {question} [y/n] "
        choice = input(question).lower()[:1]
        if choice == "y":
            return True
        elif choice == "n":
            return False
        elif choice == "":  # Default
            choice = "y" if default else "n"
            print(f"\033[F\033[{len(strip_ansi(question))}G {choice}")  # Place default choice in question answer
            return default

def ask_any(question, default):
    """Ask a question for any input the user needs to type in. Will be prefixed with `[?]`. Returns the raw input. Requires a `default` parameter for when the user does not provide an answer."""
    question = f"[{Fore.LIGHTYELLOW_EX}?{Style.RESET_ALL}] {question} [{default}] "
    choice = input(question)  # Any input
    
    if not choice:  # Default
        choice = default
        print(f"\033[F\033[{len(strip_ansi(question))}G {choice}")  # Place default choice in question answer
        
    return choice

def command(command, error_message="Failed to execute command", highlight=False, get_output=False, **kwargs):
    print(Fore.LIGHTBLACK_EX, end="\r")
    print("$", " ".join(shlex.quote(c) for c in command))
    if highlight:  
        print(Style.RESET_ALL, end="\r")
    
    errored = False
    try:
        p = subprocess.run(command, stdout=subprocess.PIPE if get_output else None, stderr=subprocess.PIPE if get_output else None, 
                           **kwargs)
    except FileNotFoundError as e:
        print(e)
        errored = True
    
    if highlight:
        print()
    else:
        print(Style.RESET_ALL, end="")
        
    if errored or p.returncode != 0:
        if error_message != None:
            error(error_message)
        
    return p.stdout

def strip_ansi(source):
    return re.sub(r'\033\[(\d|;)+?m', '', source)

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run commands with default arguments')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Load modules
    for module in (pathlib.Path(os.path.realpath(__file__)).parent / "commands").glob('*.py'):
        spec = importlib.util.spec_from_file_location(f"{__name__}.imported_{module.stem}" , module)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.setup(subparsers)
    
    # Execute function for command
    ARGS = parser.parse_args()
    try:
        ARGS.func(ARGS)
    except KeyboardInterrupt:
        print()
        error("Exiting...")
