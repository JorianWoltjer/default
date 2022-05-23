# Default

Execute actions with default arguments. Useful for quickly doing tedious things.  
Also includes some customisation in the arguments, like output file locations. 

Similar to bash function, these actions just execute bash commands under the hood. It was made to be easily customizable by just adding new commands to the [`commands/`](commands/) directory.

**Features:**
* `default apk decompile`: Decompile an APK file into an APK source folder
* `default apk create_keystore`: Create a keystore file with a password
* `default apk build`: Build, align and sign an APK source folder into an APK file
* `default nmap`: Scan a network or IP address quickly for open ports with nmap

## Usage

```Shell
default <command> [<action>] [<args>]
```

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

## Installation

```Shell
git clone https://github.com/JorianWoltjer/default.git
cd default
pip install -r requirements.txt
alias default="python3 /path/to/default/main.py"  # Add to your ~/.bashrc
default -h
```

## Dependencies

```Shell
sudo apt-get install apktool apksigner zipalign  # Install APK tools
sudo apt-get install nmap masscan  # Install network tools
# <Download latest release from https://github.com/pxb1988/dex2jar/releases>
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

## TODO:

- [ ] Add `ffuf` command for web fuzzing (`path`, `parameter`, `vhost`)
- [ ] Add `hydra` command for brute-forcing (`ssh`)
