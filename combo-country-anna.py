import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import colorama
import tldextract
from colorama import Fore, Style


# ==========================================================
# WINDOWS / POWERSHELL COLOR SUPPORT
# ==========================================================

colorama.just_fix_windows_console()
colorama.init(autoreset=True)


# ==========================================================
# COLORS
# ==========================================================

GREEN = Fore.GREEN
LIGHT_GREEN = Fore.LIGHTGREEN_EX
RED = Fore.RED
LIGHT_RED = Fore.LIGHTRED_EX
YELLOW = Fore.YELLOW
LIGHT_YELLOW = Fore.LIGHTYELLOW_EX
CYAN = Fore.CYAN
LIGHT_CYAN = Fore.LIGHTCYAN_EX
MAGENTA = Fore.MAGENTA
LIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
WHITE = Fore.WHITE
LIGHT_WHITE = Fore.LIGHTWHITE_EX

RESET = Style.RESET_ALL
BOLD = Style.BRIGHT


# ==========================================================
# SETTINGS
# ==========================================================

DEFAULT_BATCH_SIZE = 5000


# ==========================================================
# 30 POPULAR COUNTRY / DOMAIN GROUPS
#
# Every recognized public suffix is mapped to one of these
# country groups. Anything not listed goes to Other_Country.
# ==========================================================

COUNTRY_SUFFIXES = {

    "United_States": {
        "US",
        "COM",
        "NET",
        "ORG",
        "EDU",
        "GOV",
        "MIL",
    },

    "United_Kingdom": {
        "UK",
        "CO.UK",
        "ORG.UK",
        "AC.UK",
        "GOV.UK",
        "ME.UK",
        "SCH.UK",
    },

    "Australia": {
        "AU",
        "COM.AU",
        "NET.AU",
        "ORG.AU",
        "EDU.AU",
        "GOV.AU",
        "ASN.AU",
        "ID.AU",
    },

    "Canada": {
        "CA",
    },

    "Germany": {
        "DE",
    },

    "France": {
        "FR",
    },

    "Italy": {
        "IT",
    },

    "Spain": {
        "ES",
    },

    "Netherlands": {
        "NL",
    },

    "Belgium": {
        "BE",
    },

    "Switzerland": {
        "CH",
    },

    "Austria": {
        "AT",
    },

    "Sweden": {
        "SE",
    },

    "Norway": {
        "NO",
    },

    "Denmark": {
        "DK",
    },

    "Finland": {
        "FI",
    },

    "Poland": {
        "PL",
    },

    "Russia": {
        "RU",
    },

    "Ukraine": {
        "UA",
    },

    "Brazil": {
        "BR",
        "COM.BR",
        "NET.BR",
        "ORG.BR",
    },

    "Mexico": {
        "MX",
        "COM.MX",
        "NET.MX",
        "ORG.MX",
        "GOB.MX",
    },

    "Argentina": {
        "AR",
        "COM.AR",
        "NET.AR",
        "ORG.AR",
    },

    "India": {
        "IN",
        "CO.IN",
        "NET.IN",
        "ORG.IN",
        "FIRM.IN",
        "GEN.IN",
        "IND.IN",
    },

    "Japan": {
        "JP",
        "CO.JP",
        "NE.JP",
        "OR.JP",
        "AC.JP",
        "GO.JP",
    },

    "South_Korea": {
        "KR",
        "CO.KR",
        "OR.KR",
        "NE.KR",
        "AC.KR",
        "GO.KR",
    },

    "China": {
        "CN",
        "COM.CN",
        "NET.CN",
        "ORG.CN",
        "GOV.CN",
        "AC.CN",
    },

    "Indonesia": {
        "ID",
        "CO.ID",
        "WEB.ID",
        "OR.ID",
        "AC.ID",
        "GO.ID",
    },

    "Singapore": {
        "SG",
        "COM.SG",
        "NET.SG",
        "ORG.SG",
        "EDU.SG",
        "GOV.SG",
    },

    "New_Zealand": {
        "NZ",
        "CO.NZ",
        "NET.NZ",
        "ORG.NZ",
        "AC.NZ",
        "GOVT.NZ",
    },

    "South_Africa": {
        "ZA",
        "CO.ZA",
        "ORG.ZA",
        "NET.ZA",
        "AC.ZA",
        "GOV.ZA",
    },
}


# ==========================================================
# BUILD FAST SUFFIX -> COUNTRY LOOKUP
# ==========================================================

SUFFIX_TO_COUNTRY = {}

for country_name, suffixes in COUNTRY_SUFFIXES.items():
    for suffix in suffixes:
        SUFFIX_TO_COUNTRY[suffix.upper()] = country_name


# ==========================================================
# COLORED OUTPUT
# ==========================================================

def info(message):
    print(f"{LIGHT_CYAN}{BOLD}[INFO]{RESET} {message}")


def success(message):
    print(f"{LIGHT_GREEN}{BOLD}[SUCCESS]{RESET} {message}")


def warning(message):
    print(f"{LIGHT_YELLOW}{BOLD}[NOTICE]{RESET} {message}")


def error(message):
    print(f"{LIGHT_RED}{BOLD}[ERROR]{RESET} {message}")


def saved(message):
    print(f"{LIGHT_MAGENTA}{BOLD}[SAVED]{RESET} {message}")


def found(message):
    print(f"{GREEN}{BOLD}[FOUND]{RESET} {message}")


# ==========================================================
# LOGO
# ==========================================================

def logo():

    print(f"""
{LIGHT_CYAN}{BOLD}
       ___
     o|* *|o  ╔╦═╦╗╔╦╗╔╦═╦╗
     o|* *|o  ║║╔╣╚╝║║║║║║║
     o|* *|o  ║║╚╣╔╗║╚╝║╩║║
      \\===/   ║╚═╩╝╚╩══╩╩╝║
       |||    ╚═══════════╝
       |||  K.E.U.R - C.O.M.B.O.S

{LIGHT_YELLOW}      By : AnnaQitty
{RESET}
""")


# ==========================================================
# TLD EXTRACTOR
#
# Uses bundled suffix data.
# No online suffix download required.
# ==========================================================

extractor = tldextract.TLDExtract(
    suffix_list_urls=None
)


# ==========================================================
# EMAIL:PASSWORD PATTERN
# ==========================================================

COMBO_PATTERN = re.compile(
    r'([A-Za-z0-9._%+\-]+@'
    r'[A-Za-z0-9\-]+'
    r'(?:\.[A-Za-z0-9\-]+)*'
    r'\.[A-Za-z]{2,})'
    r':([^\s:]+)'
)


# ==========================================================
# GET PUBLIC SUFFIX
#
# Examples:
#
# test@gmail.com
# -> COM
#
# test@example.co.uk
# -> CO.UK
#
# test@example.com.au
# -> COM.AU
# ==========================================================

def get_tld(email):

    try:

        domain = email.rsplit(
            "@",
            1
        )[1].lower().strip()

        extracted = extractor(domain)

        if not extracted.suffix:
            return None

        return extracted.suffix.upper()

    except Exception:
        return None


# ==========================================================
# GET COUNTRY GROUP
#
# Unknown suffixes automatically go to Other_Country.
# ==========================================================

def get_country_group(tld):

    if not tld:
        return "Other_Country"

    return SUFFIX_TO_COUNTRY.get(
        tld.upper(),
        "Other_Country"
    )


# ==========================================================
# SAFE FILENAME
# ==========================================================

def safe_filename(name):

    return re.sub(
        r'[<>:"/\\|?*]',
        "_",
        name
    )


# ==========================================================
# PROCESS ONE LINE
# ==========================================================

def process_line(line):

    items = []

    for match in COMBO_PATTERN.finditer(line):

        email = match.group(1).strip()
        password = match.group(2).strip()

        if not email or not password:
            continue

        tld = get_tld(email)

        if not tld:
            continue

        country = get_country_group(tld)

        combo = f"{email}:{password}"

        items.append(
            (
                country,
                combo
            )
        )

    return items


# ==========================================================
# SAVE RESULT
#
# Results are saved immediately.
# ==========================================================

def save_result(
    output_folder,
    all_file,
    country_files,
    country,
    combo
):

    try:

        # Save to ALL_RESULTS
        with open(
            all_file,
            "a",
            encoding="utf-8",
            buffering=1024 * 1024
        ) as out:

            out.write(combo + "\n")


        # Create temporary country file path
        if country not in country_files:

            filename = (
                safe_filename(country)
                + ".tmp"
            )

            country_files[country] = os.path.join(
                output_folder,
                filename
            )


        # Save to country file
        with open(
            country_files[country],
            "a",
            encoding="utf-8",
            buffering=1024 * 1024
        ) as out:

            out.write(combo + "\n")

        return True

    except Exception as e:

        error(
            f"Save error: {e}"
        )

        return False


# ==========================================================
# MAIN
# ==========================================================

def main():

    logo()

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 65}"
        f"{RESET}"
    )

    print(
        f"{LIGHT_YELLOW}{BOLD}"
        f"      LARGE FILE COUNTRY COMBO EXTRACTOR"
        f"{RESET}"
    )

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 65}"
        f"{RESET}"
    )


    # ======================================================
    # INPUT FILE
    # ======================================================

    while True:

        input_file = input(
            f"{LIGHT_GREEN}[!]{RESET} "
            f"Input File: "
        ).strip().strip('"')

        if not input_file:

            error(
                "Input file cannot be empty."
            )

            continue

        input_file = os.path.abspath(
            input_file
        )

        if not os.path.isfile(
            input_file
        ):

            error(
                "Input file not found."
            )

            continue

        break


    # ======================================================
    # OUTPUT FOLDER
    # ======================================================

    while True:

        output_folder = input(
            f"{LIGHT_GREEN}[!]{RESET} "
            f"Output Folder: "
        ).strip().strip('"')

        if not output_folder:

            error(
                "Output folder cannot be empty."
            )

            continue

        try:

            output_folder = os.path.abspath(
                output_folder
            )

            os.makedirs(
                output_folder,
                exist_ok=True
            )

            break

        except Exception as e:

            error(
                f"Cannot create output folder: {e}"
            )


    # ======================================================
    # THREAD COUNT
    # ======================================================

    while True:

        try:

            threads = int(
                input(
                    f"{LIGHT_GREEN}[!]{RESET} "
                    f"Number of Threads: "
                ).strip()
            )

            if threads < 1:

                error(
                    "Threads must be at least 1."
                )

                continue

            break

        except ValueError:

            error(
                "Please enter a valid number."
            )


    # ======================================================
    # BATCH SIZE
    # ======================================================

    while True:

        try:

            batch_size_input = input(
                f"{LIGHT_GREEN}[!]{RESET} "
                f"Batch Size "
                f"[{DEFAULT_BATCH_SIZE}]: "
            ).strip()

            if not batch_size_input:

                batch_size = DEFAULT_BATCH_SIZE

            else:

                batch_size = int(
                    batch_size_input
                )

            if batch_size < 1:

                error(
                    "Batch size must be at least 1."
                )

                continue

            break

        except ValueError:

            error(
                "Please enter a valid number."
            )


    # ======================================================
    # FILE SIZE
    # ======================================================

    file_size = os.path.getsize(
        input_file
    )

    file_size_gb = (
        file_size / (1024 ** 3)
    )


    print()

    info(
        f"Input File    : {input_file}"
    )

    info(
        f"Output Folder : {output_folder}"
    )

    info(
        f"File Size     : "
        f"{file_size_gb:.2f} GB"
    )

    info(
        f"Threads       : {threads}"
    )

    info(
        f"Batch Size    : {batch_size}"
    )

    info(
        f"Country Groups: "
        f"{len(COUNTRY_SUFFIXES)} + Other_Country"
    )

    print()


    # ======================================================
    # TEMP OUTPUT FILES
    # ======================================================

    all_temp_file = os.path.join(
        output_folder,
        "ALL_RESULTS.tmp"
    )


    # Remove old temporary ALL file
    if os.path.exists(
        all_temp_file
    ):

        try:

            os.remove(
                all_temp_file
            )

        except Exception as e:

            error(
                f"Cannot remove old temp file: {e}"
            )

            return


    country_files = {}

    seen = set()

    total_processed = 0
    total_found = 0

    results_count = {}

    lock = threading.Lock()

    start_time = time.time()


    # ======================================================
    # HANDLE COMPLETED FUTURES
    # ======================================================

    def handle_completed(done_futures):

        nonlocal total_processed
        nonlocal total_found

        for future in done_futures:

            try:

                found_items = future.result()

            except Exception as e:

                error(
                    f"Processing error: {e}"
                )

                found_items = []


            with lock:

                total_processed += 1


                for country, combo in found_items:

                    normalized_combo = combo.lower()

                    if normalized_combo in seen:
                        continue


                    seen.add(
                        normalized_combo
                    )


                    if save_result(
                        output_folder,
                        all_temp_file,
                        country_files,
                        country,
                        combo
                    ):

                        total_found += 1

                        results_count[country] = (
                            results_count.get(
                                country,
                                0
                            )
                            + 1
                        )

                        found(
                            f"{combo} "
                            f"[{country}]"
                        )


                if total_processed % 10000 == 0:

                    elapsed = (
                        time.time()
                        - start_time
                    )

                    info(
                        f"Processed: "
                        f"{total_processed:,} | "
                        f"Found: "
                        f"{total_found:,} | "
                        f"Time: "
                        f"{elapsed:.1f}s"
                    )


    # ======================================================
    # STREAM FILE + BOUNDED THREAD QUEUE
    # ======================================================

    warning(
        "Starting large-file streaming scan..."
    )

    pending = set()


    with ThreadPoolExecutor(
        max_workers=threads
    ) as executor:

        try:

            with open(
                input_file,
                "r",
                encoding="utf-8",
                errors="ignore",
                buffering=1024 * 1024
            ) as file:

                for line in file:

                    future = executor.submit(
                        process_line,
                        line
                    )

                    pending.add(
                        future
                    )


                    # Keep queue bounded
                    if len(pending) >= batch_size:

                        done, pending = wait(
                            pending,
                            return_when=FIRST_COMPLETED
                        )

                        handle_completed(
                            done
                        )


                # Process remaining work
                while pending:

                    done, pending = wait(
                        pending,
                        return_when=FIRST_COMPLETED
                    )

                    handle_completed(
                        done
                    )


        except KeyboardInterrupt:

            warning(
                "Stopped by user. "
                "Saving current results..."
            )


    # ======================================================
    # RENAME ALL RESULTS FILE
    # ======================================================

    all_filename = (
        f"ALL_RESULTS[{total_found}].txt"
    )

    all_final_file = os.path.join(
        output_folder,
        all_filename
    )


    if os.path.exists(
        all_final_file
    ):

        os.remove(
            all_final_file
        )


    if os.path.exists(
        all_temp_file
    ):

        os.rename(
            all_temp_file,
            all_final_file
        )


    # ======================================================
    # RENAME COUNTRY TEMP FILES
    # ======================================================

    split_files = []

    warning(
        "Finalizing country files..."
    )


    for country in sorted(
        country_files.keys()
    ):

        temp_file = country_files[
            country
        ]

        count = results_count.get(
            country,
            0
        )

        filename = (
            f"{safe_filename(country)}"
            f"[{count}].txt"
        )

        final_file = os.path.join(
            output_folder,
            filename
        )


        if os.path.exists(
            final_file
        ):

            os.remove(
                final_file
            )


        if os.path.exists(
            temp_file
        ):

            os.rename(
                temp_file,
                final_file
            )

            split_files.append(
                filename
            )

            saved(
                filename
            )


    # ======================================================
    # RESULT NOTICE
    # ======================================================

    notice_file = os.path.join(
        output_folder,
        "RESULT_NOTICE.txt"
    )

    elapsed = (
        time.time()
        - start_time
    )


    try:

        with open(
            notice_file,
            "w",
            encoding="utf-8"
        ) as notice:

            notice.write(
                "=" * 65
                + "\n"
            )

            notice.write(
                "LARGE FILE COUNTRY EXTRACTION "
                "RESULT NOTICE\n"
            )

            notice.write(
                "=" * 65
                + "\n\n"
            )


            notice.write(
                f"INPUT FILE:\n"
                f"{input_file}\n\n"
            )

            notice.write(
                f"OUTPUT FOLDER:\n"
                f"{output_folder}\n\n"
            )

            notice.write(
                f"INPUT FILE SIZE: "
                f"{file_size_gb:.2f} GB\n"
            )

            notice.write(
                f"THREADS USED: "
                f"{threads}\n"
            )

            notice.write(
                f"BATCH SIZE: "
                f"{batch_size}\n"
            )

            notice.write(
                f"LINES PROCESSED: "
                f"{total_processed:,}\n"
            )

            notice.write(
                f"UNIQUE RESULTS: "
                f"{total_found:,}\n"
            )

            notice.write(
                f"TIME: "
                f"{elapsed:.2f} seconds\n\n"
            )


            notice.write(
                "=" * 65
                + "\n"
            )

            notice.write(
                f"ALL RESULTS: "
                f"{all_filename}\n"
            )

            notice.write(
                "=" * 65
                + "\n\n"
            )


            notice.write(
                "COUNTRY FILES\n\n"
            )


            for country in sorted(
                results_count.keys()
            ):

                count = results_count[
                    country
                ]

                filename = (
                    f"{safe_filename(country)}"
                    f"[{count}].txt"
                )

                notice.write(
                    f"{filename} "
                    f"= {count:,} results\n"
                )


            notice.write(
                f"\nTOTAL COUNTRY FILES: "
                f"{len(split_files)}\n"
            )


        saved(
            f"RESULT NOTICE -> "
            f"{notice_file}"
        )


    except Exception as e:

        error(
            f"Cannot save notice: {e}"
        )


    # ======================================================
    # DONE
    # ======================================================

    print()

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 65}"
        f"{RESET}"
    )

    success(
        "DONE EXTRACTING"
    )

    info(
        f"Lines Processed : "
        f"{total_processed:,}"
    )

    info(
        f"Unique Results  : "
        f"{total_found:,}"
    )

    info(
        f"Country Files   : "
        f"{len(split_files):,}"
    )

    info(
        f"Time            : "
        f"{elapsed:.2f} seconds"
    )

    saved(
        f"All Results -> "
        f"{all_final_file}"
    )

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 65}"
        f"{RESET}"
    )

    input(
        f"\n{LIGHT_YELLOW}"
        f"Press ENTER to exit..."
        f"{RESET}"
    )


if __name__ == "__main__":
    main()
