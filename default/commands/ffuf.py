from default.main import *
from urllib.parse import urlparse
import re

EXTENSIONS = ["html", "php", "txt", "bak", "log"]


def output_args(filename, n=None):
    basename, ext = os.path.splitext(filename)
    
    ext_type = ext[1:]  # Remove starting dot from extension
    if n is not None and n > 1:
        basename += str(n)  # Add number after basename
    filename = f"{basename}{ext}"  # Reassemble filename
    
    if ext_type in ["ejson", "html", "md", "csv", "ecsv"]:
        return ["-o", filename, "-of", ext_type]  # Set output format based on extension
    else:
        return ["-o", filename]  # Default: json

def FUZZ_content_keyword(url):
    if "FUZZ" in url:  # If already specified
        return url
    elif url[-1] == "/":  # If end is directory
        return url + "FUZZ"
    else:
        parts = url.split("/")
        parts[-1] = "FUZZ"  # Replace last page with FUZZ
        return "/".join(parts)

def FUZZ_param_keyword(url):
    if "FUZZ" in url:  # If already specified
        return url
    elif url[-1] != "?" and "?" in url:  # If already parameters
        return url + "&FUZZ"
    else:
        return url + "?FUZZ"

def FUZZ_vhost_keyword(domain):
    if "FUZZ" in domain:
        return domain
    else:
        return f"FUZZ.{domain}"  # Subdomain

def get_domain(url):
    if not (url.startswith("http://") or url.startswith("https://")):  # If already plain domain
        return url.split("/")[0], "http"
    else:
        return urlparse(url).netloc, urlparse(url).scheme

def FUZZ_vhost_keyword_auto(domain):
    words = re.findall(r'\w+', domain)
    fuzz_hosts = [f"FUZZ.{domain}"]  # Include subdomain as well
    for word in words:  # Replace all words with FUZZ
        fuzz_hosts.append(domain.replace(word, "FUZZ"))
        
    return fuzz_hosts


def content(ARGS):
    ARGS.url = FUZZ_content_keyword(ARGS.url)
    info(f"Fuzzing URL: {ARGS.url}")
    
    ffuf_args = ["-c", "-ac"]  # Color and auto-calibrate filter
    if not ARGS.no_extensions:
        extensions = ["." + ext for ext in EXTENSIONS]
        ffuf_args += ["-e", ",".join(extensions)]
    if ARGS.recursion:
        ffuf_args += ["-recursion"]
    
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-content.txt"
    if ARGS.output:
        ffuf_args += output_args(ARGS.output)
    
    progress("Starting ffuf...")
    command(["ffuf", "-u", ARGS.url, "-w", ARGS.wordlist, *ffuf_args], highlight=True, error_message="Failed to run ffuf")
    success("Finished fuzzing")
    if ARGS.output:
        success(f"Output saved in '{ARGS.output}'")
        info(f"Tip: Use 'jq -r .results[].url {shlex.quote(ARGS.output)}' to list all found URLs")

def param(ARGS):
    ARGS.url = FUZZ_param_keyword(ARGS.url)
    ARGS.url += f"={ARGS.value}"
    info(f"Fuzzing URL: {ARGS.url}")
    
    ffuf_args = ["-c", "-ac"]  # Color and auto-calibrate filter
    
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-param.txt"
    if ARGS.output:
        ffuf_args += output_args(ARGS.output)
    
    progress("Starting ffuf...")
    command(["ffuf", "-u", ARGS.url, "-w", ARGS.wordlist, *ffuf_args], highlight=True, error_message="Failed to run ffuf")
    success("Finished fuzzing")
    if ARGS.output:
        success(f"Output saved in '{ARGS.output}'")
        info(f"Tip: Use 'jq -r .results[].url {shlex.quote(ARGS.output)}' to list all found URLs")

def vhost(ARGS):
    ARGS.domain, scheme = get_domain(ARGS.domain)  # Normalize domain
    ffuf_args = ["-c", "-ac"]  # Color and auto-calibrate filter
    ffuf_output_args = []
    
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-vhost.txt"
    
    if ARGS.auto:
        fuzz_hosts = FUZZ_vhost_keyword_auto(ARGS.domain)
    else:
        fuzz_hosts = [FUZZ_vhost_keyword(ARGS.domain)]
        
    for i, host in enumerate(fuzz_hosts):
        info(f"Fuzzing domain: {host}")
        
        if ARGS.output:
            ffuf_output_args = output_args(ARGS.output, n=i+1)

        progress("Starting ffuf...")
        command(["ffuf", "-u", f"{scheme}://{ARGS.domain}", "-w", ARGS.wordlist, "-H", f"Host: {host}", *ffuf_args, *ffuf_output_args], highlight=True, error_message="Failed to run ffuf")
    
    success("Finished fuzzing")
    if ARGS.output:
        success(f"Output saved in '{ARGS.output}'")
        info(f"Tip: Use 'jq -r .results[].host {shlex.quote(ARGS.output)}*' to list all found domains")


def setup(subparsers):
    parser = subparsers.add_parser('ffuf', help='Fuzz websites with ffuf for directories/files, parameters or vhosts')
    parser_subparsers = parser.add_subparsers(dest='action', required=True)
    
    parser_content = parser_subparsers.add_parser('content', help='Fuzz for files or directories on a website')
    parser_content.set_defaults(func=content)
    parser_content.add_argument('url', help='The URL to fuzz from. May include the keyword "FUZZ" anywhere to specify the location to fuzz at')
    parser_content.add_argument('-w', "--wordlist", help='Wordlist of paths to use for fuzzing')
    parser_content.add_argument('-e', "--no-extensions", action="store_true", help="Don't automatically add extensions to paths in wordlist")
    parser_content.add_argument('-r', "--recursion", action="store_true", help="Recursively search when a directory was found")
    parser_content.add_argument('-o', "--output", help="File to save output of ffuf")
    
    parser_param = parser_subparsers.add_parser('param', help='Fuzz for query parameters on a page')
    parser_param.set_defaults(func=param)
    parser_param.add_argument('url', help='The URL to fuzz parameters after. May already contain other parameters')
    parser_param.add_argument('-w', "--wordlist", help='Wordlist of parameters to use for fuzzing')
    parser_param.add_argument('-v', "--value", default="1", help='Value of the parameter to use (default: 1)')
    parser_param.add_argument('-o', "--output", help="File to save output of ffuf")
    
    parser_vhost = parser_subparsers.add_parser('vhost', help='Fuzz for virtual hosts (subdomains) on a website by changing the Host header')
    parser_vhost.set_defaults(func=vhost)
    parser_vhost.add_argument('domain', help='The domain or URL to fuzz the Host header on. May include the keyword "FUZZ" anywhere to specify the location to fuzz at')
    parser_vhost.add_argument('-w', "--wordlist", help='Wordlist of subdomains to use for fuzzing')
    parser_vhost.add_argument('-a', "--auto", action="store_true", help='Automatically find words in domain to FUZZ')
    parser_vhost.add_argument('-o', "--output", help="File to save output of ffuf")
