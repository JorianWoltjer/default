from main import *
from lib import wsl_sudo  # Local lib/ folder

def get_ip():  # Get WSL IP from interface
    import netifaces
    return netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']

def wsl_as_admin(cmd):  # Run command as administrator using wsl-sudo
    progress("Starting administrator prompt...")
    try:
        wsl_sudo.UnprivilegedClient().main(["powershell.exe", "-Command", cmd], 0)
    except Exception:
        error("Failed to run as administrator")

def wsl_as_user(cmd):  # Run command normally
    return command(["powershell.exe", "-Command", cmd], get_output=True).decode("utf-8").strip()

def already_in_portproxy(ip, port):
    list_output = wsl_as_user("netsh interface portproxy show v4tov4")
    matches = re.findall(r'^\S+\s+(\d+)\s+(\S+)', list_output, re.MULTILINE)
    return (str(port), ip) in matches


def listen(ARGS):
    is_wsl = detect_wsl()
    ip = get_ip()
    portproxy_forward = None
    if is_wsl and not already_in_portproxy(ip, ARGS.port):
        portproxy_forward = ask("Detected WSL, do you want to forward connections to Windows through to WSL using portproxy?")
        if portproxy_forward:  # If portproxy forwarding
            progress(f"Forwarding port {ARGS.port} to {ip}...")
            wsl_as_admin(f"netsh interface portproxy set v4tov4 {ARGS.port} {ip}")
            success(f"Port {ARGS.port} is now forwarded to WSL")
    
    progress("Starting listener...")
    if ARGS.tool == "nc":
        command(["nc", "-lnvp", ARGS.port], interact_fg=True)
    elif ARGS.tool == "pwncat":
        command(["python3.9", "-m", "pwncat", "-lp", ARGS.port], interact_fg=True, 
                error_message="Failed to run pwncat. Make sure it is installed correctly, and if it's installed on a different python version you could change the command in commands/listen.py")
    
    success("Closed listener")
    if portproxy_forward:
        if ask(f"Port {ARGS.port} was forwarded to WSL for listener, do you want to delete the rule now?", default=False):
            wsl_as_admin(f"netsh interface portproxy delete v4tov4 {ARGS.port}")
            success("Successfully removed forwarding rule")
    

def setup(subparsers):
    parser = subparsers.add_parser('listen', help='Create network listeners')
    parser.set_defaults(func=listen)

    parser.add_argument('port', type=int, help='The port to listen on')
    parser.add_argument('--ip', help='The IP address to listen on. Will only accept connections specifically to this IP address')
    parser.add_argument('-u', '--udp', action='store_true', help='Listen on UDP port instead of TCP')
    parser.add_argument('-t', '--tool', choices=["nc", "pwncat"], default="nc", help="Tool to use for creating a listener (default is nc)")
    parser.add_argument('-n', '--ngrok', action="store_true", help="Use ngrok to create a public subdomain that points to the localhost port")
