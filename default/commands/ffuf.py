import random
import string
from tempfile import NamedTemporaryFile
from default.main import *
from urllib.parse import urlparse

EXTENSIONS = [".html", ".php", ".txt", ".bak", "~"]


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
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "http://" + url

    if "FUZZ" in url:  # If already specified
        return url
    elif url[-1] == "/":  # If end is directory
        return url + "FUZZ"
    else:
        parsed = urlparse(url)
        parts = parsed.path.split("/")[1:]
        if len(parts) > 0:
            parts[-1] = "FUZZ"  # Replace last page with FUZZ
        else:
            parts = ["FUZZ"]  # Empty
        return f"{parsed.scheme}://{parsed.netloc}/{'/'.join(parts)}"


def FUZZ_param_keyword(url):
    if "FUZZ" in url:  # If already specified
        return url
    elif url[-1] != "?" and "?" in url:  # If already parameters
        return url + "&FUZZ"
    else:
        return url + "?FUZZ"


def FUZZ_vhost_keyword(domain):
    """some.domain.example.com -> ['FUZZ.some.domain.example.com', 'FUZZ.domain.example.com', 'some.FUZZ.example.com']"""
    if "FUZZ" in domain:
        return [domain]
    else:
        fuzz_hosts = [f"FUZZ.{domain}"]  # Include subdomain as well
        
        split = domain.split(".")
        for i in range(len(split)-2):  # Replace all words with FUZZ (except main and TLD)
            fuzz_hosts.append('.'.join(split[:i] + ["FUZZ"] + split[i+1:]))

        return fuzz_hosts

def calibrate_size(domain, vhost=False):
    progress("Calibrating...")
    domain, scheme = get_domain(domain)  # Normalize domain
    
    # Try known negative paths
    wordlist = [''.join(random.choice(string.ascii_letters) for i in range(j)) for j in range(10, 30)]
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write("\n".join(wordlist).encode())
        tmp.close()
        if vhost:
            output = command(["ffuf", "-u", f"{scheme}://{domain}", "-w", tmp.name, 
                              "-H", f"Host: {FUZZ_vhost_keyword(domain)[0]}", "-mc", "0", "-json"], get_output=True)
        else:
            output = command(["ffuf", "-u", FUZZ_content_keyword(domain), "-w", tmp.name, "-mc", "0", "-json"], get_output=True)
        
        os.remove(tmp.name)
        if not output: error("No output from calibration. Is host down?")
        lines = []
        for line in output.splitlines():
            lines.append(json.loads(line))
        
        # If all lengths are the same
        length, words = lines[0]["length"], lines[0]["words"]
        if all(line["length"] == length for line in lines):
            success(f"Found negative filter: size={length}")
            return ["-fs", length]
        elif all(line["words"] == words for line in lines):
            success(f"Found negative filter: words={words}")
            return ["-fw", words]
        else:
            error("Failed to find consistent negative character or word length")

def get_domain(url):
    if not (url.startswith("http://") or url.startswith("https://")):  # If already plain domain
        return url.split("/")[0], "http"
    else:
        return urlparse(url).netloc, urlparse(url).scheme


def do_content(ARGS):
    ARGS.url = FUZZ_content_keyword(ARGS.url)
    info(f"Fuzzing URL: {ARGS.url}")

    ffuf_args = ["-c", "-ac"]  # Color and auto-calibrate filter
    if not ARGS.no_extensions:
        ffuf_args += ["-e", ",".join(EXTENSIONS)]
    if ARGS.recursion:
        ffuf_args += ["-recursion"]

    if ARGS.all:  # Removes default response code filter
        ffuf_args += ["-mc", "0"]
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-content.txt"
    if ARGS.output:
        ffuf_args += output_args(ARGS.output)

    progress("Starting ffuf (press ENTER to pause)...")
    command(["ffuf", "-u", ARGS.url, "-w", ARGS.wordlist, *ffuf_args], highlight=True, error_message="Failed to run ffuf")
    success("Finished fuzzing")
    if ARGS.output:
        success(f"Output saved in '{ARGS.output}'")
        info(f"Tip: Use 'jq -r .results[].url {shlex.quote(ARGS.output)}' to list all found URLs")


def do_param(ARGS):
    ARGS.url = FUZZ_param_keyword(ARGS.url)
    ARGS.url += f"={ARGS.value}"
    info(f"Fuzzing URL: {ARGS.url}")

    ffuf_args = ["-c", "-ac"]  # Color and auto-calibrate filter

    if ARGS.all:  # Removes default response code filter
        ffuf_args += ["-mc", "0"]
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


def do_vhost(ARGS, ffuf_args=["-ac"], silent=False):
    ARGS.domain, scheme = get_domain(ARGS.domain)  # Normalize domain
    ffuf_args += ["-c"]  # Color and auto-calibrate filter
    ffuf_output_args = []

    if ARGS.all:  # Removes default response code filter
        ffuf_args += ["-mc", "0"]
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-vhost.txt"

    fuzz_hosts = FUZZ_vhost_keyword(ARGS.domain)

    for i, host in enumerate(fuzz_hosts):
        info(f"Fuzzing domain: {host}")

        if ARGS.output:
            ffuf_output_args = output_args(ARGS.output, n=i+1)

        progress("Starting ffuf (press ENTER to pause)...")
        command(["ffuf", "-u", f"{scheme}://{ARGS.domain}", "-w", ARGS.wordlist, "-H", f"Host: {host}",
                 *ffuf_args, *ffuf_output_args], highlight=True, error_message="Failed to run ffuf")

    success("Finished fuzzing")
    info("Tip: Try fuzzing any found names again to discover deeper subdomains")
    if ARGS.output and not silent:
        success(f"Output saved in '{ARGS.output}'")
        info(f"Tip: Use `jq -r .results[].host {shlex.quote(ARGS.output)}*` to list all found domains")


def do_auto(ARGS):
    if not ARGS.wordlist:
        ARGS.wordlist = f"{LIBRARY_DIR}/list/web-content.txt"
    
    ARGS.domain, _ = get_domain(ARGS.domain)
    calibrated_filter = calibrate_size(ARGS.domain, vhost=True)
    
    tmp = NamedTemporaryFile()
    ARGS.output = tmp.name
    wordlist_backup = ARGS.wordlist
    ARGS.wordlist = ARGS.subdomains
    
    ARGS.all = True
    # Subdomain scan
    progress("Starting subdomain scan...")
    do_vhost(ARGS, calibrated_filter, silent=True)
    output = json.load(open(ARGS.output))
    
    txt_subdomains = f"ffuf-subdomains-{ARGS.domain}.txt"
    with open(txt_subdomains, "w") as f:  # Parse JSON to TXT
        hosts = [ARGS.domain] + [sub["host"] for sub in output["results"]]
        [f.write(f"{line}\n") for line in hosts]
        success(f"Subdomain scan complete! ({len(output['results'])} results in {txt_subdomains!r})")
    
    # GET scan
    txt_get = f"ffuf-get-{ARGS.domain}.txt"
    progress("Starting GET endpoint scan on hosts (press ENTER to pause)...")
    command(["ffuf", "-u", FUZZ_content_keyword(ARGS.domain), "-H", "Host: HOST", "-w", wordlist_backup, "-w", f"{txt_subdomains}:HOST", 
                "-recursion", "-e", ",".join(EXTENSIONS), "-mc", "0", "-c", "-ach", "-o", ARGS.output], highlight=True)

    output = json.load(open(ARGS.output))
    with open(txt_get, "w") as f:  # Parse JSON to TXT
        endpoints = [f"http://{r['input']['HOST']}/{r['input']['FUZZ']}" for r in output['results']]
        [f.write(f"{line}\n") for line in endpoints]
        success(f"GET endpoint scan complete! ({len(output['results'])} results in {txt_get!r})")
    
    # POST scan
    txt_post = f"ffuf-post-{ARGS.domain}.txt"
    progress("Starting POST endpoint scan on hosts (press ENTER to pause)...")
    command(["ffuf", "-u", FUZZ_content_keyword(ARGS.domain), "-H", "Host: HOST", "-w", wordlist_backup, "-w", f"{txt_subdomains}:HOST", 
                "-X", "POST", "-e", ".php", "-mc", "0", "-c", "-ach", "-o", ARGS.output], highlight=True)
    
    output = json.load(open(ARGS.output))
    with open(txt_post, "w") as f:  # Parse JSON to TXT
        endpoints = [f"http://{r['input']['HOST']}/{r['input']['FUZZ']}" for r in output['results']]
        [f.write(f"{line}\n") for line in endpoints]
        success(f"POST endpoint scan complete! ({len(output['results'])} results in {txt_post!r})")
    
    tmp.close()

def setup(subparsers):
    parser = subparsers.add_parser('ffuf', help='Fuzz websites with ffuf for directories/files, parameters or vhosts')
    parser_subparsers = parser.add_subparsers(dest='action', required=True)

    parser_content = parser_subparsers.add_parser('content', help='Fuzz for files or directories on a website')
    parser_content.set_defaults(func=do_content)
    parser_content.add_argument('url', help='The URL to fuzz from. May include the keyword "FUZZ" anywhere to specify the location to fuzz at')
    parser_content.add_argument('-w', "--wordlist", help='Wordlist of paths to use for fuzzing')
    parser_content.add_argument('-e', "--no-extensions", action="store_true", help="Don't automatically add extensions to paths in wordlist")
    parser_content.add_argument('-r', "--recursion", action="store_true", help="Recursively search when a directory was found")
    parser_content.add_argument('-o', "--output", help="File to save output of ffuf")
    parser_content.add_argument('-a', "--all", action="store_true", help="Match all out-of-place responses, removes response code filter")

    parser_param = parser_subparsers.add_parser('param', help='Fuzz for query parameters on a page')
    parser_param.set_defaults(func=do_param)
    parser_param.add_argument('url', help='The URL to fuzz parameters after. May already contain other parameters')
    parser_param.add_argument('-w', "--wordlist", help='Wordlist of parameters to use for fuzzing')
    parser_param.add_argument('-v', "--value", default="1", help='Value of the parameter to use (default: 1)')
    parser_param.add_argument('-o', "--output", help="File to save output of ffuf")
    parser_param.add_argument('-a', "--all", action="store_true", help="Match all out-of-place responses, removes response code filter")

    parser_vhost = parser_subparsers.add_parser('vhost', help='Fuzz for virtual hosts (subdomains) on a website by changing the Host header')
    parser_vhost.set_defaults(func=do_vhost)
    parser_vhost.add_argument(
        'domain', help='The domain or URL to fuzz the Host header on. May include the keyword "FUZZ" anywhere to specify the location to fuzz at')
    parser_vhost.add_argument('-w', "--wordlist", help='Wordlist of subdomains to use for fuzzing')
    parser_vhost.add_argument('-o', "--output", help="File to save output of ffuf")
    parser_vhost.add_argument('-a', "--all", action="store_true", help="Match all out-of-place responses, removes response code filter")
    
    parser_all = parser_subparsers.add_parser('auto', help='First find subdomains, then fuzz those for files and parameters')
    parser_all.set_defaults(func=do_auto)
    parser_all.add_argument('domain', help='The domain or URL to fuzz the Host header on')
    parser_all.add_argument('-s', "--subdomains", help='Wordlist of subdomains to use for fuzzing')
    parser_all.add_argument('-w', "--wordlist", help='Wordlist of paths to use for fuzzing')
