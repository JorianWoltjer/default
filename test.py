from colorama import Fore, Style
import subprocess

print(Fore.LIGHTBLACK_EX, end="")
subprocess.run(["echo", "Hello World!"])
print(Style.RESET_ALL)
