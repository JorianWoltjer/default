# Default

Some commands or actions are a bit complicated or longwinded, which isn't ideal when you want to work as **quickly** as possible. This tool allows you to **decompile** and **rebuild** APKs, scan a host using **nmap**, **crack** password-protected files and hashes, and create network **listeners**. All by just running one command with minimal arguments. 

The idea of this tool is to set a lot of **default** arguments for commands, so you only have to provide a minimal amount of arguments to have it do what you want. I made this tool mostly for Cybersecurity Capture The Flag (CTF) challenges. There is even a `flag` command for searching flags in various encodings. There is often some overlap in challenges where you have to do a common task a lot. It's annoying to have to look up the command every time or type out a whole thing checking everything is correct. This tool can quickly do those common things.  
As I use Windows Subsystem Linux (WSL) myself, all modules have this in mind and change some things up automatically when in WSL to improve the usability. 

Similar to bash scripts, these actions just execute bash commands under the hood, with nice-looking output. It was made to be easily customizable by just adding new commands to the [`commands/`](commands/) directory. I've added 5 useful modules/commands already. 

**Modules:**

* `default apk`: Decompile an APK for analyzing and rebuild it back into an APK
* `default nmap`: Scan a network or IP address quickly for open ports with nmap
* `default crack`: Crack password-protected files and hashes with hashcat and John the Ripper
* `default listen`: Create network listeners and forward certain connections to your listener
* `default flag`: Search the current directory for CTF flags in various encodings

## Usage

```Shell
default <command> [<action>] [<args>]
```

For detailed instruction on creating your **own** modules/commands, see the [`README.md` in `commands/`](commands/README.md). 

## Examples

The example videos take up too much space in this `README.md`, so you can check out examples for all commands in [`EXAMPLES.md`](EXAMPLES.md)

## Installation

```Shell
git clone https://github.com/JorianWoltjer/default.git
cd default
pip install -e .  # Install requirements and add 'default' program to PATH using pip
python3 setup_dependencies.py  # Interactive script to set up all dependencies for modules
default --help
```

The `setup_dependencies.py` asks about configuration as well, but if you ever want to change these later you can change the values in [`default/config.json`](default/config.json). More about these options in [Dependencies](#configjson)

## Dependencies

Some included modules require external tools to be installed and certain paths to be configured. There is a script [setup_dependencies.py](setup_dependencies.py) that you can run to easily install and set up all the required dependencies for all modules. Just follow the instructions in the script. 

> **Note**  
> If you have any issues while installing the dependencies using this script please let me know in a [GitHub Issue](https://github.com/JorianWoltjer/default/issues) so I can improve the experience for others

```Shell
python3 setup_dependencies.py
```

After installing everything a successful output should only contain `[~]` and `[+]` messages, without any yellow `[!]` warnings. 

### [config.json](default/config.json)

* `completed_setup`: Boolean value to tell if the [setup_dependencies.py](setup_dependencies.py) script has been completed yet. If not, you will receive a message when running a command
* `john_path`: Path to the [John the Ripper Jumbo](https://github.com/openwall/john) directory. Is used for `john` and `zip2john`-like tools
* `hashcat_windows_path`: Path to the hashcat directory on Windows. Only used if on Windows Subsystem Linux (WSL) to make use of the GPU with hashcat, since this is normally not possible in WSL. 
* `flag_prefixes`: A list of prefixes for Capture The Flag (CTF) flags. All in the `CTF{flag}` format, with `CTF` being able to change

### APK

* [**apktool**](https://ibotpeaches.github.io/Apktool/) for decompiling and building an APK
* [**apksigner**](https://developer.android.com/studio/command-line/apksigner) to sign an APK
* [**zipalign**](https://developer.android.com/studio/command-line/zipalign) to align an APK
* [**dex2jar**](https://github.com/pxb1988/dex2jar) to convert a `classes.dex` file to a JAR file
* [**xamarin-decompress**](https://github.com/NickstaDB/xamarin-decompress) to decompress DLL files (already included in [`/lib`](/lib))

### Nmap

* [**nmap**](https://nmap.org/) to get detailed information about open ports
* [**masscan**](https://github.com/robertdavidgraham/masscan) to scan ports very quickly, and pass them to nmap

### Cracking

* A [**modified** version of **Name-That-Hash**](https://github.com/JorianWoltjer/Name-That-Hash), with added hashes recognition for multiple types of archives (ZIP, RAR, etc.). At the time of writing the [Pull Request](https://github.com/HashPals/Name-That-Hash/pull/138) is not yet accepted, and I will update this README when it is included. For the time being use my fork if you want to use the archive cracking features. 
* [**hashcat**](https://hashcat.net/hashcat/) as the default cracking tool for hashes
* [**john**](https://github.com/openwall/john) for cracking passwords with the `--john` option

### Listen

* [**pwncat**](https://github.com/calebstewart/pwncat) for creating a `pwncat` listener, that automatically upgrades a reverse shell to bash and has loads more nice features like uploading files. Included in [`requirements.txt`](requirements.txt), but could cause some errors because the [listen.py](commands/listen.py) expects `python3.9`.

## TODO

Features/modules that I am planning to make in the future

- [ ] Add `ffuf` command for web fuzzing (`path`, `parameter`, `vhost`)
- [ ] Add support for recognizing and cracking linux shadow hashes (`/etc/shadow`)
