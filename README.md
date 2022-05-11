# Default

Execute actions with default arguments. Useful for quickly doing tedious things.  
Also includes some customisation in the arguments, like output file locations. 

Similar to bash function, these actions just execute bash commands under the hood. It was made to be easily customizable by just adding new commands to the [`commands/`](commands/) directory.

**Features:**
* `default apk decompile`: Decompile an APK file into an APK source folder
* `default apk create_keystore`: Create a keystore file with a password
* `default apk build`: Build, align and sign an APK source folder into an APK file

## Usage

```Shell
default <command> [<action>] [<args>]
```

## Examples

```Shell
default apk decompile click_me.apk
```

[Screenshot of decompiling APK](https://user-images.githubusercontent.com/26067369/167902168-531e4494-14ef-4d09-888f-b431896d728e.png)

```Shell
default apk create_keystore -o test.keystore --password j0r1an
```

[Screenshot of creating keystore](https://user-images.githubusercontent.com/26067369/167902624-14f0c934-5ce1-46fa-b692-9272e8972277.png)

```Shell
default apk build click_me -o new.apk -k test.keystore -p j0r1an
```

[Screenshot of building APK](https://user-images.githubusercontent.com/26067369/167902777-01b8de55-e371-48d7-b304-5e031ee2a07c.png)

## Dependencies

### APK

[**apktool**](https://ibotpeaches.github.io/Apktool/) (For decompiling and building an APK):

```Shell
sudo apt-get install apktool
```

[**apksigner**](https://developer.android.com/studio/command-line/apksigner) (to sign an APK):

```Shell
sudo apt-get install apksigner
```

[**zipalign**](https://developer.android.com/studio/command-line/zipalign) (to align an APK):

```Shell
sudo apt-get install zipalign
```

## TODO:

* Add java decompiling to `apk`
* Add `scan` command for scanning things (`nmap`, `masscan`)
* Add `brute` command for brute-forcing (`ffuf`, `hydra`)
