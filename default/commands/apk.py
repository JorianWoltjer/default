from default.main import *
from default.lib.xamarin_decompress import decompress
import os
import glob


def to_apk_name(folder):
    apk_name = folder[:-1] if folder[-1] == "/" else folder  # Remove trailing slash
    apk_name.replace(" ", "_")  # Replace spaces with underscores
    apk_name = os.path.basename(apk_name)  # Get the last folder name
    return apk_name


def decompile(ARGS):
    ARGS.output = os.path.splitext(ARGS.file)[0] if ARGS.output is None else ARGS.output
    apk_type = "Java/Smali"  # Default

    # Decompile with apktool into smali
    progress(f"Decompiling '{ARGS.file}'...")
    command(['apktool', 'd', '-f', '-r', ARGS.file, '-o', ARGS.output], 
            error_message=f"Failed to decompile '{ARGS.file}'")
    
    success(f"Decompiled smali ('{ARGS.output}/smali')")
    
    # Unzip the apk directly
    progress(f"Unzipping '{ARGS.file}'...")
    command(['unzip', '-qo', ARGS.file, '-d', f"{ARGS.output}.zip"],
            error_message=f"Failed to unzip '{ARGS.file}'")
    success(f"Unzipped '{ARGS.file}' ('{ARGS.output}.zip')")
    
    # Extract java code from smali
    for dexfile in glob.glob(f"{ARGS.output}.zip/classes*.dex"):
        progress(f"Extracting jar from '{dexfile}'...")
        command([f"{LIBRARY_DIR}/dex-tools/d2j-dex2jar.sh", '-f', f"{dexfile}", '-o', f"{ARGS.output}-tmp.jar"],
            error_message=f"Failed to extract jar from '{dexfile}'")
        command(['unzip', '-qo', f"{ARGS.output}-tmp.jar", '-d', f"{ARGS.output}.jar"],
            error_message=f"Failed to unzip '{ARGS.output}-tmp.jar'")
        os.remove(f"{ARGS.output}-tmp.jar")
    
    success(f"Extracted jar ('{ARGS.output}.jar')")
    
    # Decompile if React Native bundle
    if os.path.exists(f"{ARGS.output}.zip/assets/index.android.bundle"):
        apk_type = "React Native"
        info("Detected React Native")
        progress(f"Decompiling '{ARGS.output}.zip/assets/index.android.bundle'...")
        command(["npx", "react-native-decompiler", "-i", f"{ARGS.output}.zip/assets/index.android.bundle", "-o", f"{ARGS.output}.js"], 
                error_message=f"Failed to decompile '{ARGS.output}.zip/assets/index.android.bundle'")
        success(f"Decompiled React Native bundle ('{ARGS.output}.js')")
        
    # Decompress if C# DLLs
    if os.path.exists(f"{ARGS.output}.zip/assemblies"):   
        apk_type = "C#"
        info("Detected C#")
        progress(f"Decompressing '{ARGS.output}.zip/assemblies'...")
        success_count = decompress(f"{ARGS.output}.zip/assemblies")
        success(f"Decompressed {success_count} C# assemblies ('{ARGS.output}.zip/assemblies')")
    
    success(f"Completed ('{ARGS.file}' -> {apk_type})")

def build(ARGS):
    # Create keystore file if it doesn't exist yet
    if not os.path.exists(os.path.expanduser(ARGS.keystore)):
        choice = ask(f"Keystore file '{ARGS.keystore}' not found, do you want to create a new one?")
        if choice:
            ARGS.keystore = ask_any("Where do you want to save the keystore file?", default=ARGS.keystore)
            ARGS.password = ask_any("What should be the password for the keystore file?", default=ARGS.password)
            progress(f"Creating keystore file...")
            command(['keytool', '-genkey', '-noprompt', '-dname', 'CN=, OU=, O=, L=, S=, C=', '-keystore', os.path.expanduser(ARGS.keystore), '-alias', 'apk', '-keyalg', 'RSA', '-storepass', ARGS.password, '-keypass', ARGS.password], 
                    error_message="Failed to create keystore file")
            
            success(f"Keystore file created ('{ARGS.keystore}')")
        else:
            exit(1)
    
    apk_name = to_apk_name(ARGS.folder)
    built_apk = os.path.join(ARGS.folder, 'dist', apk_name + '.apk')
    aligned_apk = os.path.join(ARGS.folder, 'dist', apk_name + '-aligned.apk')
    signed_apk = os.path.join(ARGS.folder, 'dist', apk_name + '-signed.apk')
    
    # Build into APK
    progress(f"Building '{ARGS.folder}'...")
    command(['apktool', 'b', '-f', ARGS.folder], 
            error_message=f"Failed to build '{ARGS.folder}'")
    success(f"Build successful ('{built_apk}')")
    
    # ZIP align APK
    progress(f"Aligning '{built_apk}'...")
    command(['zipalign', '-f', '4', built_apk, aligned_apk], 
            error_message=f"Failed to align '{built_apk}'")
    success(f"Alignment successful ('{aligned_apk}')")
    
    # Sign APK with keystore
    progress(f"Signing '{aligned_apk}'...")
    if ARGS.version is not None:
        version_args = []
        for version in range(1, 4):  # Version 1-3
            if version == ARGS.version:
                version_args.append(f'--v{version}-signing-enabled=true')
            else:
                version_args.append(f'--v{version}-signing-enabled=false')
        
        command(['java', '-jar', '/usr/bin/apksigner', 'sign', '-out', signed_apk, '--ks-key-alias', 'apk', '--ks', os.path.expanduser(ARGS.keystore), '--key-pass', f'pass:{ARGS.password}', '--ks-pass', f'pass:{ARGS.password}', *version_args, '-v', aligned_apk],
                error_message=f"Failed to sign '{aligned_apk}'")
    else:
        command(['java', '-jar', '/usr/bin/apksigner', 'sign', '-out', signed_apk, '--ks-key-alias', 'apk', '--ks', os.path.expanduser(ARGS.keystore), '--key-pass', f'pass:{ARGS.password}', '--ks-pass', f'pass:{ARGS.password}', '-v', aligned_apk],
                error_message=f"Failed to sign '{aligned_apk}'")
    command(['java', '-jar', '/usr/bin/apksigner', 'verify', '-v', signed_apk])
    success(f"Signing successful ('{signed_apk}')")
    
    # Copy file to output location
    if ARGS.output:
        command(['cp', signed_apk, ARGS.output])
    else:
        ARGS.output = signed_apk
    success(f"Completed ('{ARGS.folder}' -> '{ARGS.output}')")


def setup(subparsers):
    parser = subparsers.add_parser('apk', help='Run apk command')
    parser_subparsers = parser.add_subparsers(dest='action', required=True)
    
    parser_decompile = parser_subparsers.add_parser('decompile', help='Decompile APK file')
    parser_decompile.set_defaults(func=decompile)
    parser_decompile.add_argument('file', type=PathType(), help='APK file to decompile')
    parser_decompile.add_argument('-o', '--output', help='Output folder')
    
    parser_build = parser_subparsers.add_parser('build', help='Build APK file')
    parser_build.set_defaults(func=build)
    parser_build.add_argument('folder', help='Input APK source folder', type=PathType(type='dir'))
    parser_build.add_argument('-k', '--keystore', help='Keystore file location', default="~/apk.keystore")
    parser_build.add_argument('-p', '--password', help='Keystore password', default="password")
    parser_build.add_argument('-o', '--output', help='Output APK file')  # Final output gets copied to output argument
    parser_build.add_argument('-v', '--version', help='Sign using specific APK Signature version', type=int, choices=range(1, 4),  metavar="[1-3]")
