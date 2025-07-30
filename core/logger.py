from colorama import init, Fore
import datetime

init(autoreset=True)

def log(msg, level="info"):
    time = datetime.datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": Fore.CYAN + "[*]",
        "success": Fore.GREEN + "[+]",
        "warn": Fore.YELLOW + "[!]",
        "error": Fore.RED + "[-]"
    }.get(level, Fore.WHITE + "[ ]")
    print(f"{Fore.WHITE}{time} {prefix} {msg}")
