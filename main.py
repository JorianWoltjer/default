import argparse
from argparse import ArgumentTypeError
import os
import shlex
import subprocess
from colorama import Fore, Style

LIBRARY_DIR = os.path.dirname(os.path.realpath(__file__)) + "/lib"

def progress(message):
    print(f"[{Fore.LIGHTCYAN_EX}~{Style.RESET_ALL}] {message}")
    
def error(message):
    print(f"[{Fore.LIGHTRED_EX}!{Style.RESET_ALL}] {message}")
    exit(1)
    
def success(message):
    print(f"[{Fore.LIGHTGREEN_EX}+{Style.RESET_ALL}] {message}")

def info(message):
    print(f"[{Fore.LIGHTBLUE_EX}*{Style.RESET_ALL}] {message}")

def ask(message):
    return input(f"[{Fore.LIGHTYELLOW_EX}?{Style.RESET_ALL}] {message} ")

def command(command, *, error_message="Failed to execute command"):
    print(Fore.LIGHTBLACK_EX, end="\r")
    print("$", " ".join(shlex.quote(c) for c in command))
    p = subprocess.run(command)
    print(Style.RESET_ALL, end="")
    if p.returncode != 0:
        error(error_message)

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
    
    from commands import apk
    
    ARGS = parser.parse_args()
    ARGS.func(ARGS)  # Execute function for command
