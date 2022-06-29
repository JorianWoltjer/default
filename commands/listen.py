from main import *
import socket
from pyngrok import ngrok
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


def create_forwarding(ARGS):  # Should be at the start of all listen actions
    if ARGS.ngrok:
        protocol = "http" if ARGS.action == "http" else "tcp"
        
        progress(f"Creating ngrok tunnel to port {ARGS.port}")
        if hasattr(ARGS, 'udp') and ARGS.udp:
            warning("ngrok does not support UDP, defaulting to TCP")
        
        tunnel = ngrok.connect(ARGS.port, protocol)
        success(f"Successfully created ngrok tunnel from {tunnel.public_url}/ to {protocol}://localhost:{ARGS.port}/")
        return  # No need for portproxy if ngrok is used already
    
    is_wsl = detect_wsl()
    ip = get_ip()
    if is_wsl and not already_in_portproxy(ip, ARGS.port):  # No need to ask
        if ask("Detected WSL, do you want to forward connections to Windows through to WSL using portproxy?"):  # If portproxy forwarding
            progress(f"Forwarding port {ARGS.port} to {ip}...")
            wsl_as_admin(f"netsh interface portproxy set v4tov4 {ARGS.port} {ip}")
            success(f"Port {ARGS.port} is now forwarded to WSL")
            ARGS.forward = "wsl"  # Save for later

def remove_forwarding(ARGS):  # Should be at the end of all listen actions
    if hasattr(ARGS, 'forward') and ARGS.forward == "wsl":
        if ask(f"Port {ARGS.port} was forwarded to WSL for listener, do you want to remove the rule now?"):
            wsl_as_admin(f"netsh interface portproxy delete v4tov4 {ARGS.port}")
            success("Successfully removed forwarding rule")


def listen_nc(ARGS):
    create_forwarding(ARGS)
    
    protocol = "udp" if ARGS.udp else "tcp"
    progress(f"Starting listener on {protocol}://{ARGS.ip}:{ARGS.port}/...")
    info("Ctrl+C to exit")
    if ARGS.pwncat:
        if ARGS.udp:
            warning("UDP not supported for pwncat, defaulting back to TCP")
        if ARGS.repeat:
            warning(f"Cannot repeat pwncat. Start another listener in pwncat shell with 'listen -m linux {ARGS.port}'")
        if ARGS.ip:
            warning("Cannot bind to specific IP address with pwncat, defaulting to all interfaces (0.0.0.0)")
        
        command(["python3.9", "-m", "pwncat", "-lp", ARGS.port], interact_fg=True, 
                error_message="Failed to run pwncat. Make sure it is installed correctly, and if it's installed on a different python version you could change the command in commands/listen.py")
    else:  # Default to netcat
        nc_args = []
        if ARGS.udp:
            nc_args.append("-u")
        
        while True:  # Repeat infinitely if --repeat
            returncode = command(["nc", "-lnvp", ARGS.port, "-s", socket.gethostbyname(ARGS.ip), *nc_args], interact_fg=True)
            if not ARGS.repeat or returncode != 0:
                break
            
            info("Connection was closed, starting back up because of --repeat flag")
    
    success("Closed listener")
    
    remove_forwarding(ARGS)

def listen_http(ARGS):
    create_forwarding(ARGS)
    
    directory = f"'{ARGS.directory}'" if ARGS.directory != "." else "current directory"
    progress(f"Starting HTTP server on http://{ARGS.ip}:{ARGS.port}/ and serving files in {directory}")
    info("Ctrl+C to exit")
    command(["python3", "-m", "http.server", str(ARGS.port), "-b", ARGS.ip, "-d", ARGS.directory], 
            interact_fg=True, error_message="Failed to start HTTP server")

    success("Closed HTTP server")
    
    remove_forwarding(ARGS)
        

def setup(subparsers):
    parser = subparsers.add_parser('listen', help='Create network listeners')
    parser_subparsers = parser.add_subparsers(dest='action', required=True)

    parser_nc = parser_subparsers.add_parser('nc', help='Listen for TCP or UDP connections with netcat')
    parser_nc.set_defaults(func=listen_nc)
    parser_nc.add_argument('port', type=int, help='The port to listen on')
    parser_nc.add_argument('--pwncat', action="store_true", help="Tool to use for creating a listener (default is nc)")
    parser_nc.add_argument('-u', '--udp', action="store_true", help='Listen on UDP port instead of TCP')
    parser_nc.add_argument('-r', '--repeat', action="store_true", help='After closing, start listener again until manually closed')
    
    parser_http = parser_subparsers.add_parser('http', help='Listen for HTTP connections and serve a directory as the content')
    parser_http.set_defaults(func=listen_http)
    parser_http.add_argument('directory', type=PathType(type='dir'), nargs='?', default=".", help='The directory to serve as content')
    parser_http.add_argument('-p', '--port', type=int, default=8000, help='The port to listen on')
    
    for p in [parser_nc, parser_http]:  # Add arguments to all actions
        p.add_argument('-i', '--ip', default="0.0.0.0", help='The IP address to listen on. Will only accept connections specifically to this IP address')
        p.add_argument('-n', '--ngrok', action="store_true", help="Use ngrok to create a public subdomain that points to the localhost port")
