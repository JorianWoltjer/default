# Default

Some commands or actions are a bit complicated or longwinded, which isn't ideal when you want to work as **quick** as possible. This tool allows you to **decompile** and **build** APKs, scan a host using **nmap**, **crack** password protected files and hashes, and create network **listeners**. All by just running one command with minimal arguments. 

The idea of this tool is to set a lot of **default** arguments for commands, so you only have to provide the minimal amount of arguments to have it do what you want. I made this tool mostly for Cybersecurity Capture The Flag (CTF) challenges. There is often some overlap in challenges where you have to do a common task a lot. It might be annoying to have to look up the command every time, or type out a whole thing checking everything is correct. This tool can quickly do common things.  
As I personally use Windows Subsystem Linux (WSL), all modules have this in mind and change some things up automatically when in WSL to improve the usability. 

Similar to bash scripts, these actions just execute bash commands under the hood, with nice-looking output. It was made to be easily customizable by just adding new commands to the [`commands/`](commands/) directory. I've added 4 modules/commands that I personally use already. 

**Modules:**

* `default apk`: Decompile an APK for analysing and rebuild it back into an APK
* `default nmap`: Scan a network or IP address quickly for open ports with nmap
* `default crack`: Crack password protected files and hashes with hashcat and John the Ripper
* `default listen`: Create network listeners and forward certain connections to your listener

## Usage

```Shell
default <command> [<action>] [<args>]
```

For detailed instruction on creating your **own** modules/commands, see the [`README.md` in `commands/`](commands/README.md). 

## Examples

### APK

* `default apk decompile seethesharpflag.apk`

[![Default Example: decompile C# APK](https://asciinema.org/a/hEDUJNUkZideirH6Z2VcE3WKF.svg)](https://asciinema.org/a/hEDUJNUkZideirH6Z2VcE3WKF?autoplay=1)

* `default apk build click_me`

[![Default Example: rebuild APK](https://asciinema.org/a/lMlBrtsY2BRAiKC3GmSJswYMN.svg)](https://asciinema.org/a/lMlBrtsY2BRAiKC3GmSJswYMN?autoplay=1)

### Nmap

* `default nmap scanme.nmap.org`

[![Default Example: nmap scanme.nmap.org](https://asciinema.org/a/zDJRJWEOwQ3S5cY4Cb8zPTUdv.svg)](https://asciinema.org/a/zDJRJWEOwQ3S5cY4Cb8zPTUdv?autoplay=1)

### Cracking

* `default crack archive.zip`

[![Default Example: crack .zip archive](https://asciinema.org/a/uyARfOc0CWz0yCmLoZDbxjjKK.svg)](https://asciinema.org/a/uyARfOc0CWz0yCmLoZDbxjjKK?autoplay=1)

* `default crack netntlm.txt` & `default crack hashes.txt`

[![Default Example: crack NTLM and SHA256 hashes](https://asciinema.org/a/pgEoqrqYP4Bqj4AV8ao8BSy2H.svg)](https://asciinema.org/a/pgEoqrqYP4Bqj4AV8ao8BSy2H?autoplay=1)

### Listen

* `default listen nc 1337`

[![Default Example: Netcat listener](https://asciinema.org/a/tIsAawiGLwtFTrKe3hC1wL4zE.svg)](https://asciinema.org/a/tIsAawiGLwtFTrKe3hC1wL4zE?autoplay=1)

* `default listen http`

[![Default Example: HTTP server](https://asciinema.org/a/XbDgCx6Z7JjOY5Sct6WWyr4HF.svg)](https://asciinema.org/a/XbDgCx6Z7JjOY5Sct6WWyr4HF?autoplay=1)

* `default listen dns`

[![Default Example: DNS server](https://asciinema.org/a/Ge4Wd96aboFsZaEXvDeJ7WZ1l.svg)](https://asciinema.org/a/Ge4Wd96aboFsZaEXvDeJ7WZ1l?autoplay=1)

## Installation

```Shell
git clone https://github.com/JorianWoltjer/default.git
cd default
pip install -r requirements.txt  # Install requirements
sudo ln -s $(pwd)/main.py /usr/bin/default  # Put `default` into PATH
default -h
```

Then there are a few things left to configure in [config.py](config.py). I am planning to make this a setup script at some point, but for now just put the correct values for your setup in here.

## Dependencies

```Shell
sudo apt-get install apktool apksigner zipalign  # Install APK tools
sudo apt-get install nmap masscan  # Install network tools
pip install git+https://github.com/JorianWoltjer/Name-That-Hash.git  # Temporary fork of name-that-hash
# *Download latest release of dex2jar from https://github.com/pxb1988/dex2jar/releases manually*
sudo ln -s /path/to/dex2jar/d2j-dex2jar.sh /usr/local/bin/dex2jar  # Add dex2jar to PATH
```

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

* [**pwncat**](https://github.com/calebstewart/pwncat) for creating a `pwncat` listener, that automatically upgrades a reverse shell to bash and has loads more nice features like uploading files. Included in [`requirements.txt`](requirements.txt), but cloud cause some errors because the [listen.py](commands/listen.py) expects `python3.9`.

## TODO:

- [ ] Add `ffuf` command for web fuzzing (`path`, `parameter`, `vhost`)
