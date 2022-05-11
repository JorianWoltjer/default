from main import PathType, progress, error, success, command, ask
import os

def decompile(ARGS):
    ARGS.output = os.path.splitext(ARGS.file)[0] if ARGS.output is None else ARGS.output

    progress(f"Decompiling '{ARGS.file}'...")
    command(['apktool', 'd', '-f', '-r', ARGS.file, '-o', ARGS.output], 
            error_message=f"Error decompiling '{ARGS.file}'")
    
    success(f"Successfully decompiled ('{ARGS.file}' -> '{ARGS.output}')")


def create_keystore(ARGS):
    if os.path.exists(os.path.expanduser(ARGS.output)):
        while True:
            choice = ask(f"Keystore '{ARGS.output}' already exists, do you want to overwrite it? [y/n]").lower()[:1]
            if choice == "y":
                os.remove(os.path.expanduser(ARGS.output))
                break
            elif choice == "n":
                exit(1)
    
    progress(f"Creating keystore file...")
    command(['keytool', '-genkey', '-noprompt', '-dname', 'CN=, OU=, O=, L=, S=, C=', '-keystore', os.path.expanduser(ARGS.output), '-alias', 'apk', '-storepass', ARGS.password, '-keypass', ARGS.password], 
            error_message="Failed to create keystore file")
    
    success(f"Keystore file created ('{ARGS.output}')")


def to_apk_name(folder):
    apk_name = folder[:-1] if folder[-1] == "/" else folder  # Remove trailing slash
    apk_name.replace(" ", "_")  # Replace spaces with underscores
    apk_name = os.path.basename(apk_name)  # Get the last folder name
    return apk_name

def build(ARGS):
    if not os.path.exists(os.path.expanduser(ARGS.keystore)):
        error("Keystore file not found, create one with 'default apk create_keystore'")
    
    apk_name = to_apk_name(ARGS.folder)
    built_apk = os.path.join(ARGS.folder, 'dist', apk_name + '.apk')
    aligned_apk = os.path.join(ARGS.folder, 'dist', apk_name + '-aligned.apk')
    signed_apk = os.path.join(ARGS.folder, 'dist', apk_name + '-signed.apk')
    
    progress(f"Building '{ARGS.folder}'...")
    command(['apktool', 'b', '-f', ARGS.folder], 
            error_message=f"Failed to build '{ARGS.folder}'")
    
    success("Build successful")
    progress(f"Aligning '{built_apk}'...")
    command(['zipalign', '-f', '4', built_apk, aligned_apk], 
            error_message=f"Failed to align '{built_apk}'")
    
    success("Alignment successful")
    progress(f"Signing '{aligned_apk}'...")
    if ARGS.sign_v3:
        command(['java', '-jar', '/usr/bin/apksigner', 'sign', '-out', signed_apk, '--ks-key-alias', 'apk', '--ks', os.path.expanduser(ARGS.keystore), '--key-pass', f'pass:{ARGS.password}', '--ks-pass', f'pass:{ARGS.password}', '--v2-signing-enabled=true', '--v3-signing-enabled=true', '-v', aligned_apk],
                error_message=f"Failed to sign '{aligned_apk}'")
    else:
        command(['java', '-jar', '/usr/bin/apksigner', 'sign', '-out', signed_apk, '--ks-key-alias', 'apk', '--ks', os.path.expanduser(ARGS.keystore), '--key-pass', f'pass:{ARGS.password}', '--ks-pass', f'pass:{ARGS.password}', '-v', aligned_apk],
                error_message=f"Failed to sign '{aligned_apk}'")
    command(['java', '-jar', '/usr/bin/apksigner', 'verify', '-v', signed_apk])
    
    success("Signing successful")
    
    if ARGS.output:
        command(['cp', signed_apk, ARGS.output])
    else:
        ARGS.output = signed_apk
    success(f"Completed ('{ARGS.folder}' -> '{ARGS.output}')")


import sys  # Import live values from main.py
__main__ = sys.modules['__main__']

parser_apk = __main__.subparsers.add_parser('apk', help='Run apk command')
parser_apk_subparsers = parser_apk.add_subparsers(dest='action', required=True)
parser_apk_decompile = parser_apk_subparsers.add_parser('decompile', help='Decompile APK file')
parser_apk_decompile.add_argument('file', type=PathType(), help='APK file to decompile')
parser_apk_decompile.add_argument('-o', '--output', type=PathType(exists=False, type='dir'), help='Output folder')
parser_apk_decompile.set_defaults(func=decompile)
parser_apk_create_keystore = parser_apk_subparsers.add_parser('create_keystore', help='Create a keystore file for APK signing')
parser_apk_create_keystore.add_argument('-o', '--output', help='Output keystore file location', default="~/apk.keystore")
parser_apk_create_keystore.add_argument('-p', '--password', help='Keystore password', default="password")
parser_apk_create_keystore.set_defaults(func=create_keystore)
parser_apk_build = parser_apk_subparsers.add_parser('build', help='Build APK file')
parser_apk_build.add_argument('folder', help='Input APK source folder', type=PathType(type='dir'))
parser_apk_build.add_argument('-k', '--keystore', help='Keystore file location', default="~/apk.keystore")
parser_apk_build.add_argument('-p', '--password', help='Keystore password', default="password")
parser_apk_build.add_argument('-o', '--output', help='Output APK file')  # Final output gets copied to output argument
parser_apk_build.add_argument('-v3', '--sign-v3', help='Sign using v3 APK signatures', action='store_true')
parser_apk_build.set_defaults(func=build)
