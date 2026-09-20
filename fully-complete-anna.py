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
    # ==========================================
    # 1. THE BIG TECH GIANTS
    # ==========================================

    # --- Microsoft Family (Hotmail, Outlook, Live, MSN) ---
    "hotmail.com": "Microsoft Family", "hotmail.co.uk": "Microsoft Family", 
    "hotmail.de": "Microsoft Family", "hotmail.fr": "Microsoft Family",
    "hotmail.it": "Microsoft Family", "hotmail.es": "Microsoft Family", 
    "hotmail.ca": "Microsoft Family", "hotmail.com.au": "Microsoft Family",
    "hotmail.co.jp": "Microsoft Family", "hotmail.co.in": "Microsoft Family", 
    "hotmail.com.br": "Microsoft Family", "hotmail.com.mx": "Microsoft Family",
    "hotmail.com.ar": "Microsoft Family", "hotmail.cl": "Microsoft Family", 
    "hotmail.be": "Microsoft Family", "hotmail.nl": "Microsoft Family",
    "hotmail.at": "Microsoft Family", "hotmail.ch": "Microsoft Family", 
    "hotmail.dk": "Microsoft Family", "hotmail.no": "Microsoft Family",
    "hotmail.se": "Microsoft Family", "hotmail.fi": "Microsoft Family", 
    "hotmail.pt": "Microsoft Family", "hotmail.gr": "Microsoft Family",
    "hotmail.pl": "Microsoft Family", "hotmail.cz": "Microsoft Family", 
    "hotmail.hu": "Microsoft Family", "hotmail.ro": "Microsoft Family",
    "hotmail.ru": "Microsoft Family", "hotmail.co.za": "Microsoft Family", 
    "hotmail.co.nz": "Microsoft Family", "hotmail.com.tr": "Microsoft Family",
    "hotmail.co.il": "Microsoft Family", "hotmail.co.th": "Microsoft Family", 
    "hotmail.sg": "Microsoft Family", "hotmail.my": "Microsoft Family",
    
    "outlook.com": "Microsoft Family", "outlook.co.uk": "Microsoft Family", 
    "outlook.de": "Microsoft Family", "outlook.fr": "Microsoft Family",
    "outlook.it": "Microsoft Family", "outlook.es": "Microsoft Family", 
    "outlook.ca": "Microsoft Family", "outlook.com.au": "Microsoft Family",
    "outlook.co.jp": "Microsoft Family", "outlook.co.in": "Microsoft Family", 
    "outlook.com.br": "Microsoft Family", "outlook.com.mx": "Microsoft Family",
    "outlook.in": "Microsoft Family", "outlook.sa": "Microsoft Family", 
    "outlook.sg": "Microsoft Family", "outlook.cl": "Microsoft Family",
    "outlook.ph": "Microsoft Family", "outlook.co.th": "Microsoft Family",
    
    "live.com": "Microsoft Family", "live.co.uk": "Microsoft Family", 
    "live.ca": "Microsoft Family", "live.fr": "Microsoft Family",
    "live.de": "Microsoft Family", "live.it": "Microsoft Family", 
    "live.nl": "Microsoft Family", "live.com.au": "Microsoft Family",
    "live.com.mx": "Microsoft Family", "live.com.ar": "Microsoft Family", 
    "live.cl": "Microsoft Family", "live.cn": "Microsoft Family",
    "live.hk": "Microsoft Family", "live.jp": "Microsoft Family", 
    "live.co.kr": "Microsoft Family", "live.in": "Microsoft Family",
    "live.co.za": "Microsoft Family", "live.se": "Microsoft Family", 
    "live.no": "Microsoft Family", "live.dk": "Microsoft Family",
    
    "msn.com": "Microsoft Family", "msn.co.uk": "Microsoft Family", 
    "windowslive.com": "Microsoft Family",

    # --- Yahoo Family (Yahoo, Ymail, Rocketmail) ---
    "yahoo.com": "Yahoo Family", "yahoo.co.uk": "Yahoo Family", 
    "yahoo.ca": "Yahoo Family", "yahoo.com.au": "Yahoo Family",
    "yahoo.co.nz": "Yahoo Family", "yahoo.co.in": "Yahoo Family", 
    "yahoo.in": "Yahoo Family", "yahoo.co.jp": "Yahoo Family",
    "yahoo.com.hk": "Yahoo Family", "yahoo.com.tw": "Yahoo Family", 
    "yahoo.com.sg": "Yahoo Family", "yahoo.com.my": "Yahoo Family",
    "yahoo.com.ph": "Yahoo Family", "yahoo.co.id": "Yahoo Family", 
    "yahoo.co.th": "Yahoo Family", "yahoo.com.br": "Yahoo Family",
    "yahoo.com.mx": "Yahoo Family", "yahoo.com.ar": "Yahoo Family", 
    "yahoo.cl": "Yahoo Family", "yahoo.com.co": "Yahoo Family",
    "yahoo.com.pe": "Yahoo Family", "yahoo.co.ve": "Yahoo Family", 
    "yahoo.es": "Yahoo Family", "yahoo.fr": "Yahoo Family",
    "yahoo.de": "Yahoo Family", "yahoo.it": "Yahoo Family", 
    "yahoo.nl": "Yahoo Family", "yahoo.be": "Yahoo Family",
    "yahoo.ch": "Yahoo Family", "yahoo.at": "Yahoo Family", 
    "yahoo.dk": "Yahoo Family", "yahoo.se": "Yahoo Family",
    "yahoo.no": "Yahoo Family", "yahoo.fi": "Yahoo Family", 
    "yahoo.pl": "Yahoo Family", "yahoo.ro": "Yahoo Family",
    "yahoo.ru": "Yahoo Family", "yahoo.com.tr": "Yahoo Family", 
    "yahoo.gr": "Yahoo Family", "yahoo.pt": "Yahoo Family",
    "yahoo.co.za": "Yahoo Family", "ymail.com": "Yahoo Family", 
    "rocketmail.com": "Yahoo Family",

    # --- Google / Gmail Family ---
    "gmail.com": "Google Family", 
    "googlemail.com": "Google Family",

    # --- Apple / iCloud Family ---
    "icloud.com": "Apple Family", 
    "me.com": "Apple Family", 
    "mac.com": "Apple Family",

    # ==========================================
    # 2. PRIVACY & INDEPENDENT WEBMAIL
    # ==========================================
    
    # --- Proton Family ---
    "proton.me": "Proton Family", "protonmail.com": "Proton Family",
    "protonmail.ch": "Proton Family", "pm.me": "Proton Family",
    
    # --- Tutanota / Tuta Family ---
    "tutanota.com": "Tuta Family", "tutanota.de": "Tuta Family",
    "tutamail.com": "Tuta Family", "tuta.io": "Tuta Family", 
    "keemail.me": "Tuta Family",
    
    # --- Zoho Family ---
    "zoho.com": "Zoho Family", "zohomail.com": "Zoho Family",
    "zohomail.eu": "Zoho Family", "zohomail.in": "Zoho Family",
    
    # --- Fastmail Family ---
    "fastmail.com": "Fastmail Family", "fastmail.fm": "Fastmail Family",
    "fastmail.co.uk": "Fastmail Family", "fastmail.com.au": "Fastmail Family",
    
    # --- Other Secure/Privacy Webmail ---
    "mailbox.org": "Mailbox.org Family",
    "posteo.de": "Posteo Family", "posteo.net": "Posteo Family",
    "runbox.com": "Runbox Family",
    "hushmail.com": "Hushmail Family",
    "startmail.com": "StartMail Family",
    "skiff.com": "Skiff Family",

    # ==========================================
    # 3. MAIL.COM / UNITED INTERNET MASSIVE NETWORK
    # ==========================================
    "gmx.com": "GMX Family", "gmx.de": "GMX Family", "gmx.at": "GMX Family", 
    "gmx.ch": "GMX Family", "gmx.net": "GMX Family", "gmx.org": "GMX Family",
    "gmx.fr": "GMX Family", "gmx.co.uk": "GMX Family", "gmx.es": "GMX Family",
    "web.de": "WEB.DE Family",
    
    # Mail.com specific subdomains
    "mail.com": "Mail.com Family", "email.com": "Mail.com Family", 
    "usa.com": "Mail.com Family", "myself.com": "Mail.com Family", 
    "post.com": "Mail.com Family", "consultant.com": "Mail.com Family", 
    "dr.com": "Mail.com Family", "engineer.com": "Mail.com Family", 
    "europe.com": "Mail.com Family", "asia.com": "Mail.com Family", 
    "iname.com": "Mail.com Family", "writeme.com": "Mail.com Family", 
    "techie.com": "Mail.com Family", "cheerful.com": "Mail.com Family", 
    "programmer.net": "Mail.com Family", "musician.org": "Mail.com Family",
    "contractor.net": "Mail.com Family", "linuxmail.org": "Mail.com Family",
    "accountant.com": "Mail.com Family", "clerk.com": "Mail.com Family",
    "financialservices.com": "Mail.com Family", "lawyer.com": "Mail.com Family",
    "realtyagent.com": "Mail.com Family", "teachers.org": "Mail.com Family",
    "activist.com": "Mail.com Family", "artlover.com": "Mail.com Family",
    "atheist.com": "Mail.com Family", "bikerider.com": "Mail.com Family",
    "elvisfan.com": "Mail.com Family", "gardener.com": "Mail.com Family",

    # ==========================================
    # 4. NORTH AMERICAN ISPs & LEGACY
    # ==========================================
    
    # --- AOL / OATH Legacy ---
    "aol.com": "AOL Family", "aol.co.uk": "AOL Family", "aol.de": "AOL Family",
    "aol.fr": "AOL Family", "aol.it": "AOL Family", "aol.es": "AOL Family",
    "aol.ca": "AOL Family", "aol.com.au": "AOL Family", "aol.co.jp": "AOL Family",
    "aol.com.br": "AOL Family", "netscape.net": "AOL Family", "cs.com": "AOL Family",
    "compuserve.com": "AOL Family", "wmconnect.com": "AOL Family",
    
    # --- US Telecoms/ISPs ---
    "verizon.net": "Verizon Family",
    "comcast.net": "Comcast Family",
    "att.net": "AT&T Family", "sbcglobal.net": "AT&T Family", 
    "bellsouth.net": "AT&T Family", "prodigy.net": "AT&T Family",
    "charter.net": "Spectrum Family", "spectrum.net": "Spectrum Family",
    "cox.net": "Cox Family",
    "earthlink.net": "EarthLink Family", "mindspring.com": "EarthLink Family",
    "optonline.net": "Optimum Family", "optimum.net": "Optimum Family",
    "centurylink.net": "CenturyLink Family", "embarqmail.com": "CenturyLink Family",
    "frontier.com": "Frontier Family", "frontiernet.net": "Frontier Family",
    "windstream.net": "Windstream Family",
    "juno.com": "United Online Family", "netzero.net": "United Online Family", "netzero.com": "United Online Family",
    "suddenlink.net": "Suddenlink Family",
    
    # --- Canadian Telecoms/ISPs ---
    "sympatico.ca": "Bell Canada Family", "bell.net": "Bell Canada Family",
    "shaw.ca": "Shaw Family",
    "rogers.com": "Rogers Family",
    "telus.net": "Telus Family",
    "videotron.ca": "Videotron Family",
    "cogeco.ca": "Cogeco Family",

    # ==========================================
    # 5. EUROPEAN ISPs & REGIONAL GIANTS
    # ==========================================

    # --- UK ---
    "btinternet.com": "BT Family", "btopenworld.com": "BT Family",
    "talktalk.net": "TalkTalk Family", "tiscali.co.uk": "TalkTalk Family",
    "virginmedia.com": "Virgin Media Family", "blueyonder.co.uk": "Virgin Media Family", 
    "ntlworld.com": "Virgin Media Family",
    "sky.com": "Sky Family",
    "tesco.net": "Tesco Family", "o2.co.uk": "O2 Family", "orange.net": "Orange UK Family",
    
    # --- Germany ---
    "freenet.de": "Freenet Family",
    "t-online.de": "Telekom Family",
    "mail.de": "Mail.de Family",
    "arcor.de": "Vodafone Germany Family", "vodafone.de": "Vodafone Germany Family", 
    "kabelmail.de": "Vodafone Germany Family", "alice.de": "O2 Germany Family",

    # --- France ---
    "orange.fr": "Orange Family", "wanadoo.fr": "Orange Family",
    "sfr.fr": "SFR Family", "neuf.fr": "SFR Family", "club-internet.fr": "SFR Family",
    "free.fr": "Free Family", "aliceadsl.fr": "Free Family",
    "laposte.net": "La Poste Family",
    "bbox.fr": "Bouygues Family", "numericable.fr": "Numericable Family",

    # --- Italy ---
    "libero.it": "Libero Family", "virgilio.it": "Virgilio Family",
    "alice.it": "TIM Family", "tin.it": "TIM Family", "tim.it": "TIM Family",
    "tiscali.it": "Tiscali Family", "fastwebnet.it": "Fastweb Family",

    # --- Spain ---
    "terra.es": "Terra Family", "telefonica.net": "Telefonica Family", 
    "movistar.es": "Telefonica Family", "ya.com": "Ya.com Family",
    "orange.es": "Orange Spain Family", "vodafone.es": "Vodafone Spain Family", "ono.com": "Vodafone Spain Family",

    # --- Netherlands & Belgium ---
    "ziggo.nl": "Ziggo Family", "home.nl": "Ziggo Family",
    "kpnmail.nl": "KPN Family", "planet.nl": "KPN Family", "hetnet.nl": "KPN Family",
    "telenet.be": "Telenet Family",
    "proximus.be": "Proximus Family", "skynet.be": "Proximus Family",

    # --- Switzerland & Austria ---
    "bluewin.ch": "Swisscom Family", "sunrise.ch": "Sunrise Family",
    "aon.at": "A1 Austria Family", "chello.at": "Magenta Austria Family",

    # --- Nordics (Sweden, Norway, Denmark, Finland) ---
    "telia.com": "Telia Family",
    "tele2.se": "Tele2 Family", "comhem.se": "Tele2 Family",
    "spray.se": "Spray Family", "bahnhof.se": "Bahnhof Family",
    "online.no": "Telenor Family",
    "tdc.dk": "TDC Family", "yousee.dk": "TDC Family",
    "elisa.fi": "Elisa Family", "saunalahti.fi": "Elisa Family",

    # --- Eastern Europe (Russia, Ukraine, Poland, Czech, Romania, etc.) ---
    "mail.ru": "Mail.ru Family", "inbox.ru": "Mail.ru Family", 
    "list.ru": "Mail.ru Family", "bk.ru": "Mail.ru Family", "internet.ru": "Mail.ru Family",
    "yandex.ru": "Yandex Family", "yandex.com": "Yandex Family", "ya.ru": "Yandex Family",
    "rambler.ru": "Rambler Family",
    "ukr.net": "Ukr.net Family", "i.ua": "I.UA Family", "meta.ua": "Meta.ua Family",
    "wp.pl": "Wirtualna Polska Family", "o2.pl": "O2 Poland Family",
    "interia.pl": "Interia Family", "onet.pl": "Onet Family",
    "seznam.cz": "Seznam Family", "email.cz": "Seznam Family", "centrum.cz": "Centrum Family",
    "zappmobile.ro": "Zapp Family", "abv.bg": "ABV Bulgaria Family", "mail.bg": "Mail.bg Family",
    "freemail.hu": "Freemail Hungary Family", "citromail.hu": "Citromail Hungary Family",
    "azet.sk": "Azet Slovakia Family",
    "otenet.gr": "Cosmote Greece Family", "forthnet.gr": "Nova Greece Family",

    # ==========================================
    # 6. ASIA & OCEANIA ISPs & REGIONAL GIANTS
    # ==========================================

    # --- China ---
    "qq.com": "Tencent Family", "foxmail.com": "Tencent Family",
    "163.com": "NetEase Family", "126.com": "NetEase Family", "yeah.net": "NetEase Family",
    "sina.com": "Sina Family", "sina.cn": "Sina Family", "vip.sina.com": "Sina Family",
    "sohu.com": "Sohu Family",
    "aliyun.com": "Alibaba Family",
    "tom.com": "TOM Family",
    "139.com": "China Mobile Family", "189.cn": "China Telecom Family", "wo.cn": "China Unicom Family",

    # --- Japan ---
    "docomo.ne.jp": "NTT Docomo Family",
    "softbank.ne.jp": "SoftBank Family", "i.softbank.jp": "SoftBank Family",
    "ezweb.ne.jp": "au KDDI Family", "au.com": "au KDDI Family",
    "nifty.com": "Nifty Family", "ybb.ne.jp": "Yahoo Japan BB Family",
    "plala.or.jp": "Plala Family", "ocn.ne.jp": "OCN Family",
    "goo.jp": "Goo Family", "biglobe.ne.jp": "Biglobe Family", "so-net.ne.jp": "So-net Family",

    # --- South Korea ---
    "naver.com": "Naver Family", "line.me": "Naver Family",
    "daum.net": "Kakao Family", "hanmail.net": "Kakao Family", "kakao.com": "Kakao Family",
    "nate.com": "Nate Family", "korea.com": "Korea.com Family", 
    "empas.com": "Empas Family", "chol.com": "Chol Family", "dreamwiz.com": "DreamWiz Family",

    # --- India ---
    "rediffmail.com": "Rediffmail Family",
    "sify.com": "Sify Family",
    "indiatimes.com": "IndiaTimes Family",
    "jio.com": "Jio Family", "bsnl.in": "BSNL Family", "mtnl.net.in": "MTNL Family",

    # --- Taiwan & Hong Kong ---
    "msa.hinet.net": "HiNet Taiwan Family", "pchome.com.tw": "PChome Taiwan Family",
    "seed.net.tw": "Seednet Taiwan Family", "sparqnet.net": "Sparq Taiwan Family",
    "netvigator.com": "Netvigator HK Family",

    # --- Southeast Asia (Indonesia, Philippines, etc.) ---
    "plasa.com": "Telkom Indonesia Family", "telkom.net": "Telkom Indonesia Family",
    "cbn.net.id": "CBN Indonesia Family", "centrin.net.id": "Centrin Indonesia Family", 
    "indosat.net.id": "Indosat Indonesia Family",

    # --- Australia & New Zealand ---
    "bigpond.com": "Telstra Family", "bigpond.net.au": "Telstra Family",
    "optusnet.com.au": "Optus Family",
    "tpg.com.au": "TPG Family",
    "iinet.net.au": "iiNet Family",
    "xtra.co.nz": "Spark NZ Family", "clear.net.nz": "Vodafone NZ Family",

    # ==========================================
    # 7. LATIN AMERICA, MIDDLE EAST & AFRICA
    # ==========================================
    
    # --- Brazil ---
    "uol.com.br": "UOL Family", "bol.com.br": "BOL Family",
    "terra.com.br": "Terra Family", "ig.com.br": "iG Family",
    "globomail.com": "Globo Family",
    
    # --- Rest of Latin America ---
    "uol.com.ar": "UOL Argentina Family", "fibertel.com.ar": "Fibertel Argentina Family", 
    "arnet.com.ar": "Telecom Argentina Family",
    "prodigy.net.mx": "Telmex Mexico Family",
    "vtr.net": "VTR Chile Family",

    # --- Middle East (Israel, Turkey, etc.) ---
    "walla.co.il": "Walla Israel Family", "bezeqint.net": "Bezeq Israel Family", 
    "netvision.net.il": "Cellcom Israel Family",
    "mynet.com": "Mynet Turkey Family", "ttmail.com": "Turk Telekom Family",

    # --- Africa ---
    "mweb.co.za": "MWeb South Africa Family",
    "telkomsa.net": "Telkom South Africa Family",
    "vodamail.co.za": "Vodacom South Africa Family",
}


# =====================================================================
# EDUCATION TLD SUFFIXES (checked as domain suffix)
# =====================================================================
EDU_SUFFIXES = {
    # Generic / New Top-Level Domains (gTLDs)
    "edu", "ac", "sch",
    "academy", "college", "degree", "education", "institute", 
    "school", "university", "courses", "study", "mba", "phd", 
    "scholarships", "training", "alumni",

    # UK
    "ac.uk", "edu.uk", "sch.uk", "gov.uk", 

    # North America
    "edu.ca", "ac.ca", "k12.ca", "cegep.ca",
    "edu.mx",
    
    # United States (State-level K-12 and Community Colleges)
    "k12.al.us", "cc.al.us", "k12.ak.us", "cc.ak.us", "k12.az.us", "cc.az.us",
    "k12.ar.us", "cc.ar.us", "k12.ca.us", "cc.ca.us", "k12.co.us", "cc.co.us",
    "k12.ct.us", "cc.ct.us", "k12.de.us", "cc.de.us", "k12.fl.us", "cc.fl.us",
    "k12.ga.us", "cc.ga.us", "k12.hi.us", "cc.hi.us", "k12.id.us", "cc.id.us",
    "k12.il.us", "cc.il.us", "k12.in.us", "cc.in.us", "k12.ia.us", "cc.ia.us",
    "k12.ks.us", "cc.ks.us", "k12.ky.us", "cc.ky.us", "k12.la.us", "cc.la.us",
    "k12.me.us", "cc.me.us", "k12.md.us", "cc.md.us", "k12.ma.us", "cc.ma.us",
    "k12.mi.us", "cc.mi.us", "k12.mn.us", "cc.mn.us", "k12.ms.us", "cc.ms.us",
    "k12.mo.us", "cc.mo.us", "k12.mt.us", "cc.mt.us", "k12.ne.us", "cc.ne.us",
    "k12.nv.us", "cc.nv.us", "k12.nh.us", "cc.nh.us", "k12.nj.us", "cc.nj.us",
    "k12.nm.us", "cc.nm.us", "k12.ny.us", "cc.ny.us", "k12.nc.us", "cc.nc.us",
    "k12.nd.us", "cc.nd.us", "k12.oh.us", "cc.oh.us", "k12.ok.us", "cc.ok.us",
    "k12.or.us", "cc.or.us", "k12.pa.us", "cc.pa.us", "k12.ri.us", "cc.ri.us",
    "k12.sc.us", "cc.sc.us", "k12.sd.us", "cc.sd.us", "k12.tn.us", "cc.tn.us",
    "k12.tx.us", "cc.tx.us", "k12.ut.us", "cc.ut.us", "k12.vt.us", "cc.vt.us",
    "k12.va.us", "cc.va.us", "k12.wa.us", "cc.wa.us", "k12.wv.us", "cc.wv.us",
    "k12.wi.us", "cc.wi.us", "k12.wy.us", "cc.wy.us", "edu.pr", 

    # Oceania
    "edu.au", "ac.au", "schools.nsw.edu.au", "vic.edu.au", "qld.edu.au", 
    "sa.edu.au", "wa.edu.au", "tas.edu.au", "nt.edu.au", "act.edu.au",
    "catholic.edu.au", "eq.edu.au", "det.nsw.edu.au",
    "ac.nz", "edu.nz", "school.nz",
    "ac.pg", "ac.fj", "ac.ws", "edu.vu", 

    # Asia (East & Southeast)
    "edu.cn", "ac.cn",
    "ac.jp", "edu.jp", "ed.jp", "sch.jp",
    "ac.kr", "edu.kr", "hs.kr", "ms.kr", "es.kr", "sc.kr",
    "edu.tw", "ac.tw",
    "edu.hk", "ac.hk",
    "edu.mo", "ac.mo",
    "ac.id", "edu.id", "sch.id", "ponpes.id", "ptn.id", "pts.id",
    "edu.my", "ac.my",
    "edu.sg", "ac.sg", "sch.sg",
    "edu.ph", "ac.ph",
    "ac.th", "edu.th", "sch.th",
    "edu.vn", "ac.vn",
    "edu.bn", "edu.mm", "edu.kh", "edu.la", 

    # Asia (South & Central)
    "edu.in", "ac.in", "ernet.in", "res.in", "sch.in",
    "edu.pk", "ac.pk",
    "edu.bd", "ac.bd",
    "edu.lk", "ac.lk", "sch.lk",
    "edu.np", "ac.np",
    "edu.af", "edu.bt", "edu.mv", 
    "edu.kz", "edu.uz", "edu.kg", "edu.tj", "edu.tm", 

    # Middle East
    "ac.ir", "edu.ir", "sch.ir",
    "edu.tr", "ac.tr", "k12.tr",
    "ac.il", "edu.il", "k12.il",
    "edu.sa", "ac.sa", "sch.sa",
    "ac.ae", "edu.ae", "sch.ae",
    "edu.bh", "edu.om", "edu.qa", "edu.kw", "edu.lb", "edu.jo", "edu.sy", 
    "edu.iq", "edu.ye", "edu.ps", 

    # Africa
    "ac.za", "edu.za", "school.za", "nom.za",
    "edu.ng", "ac.ng", "sch.ng",
    "ac.ke", "edu.ke", "sc.ke",
    "edu.eg", "eun.eg", "sci.eg",
    "ac.ma", "ac.mz", "ac.mw", "ac.mu",
    "edu.dz", "edu.gh", "edu.et", "edu.zm", "ac.zm", "ac.zw", "edu.sd",
    "ac.ug", "ac.tz", "ac.rw",
    "edu.so", "edu.ly", "edu.sn", "edu.ci", "edu.bi", "edu.lr",

    # South & Central America / Caribbean
    "edu.br", "ac.br",
    "edu.ar", "edu.co", "edu.cl", "edu.pe", "edu.ve", "edu.ec", 
    "edu.uy", "edu.py", "edu.bo",
    "ac.cr", "ed.cr",
    "ac.pa", "edu.pa", "edu.gt", "edu.sv", "edu.hn", "edu.ni", 
    "edu.do", "edu.cu", "edu.jm", "edu.ht", "edu.bs", "edu.bb",

    # Europe
    "ac.de", "edu.de", "schule.de",
    "ac.fr", "edu.fr", "educ.fr",
    "ac.it", "edu.it", "scuola.it",
    "ac.es", "edu.es",
    "ac.nl", "edu.nl",
    "ac.be", "edu.be",
    "ac.ch", "edu.ch",
    "ac.at", "edu.at",
    "ac.dk", "edu.dk",
    "ac.se", "edu.se",
    "ac.no", "edu.no", "skole.no",
    "ac.fi", "edu.fi",
    "ac.pl", "edu.pl",
    "ac.cz", "edu.cz",
    "ac.hu", "edu.hu",
    "ac.ro", "edu.ro",
    "ac.gr", "edu.gr", "sch.gr",
    "ac.pt", "edu.pt",
    "ac.ie", "edu.ie",
    "edu.ru", "ac.ru",
    "edu.ua", "edu.ee", "edu.lv", "edu.lt",
    "skole.hr",
    "edu.rs", "ac.rs",
    "edu.sk", "edu.si",
    "ac.cy", "edu.mt",
    "edu.bg", "edu.ge", "edu.am", "edu.az",
    "edu.ba", "edu.mk", "edu.al", "edu.md", "edu.by",
}


# =====================================================================
# EDUCATION LABELS (checked as domain labels, NOT the last/TLD label)
# E.g., "harvard.edu" -> "harvard" and "edu" are labels.
# 2-letter keys that heavily conflict with country TLDs are mostly 
# excluded unless highly specific to school infrastructure.
# =====================================================================
EDU_LABELS = {
    # Core English Terms
    "edu", "ac", "ach", "acad",
    "school", "schools", "schooling",
    "univ", "university", "universities", "uni",
    "college", "colleges", "collegiate",
    "academy", "academies", "academic", "academia",
    "institute", "institutes", "institution", "institutions",
    "education", "educational", "educator", "educators", "edtech",
    "polytechnic", "seminary", "conservatory", "conservatoire", "vocational",
    
    # Campus & People
    "campus", "faculty", "staff", "faculty-staff",
    "student", "students", "studentmail", "scholars",
    "alumni", "alum", "alumnus", "alumnae", "alumninetwork",
    "research", "researcher", "researchers", "laboratory", "labs",
    "teacher", "teachers", "professor", "professors", "lecturer", "lecturers",
    "tutor", "tutors", "tutoring",
    "chancellor", "provost", "dean", "deans", "principal", "headmaster",
    "fraternity", "sorority", "varsity", "intramural", "athletics",
    
    # Facilities & Departments
    "library", "libraries", "registrar", "admissions", "enrollment", 
    "financialaid", "bursar", "department", "departments", "dept",
    "dorm", "dormitory", "residence", "reslife", "dininghall",
    "medschool", "lawschool", "bizschool", "engineering", "humanities", "sciences",

    # School Types
    "elementary", "primary", "secondary",
    "highschool", "high-school", "middleschool", "middle-school",
    "juniorhigh", "junior-high", "seniorhigh",
    "kindergarten", "kinder", "preschool", "pre-school", "k12", "prek",
    "nursery", "creche", "playschool",
    "boardingschool", "prep", "preparatory", "trade-school",
    "daycare", "childcare", "homeschool", "homeschooling",
    "specialed", "specialneeds", "charterschool", "magnet-school",

    # Degrees & Programs
    "phd", "mba", "msc", "mse", "bachelors", "masters", "doctorate", "postdoc",
    "degree", "degrees",
    "graduate", "graduates", "gradschool",
    "undergraduate", "undergrad", "postgraduate", "postgrad",
    "diploma", "certificate", "certification", "baccalaureate",

    # Academics & Tech Operations (LMS / Portals)
    "learning", "learn", "study", "studies",
    "scholarship", "scholarships", "fellowship", "fellowships", "grants",
    "training", "course", "courses", "class", "classes", "classroom", "classrooms",
    "lesson", "lessons", "tutorial", "tutorials", "lecture", "lectures",
    "homework", "assignment", "assignments", "exam", "exams", "quiz", "quizzes", 
    "testing", "syllabus", "curriculum", "pedagogy", "pedagogical",
    "textbook", "textbooks", "tuition",
    
    # Online Education / Tech
    "elearning", "e-learning", "lms", "mooc", "moocs",
    "virtualschool", "onlineeducation", "onlinelearning",
    "blackboard", "canvas", "moodle", "turnitin", "powerschool", "banner",
    "studentportal", "student-portal", "webmail", "studentemail", 
    "library-proxy", "ezproxy", "distancelearning",

    # --- INTERNATIONAL / MULTILINGUAL TERMS ---
    
    # Spanish / Portuguese
    "escuela", "escuelas", "escola", "universidad", "universidade",
    "colegio", "colegios", "instituto", "educacion", "ensino",
    "profesor", "alumno", "alumnos", "estudiante", "estudiantes", 
    "facultad", "faculdade", "academico",
    "colegiatura", "licenciatura", "maestria", "doctorado", "beca", "becas",
    "preescolar", "primaria", "secundaria", "preparatoria", "bachillerato", 
    "catedratico", "docente",

    # French
    "ecole", "universite", "lycee", "college", "etudiant", "professeur", 
    "formation", "enseignement", "academie", "collegien", "lyceen", 
    "maternelle", "bac", "baccalaureat", "licence", "maitrise", "doctorat", 
    "bourses", "crous", "rectorat",

    # German / Dutch
    "schule", "universitat", "hochschule", "gymnasium", "studenten",
    "bildung", "lehrer", "fachhochschule", "onderwijs", "universiteit",
    "grundschule", "realschule", "hauptschule", "gesamtschule", 
    "berufsschule", "studium", "studentenwerk", "professur", "fakultaet", "dozent",

    # Italian
    "scuola", "universita", "insegnante", "alunno", "ateneo", "liceo", "facolta",

    # Indonesian / Malay
    "sekolah", "universitas", "kampus", "akademik", "siswa", "mahasiswa",
    "guru", "dosen", "pendidikan", "belajar", "pelajar", "pesantren",
    "madrasah", "politeknik", "institut", "dikti", "kemdikbud", "kemenag",
    "ristekdikti", "lldikti", "kopertis", "ptn", "pts", "ptkin", "ptkis",
    "tk", "paud", "sd", "smp", "sma", "smk", "mts", "man", "min", 
    "bimbel", "bimbinganbelajar", "les",
    "skripsi", "tesis", "disertasi", "jurnal",
    "rektor", "rektorat", "dekan", "dekanat", "kaprodi", "kajur",
    "siakad", "simak", "spada", "vokasi", "sarjana", "pascasarjana",

    # Nordic / Scandinavian
    "skole", "skola", "gymnasieskola", "universitet", "hogskola", "studerende", 
    "utdanning", "opplaering", "videregaende",

    # Russian / Slavic (Transliterated)
    "shkola", "universitet", "akademia", "fakultet", "kafedra", 
    "abiturient", "aspirantura", "magistratura", "bakalavriat", 
    "uchilishche", "tekhnikum", "institut",

    # Turkish
    "okul", "universite", "ogrenci", "egitim", "lise", "fakulte", "kampus",

    # Arabic / Hindi / Japanese / Others (Transliterated)
    "madrasa", "jamia", "tarbiya", "kulliya",
    "vidyalaya", "shiksha", "vishvavidyalaya", "gurukul",
    "daigaku", "gakko", "sensei", "juku",
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
