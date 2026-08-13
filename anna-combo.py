import os
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from colorama import Fore, init

init(autoreset=True)

GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
RESET = Fore.RESET


def safe_filename(name):
    """Convert a domain into a safe Windows filename."""

    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.strip(' .')

    if not name:
        name = "unknown"

    return name


def scan(line):
    """
    Extract email, domain, and password.

    Expected format:
    email@domain.com:password
    """

    pattern = re.compile(
        r'([A-Za-z0-9._%+-]+@'
        r'([A-Za-z0-9.-]+\.[A-Za-z]{2,}))'
        r':([^\s]+)'
    )

    match = pattern.search(line.strip())

    if match:
        email = match.group(1)
        domain = match.group(2).lower()
        password = match.group(3)

        combo = f"{email}:{password}"

        return domain, combo

    return None, None


def main():

    input_file = input("Input file name/path: ").strip()

    output_folder = input(
        YELLOW + "[!] Output folder name: "
    ).strip()

    if not output_folder:
        output_folder = "RESULT"

    # Thread input
    while True:
        try:
            threads = int(
                input(YELLOW + "[!] Number of threads: ").strip()
            )

            if threads < 1:
                print(RED + "[ERROR] Threads must be at least 1.")
                continue

            break

        except ValueError:
            print(RED + "[ERROR] Please enter a valid number.")


    # Check input file
    if not os.path.isfile(input_file):
        print(RED + "\n[ERROR] Input file not found!")
        return


    # Create output folder
    os.makedirs(output_folder, exist_ok=True)


    # Store combos grouped by domain
    domains = defaultdict(list)

    total_found = 0

    lock = Lock()


    print(
        YELLOW +
        f"\n[!] Processing with {threads} threads...\n"
    )


    try:
        with open(
            input_file,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            lines = list(f)


        with ThreadPoolExecutor(
            max_workers=threads
        ) as executor:

            futures = [
                executor.submit(scan, line)
                for line in lines
            ]


            for future in as_completed(futures):

                domain, combo = future.result()

                if domain and combo:

                    with lock:
                        domains[domain].append(combo)
                        total_found += 1

                    print(
                        f"{GREEN}[FOUND]{RESET} "
                        f"{combo} "
                        f"{YELLOW}-> {domain}{RESET}"
                    )


    except Exception as e:
        print(RED + f"\n[ERROR] {e}")
        return


    print(
        YELLOW +
        "\n[!] Saving results...\n"
    )


    # Save each domain
    for domain, combos in domains.items():

        domain_found = len(combos)

        clean_domain = safe_filename(domain)

        filename = f"{clean_domain}-[{domain_found}].txt"

        output_file = os.path.join(
            output_folder,
            filename
        )


        try:
            with open(
                output_file,
                "w",
                encoding="utf-8"
            ) as out:

                for combo in combos:
                    out.write(combo + "\n")


            print(
                f"{GREEN}[SAVED]{RESET} "
                f"{filename}"
            )


        except Exception as e:

            print(
                RED +
                f"[ERROR] Cannot save {filename}: {e}"
            )


    print(GREEN + "\nDone extracting.")

    print(
        YELLOW +
        f"Total combos found: {total_found}"
    )

    print(
        YELLOW +
        f"Total domains found: {len(domains)}"
    )

    print(
        YELLOW +
        f"Threads used: {threads}"
    )

    print(
        YELLOW +
        f"Output folder: {output_folder}"
    )


if __name__ == "__main__":
    main()
