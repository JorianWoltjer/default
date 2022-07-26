# Modules

This file explains how modules work and how to create your own. 

## What is a module?

The idea of a module is a bash script with python logic. A module would be some type of action, with multiple ways of doing that action or small sub-actions. For example:

* The [`nmap`](nmap.py) module has one main action, which is scanning a host. But it has some configurable options that you can use to customize your scan.
* The [`apk`](apk.py) module is about APKs, and has 3 actions. It can decompile an APK, build an APK and create a keystore. These actions all have their own options that you can set, and they do different things. But everything has to do with APKs

## Creating a module

Creating your own module is pretty simple. You just need to put the bash commands into a python file and add some logic and messages to it. 

### Initial Setup

First create a Python file in this [`commands/`](.) directory with the `.py` extension. This file will contain all the code for the module.

On the top of the file, you'll want a `from main import *` line. This is to import all useful function from the main file. More information about these function and how to use them in the [Functions](#functions) section.

Now define a `setup(subparsers)` function. This is needed to add your arguments to the main `default` program. In this function the `subparser` object is a global variable that all modules share. So to create our own parser within this, use the `subparsers.add_parser()` function with the name of your module. 

You also need to define a function that your module will use, and set it using the `.set_defaults(func=...)` method. This function will be called with `ARGS` as the first and only argument. 

If we want to make a module called `hello.py` for example, it would look something like this:

```Python
from main import *

def hello(ARGS):
    ...

def setup(subparsers):
    parser = subparsers.add_parser('hello', help='Say hello')
    parser.set_defaults(func=hello)
```

### Arguments

You likely want to use arguments to give options in your command. Arguments are made using the Python `argparse` library. 

You can add arguments to the `parser` object with the `add_argument` method. For more detailed instructions see the [`argparse` documentation](https://docs.python.org/3/library/argparse.html#adding-arguments). 

The parsed arguments will then be passed as `ARGS` to your defined function. You can use these arguments to change the logic of your command. 

Continuing the example, an argument for specifying a name could look like this:

```Python
from main import *

def hello(ARGS):
    print(f"Hello, {ARGS.name}!")

def setup(subparsers):
    parser = subparsers.add_parser('hello', help='Say hello')
    parser.set_defaults(func=hello)

    parser.add_argument('name', help='The name to say hello to')
```

We can then supply a name as the first argument:

```Shell
$ default hello Jorian
Hello, Jorian!
```

### Functions

With the first `from main import *` line you imported all the useful function from the main file. Here are the functions you can use and how they work:

* `info(message)`: Print an informational message. Will be prefixed with `[*]`
* `progress(message)`: Print a progress message, for telling the user what is happening. Will be prefixed with `[~]`
* `success(message)`: Print a success message, for when something completed or succeeded. Will be prefixed with `[+]`
* `error(message)`: Print an error message, for when something went wrong. Will be prefixed with `[-]` and will **exit the program**.
* `ask(question)`: Ask a yes/no question. Will be prefixed with `[?]`. Returns `True` or `False` for yes or no. You can provide a `default=` parameter for when the user does not provide an answer. 
* `ask_any(question)`: Ask a question for any input the user needs to type in. Will be prefixed with `[?]`. Returns the raw input. Requires a `default` parameter for when the user does not provide an answer.
* `command(command)`: Run the specified system command. Needs to be passed as a list of arguments like `["uname", "-a"]`. Prints the command and output in gray, unless `highlight=` is set to `True`. The output of the command is only returned if `get_output=` is set to `True`.
* `detect_wsl()`: Detect if program is running in Windows Subsystem Linux. Useful for automatically setting certain options in that case. Returns `True` or `False`
