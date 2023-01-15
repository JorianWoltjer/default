from default.main import *
import json
import os
from socket import gethostbyname

def masscan(ARGS):
    if ARGS.udp:
        error("Masscan does not support UDP scans")
    
    progress(f"Running masscan...")
    masscan_args = ["--wait", "3", "--output-format", "JSON", "--output-file", f"/tmp/masscan.json"]
    masscan_args += ["-p-"] if ARGS.all else ["--top-ports", "1000"]
    masscan_args += ["--rate", "10000"] if ARGS.all and not ARGS.slow else ["--rate", "1000"]
    command(['sudo', 'masscan', *masscan_args, gethostbyname(ARGS.ip)])
    success(f"Finished masscan")
    with open(f"/tmp/masscan.json") as f:
        data = f.read()
        if data:
            results = json.loads(data)
            print(f"\n{results}\n")
            return results

def nmap(ARGS):
    if os.path.exists(ARGS.output):
        choice = ask(f"Nmap output file '{ARGS.output}' already exists, do you want to overwrite it?")
        if choice:
            pass  # Nmap will overwrite itself later
        else:
            exit(1)
                
    if ARGS.masscan:
        results = masscan(ARGS)
        if results is None:
            error("No results from masscan")
        
        ports = []
        for ip in results:
            ports += [str(p["port"]) for p in ip["ports"]]
    
    nmap_args = ['-Pn', '-n', '-sV', '-sC', '-O', '-vv']  # Default
    sudo = True
    
    # https://nmap.org/book/man-output.html
    ext = os.path.splitext(ARGS.output)[1]
    if ext == ".xml":  # XML format
        info("Saving output in XML format")
        nmap_args += ['-oX', ARGS.output]
    elif ext == "":  # All formats
        info("Saving output in all formats (.nmap, .xml, .gnmap)")
        nmap_args += ['-oA', ARGS.output]
    else:  # Nmap format
        nmap_args += ['-oN', ARGS.output]
    
    # https://nmap.org/book/performance-port-selection.html
    if ARGS.masscan:
        nmap_args += ['-p' + ",".join(ports)]
    else:
        if ARGS.all:
            nmap_args += ['-p-']
        elif ARGS.udp:
            nmap_args += ['--top-ports', '100']
        else:
            nmap_args += ['--top-ports', '1000']
    
    # https://nmap.org/book/man-port-scanning-techniques.html
    if ARGS.connect:  # Doesn't require sudo
        nmap_args += ["-sT"]
        sudo = False
    elif ARGS.udp:
        nmap_args += ["-sU", "--version-intensity", "0"]
    else:
        nmap_args += ["-sS"]
    
    nmap_args.append('-T3' if ARGS.slow else '-T4')  # https://nmap.org/book/performance-timing-templates.html
    
    progress(f"Running nmap...")
    if sudo:
        command(['sudo', 'nmap', *nmap_args, ARGS.ip], highlight=True)
    else:
        command(['nmap', *nmap_args, ARGS.ip], highlight=True)
    success(f"Completed ('{ARGS.ip}' -> '{ARGS.output}')")


def setup(subparsers):
    parser = subparsers.add_parser('nmap', help='Scan a network with nmap')
    parser.set_defaults(func=nmap)
    
    parser.add_argument('ip', help='IP address to scan (can be a range in CIDR notation)')
    parser.add_argument('-o', '--output', help='Output file (default: nmap.txt)', default="nmap.txt")
    parser.add_argument('-a', '--all', help="Scan all ports (0-65535)", action='store_true')
    parser.add_argument('-s', '--slow', help="Slow scan (slower but more thorough)", action='store_true')
    parser.add_argument('-m', '--masscan', help="Use Masscan to find ports, then send to nmap (sudo needed)", action='store_true')
    scan_type_group = parser.add_mutually_exclusive_group()
    scan_type_group.add_argument('-c', '--connect', help="Use TCP Connect scan type (no sudo needed)", action='store_true')
    scan_type_group.add_argument('-u', '--udp', help="Scan for UDP ports", action='store_true')
