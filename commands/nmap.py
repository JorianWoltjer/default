from main import PathType, progress, error, success, info, command, ask, LIBRARY_DIR
import json
import os

def masscan(ARGS):
    progress(f"Running masscan...")
    masscan_args = ["--wait", "3", "--output-format", "JSON", "--output-file", f"/tmp/masscan.json"]
    masscan_args += ["--top-ports", "1000"] if ARGS.top else ["-p-"]
    masscan_args += ["--rate", "1000"] if ARGS.slow or ARGS.top else ["--rate", "10000"]
    command(['sudo', 'masscan', *masscan_args, ARGS.ip])
    success(f"Finished masscan")
    with open(f"/tmp/masscan.json") as f:
        data = f.read()
        if data:
            results = json.loads(data)
            print(f"\n{results}\n")
            return results

def nmap(ARGS):
    if os.path.exists(ARGS.output):
        while True:
            choice = ask(f"Nmap output file '{ARGS.output}' already exists, do you want to overwrite it? [y/n]").lower()[:1]
            if choice == "y":
                os.remove(ARGS.output)
                break
            elif choice == "n":
                exit(1)
                
    if ARGS.masscan:
        results = masscan(ARGS)
        if results is None:
            error("No results from masscan")
        
        ports = []
        for ip in results:
            ports += [str(p["port"]) for p in ip["ports"]]
    
    nmap_args = ['-Pn', '-n', '-sV', '-sC']  # Default
    
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
    
    if ARGS.masscan:
        nmap_args += ['-p' + ",".join(ports)]
    else:
        nmap_args += ['--top-ports', '1000'] if ARGS.top else ['-p-']  # https://nmap.org/book/performance-port-selection.html
    
    nmap_args.append('-T3' if ARGS.slow else '-T4')  # https://nmap.org/book/performance-timing-templates.html
    nmap_args.append('-sT' if ARGS.connect else '-sS')  # https://nmap.org/book/man-port-scanning-techniques.html
    sudo = not ARGS.connect
    
    progress(f"Running nmap...")
    if sudo:
        command(['sudo', 'nmap', *nmap_args, ARGS.ip], highlight=True)
    else:
        command(['nmap', *nmap_args, ARGS.ip], highlight=True)
    success(f"Completed ('{ARGS.ip}' -> '{ARGS.output}')")


import sys  # Import live values from main.py
__main__ = sys.modules['__main__']

parser_nmap = __main__.subparsers.add_parser('nmap', help='Scan a network with nmap')
parser_nmap.set_defaults(func=nmap)
parser_nmap.add_argument('ip', help='IP address to scan (can be a range in CIDR notation)')
parser_nmap.add_argument('-o', '--output', help='Output file', default="nmap.txt")
parser_nmap.add_argument('-t', '--top', help="Scan only top 1000 ports", action='store_true')
parser_nmap.add_argument('-s', '--slow', help="Slow scan (slower but more thorough)", action='store_true')
parser_nmap.add_argument('-c', '--connect', help="Use TCP Connect scan type (no sudo needed)", action='store_true')
parser_nmap.add_argument('-m', '--masscan', help="Use Masscan to find ports, then send to nmap (sudo needed)", action='store_true')
