import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    import colorama
    colorama.init(autoreset=True)
    GREEN = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    RED = colorama.Fore.RED
    CYAN = colorama.Fore.CYAN
    RESET = colorama.Fore.RESET
except ImportError:
    GREEN = YELLOW = RED = CYAN = RESET = ""


# =====================================================================
# KNOWN DOMAINS (exact match, checked FIRST)
# =====================================================================
KNOWN_DOMAINS = {
    # --- Hotmail Family ---
    "hotmail.com": "Hotmail Family",
    "hotmail.co.uk": "Hotmail Family",
    "hotmail.de": "Hotmail Family",
    "hotmail.fr": "Hotmail Family",
    "hotmail.it": "Hotmail Family",
    "hotmail.es": "Hotmail Family",
    "hotmail.ca": "Hotmail Family",
    "hotmail.com.au": "Hotmail Family",
    "hotmail.co.jp": "Hotmail Family",
    "hotmail.co.in": "Hotmail Family",
    "hotmail.com.br": "Hotmail Family",
    "hotmail.com.mx": "Hotmail Family",
    "hotmail.com.ar": "Hotmail Family",
    "hotmail.cl": "Hotmail Family",
    "hotmail.be": "Hotmail Family",
    "hotmail.nl": "Hotmail Family",
    "hotmail.at": "Hotmail Family",
    "hotmail.ch": "Hotmail Family",
    "hotmail.dk": "Hotmail Family",
    "hotmail.no": "Hotmail Family",
    "hotmail.se": "Hotmail Family",
    "hotmail.fi": "Hotmail Family",
    "hotmail.pt": "Hotmail Family",
    "hotmail.gr": "Hotmail Family",
    "hotmail.pl": "Hotmail Family",
    "hotmail.cz": "Hotmail Family",
    "hotmail.hu": "Hotmail Family",
    "hotmail.ro": "Hotmail Family",
    "hotmail.ru": "Hotmail Family",
    "hotmail.co.za": "Hotmail Family",
    "hotmail.co.nz": "Hotmail Family",
    "hotmail.com.tr": "Hotmail Family",
    "hotmail.co.il": "Hotmail Family",

    "outlook.com": "Hotmail Family",
    "outlook.co.uk": "Hotmail Family",
    "outlook.de": "Hotmail Family",
    "outlook.fr": "Hotmail Family",
    "outlook.it": "Hotmail Family",
    "outlook.es": "Hotmail Family",
    "outlook.ca": "Hotmail Family",
    "outlook.com.au": "Hotmail Family",
    "outlook.co.jp": "Hotmail Family",
    "outlook.co.in": "Hotmail Family",
    "outlook.com.br": "Hotmail Family",
    "outlook.com.mx": "Hotmail Family",

    "msn.com": "Hotmail Family",

    # --- Yahoo Family ---
    "yahoo.com": "Yahoo Family",
    "yahoo.co.uk": "Yahoo Family",
    "yahoo.ca": "Yahoo Family",
    "yahoo.com.au": "Yahoo Family",
    "yahoo.co.nz": "Yahoo Family",
    "yahoo.co.in": "Yahoo Family",
    "yahoo.co.jp": "Yahoo Family",
    "yahoo.com.hk": "Yahoo Family",
    "yahoo.com.tw": "Yahoo Family",
    "yahoo.com.sg": "Yahoo Family",
    "yahoo.com.my": "Yahoo Family",
    "yahoo.com.ph": "Yahoo Family",
    "yahoo.co.id": "Yahoo Family",
    "yahoo.co.th": "Yahoo Family",
    "yahoo.com.br": "Yahoo Family",
    "yahoo.com.mx": "Yahoo Family",
    "yahoo.com.ar": "Yahoo Family",
    "yahoo.cl": "Yahoo Family",
    "yahoo.com.co": "Yahoo Family",
    "yahoo.com.pe": "Yahoo Family",
    "yahoo.co.ve": "Yahoo Family",
    "yahoo.es": "Yahoo Family",
    "yahoo.fr": "Yahoo Family",
    "yahoo.de": "Yahoo Family",
    "yahoo.it": "Yahoo Family",
    "yahoo.nl": "Yahoo Family",
    "yahoo.be": "Yahoo Family",
    "yahoo.ch": "Yahoo Family",
    "yahoo.at": "Yahoo Family",
    "yahoo.dk": "Yahoo Family",
    "yahoo.se": "Yahoo Family",
    "yahoo.no": "Yahoo Family",
    "yahoo.fi": "Yahoo Family",
    "yahoo.pl": "Yahoo Family",
    "yahoo.ro": "Yahoo Family",
    "yahoo.ru": "Yahoo Family",
    "yahoo.com.tr": "Yahoo Family",
    "yahoo.gr": "Yahoo Family",
    "yahoo.pt": "Yahoo Family",
    "yahoo.co.za": "Yahoo Family",

    # --- Gmail Family ---
    "gmail.com": "Gmail Family",
    "googlemail.com": "Gmail Family",

    # --- iCloud Family ---
    "icloud.com": "iCloud Family",
    "me.com": "iCloud Family",
    "mac.com": "iCloud Family",

    # --- AOL Family ---
    "aol.com": "AOL Family",
    "aol.co.uk": "AOL Family",
    "aol.de": "AOL Family",
    "aol.fr": "AOL Family",
    "aol.it": "AOL Family",
    "aol.es": "AOL Family",
    "aol.ca": "AOL Family",
    "aol.com.au": "AOL Family",
    "aol.co.jp": "AOL Family",
    "aol.com.br": "AOL Family",

    # --- GMX Family ---
    "gmx.com": "GMX Family",
    "gmx.de": "GMX Family",
    "gmx.at": "GMX Family",
    "gmx.ch": "GMX Family",
    "gmx.net": "GMX Family",
    "gmx.org": "GMX Family",

    # --- WEB.DE ---
    "web.de": "WEB.DE Family",

    # --- Freenet / Mail.de ---
    "freenet.de": "Freenet Family",
    "mail.de": "Mail.de Family",

    # --- T-Online ---
    "t-online.de": "T-Online Family",

    # --- Mail.ru Family ---
    "mail.ru": "Mail.ru Family",
    "inbox.ru": "Mail.ru Family",
    "list.ru": "Mail.ru Family",
    "bk.ru": "Mail.ru Family",

    # --- Yandex Family ---
    "yandex.ru": "Yandex Family",
    "yandex.com": "Yandex Family",

    # --- Proton Family ---
    "proton.me": "Proton Family",
    "protonmail.com": "Proton Family",
    "pm.me": "Proton Family",

    # --- Zoho Family ---
    "zoho.com": "Zoho Family",
    "zohomail.com": "Zoho Family",

    # --- Fastmail Family ---
    "fastmail.com": "Fastmail Family",
    "fastmail.fm": "Fastmail Family",

    # --- Mail.com Family ---
    "mail.com": "Mail.com Family",
    "email.com": "Mail.com Family",
    "usa.com": "Mail.com Family",
    "myself.com": "Mail.com Family",
    "post.com": "Mail.com Family",
    "consultant.com": "Mail.com Family",
    "dr.com": "Mail.com Family",
    "engineer.com": "Mail.com Family",
    "europe.com": "Mail.com Family",
    "asia.com": "Mail.com Family",
    "iname.com": "Mail.com Family",
    "writeme.com": "Mail.com Family",
    "techie.com": "Mail.com Family",

    # --- Verizon ---
    "verizon.net": "Verizon Family",

    # --- Comcast ---
    "comcast.net": "Comcast Family",

    # --- AT&T ---
    "att.net": "AT&T Family",
    "sbcglobal.net": "AT&T Family",
    "bellsouth.net": "AT&T Family",
    "prodigy.net": "AT&T Family",

    # --- UK ISP ---
    "btinternet.com": "BT Family",
    "btopenworld.com": "BT Family",
    "talktalk.net": "TalkTalk Family",
    "virginmedia.com": "Virgin Media Family",
    "sky.com": "Sky Family",

    # --- France ---
    "orange.fr": "Orange Family",
    "wanadoo.fr": "Orange Family",
    "sfr.fr": "SFR Family",
    "free.fr": "Free Family",
    "laposte.net": "La Poste Family",

    # --- Italy ---
    "libero.it": "Libero Family",
    "virgilio.it": "Virgilio Family",
    "alice.it": "TIM Family",
    "tin.it": "TIM Family",
    "tiscali.it": "Tiscali Family",

    # --- Spain ---
    "terra.es": "Terra Family",
    "telefonica.net": "Telefonica Family",
    "ya.com": "Ya.com Family",

    # --- Netherlands ---
    "ziggo.nl": "Ziggo Family",
    "kpnmail.nl": "KPN Family",
    "planet.nl": "KPN Family",

    # --- Belgium ---
    "telenet.be": "Telenet Family",
    "proximus.be": "Proximus Family",
    "skynet.be": "Proximus Family",

    # --- Switzerland ---
    "bluewin.ch": "Bluewin Family",

    # --- Australia ---
    "bigpond.com": "Telstra Family",
    "bigpond.net.au": "Telstra Family",
    "optusnet.com.au": "Optus Family",
    "tpg.com.au": "TPG Family",
    "iinet.net.au": "iiNet Family",

    # --- New Zealand ---
    "xtra.co.nz": "Spark Family",

    # --- Japan ---
    "docomo.ne.jp": "NTT Docomo Family",
    "softbank.ne.jp": "SoftBank Family",
    "i.softbank.jp": "SoftBank Family",
    "ezweb.ne.jp": "au Family",
    "au.com": "au Family",

    # --- South Korea ---
    "naver.com": "Naver Family",
    "daum.net": "Daum Family",
    "hanmail.net": "Daum Family",
    "kakao.com": "Kakao Family",

    # --- China ---
    "qq.com": "QQ Family",
    "foxmail.com": "Foxmail Family",
    "163.com": "NetEase Family",
    "126.com": "NetEase Family",
    "yeah.net": "NetEase Family",
    "139.com": "China Mobile Family",
    "189.cn": "China Telecom Family",

    # --- Hong Kong ---
    "netvigator.com": "Netvigator Family",

    # --- Taiwan ---
    "msa.hinet.net": "HiNet Family",
    "pchome.com.tw": "PChome Family",

    # --- India ---
    "rediffmail.com": "Rediffmail Family",
    "sify.com": "Sify Family",
    "indiatimes.com": "IndiaTimes Family",

    # --- Indonesia ---
    "plasa.com": "Plasa Family",
    "telkom.net": "Telkom Family",

    # --- Ukraine ---
    "ukr.net": "Ukr.net Family",
    "i.ua": "I.UA Family",
    "meta.ua": "Meta.ua Family",

    # --- Poland ---
    "wp.pl": "Wirtualna Polska Family",
    "o2.pl": "O2 Family",
    "interia.pl": "Interia Family",
    "onet.pl": "Onet Family",

    # --- Czech Republic ---
    "seznam.cz": "Seznam Family",
    "email.cz": "Seznam Family",
    "centrum.cz": "Centrum Family",

    # --- Romania ---
    "zappmobile.ro": "Zapp Family",

    # --- Brazil ---
    "uol.com.br": "UOL Family",
    "bol.com.br": "BOL Family",
    "terra.com.br": "Terra Family",
    "ig.com.br": "iG Family",

    # --- South Africa ---
    "mweb.co.za": "MWeb Family",
    "telkomsa.net": "Telkom Family",
    "vodamail.co.za": "Vodacom Family",

    # --- Turkey ---
    "mynet.com": "Mynet Family",

    # --- Portugal ---
    "sapo.pt": "SAPO Family",

    # --- Bulgaria ---
    "abv.bg": "ABV Family",
    "mail.bg": "Mail.bg Family",
}


# =====================================================================
# EDUCATION TLD SUFFIXES (checked as domain suffix)
# =====================================================================
EDU_SUFFIXES = {
    "edu",
    "ac",
    "sch",

    # UK
    "ac.uk", "edu.uk", "sch.uk",

    # Australia
    "edu.au", "ac.au", "schools.nsw.edu.au", "vic.edu.au", "qld.edu.au",

    # New Zealand
    "ac.nz", "edu.nz", "school.nz",

    # Canada
    "edu.ca", "ac.ca",

    # India
    "edu.in", "ac.in", "ernet.in",

    # China
    "edu.cn", "ac.cn",

    # Japan
    "ac.jp", "edu.jp",

    # South Korea
    "ac.kr", "edu.kr",

    # Indonesia
    "ac.id", "edu.id", "sch.id",

    # Malaysia
    "edu.my", "ac.my",

    # Singapore
    "edu.sg", "ac.sg",

    # Philippines
    "edu.ph", "ac.ph",

    # Thailand
    "ac.th", "edu.th",

    # Vietnam
    "edu.vn", "ac.vn",

    # Pakistan
    "edu.pk", "ac.pk",

    # Bangladesh
    "edu.bd", "ac.bd",

    # Sri Lanka
    "edu.lk", "ac.lk",

    # Nepal
    "edu.np", "ac.np",

    # Iran
    "ac.ir", "edu.ir",

    # Turkey
    "edu.tr", "ac.tr",

    # Israel
    "ac.il", "edu.il",

    # Saudi Arabia
    "edu.sa", "ac.sa",

    # UAE
    "ac.ae", "edu.ae",

    # South Africa
    "ac.za", "edu.za",

    # Nigeria
    "edu.ng", "ac.ng",

    # Kenya
    "ac.ke", "edu.ke",

    # Brazil
    "edu.br", "ac.br",

    # Mexico
    "edu.mx",

    # Argentina
    "edu.ar",

    # Colombia
    "edu.co",

    # Chile
    "edu.cl",

    # Peru
    "edu.pe",

    # Germany
    "ac.de", "edu.de",

    # France
    "ac.fr", "edu.fr",

    # Italy
    "ac.it", "edu.it",

    # Spain
    "ac.es", "edu.es",

    # Netherlands
    "ac.nl", "edu.nl",

    # Belgium
    "ac.be", "edu.be",

    # Switzerland
    "ac.ch", "edu.ch",

    # Austria
    "ac.at", "edu.at",

    # Denmark
    "ac.dk", "edu.dk",

    # Sweden
    "ac.se", "edu.se",

    # Norway
    "ac.no", "edu.no",

    # Finland
    "ac.fi", "edu.fi",

    # Poland
    "ac.pl", "edu.pl",

    # Czech Republic
    "ac.cz", "edu.cz",

    # Hungary
    "ac.hu", "edu.hu",

    # Romania
    "ac.ro", "edu.ro",

    # Greece
    "ac.gr", "edu.gr",

    # Portugal
    "ac.pt", "edu.pt",

    # Ireland
    "ac.ie", "edu.ie",
}


# =====================================================================
# EDUCATION LABELS (checked as domain labels, NOT the last/TLD label)
# 2-letter keys that conflict with country TLDs are excluded.
# =====================================================================
EDU_LABELS = {
    "edu", "ac", "ach",
    "school", "schools", "student", "students",
    "univ", "university", "universities",
    "college", "colleges",
    "academy", "academies", "academic", "academia",
    "campus", "faculty",
    "institute", "institutes", "institution",
    "education", "educational",
    "learning", "learn",
    "study", "studies",
    "scholar", "scholars", "scholarship", "scholarships",
    "research", "researcher", "researchers",
    "training", "teacher", "teachers", "professor", "professors",
    "studentmail", "alumni", "alum",
    "library", "registrar",
    "department", "departments", "dept",

    # School types
    "elementary", "primary", "secondary",
    "highschool", "high-school", "middleschool", "middle-school",
    "kindergarten", "preschool", "pre-school", "k12",

    # Degrees
    "phd", "mba", "msc", "mse",
    "degree", "degrees",
    "graduate", "graduates",
    "undergraduate", "postgraduate",
    # NOTE: 'ma','ba','bs','md','ms' excluded here because they are
    # also 2-letter country TLDs (Morocco, Bahamas, Bosnia, Moldova,
    # Montserrat). They will still be caught by EDU_SUFFIXES if part
    # of a proper education domain.

    # Online education
    "elearning", "e-learning", "edtech", "lms",
    "mooc", "moocs",
    "course", "courses", "class", "classes",
    "lesson", "lessons", "tutorial", "tutorials",
    "virtualschool", "onlineeducation", "onlinelearning",
}


# =====================================================================
# COUNTRY TLDs (2-letter + gTLDs)
# =====================================================================
COUNTRY_TLDS = {
    "af": "Afghanistan",
    "al": "Albania",
    "dz": "Algeria",
    "as": "American Samoa",
    "ad": "Andorra",
    "ao": "Angola",
    "ai": "Anguilla",
    "aq": "Antarctica",
    "ag": "Antigua and Barbuda",
    "ar": "Argentina",
    "am": "Armenia",
    "aw": "Aruba",
    "au": "Australia",
    "at": "Austria",
    "az": "Azerbaijan",
    "bs": "Bahamas",
    "bh": "Bahrain",
    "bd": "Bangladesh",
    "bb": "Barbados",
    "by": "Belarus",
    "be": "Belgium",
    "bz": "Belize",
    "bj": "Benin",
    "bm": "Bermuda",
    "bt": "Bhutan",
    "bo": "Bolivia",
    "ba": "Bosnia and Herzegovina",
    "bw": "Botswana",
    "bv": "Bouvet Island",
    "br": "Brazil",
    "io": "British Indian Ocean Territory",
    "bn": "Brunei Darussalam",
    "bg": "Bulgaria",
    "bf": "Burkina Faso",
    "bi": "Burundi",
    "kh": "Cambodia",
    "cm": "Cameroon",
    "ca": "Canada",
    "cv": "Cape Verde",
    "ky": "Cayman Islands",
    "cf": "Central African Republic",
    "td": "Chad",
    "cl": "Chile",
    "cn": "China",
    "cx": "Christmas Island",
    "cc": "Cocos (Keeling) Islands",
    "co": "Colombia",
    "km": "Comoros",
    "cg": "Congo",
    "cd": "Congo, The Democratic Republic of the",
    "ck": "Cook Islands",
    "cr": "Costa Rica",
    "ci": "Cote d'Ivoire",
    "hr": "Croatia",
    "cu": "Cuba",
    "cy": "Cyprus",
    "cz": "Czech Republic",
    "dk": "Denmark",
    "dj": "Djibouti",
    "dm": "Dominica",
    "do": "Dominican Republic",
    "ec": "Ecuador",
    "eg": "Egypt",
    "sv": "El Salvador",
    "gq": "Equatorial Guinea",
    "er": "Eritrea",
    "ee": "Estonia",
    "et": "Ethiopia",
    "fk": "Falkland Islands (Malvinas)",
    "fo": "Faroe Islands",
    "fj": "Fiji",
    "fi": "Finland",
    "fr": "France",
    "gf": "French Guiana",
    "pf": "French Polynesia",
    "tf": "French Southern Territories",
    "ga": "Gabon",
    "gm": "Gambia",
    "ge": "Georgia",
    "de": "Germany",
    "gh": "Ghana",
    "gi": "Gibraltar",
    "gr": "Greece",
    "gl": "Greenland",
    "gd": "Grenada",
    "gp": "Guadeloupe",
    "gu": "Guam",
    "gt": "Guatemala",
    "gg": "Guernsey",
    "gn": "Guinea",
    "gw": "Guinea-Bissau",
    "gy": "Guyana",
    "ht": "Haiti",
    "hm": "Heard Island and McDonald Islands",
    "va": "Holy See (Vatican City State)",
    "hn": "Honduras",
    "hk": "Hong Kong",
    "hu": "Hungary",
    "is": "Iceland",
    "in": "India",
    "id": "Indonesia",
    "ir": "Iran, Islamic Republic of",
    "iq": "Iraq",
    "ie": "Ireland",
    "im": "Isle of Man",
    "il": "Israel",
    "it": "Italy",
    "jm": "Jamaica",
    "jp": "Japan",
    "je": "Jersey",
    "jo": "Jordan",
    "kz": "Kazakhstan",
    "ke": "Kenya",
    "ki": "Kiribati",
    "kp": "Korea, Democratic People's Republic of",
    "kr": "Korea, Republic of",
    "kw": "Kuwait",
    "kg": "Kyrgyzstan",
    "la": "Lao People's Democratic Republic",
    "lv": "Latvia",
    "lb": "Lebanon",
    "ls": "Lesotho",
    "lr": "Liberia",
    "ly": "Libyan Arab Jamahiriya",
    "li": "Liechtenstein",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "mo": "Macao",
    "mk": "Macedonia, The Former Yugoslav Republic of",
    "mg": "Madagascar",
    "mw": "Malawi",
    "my": "Malaysia",
    "mv": "Maldives",
    "ml": "Mali",
    "mt": "Malta",
    "mh": "Marshall Islands",
    "mq": "Martinique",
    "mr": "Mauritania",
    "mu": "Mauritius",
    "yt": "Mayotte",
    "mx": "Mexico",
    "fm": "Micronesia, Federated States of",
    "md": "Moldova, Republic of",
    "mc": "Monaco",
    "mn": "Mongolia",
    "me": "Montenegro",
    "ms": "Montserrat",
    "ma": "Morocco",
    "mz": "Mozambique",
    "mm": "Myanmar",
    "na": "Namibia",
    "nr": "Nauru",
    "np": "Nepal",
    "nl": "Netherlands",
    "nc": "New Caledonia",
    "nz": "New Zealand",
    "ni": "Nicaragua",
    "ne": "Niger",
    "ng": "Nigeria",
    "nu": "Niue",
    "nf": "Norfolk Island",
    "mp": "Northern Mariana Islands",
    "no": "Norway",
    "om": "Oman",
    "pk": "Pakistan",
    "pw": "Palau",
    "ps": "Palestinian Territory, Occupied",
    "pa": "Panama",
    "pg": "Papua New Guinea",
    "py": "Paraguay",
    "pe": "Peru",
    "ph": "Philippines",
    "pn": "Pitcairn",
    "pl": "Poland",
    "pt": "Portugal",
    "pr": "Puerto Rico",
    "qa": "Qatar",
    "re": "Reunion",
    "ro": "Romania",
    "ru": "Russian Federation",
    "rw": "Rwanda",
    "bl": "Saint Barthelemy",
    "sh": "Saint Helena, Ascension and Tristan da Cunha",
    "kn": "Saint Kitts and Nevis",
    "lc": "Saint Lucia",
    "mf": "Saint Martin (French Part)",
    "pm": "Saint Pierre and Miquelon",
    "vc": "Saint Vincent and the Grenadines",
    "ws": "Samoa",
    "sm": "San Marino",
    "st": "Sao Tome and Principe",
    "sa": "Saudi Arabia",
    "sn": "Senegal",
    "rs": "Serbia",
    "sc": "Seychelles",
    "sl": "Sierra Leone",
    "sg": "Singapore",
    "sk": "Slovakia",
    "si": "Slovenia",
    "sb": "Solomon Islands",
    "so": "Somalia",
    "za": "South Africa",
    "gs": "South Georgia and the South Sandwich Islands",
    "es": "Spain",
    "lk": "Sri Lanka",
    "sd": "Sudan",
    "sr": "Suriname",
    "sj": "Svalbard and Jan Mayen",
    "sz": "Eswatini",
    "se": "Sweden",
    "ch": "Switzerland",
    "sy": "Syrian Arab Republic",
    "tw": "Taiwan, Province of China",
    "tj": "Tajikistan",
    "tz": "Tanzania, United Republic of",
    "th": "Thailand",
    "tl": "Timor-Leste",
    "tg": "Togo",
    "tk": "Tokelau",
    "to": "Tonga",
    "tt": "Trinidad and Tobago",
    "tn": "Tunisia",
    "tr": "Turkey",
    "tm": "Turkmenistan",
    "tc": "Turks and Caicos Islands",
    "tv": "Tuvalu",
    "ug": "Uganda",
    "ua": "Ukraine",
    "ae": "United Arab Emirates",
    "gb": "United Kingdom",
    "uk": "United Kingdom",
    "us": "United States",
    "com": "United States",
    "net": "United States",
    "org": "United States",
    "um": "United States Minor Outlying Islands",
    "uy": "Uruguay",
    "uz": "Uzbekistan",
    "vu": "Vanuatu",
    "ve": "Venezuela",
    "vn": "Viet Nam",
    "vg": "Virgin Islands, British",
    "vi": "Virgin Islands, U.S.",
    "wf": "Wallis and Futuna",
    "eh": "Western Sahara",
    "ye": "Yemen",
    "zm": "Zambia",
    "zw": "Zimbabwe",
}


# =====================================================================
# COMPILED REGEX (compile once, not per line)
# =====================================================================
COMBO_RE = re.compile(
    r"([A-Za-z0-9._%+-]+@"
    r"([A-Za-z0-9.-]+\.[A-Za-z]{2,}))"
    r":([^\s]+)"
)


# =====================================================================
# HELPERS
# =====================================================================

def safe_filename(name):
    """Convert any string into a safe filename for Windows/Linux."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.strip(" .")
    if not name:
        name = "unknown"
    # Avoid Windows reserved names
    if re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])", name):
        name = "_" + name
    return name


def extract_country_from_domain(domain):
    """
    Determine country/category for a domain.

    Priority:
      1. Exact known domain  (gmail.com -> Gmail Family)
      2. Education suffix    (user.ac.uk -> Education)
      3. Education label     (user.university.com -> Education)
      4. TLD country         (user.fr -> France)
    """
    domain = domain.strip().lower()
    if not domain:
        return "Other_Country"

    # 1. Exact known domain
    if domain in KNOWN_DOMAINS:
        return KNOWN_DOMAINS[domain]

    labels = domain.split(".")
    tld = labels[-1]

    # 2. Education suffix (e.g. .edu, .ac.uk, .edu.au)
    for suffix in EDU_SUFFIXES:
        if domain == suffix or domain.endswith("." + suffix):
            return "Education"

    # 3. Education label in any label EXCEPT the TLD
    #    This prevents 'ma','bs','ba','md','ms' TLDs from being
    #    mistaken for education keywords.
    for label in labels[:-1]:
        if label in EDU_LABELS:
            return "Education"

    # 4. TLD -> country
    return COUNTRY_TLDS.get(tld, "Other_Country")


def scan_line(line):
    """
    Try to extract (domain, combo) from a single line.
    Expected: email@domain.com:password
    Returns (domain, combo) or (None, None).
    """
    match = COMBO_RE.search(line)
    if match:
        email = match.group(1)
        domain = match.group(2).lower()
        password = match.group(3)
        combo = f"{email}:{password}"
        return domain, combo
    return None, None


def process_chunk(chunk, results, domains_seen, counter, lock):
    """
    Worker: process a chunk of lines.

    results      : dict  {category: set of combos}
    domains_seen : set   of domains
    counter      : list  [int]  – mutable, so threads can update it
    lock         : threading.Lock
    """
    for line in chunk:
        domain, combo = scan_line(line)
        if not domain or not combo:
            continue

        category = extract_country_from_domain(domain)

        with lock:
            bucket = results.get(category)
            if bucket is None:
                bucket = set()
                results[category] = bucket

            if combo not in bucket:
                bucket.add(combo)
                counter[0] += 1
                domains_seen.add(domain)


def read_chunks(filepath, chunk_size=100_000):
    """Yield lists of lines in chunks without loading whole file."""
    chunk = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            chunk.append(line)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def process_file(filepath, threads, results, domains_seen, counter, lock):
    """Process one file using a thread pool."""
    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = []
        for chunk in read_chunks(filepath):
            futures.append(
                pool.submit(process_chunk, chunk, results, domains_seen,
                            counter, lock)
            )
            # Prevent unbounded queue growth
            if len(futures) >= threads * 4:
                for fut in as_completed(futures):
                    fut.result()
                futures = []
        for fut in as_completed(futures):
            fut.result()


def collect_input_files(input_path, output_dir_abs):
    """
    Return a list of input files.
    - If input_path is a file  -> [that file]
    - If input_path is a dir   -> all files recursively, skipping output_dir
    """
    input_abs = os.path.abspath(input_path)

    if os.path.isfile(input_abs):
        return [input_abs]

    if not os.path.isdir(input_abs):
        return []

    files = []
    for root, dirs, names in os.walk(input_abs):
        # Prune output directory from traversal
        dirs[:] = [
            d for d in dirs
            if os.path.abspath(os.path.join(root, d)) != output_dir_abs
        ]
        for n in names:
            files.append(os.path.join(root, n))

    return sorted(files)


def write_output(results, output_dir):
    """Write one file per category: CategoryName[count].txt"""
    if not results:
        print(YELLOW + "[!] No combos found. Nothing to write.")
        return

    for category in sorted(results.keys()):
        combos = list(results[category])
        fname = safe_filename(category) + f"[{len(combos)}].txt"
        fpath = os.path.join(output_dir, fname)

        try:
            with open(fpath, "w", encoding="utf-8", newline="\n") as out:
                for combo in combos:
                    out.write(combo + "\n")
            print(f"{GREEN}[SAVED] {fpath}  ({len(combos)})")
        except Exception as e:
            print(f"{RED}[ERROR] Cannot write {fpath}: {e}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    # ---------- input ----------
    input_path = input(YELLOW + "[!] Input folder or file path: ").strip()

    output_folder = input(YELLOW + "[!] Output folder name: ").strip()
    if not output_folder:
        output_folder = "RESULT_BY_COUNTRY"

    while True:
        try:
            threads = int(input(YELLOW + "[!] Number of threads: ").strip())
            if threads < 1:
                print(RED + "[!] Threads must be >= 1")
                continue
            break
        except ValueError:
            print(RED + "[!] Please enter a valid integer")

    output_dir_abs = os.path.abspath(output_folder)

    # If output path exists as a file, bail
    if os.path.exists(output_dir_abs) and not os.path.isdir(output_dir_abs):
        print(RED + "[!] Output path exists and is not a folder.")
        input("Press Enter to exit...")
        return

    # ---------- gather files ----------
    input_files = collect_input_files(input_path, output_dir_abs)

    if not input_files:
        print(RED + "[!] No input files found.")
        input("Press Enter to exit...")
        return

    os.makedirs(output_dir_abs, exist_ok=True)

    # ---------- shared state ----------
    results = {}            # {category: set(combo)}
    domains_seen = set()
    counter = [0]           # mutable so threads can update
    lock = Lock()

    # ---------- banner ----------
    print(YELLOW + "\n" + "=" * 50)
    print(YELLOW + f"  Files to scan : {len(input_files)}")
    print(YELLOW + f"  Threads       : {threads}")
    print(YELLOW + f"  Output folder : {output_dir_abs}")
    print(YELLOW + "=" * 50 + "\n")

    # ---------- process ----------
    total_files = len(input_files)
    for idx, fpath in enumerate(input_files, 1):
        print(CYAN + f"[{idx}/{total_files}] {fpath}")
        try:
            process_file(fpath, threads, results, domains_seen, counter, lock)
        except Exception as e:
            print(RED + f"  SKIPPED – {e}")

    # ---------- write output ----------
    print(YELLOW + "\n[!] Writing output files...\n")
    write_output(results, output_dir_abs)

    # ---------- summary ----------
    print(GREEN + "\n" + "=" * 50)
    print(GREEN + "  Done.")
    print(YELLOW + f"  Unique combos  : {counter[0]}")
    print(YELLOW + f"  Unique domains : {len(domains_seen)}")
    print(YELLOW + f"  Categories     : {len(results)}")
    print(YELLOW + f"  Threads used   : {threads}")
    print(YELLOW + f"  Output folder  : {output_dir_abs}")
    print(GREEN + "=" * 50)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
