import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import colorama
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

RESET = Style.RESET_ALL
BOLD = Style.BRIGHT


# ==========================================================
# SETTINGS
# ==========================================================

DEFAULT_BATCH_SIZE = 5000

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@"
    r"[A-Za-z0-9\-]+"
    r"(?:\.[A-Za-z0-9\-]+)*"
    r"\.[A-Za-z]{2,}\b",
    re.IGNORECASE
)


# ==========================================================
# PROVIDER FAMILIES
# ==========================================================

HOTMAIL_FAMILY = {
    "hotmail",
    "live",
    "outlook",
    "msn",
}

YAHOO_FAMILY = {
    "yahoo",
    "btinternet",
    "ymail",
    "rocketmail",
}

AOL_FAMILY = {
    "aol",
}


# ==========================================================
# EXCLUDED PROVIDERS
# These will NOT be written to any output file.
# ==========================================================

EXCLUDED_PROVIDERS = {
    "zoho",
    "mail",
    "gmx",
    "comcast",
    "juno",
    "netzero",
    "t-online",
    "proton",
    "icloud",
    "me",
    "mac",
    "yandex",
    "mail.ru",
    "web.de",
    "qq",
    "163",
    "126",
    "fastmail",
    "hey",
    "tutanota",
}


# ==========================================================
# COUNTRY / TLD GROUPS
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
# BUILD SUFFIX LOOKUP
# ==========================================================

SUFFIX_TO_COUNTRY = {}

for country, suffixes in COUNTRY_SUFFIXES.items():

    for suffix in suffixes:
        SUFFIX_TO_COUNTRY[suffix.upper()] = country


# ==========================================================
# COUNTRY DETECTION
# ==========================================================

def get_country(email):

    try:
        domain = email.rsplit("@", 1)[1].lower().strip()
    except Exception:
        return "Other_Country"

    parts = domain.split(".")

    if len(parts) < 2:
        return "Other_Country"

    # Check longest suffix first.
    # Example:
    # example.co.uk -> CO.UK
    # example.com.au -> COM.AU

    if len(parts) >= 3:

        last_two = (
            parts[-2] + "." + parts[-1]
        ).upper()

        if last_two in SUFFIX_TO_COUNTRY:
            return SUFFIX_TO_COUNTRY[last_two]

    last_one = parts[-1].upper()

    return SUFFIX_TO_COUNTRY.get(
        last_one,
        "Other_Country"
    )


# ==========================================================
# PROVIDER DETECTION
# ==========================================================

def get_provider_category(email):

    try:
        domain = email.rsplit("@", 1)[1].lower().strip()
    except Exception:
        return None

    domain = domain.removeprefix("www.")

    # ------------------------------------------------------
    # Check exact excluded domains first
    # ------------------------------------------------------

    if domain in EXCLUDED_PROVIDERS:
        return "Excluded"

    # ------------------------------------------------------
    # Provider name
    # ------------------------------------------------------

    provider = domain.split(".", 1)[0]

    # ------------------------------------------------------
    # Excluded providers
    # ------------------------------------------------------

    if provider in EXCLUDED_PROVIDERS:
        return "Excluded"

    # ------------------------------------------------------
    # Hotmail family
    # ------------------------------------------------------

    if provider in HOTMAIL_FAMILY:
        return "Hotmail_Family"

    # ------------------------------------------------------
    # Yahoo family
    # ------------------------------------------------------

    if provider in YAHOO_FAMILY:
        return "Yahoo_Family"

    # ------------------------------------------------------
    # AOL family
    # ------------------------------------------------------

    if provider in AOL_FAMILY:
        return "AOL_Family"

    return "Other"


# ==========================================================
# PROCESS ONE LINE
# ==========================================================

def process_line(line):

    results = []

    for match in EMAIL_PATTERN.finditer(line):

        email = match.group(0).strip().lower()

        if not email:
            continue

        category = get_provider_category(email)

        # Only requested families are exported.
        if category not in {
            "Hotmail_Family",
            "Yahoo_Family",
            "AOL_Family",
        }:
            continue

        country = get_country(email)

        results.append(
            (
                category,
                country,
                email
            )
        )

    return results


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
# COLORED OUTPUT
# ==========================================================

def info(message):

    print(
        f"{LIGHT_CYAN}{BOLD}[INFO]{RESET} "
        f"{message}"
    )


def success(message):

    print(
        f"{LIGHT_GREEN}{BOLD}[SUCCESS]{RESET} "
        f"{message}"
    )


def warning(message):

    print(
        f"{LIGHT_YELLOW}{BOLD}[NOTICE]{RESET} "
        f"{message}"
    )


def error(message):

    print(
        f"{LIGHT_RED}{BOLD}[ERROR]{RESET} "
        f"{message}"
    )


def found(message):

    print(
        f"{GREEN}{BOLD}[FOUND]{RESET} "
        f"{message}"
    )


def saved(message):

    print(
        f"{LIGHT_MAGENTA}{BOLD}[SAVED]{RESET} "
        f"{message}"
    )


# ==========================================================
# LOGO
# ==========================================================

def logo():

    print(
        f"""
{LIGHT_CYAN}{BOLD}
       ___
      o|* *|o  ╔╦═╦╗╔╦╗╔╦═╦╗
      o|* *|o  ║║╔╣╚╝║║║║║║║
      o|* *|o  ║║╚╣╔╗║╚╝║╩║║
       \\===/   ║╚═╩╝╚╩══╩╩╝║
        |||    ╚═══════════╝
        |||  EMAIL FAMILY + COUNTRY
{LIGHT_YELLOW}
       EMAIL-ONLY CLASSIFIER
{RESET}
"""
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    logo()

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 70}"
        f"{RESET}"
    )

    print(
        f"{LIGHT_YELLOW}{BOLD}"
        f"       EMAIL FAMILY + COUNTRY FILTER"
        f"{RESET}"
    )

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 70}"
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

        output_folder = os.path.abspath(
            output_folder
        )

        try:

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
    # THREADS
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

            batch_input = input(
                f"{LIGHT_GREEN}[!]{RESET} "
                f"Batch Size "
                f"[{DEFAULT_BATCH_SIZE}]: "
            ).strip()

            if not batch_input:

                batch_size = (
                    DEFAULT_BATCH_SIZE
                )

            else:

                batch_size = int(
                    batch_input
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
    # FILE INFORMATION
    # ======================================================

    file_size = os.path.getsize(
        input_file
    )

    file_size_gb = (
        file_size / (1024 ** 3)
    )

    print()

    info(
        f"Input File    : "
        f"{input_file}"
    )

    info(
        f"Output Folder : "
        f"{output_folder}"
    )

    info(
        f"File Size     : "
        f"{file_size_gb:.2f} GB"
    )

    info(
        f"Threads       : "
        f"{threads}"
    )

    info(
        f"Batch Size    : "
        f"{batch_size}"
    )

    info(
        f"Country Groups: "
        f"{len(COUNTRY_SUFFIXES)} + Other_Country"
    )

    info(
        f"Excluded      : "
        f"{len(EXCLUDED_PROVIDERS)} providers"
    )

    print()

    # ======================================================
    # TEMP FILES
    # ======================================================

    temp_files = {}

    # Family files
    family_names = [
        "Hotmail_Family",
        "Yahoo_Family",
        "AOL_Family",
    ]

    for family in family_names:

        temp_files[family] = os.path.join(
            output_folder,
            family + ".tmp"
        )

    # Country files
    for country in COUNTRY_SUFFIXES:

        temp_files[country] = os.path.join(
            output_folder,
            country + ".tmp"
        )

    temp_files["Other_Country"] = os.path.join(
        output_folder,
        "Other_Country.tmp"
    )

    # Remove old temporary files
    for path in temp_files.values():

        try:

            if os.path.exists(path):
                os.remove(path)

        except Exception as e:

            error(
                f"Cannot remove temp file "
                f"{path}: {e}"
            )

            return

    # ======================================================
    # COUNTERS
    # ======================================================

    family_counts = {
        "Hotmail_Family": 0,
        "Yahoo_Family": 0,
        "AOL_Family": 0,
    }

    country_counts = {
        country: 0
        for country in COUNTRY_SUFFIXES
    }

    country_counts["Other_Country"] = 0

    seen = set()

    total_processed = 0
    total_found = 0

    lock = threading.Lock()

    start_time = time.time()

    # ======================================================
    # SAVE EMAIL
    # ======================================================

    def save_email(
        family,
        country,
        email
    ):

        try:

            # ----------------------------------------------
            # Family file
            # ----------------------------------------------

            with open(
                temp_files[family],
                "a",
                encoding="utf-8",
                buffering=1024 * 1024
            ) as out:

                out.write(
                    email + "\n"
                )

            # ----------------------------------------------
            # Country file
            # ----------------------------------------------

            with open(
                temp_files[country],
                "a",
                encoding="utf-8",
                buffering=1024 * 1024
            ) as out:

                out.write(
                    email + "\n"
                )

            return True

        except Exception as e:

            error(
                f"Save error: {e}"
            )

            return False

    # ======================================================
    # HANDLE COMPLETED FUTURES
    # ======================================================

    def handle_completed(
        done_futures
    ):

        nonlocal total_processed
        nonlocal total_found

        for future in done_futures:

            try:

                found_items = (
                    future.result()
                )

            except Exception as e:

                error(
                    f"Processing error: {e}"
                )

                found_items = []

            with lock:

                total_processed += 1

                for (
                    family,
                    country,
                    email
                ) in found_items:

                    # --------------------------------------
                    # Global duplicate check
                    # --------------------------------------

                    if email in seen:
                        continue

                    seen.add(email)

                    # --------------------------------------
                    # Save
                    # --------------------------------------

                    if save_email(
                        family,
                        country,
                        email
                    ):

                        family_counts[
                            family
                        ] += 1

                        country_counts[
                            country
                        ] += 1

                        total_found += 1

                        found(
                            f"{email} "
                            f"[{family}] "
                            f"[{country}]"
                        )

                # ------------------------------------------
                # Progress
                # ------------------------------------------

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
                        f"Hotmail: "
                        f"{family_counts['Hotmail_Family']:,} | "
                        f"Yahoo: "
                        f"{family_counts['Yahoo_Family']:,} | "
                        f"AOL: "
                        f"{family_counts['AOL_Family']:,} | "
                        f"Time: "
                        f"{elapsed:.1f}s"
                    )

    # ======================================================
    # START STREAMING
    # ======================================================

    warning(
        "Starting large-file streaming scan..."
    )

    pending = set()

    try:

        with ThreadPoolExecutor(
            max_workers=threads
        ) as executor:

            with open(
                input_file,
                "r",
                encoding="utf-8",
                errors="ignore",
                buffering=1024 * 1024
            ) as file:

                for line in file:

                    future = (
                        executor.submit(
                            process_line,
                            line
                        )
                    )

                    pending.add(
                        future
                    )

                    # --------------------------------------
                    # Bounded queue
                    # --------------------------------------

                    if len(pending) >= batch_size:

                        done, pending = wait(
                            pending,
                            return_when=(
                                FIRST_COMPLETED
                            )
                        )

                        handle_completed(
                            done
                        )

                # ------------------------------------------
                # Remaining tasks
                # ------------------------------------------

                while pending:

                    done, pending = wait(
                        pending,
                        return_when=(
                            FIRST_COMPLETED
                        )
                    )

                    handle_completed(
                        done
                    )

    except KeyboardInterrupt:

        warning(
            "Stopped by user. "
            "Current results were saved."
        )

    except Exception as e:

        error(
            f"Fatal processing error: {e}"
        )

    # ======================================================
    # FINALIZE FAMILY FILES
    # ======================================================

    print()

    warning(
        "Finalizing family files..."
    )

    final_files = []

    for family in family_names:

        count = family_counts[
            family
        ]

        temp_file = temp_files[
            family
        ]

        filename = (
            f"{safe_filename(family)}"
            f"[{count}].txt"
        )

        final_file = os.path.join(
            output_folder,
            filename
        )

        try:

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

                final_files.append(
                    filename
                )

                saved(
                    f"{filename} "
                    f"-> {count:,} emails"
                )

        except Exception as e:

            error(
                f"Cannot finalize "
                f"{filename}: {e}"
            )

    # ======================================================
    # FINALIZE COUNTRY FILES
    # ======================================================

    print()

    warning(
        "Finalizing country files..."
    )

    for country in sorted(
        country_counts.keys()
    ):

        count = country_counts[
            country
        ]

        temp_file = temp_files[
            country
        ]

        filename = (
            f"{safe_filename(country)}"
            f"[{count}].txt"
        )

        final_file = os.path.join(
            output_folder,
            filename
        )

        try:

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

                final_files.append(
                    filename
                )

                saved(
                    f"{filename} "
                    f"-> {count:,} emails"
                )

        except Exception as e:

            error(
                f"Cannot finalize "
                f"{filename}: {e}"
            )

    # ======================================================
    # RESULT NOTICE
    # ======================================================

    elapsed = (
        time.time()
        - start_time
    )

    notice_file = os.path.join(
        output_folder,
        "RESULT_NOTICE.txt"
    )

    try:

        with open(
            notice_file,
            "w",
            encoding="utf-8"
        ) as notice:

            notice.write(
                "=" * 70
                + "\n"
            )

            notice.write(
                "EMAIL FAMILY + COUNTRY "
                "FILTER RESULT\n"
            )

            notice.write(
                "=" * 70
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
                f"FILE SIZE:\n"
                f"{file_size_gb:.2f} GB\n\n"
            )

            notice.write(
                f"THREADS:\n"
                f"{threads}\n\n"
            )

            notice.write(
                f"BATCH SIZE:\n"
                f"{batch_size}\n\n"
            )

            notice.write(
                f"LINES PROCESSED:\n"
                f"{total_processed:,}\n\n"
            )

            notice.write(
                f"UNIQUE EXPORTED EMAILS:\n"
                f"{total_found:,}\n\n"
            )

            notice.write(
                "=" * 70
                + "\n"
            )

            notice.write(
                "FAMILY RESULTS\n"
            )

            notice.write(
                "=" * 70
                + "\n"
            )

            for family in family_names:

                count = family_counts[
                    family
                ]

                filename = (
                    f"{family}"
                    f"[{count}].txt"
                )

                notice.write(
                    f"{filename} "
                    f"= {count:,}\n"
                )

            notice.write(
                "\n"
            )

            notice.write(
                "=" * 70
                + "\n"
            )

            notice.write(
                "COUNTRY RESULTS\n"
            )

            notice.write(
                "=" * 70
                + "\n"
            )

            for country in sorted(
                country_counts.keys()
            ):

                count = country_counts[
                    country
                ]

                filename = (
                    f"{country}"
                    f"[{count}].txt"
                )

                notice.write(
                    f"{filename} "
                    f"= {count:,}\n"
                )

            notice.write(
                "\n"
            )

            notice.write(
                f"TIME:\n"
                f"{elapsed:.2f} seconds\n"
            )

        saved(
            f"RESULT_NOTICE.txt"
        )

    except Exception as e:

        error(
            f"Cannot save result notice: "
            f"{e}"
        )

    # ======================================================
    # FINAL SUMMARY
    # ======================================================

    print()

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 70}"
        f"{RESET}"
    )

    success(
        "DONE"
    )

    info(
        f"Lines Processed : "
        f"{total_processed:,}"
    )

    info(
        f"Unique Found    : "
        f"{total_found:,}"
    )

    print()

    info(
        f"Hotmail Family  : "
        f"{family_counts['Hotmail_Family']:,}"
    )

    info(
        f"Yahoo Family    : "
        f"{family_counts['Yahoo_Family']:,}"
    )

    info(
        f"AOL Family      : "
        f"{family_counts['AOL_Family']:,}"
    )

    print()

    info(
        f"Country Files   : "
        f"{len(country_counts):,}"
    )

    info(
        f"Excluded        : "
        f"{len(EXCLUDED_PROVIDERS)} providers"
    )

    info(
        f"Time            : "
        f"{elapsed:.2f} seconds"
    )

    info(
        f"Output Folder   : "
        f"{output_folder}"
    )

    print(
        f"{LIGHT_CYAN}"
        f"{'=' * 70}"
        f"{RESET}"
    )

    input(
        f"\n{LIGHT_YELLOW}"
        f"Press ENTER to exit..."
        f"{RESET}"
    )


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    main()
