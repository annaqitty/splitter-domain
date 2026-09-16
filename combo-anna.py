import os
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import colorama
from threading import Lock

colorama.init(autoreset=True)

GREEN = colorama.Fore.GREEN
YELLOW = colorama.Fore.YELLOW
RED = colorama.Fore.RED
RESET = colorama.Fore.RESET

def safe_filename(name):
    """Convert a domain into a safe Windows filename."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    name = name.strip(' .')
    
    if not name:
        name = "unknown"
    
    return name

def extract_country_from_domain(domain):
    """Extract country from the domain name."""
    countries = {
        'af': 'Afghanistan',
        'al': 'Albania',
        'dz': 'Algeria',
        'as': 'American Samoa',
        'ad': 'Andorra',
        'ao': 'Angola',
        'ai': 'Anguilla',
        'aq': 'Antarctica',
        'ag': 'Antigua and Barbuda',
        'ar': 'Argentina',
        'am': 'Armenia',
        'aw': 'Aruba',
        'au': 'Australia',
        'at': 'Austria',
        'az': 'Azerbaijan',
        'bs': 'Bahamas',
        'bh': 'Bahrain',
        'bd': 'Bangladesh',
        'bb': 'Barbados',
        'by': 'Belarus',
        'be': 'Belgium',
        'bz': 'Belize',
        'bj': 'Benin',
        'bm': 'Bermuda',
        'bt': 'Bhutan',
        'bo': 'Bolivia',
        'ba': 'Bosnia and Herzegovina',
        'bw': 'Botswana',
        'bv': 'Bouvet Island',
        'br': 'Brazil',
        'io': 'British Indian Ocean Territory',
        'bn': 'Brunei Darussalam',
        'bg': 'Bulgaria',
        'bf': 'Burkina Faso',
        'bi': 'Burundi',
        'kh': 'Cambodia',
        'cm': 'Cameroon',
        'ca': 'Canada',
        'cv': 'Cape Verde',
        'ky': 'Cayman Islands',
        'cf': 'Central African Republic',
        'td': 'Chad',
        'cl': 'Chile',
        'cn': 'China',
        'cx': 'Christmas Island',
        'cc': 'Cocos (Keeling) Islands',
        'co': 'Colombia',
        'km': 'Comoros',
        'cg': 'Congo',
        'cd': 'Congo, The Democratic Republic of the',
        'ck': 'Cook Islands',
        'cr': 'Costa Rica',
        'ci': 'Côte d\'Ivoire',
        'hr': 'Croatia',
        'cu': 'Cuba',
        'cy': 'Cyprus',
        'cz': 'Czech Republic',
        'dk': 'Denmark',
        'dj': 'Djibouti',
        'dm': 'Dominica',
        'do': 'Dominican Republic',
        'ec': 'Ecuador',
        'eg': 'Egypt',
        'sv': 'El Salvador',
        'gq': 'Equatorial Guinea',
        'er': 'Eritrea',
        'ee': 'Estonia',
        'et': 'Ethiopia',
        'fk': 'Falkland Islands (Malvinas)',
        'fo': 'Faroe Islands',
        'fj': 'Fiji',
        'fi': 'Finland',
        'fr': 'France',
        'gf': 'French Guiana',
        'pf': 'French Polynesia',
        'tf': 'French Southern Territories',
        'ga': 'Gabon',
        'gm': 'Gambia',
        'ge': 'Georgia',
        'de': 'Germany',
        'gh': 'Ghana',
        'gi': 'Gibraltar',
        'gr': 'Greece',
        'gl': 'Greenland',
        'gd': 'Grenada',
        'gp': 'Guadeloupe',
        'gu': 'Guam',
        'gt': 'Guatemala',
        'gg': 'Guernsey',
        'gn': 'Guinea',
        'gw': 'Guinea-Bissau',
        'gy': 'Guyana',
        'ht': 'Haiti',
        'hm': 'Heard Island and McDonald Islands',
        'va': 'Holy See (Vatican City State)',
        'hn': 'Honduras',
        'hk': 'Hong Kong',
        'hu': 'Hungary',
        'is': 'Iceland',
        'in': 'India',
        'id': 'Indonesia',
        'ir': 'Iran, Islamic Republic of',
        'iq': 'Iraq',
        'ie': 'Ireland',
        'im': 'Isle of Man',
        'il': 'Israel',
        'it': 'Italy',
        'jm': 'Jamaica',
        'jp': 'Japan',
        'je': 'Jersey',
        'jo': 'Jordan',
        'kz': 'Kazakhstan',
        'ke': 'Kenya',
        'ki': 'Kiribati',
        'kp': 'Korea, Democratic People\'s Republic of',
        'kr': 'Korea, Republic of',
        'kw': 'Kuwait',
        'kg': 'Kyrgyzstan',
        'la': 'Lao People\'s Democratic Republic',
        'lv': 'Latvia',
        'lb': 'Lebanon',
        'ls': 'Lesotho',
        'lr': 'Liberia',
        'ly': 'Libyan Arab Jamahiriya',
        'li': 'Liechtenstein',
        'lt': 'Lithuania',
        'lu': 'Luxembourg',
        'mo': 'Macao',
        'mk': 'Macedonia, The Former Yugoslav Republic of',
        'mg': 'Madagascar',
        'mw': 'Malawi',
        'my': 'Malaysia',
        'mv': 'Maldives',
        'ml': 'Mali',
        'mt': 'Malta',
        'mh': 'Marshall Islands',
        'mq': 'Martinique',
        'mr': 'Mauritania',
        'mu': 'Mauritius',
        'yt': 'Mayotte',
        'mx': 'Mexico',
        'fm': 'Micronesia, Federated States of',
        'md': 'Moldova, Republic of',
        'mc': 'Monaco',
        'mn': 'Mongolia',
        'me': 'Montenegro',
        'ms': 'Montserrat',
        'ma': 'Morocco',
        'mz': 'Mozambique',
        'mm': 'Myanmar',
        'na': 'Namibia',
        'nr': 'Nauru',
        'np': 'Nepal',
        'nl': 'Netherlands',
        'nc': 'New Caledonia',
        'nz': 'New Zealand',
        'ni': 'Nicaragua',
        'ne': 'Niger',
        'ng': 'Nigeria',
        'nu': 'Niue',
        'nf': 'Norfolk Island',
        'mp': 'Northern Mariana Islands',
        'no': 'Norway',
        'om': 'Oman',
        'pk': 'Pakistan',
        'pw': 'Palau',
        'ps': 'Palestinian Territory, Occupied',
        'pa': 'Panama',
        'pg': 'Papua New Guinea',
        'py': 'Paraguay',
        'pe': 'Peru',
        'ph': 'Philippines',
        'pn': 'Pitcairn',
        'pl': 'Poland',
        'pt': 'Portugal',
        'pr': 'Puerto Rico',
        'qa': 'Qatar',
        're': 'Réunion',
        'ro': 'Romania',
        'ru': 'Russian Federation',
        'rw': 'Rwanda',
        'bl': 'Saint Barthélemy',
        'sh': 'Saint Helena, Ascension and Tristan da Cunha',
        'kn': 'Saint Kitts and Nevis',
        'lc': 'Saint Lucia',
        'mf': 'Saint Martin (French Part)',
        'pm': 'Saint Pierre and Miquelon',
        'vc': 'Saint Vincent and the Grenadines',
        'ws': 'Samoa',
        'sm': 'San Marino',
        'st': 'São Tomé and Príncipe',
        'sa': 'Saudi Arabia',
        'sn': 'Senegal',
        'rs': 'Serbia',
        'sc': 'Seychelles',
        'sl': 'Sierra Leone',
        'sg': 'Singapore',
        'sk': 'Slovakia',
        'si': 'Slovenia',
        'sb': 'Solomon Islands',
        'so': 'Somalia',
        'za': 'South Africa',
        'gs': 'South Georgia and the South Sandwich Islands',
        'es': 'Spain',
        'lk': 'Sri Lanka',
        'sd': 'Sudan',
        'sr': 'Suriname',
        'sj': 'Svalbard and Jan Mayen',
        'sz': 'Swaziland',
        'se': 'Sweden',
        'ch': 'Switzerland',
        'sy': 'Syrian Arab Republic',
        'tw': 'Taiwan, Province of China',
        'tj': 'Tajikistan',
        'tz': 'Tanzania, United Republic of',
        'th': 'Thailand',
        'tl': 'Timor-Leste',
        'tg': 'Togo',
        'tk': 'Tokelau',
        'to': 'Tonga',
        'tt': 'Trinidad and Tobago',
        'tn': 'Tunisia',
        'tr': 'Turkey',
        'tm': 'Turkmenistan',
        'tc': 'Turks and Caicos Islands',
        'tv': 'Tuvalu',
        'ug': 'Uganda',
        'ua': 'Ukraine',
        'ae': 'United Arab Emirates',
        'gb': 'United Kingdom',
        'uk': 'United Kingdom',
        'us': 'United States',
        'com': 'United States',
        'net': 'United States',
        'org': 'United States',
	    'hotmail.com': 'Hotmail Family',
	    'hotmail.co.uk': 'Hotmail Family',
	    'hotmail.de': 'Hotmail Family',
	    'hotmail.fr': 'Hotmail Family',
	    'hotmail.it': 'Hotmail Family',
	    'hotmail.es': 'Hotmail Family',
	    'hotmail.ca': 'Hotmail Family',
	    'hotmail.com.au': 'Hotmail Family',
	    'hotmail.co.jp': 'Hotmail Family',
	    'hotmail.co.in': 'Hotmail Family',
	    'hotmail.com.br': 'Hotmail Family',
	    'hotmail.com.mx': 'Hotmail Family',
	    'hotmail.com.ar': 'Hotmail Family',
	    'hotmail.cl': 'Hotmail Family',
	    'hotmail.be': 'Hotmail Family',
	    'hotmail.nl': 'Hotmail Family',
	    'hotmail.at': 'Hotmail Family',
	    'hotmail.ch': 'Hotmail Family',
	    'hotmail.dk': 'Hotmail Family',
	    'hotmail.no': 'Hotmail Family',
	    'hotmail.se': 'Hotmail Family',
	    'hotmail.fi': 'Hotmail Family',
	    'hotmail.pt': 'Hotmail Family',
	    'hotmail.gr': 'Hotmail Family',
	    'hotmail.pl': 'Hotmail Family',
	    'hotmail.cz': 'Hotmail Family',
	    'hotmail.hu': 'Hotmail Family',
	    'hotmail.ro': 'Hotmail Family',
	    'hotmail.ru': 'Hotmail Family',
	    'hotmail.co.za': 'Hotmail Family',
	    'hotmail.co.nz': 'Hotmail Family',
	    'hotmail.com.tr': 'Hotmail Family',
	    'hotmail.co.il': 'Hotmail Family',

	    'outlook.com': 'Hotmail Family',
	    'outlook.co.uk': 'Hotmail Family',
	    'outlook.de': 'Hotmail Family',
	    'outlook.fr': 'Hotmail Family',
	    'outlook.it': 'Hotmail Family',
	    'outlook.es': 'Hotmail Family',
	    'outlook.ca': 'Hotmail Family',
	    'outlook.com.au': 'Hotmail Family',
	    'outlook.co.jp': 'Hotmail Family',
	    'outlook.co.in': 'Hotmail Family',
	    'outlook.com.br': 'Hotmail Family',
	    'outlook.com.mx': 'Hotmail Family',

	    'msn.com': 'Hotmail Family',

	    # =========================================================
	    # YAHOO
	    # =========================================================
	    'yahoo.com': 'Yahoo Family',
	    'yahoo.co.uk': 'Yahoo Family',
	    'yahoo.ca': 'Yahoo Family',
	    'yahoo.com.au': 'Yahoo Family',
	    'yahoo.co.nz': 'Yahoo Family',
	    'yahoo.co.in': 'Yahoo Family',
	    'yahoo.co.jp': 'Yahoo Family',
	    'yahoo.com.hk': 'Yahoo Family',
	    'yahoo.com.tw': 'Yahoo Family',
	    'yahoo.com.sg': 'Yahoo Family',
	    'yahoo.com.my': 'Yahoo Family',
	    'yahoo.com.ph': 'Yahoo Family',
	    'yahoo.co.id': 'Yahoo Family',
	    'yahoo.co.th': 'Yahoo Family',
	    'yahoo.com.br': 'Yahoo Family',
	    'yahoo.com.mx': 'Yahoo Family',
	    'yahoo.com.ar': 'Yahoo Family',
	    'yahoo.cl': 'Yahoo Family',
	    'yahoo.com.co': 'Yahoo Family',
	    'yahoo.com.pe': 'Yahoo Family',
	    'yahoo.co.ve': 'Yahoo Family',
	    'yahoo.es': 'Yahoo Family',
	    'yahoo.fr': 'Yahoo Family',
	    'yahoo.de': 'Yahoo Family',
	    'yahoo.it': 'Yahoo Family',
	    'yahoo.nl': 'Yahoo Family',
	    'yahoo.be': 'Yahoo Family',
	    'yahoo.ch': 'Yahoo Family',
	    'yahoo.at': 'Yahoo Family',
	    'yahoo.dk': 'Yahoo Family',
	    'yahoo.se': 'Yahoo Family',
	    'yahoo.no': 'Yahoo Family',
	    'yahoo.fi': 'Yahoo Family',
	    'yahoo.pl': 'Yahoo Family',
	    'yahoo.ro': 'Yahoo Family',
	    'yahoo.ru': 'Yahoo Family',
	    'yahoo.com.tr': 'Yahoo Family',
	    'yahoo.gr': 'Yahoo Family',
	    'yahoo.pt': 'Yahoo Family',
	    'yahoo.co.za': 'Yahoo Family',

	    # =========================================================
	    # GOOGLE / GMAIL
	    # =========================================================
	    'gmail.com': 'Gmail Family',
	    'googlemail.com': 'Gmail Family',

	    # =========================================================
	    # APPLE
	    # =========================================================
	    'icloud.com': 'iCloud Family',
	    'me.com': 'iCloud Family',
	    'mac.com': 'iCloud Family',

	    # =========================================================
	    # AOL
	    # =========================================================
	    'aol.com': 'AOL Family',
	    'aol.co.uk': 'AOL Family',
	    'aol.de': 'AOL Family',
	    'aol.fr': 'AOL Family',
	    'aol.it': 'AOL Family',
	    'aol.es': 'AOL Family',
	    'aol.ca': 'AOL Family',
	    'aol.com.au': 'AOL Family',
	    'aol.co.jp': 'AOL Family',
	    'aol.com.br': 'AOL Family',

	    # =========================================================
	    # GMX
	    # =========================================================
	    'gmx.com': 'GMX Family',
	    'gmx.de': 'GMX Family',
	    'gmx.at': 'GMX Family',
	    'gmx.ch': 'GMX Family',
	    'gmx.net': 'GMX Family',
	    'gmx.org': 'GMX Family',

	    # =========================================================
	    # WEB.DE
	    # =========================================================
	    'web.de': 'WEB.DE Family',

	    # =========================================================
	    # FREEMAIL / FREEMAIL GERMANY
	    # =========================================================
	    'freenet.de': 'Freenet Family',
	    'mail.de': 'Mail.de Family',

	    # =========================================================
	    # T-ONLINE
	    # =========================================================
	    't-online.de': 'T-Online Family',

	    # =========================================================
	    # MAIL.RU
	    # =========================================================
	    'mail.ru': 'Mail.ru Family',
	    'inbox.ru': 'Mail.ru Family',
	    'list.ru': 'Mail.ru Family',
	    'bk.ru': 'Mail.ru Family',

	    # =========================================================
	    # YANDEX
	    # =========================================================
	    'yandex.ru': 'Yandex Family',
	    'yandex.com': 'Yandex Family',

	    # =========================================================
	    # PROTON
	    # =========================================================
	    'proton.me': 'Proton Family',
	    'protonmail.com': 'Proton Family',
	    'pm.me': 'Proton Family',

	    # =========================================================
	    # ZOHO
	    # =========================================================
	    'zoho.com': 'Zoho Family',
	    'zohomail.com': 'Zoho Family',

	    # =========================================================
	    # FASTMAIL
	    # =========================================================
	    'fastmail.com': 'Fastmail Family',
	    'fastmail.fm': 'Fastmail Family',

	    # =========================================================
	    # MAIL.COM
	    # =========================================================
	    'mail.com': 'Mail.com Family',
	    'email.com': 'Mail.com Family',
	    'usa.com': 'Mail.com Family',
	    'myself.com': 'Mail.com Family',
	    'post.com': 'Mail.com Family',
	    'consultant.com': 'Mail.com Family',
	    'dr.com': 'Mail.com Family',
	    'engineer.com': 'Mail.com Family',
	    'europe.com': 'Mail.com Family',
	    'asia.com': 'Mail.com Family',
	    'iname.com': 'Mail.com Family',
	    'writeme.com': 'Mail.com Family',
	    'techie.com': 'Mail.com Family',

	    # =========================================================
	    # AOL / VERIZON LEGACY
	    # =========================================================
	    'verizon.net': 'Verizon Family',

	    # =========================================================
	    # COMCAST
	    # =========================================================
	    'comcast.net': 'Comcast Family',

	    # =========================================================
	    # AT&T
	    # =========================================================
	    'att.net': 'AT&T Family',
	    'sbcglobal.net': 'AT&T Family',
	    'bellsouth.net': 'AT&T Family',
	    'prodigy.net': 'AT&T Family',

	    # =========================================================
	    # UK ISP EMAIL
	    # =========================================================
	    'btinternet.com': 'BT Family',
	    'btopenworld.com': 'BT Family',
	    'talktalk.net': 'TalkTalk Family',
	    'virginmedia.com': 'Virgin Media Family',
	    'sky.com': 'Sky Family',

	    # =========================================================
	    # FRANCE
	    # =========================================================
	    'orange.fr': 'Orange Family',
	    'wanadoo.fr': 'Orange Family',
	    'sfr.fr': 'SFR Family',
	    'free.fr': 'Free Family',
	    'laposte.net': 'La Poste Family',

	    # =========================================================
	    # ITALY
	    # =========================================================
	    'libero.it': 'Libero Family',
	    'virgilio.it': 'Virgilio Family',
	    'alice.it': 'TIM Family',
	    'tin.it': 'TIM Family',
	    'tiscali.it': 'Tiscali Family',

	    # =========================================================
	    # SPAIN
	    # =========================================================
	    'terra.es': 'Terra Family',
	    'telefonica.net': 'Telefonica Family',
	    'ya.com': 'Ya.com Family',

	    # =========================================================
	    # NETHERLANDS
	    # =========================================================
	    'ziggo.nl': 'Ziggo Family',
	    'kpnmail.nl': 'KPN Family',
	    'planet.nl': 'KPN Family',

	    # =========================================================
	    # BELGIUM
	    # =========================================================
	    'telenet.be': 'Telenet Family',
	    'proximus.be': 'Proximus Family',
	    'skynet.be': 'Proximus Family',

	    # =========================================================
	    # SWITZERLAND
	    # =========================================================
	    'bluewin.ch': 'Bluewin Family',

	    # =========================================================
	    # AUSTRALIA
	    # =========================================================
	    'bigpond.com': 'Telstra Family',
	    'bigpond.net.au': 'Telstra Family',
	    'optusnet.com.au': 'Optus Family',
	    'tpg.com.au': 'TPG Family',
	    'iinet.net.au': 'iiNet Family',

	    # =========================================================
	    # NEW ZEALAND
	    # =========================================================
	    'xtra.co.nz': 'Spark Family',

	    # =========================================================
	    # JAPAN
	    # =========================================================
	    'docomo.ne.jp': 'NTT Docomo Family',
	    'softbank.ne.jp': 'SoftBank Family',
	    'i.softbank.jp': 'SoftBank Family',
	    'ezweb.ne.jp': 'au Family',
	    'au.com': 'au Family',

	    # =========================================================
	    # SOUTH KOREA
	    # =========================================================
	    'naver.com': 'Naver Family',
	    'daum.net': 'Daum Family',
	    'hanmail.net': 'Daum Family',
	    'kakao.com': 'Kakao Family',

	    # =========================================================
	    # CHINA
	    # =========================================================
	    'qq.com': 'QQ Family',
	    'foxmail.com': 'Foxmail Family',
	    '163.com': 'NetEase Family',
	    '126.com': 'NetEase Family',
	    'yeah.net': 'NetEase Family',
	    '139.com': 'China Mobile Family',
	    '189.cn': 'China Telecom Family',

	    # =========================================================
	    # HONG KONG
	    # =========================================================
	    'netvigator.com': 'Netvigator Family',

	    # =========================================================
	    # TAIWAN
	    # =========================================================
	    'msa.hinet.net': 'HiNet Family',
	    'pchome.com.tw': 'PChome Family',

	    # =========================================================
	    # INDIA
	    # =========================================================
	    'rediffmail.com': 'Rediffmail Family',
	    'sify.com': 'Sify Family',
	    'indiatimes.com': 'IndiaTimes Family',

	    # =========================================================
	    # INDONESIA
	    # =========================================================
	    'plasa.com': 'Plasa Family',
	    'telkom.net': 'Telkom Family',

	    # =========================================================
	    # RUSSIA
	    # =========================================================
	    'mail.ru': 'Mail.ru Family',
	    'inbox.ru': 'Mail.ru Family',
	    'list.ru': 'Mail.ru Family',
	    'bk.ru': 'Mail.ru Family',

	    # =========================================================
	    # UKRAINE
	    # =========================================================
	    'ukr.net': 'Ukr.net Family',
	    'i.ua': 'I.UA Family',
	    'meta.ua': 'Meta.ua Family',

	    # =========================================================
	    # POLAND
	    # =========================================================
	    'wp.pl': 'Wirtualna Polska Family',
	    'o2.pl': 'O2 Family',
	    'interia.pl': 'Interia Family',
	    'onet.pl': 'Onet Family',

	    # =========================================================
	    # CZECH REPUBLIC
	    # =========================================================
	    'seznam.cz': 'Seznam Family',
	    'email.cz': 'Seznam Family',
	    'centrum.cz': 'Centrum Family',

	    # =========================================================
	    # ROMANIA
	    # =========================================================
	    'zappmobile.ro': 'Zapp Family',

	    # =========================================================
	    # BRAZIL
	    # =========================================================
	    'uol.com.br': 'UOL Family',
	    'bol.com.br': 'BOL Family',
	    'terra.com.br': 'Terra Family',
	    'ig.com.br': 'iG Family',

	    # =========================================================
	    # SOUTH AFRICA
	    # =========================================================
	    'mweb.co.za': 'MWeb Family',
	    'telkomsa.net': 'Telkom Family',
	    'vodamail.co.za': 'Vodacom Family',

	    # =========================================================
	    # TURKEY
	    # =========================================================
	    'mynet.com': 'Mynet Family',

	    # =========================================================
	    # PORTUGAL
	    # =========================================================
	    'sapo.pt': 'SAPO Family',

	    # =========================================================
	    # BULGARIA
	    # =========================================================
	    'abv.bg': 'ABV Family',
	    'mail.bg': 'Mail.bg Family',



	    'edu': 'Education',
	    'ac': 'Education',
	    'ach': 'Education',
	    'sch': 'Education',
	    'school': 'Education',
	    'schools': 'Education',
	    'student': 'Education',
	    'students': 'Education',
	    'univ': 'Education',
	    'university': 'Education',
	    'universities': 'Education',
	    'college': 'Education',
	    'colleges': 'Education',
	    'academy': 'Education',
	    'academies': 'Education',
	    'academic': 'Education',
	    'academia': 'Education',
	    'campus': 'Education',
	    'faculty': 'Education',
	    'institute': 'Education',
	    'institutes': 'Education',
	    'institution': 'Education',
	    'education': 'Education',
	    'educational': 'Education',
	    'learning': 'Education',
	    'learn': 'Education',
	    'study': 'Education',
	    'studies': 'Education',
	    'scholar': 'Education',
	    'scholars': 'Education',
	    'scholarship': 'Education',
	    'scholarships': 'Education',
	    'research': 'Education',
	    'researcher': 'Education',
	    'researchers': 'Education',
	    'training': 'Education',
	    'teacher': 'Education',
	    'teachers': 'Education',
	    'professor': 'Education',
	    'professors': 'Education',
	    'studentmail': 'Education',
	    'alumni': 'Education',
	    'alum': 'Education',
	    'library': 'Education',
	    'registrar': 'Education',
	    'department': 'Education',
	    'departments': 'Education',
	    'dept': 'Education',

	    # =========================================================
	    # SCHOOL TYPES
	    # =========================================================

	    'elementary': 'Education',
	    'primary': 'Education',
	    'secondary': 'Education',
	    'highschool': 'Education',
	    'high-school': 'Education',
	    'middleschool': 'Education',
	    'middle-school': 'Education',
	    'kindergarten': 'Education',
	    'preschool': 'Education',
	    'pre-school': 'Education',
	    'k12': 'Education',

	    # =========================================================
	    # DEGREES / ACADEMIC PROGRAMS
	    # =========================================================

	    'phd': 'Education',
	    'mba': 'Education',
	    'msc': 'Education',
	    'mse': 'Education',
	    'ma': 'Education',
	    'ba': 'Education',
	    'bs': 'Education',
	    'bsc': 'Education',
	    'ms': 'Education',
	    'md': 'Education',
	    'jd': 'Education',
	    'llm': 'Education',
	    'degree': 'Education',
	    'degrees': 'Education',
	    'graduate': 'Education',
	    'graduates': 'Education',
	    'undergraduate': 'Education',
	    'postgraduate': 'Education',

	    # =========================================================
	    # ONLINE EDUCATION
	    # =========================================================

	    'elearning': 'Education',
	    'e-learning': 'Education',
	    'edtech': 'Education',
	    'lms': 'Education',
	    'mooc': 'Education',
	    'moocs': 'Education',
	    'course': 'Education',
	    'courses': 'Education',
	    'class': 'Education',
	    'classes': 'Education',
	    'lesson': 'Education',
	    'lessons': 'Education',
	    'tutorial': 'Education',
	    'tutorials': 'Education',
	    'training': 'Education',
	    'virtualschool': 'Education',
	    'onlineeducation': 'Education',
	    'onlinelearning': 'Education',

	    # =========================================================
	    # UNITED STATES
	    # =========================================================

	    '.edu': 'Education',

	    # =========================================================
	    # UNITED KINGDOM
	    # =========================================================

	    '.ac.uk': 'Education',
	    '.edu.uk': 'Education',
	    '.sch.uk': 'Education',

	    # =========================================================
	    # AUSTRALIA
	    # =========================================================

	    '.edu.au': 'Education',
	    '.ac.au': 'Education',
	    '.schools.nsw.edu.au': 'Education',
	    '.vic.edu.au': 'Education',
	    '.qld.edu.au': 'Education',

	    # =========================================================
	    # NEW ZEALAND
	    # =========================================================

	    '.ac.nz': 'Education',
	    '.edu.nz': 'Education',
	    '.school.nz': 'Education',

	    # =========================================================
	    # CANADA
	    # =========================================================

	    '.edu.ca': 'Education',
	    '.ac.ca': 'Education',

	    # =========================================================
	    # INDIA
	    # =========================================================

	    '.edu.in': 'Education',
	    '.ac.in': 'Education',
	    '.ernet.in': 'Education',

	    # =========================================================
	    # CHINA
	    # =========================================================

	    '.edu.cn': 'Education',
	    '.ac.cn': 'Education',

	    # =========================================================
	    # JAPAN
	    # =========================================================

	    '.ac.jp': 'Education',
	    '.edu.jp': 'Education',

	    # =========================================================
	    # SOUTH KOREA
	    # =========================================================

	    '.ac.kr': 'Education',
	    '.edu.kr': 'Education',

	    # =========================================================
	    # INDONESIA
	    # =========================================================

	    '.ac.id': 'Education',
	    '.edu.id': 'Education',
	    '.sch.id': 'Education',

	    # =========================================================
	    # MALAYSIA
	    # =========================================================

	    '.edu.my': 'Education',
	    '.ac.my': 'Education',

	    # =========================================================
	    # SINGAPORE
	    # =========================================================

	    '.edu.sg': 'Education',
	    '.ac.sg': 'Education',

	    # =========================================================
	    # PHILIPPINES
	    # =========================================================

	    '.edu.ph': 'Education',
	    '.ac.ph': 'Education',

	    # =========================================================
	    # THAILAND
	    # =========================================================

	    '.ac.th': 'Education',
	    '.edu.th': 'Education',

	    # =========================================================
	    # VIETNAM
	    # =========================================================

	    '.edu.vn': 'Education',
	    '.ac.vn': 'Education',

	    # =========================================================
	    # PAKISTAN
	    # =========================================================

	    '.edu.pk': 'Education',
	    '.ac.pk': 'Education',

	    # =========================================================
	    # BANGLADESH
	    # =========================================================

	    '.edu.bd': 'Education',
	    '.ac.bd': 'Education',

	    # =========================================================
	    # SRI LANKA
	    # =========================================================

	    '.edu.lk': 'Education',
	    '.ac.lk': 'Education',

	    # =========================================================
	    # NEPAL
	    # =========================================================

	    '.edu.np': 'Education',
	    '.ac.np': 'Education',

	    # =========================================================
	    # IRAN
	    # =========================================================

	    '.ac.ir': 'Education',
	    '.edu.ir': 'Education',

	    # =========================================================
	    # TURKEY
	    # =========================================================

	    '.edu.tr': 'Education',
	    '.ac.tr': 'Education',

	    # =========================================================
	    # ISRAEL
	    # =========================================================

	    '.ac.il': 'Education',
	    '.edu.il': 'Education',

	    # =========================================================
	    # SAUDI ARABIA
	    # =========================================================

	    '.edu.sa': 'Education',
	    '.ac.sa': 'Education',

	    # =========================================================
	    # UNITED ARAB EMIRATES
	    # =========================================================

	    '.ac.ae': 'Education',
	    '.edu.ae': 'Education',

	    # =========================================================
	    # SOUTH AFRICA
	    # =========================================================

	    '.ac.za': 'Education',
	    '.edu.za': 'Education',

	    # =========================================================
	    # NIGERIA
	    # =========================================================

	    '.edu.ng': 'Education',
	    '.ac.ng': 'Education',

	    # =========================================================
	    # GHANA
	    # =========================================================

	    '.edu.gh': 'Education',
	    '.ac.gh': 'Education',

	    # =========================================================
	    # KENYA
	    # =========================================================

	    '.ac.ke': 'Education',
	    '.edu.ke': 'Education',

	    # =========================================================
	    # BRAZIL
	    # =========================================================

	    '.edu.br': 'Education',
	    '.ac.br': 'Education',

	    # =========================================================
	    # MEXICO
	    # =========================================================

	    '.edu.mx': 'Education',

	    # =========================================================
	    # ARGENTINA
	    # =========================================================

	    '.edu.ar': 'Education',

	    # =========================================================
	    # COLOMBIA
	    # =========================================================

	    '.edu.co': 'Education',

	    # =========================================================
	    # CHILE
	    # =========================================================

	    '.edu.cl': 'Education',

	    # =========================================================
	    # PERU
	    # =========================================================

	    '.edu.pe': 'Education',

	    # =========================================================
	    # EUROPE
	    # =========================================================

	    '.ac.de': 'Education',
	    '.edu.de': 'Education',
	    '.ac.fr': 'Education',
	    '.edu.fr': 'Education',
	    '.ac.it': 'Education',
	    '.edu.it': 'Education',
	    '.ac.es': 'Education',
	    '.edu.es': 'Education',
	    '.ac.nl': 'Education',
	    '.edu.nl': 'Education',
	    '.ac.be': 'Education',
	    '.edu.be': 'Education',
	    '.ac.ch': 'Education',
	    '.edu.ch': 'Education',
	    '.ac.at': 'Education',
	    '.edu.at': 'Education',
	    '.ac.dk': 'Education',
	    '.edu.dk': 'Education',
	    '.ac.se': 'Education',
	    '.edu.se': 'Education',
	    '.ac.no': 'Education',
	    '.edu.no': 'Education',
	    '.ac.fi': 'Education',
	    '.edu.fi': 'Education',
	    '.ac.pl': 'Education',
	    '.edu.pl': 'Education',
	    '.ac.cz': 'Education',
	    '.edu.cz': 'Education',
	    '.ac.hu': 'Education',
	    '.edu.hu': 'Education',
	    '.ac.ro': 'Education',
	    '.edu.ro': 'Education',
	    '.ac.gr': 'Education',
	    '.edu.gr': 'Education',
	    '.ac.pt': 'Education',
	    '.edu.pt': 'Education',
	    '.ac.ie': 'Education',
	    '.edu.ie': 'Education',

	    # =========================================================
	    # OTHER INTERNATIONAL ACADEMIC SUFFIXES
	    # =========================================================

	    '.ac': 'Education',
	    '.edu': 'Education',
	    '.sch': 'Education',
        'um': 'United States Minor Outlying Islands',
        'uy': 'Uruguay',
        'uz': 'Uzbekistan',
        'vu': 'Vanuatu',
        've': 'Venezuela',
        'vn': 'Viet Nam',
        'vg': 'Virgin Islands, British',
        'vi': 'Virgin Islands, U.S.',
        'wf': 'Wallis and Futuna',
        'eh': 'Western Sahara',
        'ye': 'Yemen',
        'zm': 'Zambia',
        'zw': 'Zimbabwe'
    }
    country_code = domain.split('.')[-1].lower()
    return countries.get(country_code, 'Other_Country')

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

def process_line(line, domains, total_found, lock, output_folder):
    domain, combo = scan(line)
    if domain and combo:
        with lock:
            domains[domain].append(combo)
            total_found += 1
        
        print(f"{GREEN}[FOUND]\r{combo} -> {domain}", end='', flush=True)
        write_to_file(domain, combo, output_folder)

def write_to_file(domain, combo, output_folder):
    country = extract_country_from_domain(domain)
    if country != 'Unknown':
        temp_file_path = os.path.join(output_folder, f"temp_{country}.txt")
        
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            with open(temp_file_path, "a", encoding="utf-8") as out:
                out.write(combo + "\n")
            print(f"{GREEN}[SAVED]\r{temp_file_path}", end='', flush=True)
        except Exception as e:
            print(RED + f"[ERROR] Cannot save {temp_file_path}: {e}", end='', flush=True)

def finalize_output_files(domains, output_folder):
    country_combos = defaultdict(list)
    for domain, combos in domains.items():
        country = extract_country_from_domain(domain)
        if country != 'Unknown':
            country_combos[country].extend(combos)
    
    for country, combos in country_combos.items():
        output_file = os.path.join(output_folder, f"{country}[{len(combos)}].txt")
        
        # Ensure the output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            with open(output_file, "w", encoding="utf-8") as out:
                for combo in combos:
                    out.write(combo + "\n")
            print(f"{GREEN}[SAVED]\r{output_file}", end='', flush=True)
        except Exception as e:
            print(RED + f"[ERROR] Cannot save {output_file}: {e}", end='', flush=True)

def main():
    input_folder_or_file = input(YELLOW + "[!] Input folder or file path: ").strip()

    output_folder = input(YELLOW + "[!] Output folder name: ").strip()
    if not output_folder:
        output_folder = "RESULT_BY_COUNTRY"

    while True:
        try:
            threads = int(input(YELLOW + "[!] Number of threads: ").strip())
            if threads < 1:
                print(RED + "[ERROR] Threads must be at least 1.")
                continue
            break
        except ValueError:
            print(RED + "[ERROR] Please enter a valid number.")

    if os.path.isdir(input_folder_or_file):
        input_files = [os.path.join(input_folder_or_file, f) for f in os.listdir(input_folder_or_file)]
    elif os.path.isfile(input_folder_or_file):
        input_files = [input_folder_or_file]
    else:
        print(RED + "\n[ERROR] Input path does not exist!")
        return

    domains = defaultdict(list)
    total_found = 0
    lock = Lock()

    print(YELLOW + f"\n[!] Processing with {threads} threads...\n")

    chunk_size = 100000  # Process lines in chunks of 100,000

    for input_file in input_files:
        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            for i in range(0, len(lines), chunk_size):
                chunk = lines[i:i + chunk_size]
                future = executor.submit(lambda chunk: [process_line(line, domains, total_found, lock, output_folder) for line in chunk], chunk)
                futures.append(future)

            for future in as_completed(futures):
                future.result()

    print(YELLOW + "\n[!] Saving results...\n")

    finalize_output_files(domains, output_folder)

    print(GREEN + "\nDone extracting.")
    print(YELLOW + f"Total combos found: {total_found}")
    print(YELLOW + f"Total domains found: {len(domains)}")
    print(YELLOW + f"Threads used: {threads}")
    print(YELLOW + f"Output folder: {output_folder}")

if __name__ == "__main__":
    main()
