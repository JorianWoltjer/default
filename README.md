# Default

Some commands or actions are a bit complicated or longwinded, which isn't ideal when you want to work as **quick** as possible. This tool allows you to **decompile** and **build** APKs, scan a host using **nmap**, **crack** password protected files and hashes, and create network **listeners**. All by just running one command with minimal arguments. 

The idea of this tool is to set a lot of **default** arguments for commands, so you only have to provide the minimal amount of arguments to have it do what you want. I made this tool mostly for Cybersecurity Capture The Flag (CTF) challenges. There is often some overlap in challenges where you have to do a common task a lot. It might be annoying to have to look up the command every time, or type out a whole thing checking everything is correct. This tool can quickly do common things.  
As I personally use Windows Subsystem Linux (WSL), all modules have this in mind and change some things up automatically when in WSL to improve the usability. 

Similar to bash scripts, these actions just execute bash commands under the hood, with nice-looking output. It was made to be easily customizable by just adding new commands to the [`commands/`](commands/) directory. I've added 4 modules/commands that I personally use already. 

**Features:**

* `default apk decompile`: Decompile an APK file into an APK source folder
* `default apk create_keystore`: Create a keystore file with a password
* `default apk build`: Build, align and sign an APK source folder into an APK file
* `default nmap`: Scan a network or IP address quickly for open ports with nmap
* `default crack`: Crack password protected files and hashes with hashcat and John the Ripper
* `default listen`: Create network listeners and forward certain connections to your listener

## Usage

```Shell
default <command> [<action>] [<args>]
```

For detailed instruction on creating your own modules/commands, see the [`README.md` in `commands`](commands/README.md). 

## Examples

### APK

```Shell
default apk decompile click_me.apk
```

<img src="https://user-images.githubusercontent.com/26067369/167905287-52fe9a11-4d1b-4e9b-9209-7e36eeda1971.png" width="800" alt="Screenshot of decompiling APK">

```Shell
default apk create_keystore -o test.keystore --password j0r1an
```

<img src="https://user-images.githubusercontent.com/26067369/167904317-55940be3-2a56-463a-a4a5-856bb307238c.png" width="800" alt="Screenshot of creating keystore">

```Shell
default apk build click_me -o new.apk -k test.keystore -p j0r1an
```

<img src="https://user-images.githubusercontent.com/26067369/167902777-01b8de55-e371-48d7-b304-5e031ee2a07c.png" width="800" alt="Screenshot of building APK">

### Nmap

```Shell
default nmap scanme.nmap.org --top
```

<img src="https://user-images.githubusercontent.com/26067369/169713168-e030914e-2665-4ac6-bf76-c5efbd3bb535.png" width="800" alt="Screenshot of nmap scan on scanme.nmap.org">

### Cracking

```Shell
default crack archive.rar
```

<img src="https://cdn.discordapp.com/attachments/901100796316356639/983047063346499685/default_crack_zip.gif" width="800" alt="GIF animation of cracking a RAR archive using hashcat in WSL">

```Shell
default crack hash.txt --john
```

<img src="https://user-images.githubusercontent.com/26067369/172061551-63801284-b227-4ea8-9fe1-cee595cca68b.png" width="800" alt="Screenshot of cracking a SHA256 hash using John the Ripper">

## Installation

```Shell
git clone https://github.com/JorianWoltjer/default.git
cd default
pip install -r requirements.txt  # Install requirements
sudo ln -s $(pwd)/main.py /usr/bin/default  # Put `default` into PATH
default -h
```

## Dependencies

```Shell
sudo apt-get install apktool apksigner zipalign  # Install APK tools
sudo apt-get install nmap masscan  # Install network tools
# <Download latest release of dex2jar from https://github.com/pxb1988/dex2jar/releases>
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

### Listen

* [**pwncat**](https://github.com/calebstewart/pwncat) for creating a `pwncat` listener, that automatically upgrades a reverse shell to bash and has loads more nice features like uploading files. Included in [`requirements.txt`](requirements.txt), but cloud cause some errors because the [listen.py](commands/listen.py) expects `python3.9`.

## TODO:

- [ ] Add `ffuf` command for web fuzzing (`path`, `parameter`, `vhost`)
