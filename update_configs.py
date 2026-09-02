#!/usr/bin/env python3
import requests
import random
import base64
import re
from datetime import datetime, timezone
from urllib.parse import unquote, quote

# ─── Заголовок файла ──────────────────────────────────────────────────────────
def build_header():
    now = datetime.now(timezone.utc).strftime('%H:%M %d.%m.%Y UTC')
    return f"""\
#profile-title: nzpn wl 2.0.2
#announce: Последний апдейт на GitHub: {now}| Не работает — обнови подписку | Версия 2.0.2
#support-url: https://t.me/nzea_tri_bykvi
#profile-web-page-url:https://t.me/send?start=IV9P4rO9112W
#profile-update-interval: 1
#profile-locked: true
#profile-type: encrypted
#profile-locked: true
#hide-settings: 1"""

SEPARATOR_BYPASS = "vless://info@0.0.0.0:443?type=tcp&security=none#для обхода бс👇"

BYPASS_SOURCES = [
    "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-all.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass/bypass-all.txt",
    "https://raw.githubusercontent.com/VOID-Anonymity/V.O.I.D-VPN_Bypass/refs/heads/main/url_work.txt",
    "https://sub.obbhod.online/premium",
    "https://raw.githubusercontent.com/Temnuk/naabuzil/refs/heads/main/whitelist_full",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/V2RAY_RAW.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-checker-backend/refs/heads/main/checked/RU_Best/ru_white_all_WHITE.txt",
    "https://gitverse.ru/api/repos/kfwlru/sub/raw/branch/main/212.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/26.txt",
    "https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/selected.txt",
    "https://gitverse.ru/api/repos/bywarm/rser/raw/branch/master/merged.txt",
    "https://gist.github.com/DestroyST6767/50af50221ca1858ba2084efc0f524fbc.txt",
    "https://drive.usercontent.google.com/download?id=1Rl6jIlf2Ula__J9F9nRmCuE6RFdqMTgk&export=download&confirm=t",
    "https://raw.githubusercontent.com/AirLinkVPN1/AirLinkVPN/refs/heads/main/rkn_white_list",
    "https://raw.githubusercontent.com/dequar/deqwl/refs/heads/main/deray.txt",
    "https://gitflic.ru/project/sigil/my-new-cool-project/blob/raw?file=whitelist",
    "https://raw.githubusercontent.com/Sanuyyq/sub-storage1/refs/heads/main/bs.txt",
    "https://raw.githubusercontent.com/ewecrow78-gif/whitelist1/main/list.txt",
    "https://ety.twinkvibe.gay/whitelist",
    "https://raw.githubusercontent.com/ByeWhiteLists/ByeWhiteLists2/refs/heads/main/ByeWhiteLists2.txt",
    "https://raw.githubusercontent.com/Maskkost93/kizyak-vpn-4.0/refs/heads/main/kizyakbeta6.txt",
]

VALID_PREFIXES = ('vless://',)
IP_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

# ─── Настройки подписки для Hiddify ───────────────────────────────────────────
HIDDIFY_BANNED_TRANSPORTS = ('kcp', 'domainsocket', 'tcp', 'xhttp')

def get_query_params(config: str) -> dict[str, str]:
    s = config.split('#', 1)[0]
    if '?' not in s:
        return {}
    query = s.split('?', 1)[1]
    params = {}
    for part in query.split('&'):
        if not part:
            continue
        if '=' in part:
            k, v = part.split('=', 1)
        else:
            k, v = part, ''
        params[unquote(k).lower()] = unquote(v).lower()
    return params

def get_transport(config: str) -> str:
    params = get_query_params(config)
    return params.get('type', 'tcp')

def is_transport_allowed(config: str) -> bool:
    return get_transport(config) not in HIDDIFY_BANNED_TRANSPORTS

# ─── База стран ───────────────────────────────────────────────────────────────
def _flag(cc):
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in cc.upper())

_NAMES = [
    ('RU', ['🇷🇺', 'Russia', 'Россия', 'RUS', r'\bRU\b']),
    ('UA', ['🇺🇦', 'Ukraine', 'Украина', r'\bUA\b']),
    ('BY', ['🇧🇾', 'Belarus', 'Беларусь', r'\bBY\b']),
    ('KZ', ['🇰🇿', 'Kazakhstan', 'Казахстан', r'\bKZ\b']),
    ('UZ', ['🇺🇿', 'Uzbekistan', 'Узбекистан', r'\bUZ\b']),
    ('AZ', ['🇦🇿', 'Azerbaijan', r'\bAZ\b']),
    ('GE', ['🇬🇪', 'Georgia', r'\bGE\b']),
    ('AM', ['🇦🇲', 'Armenia', r'\bAM\b']),
    ('MD', ['🇲🇩', 'Moldova', r'\bMD\b']),
    ('KG', ['🇰🇬', 'Kyrgyzstan', r'\bKG\b']),
    ('TJ', ['🇹🇯', 'Tajikistan', r'\bTJ\b']),
    ('TM', ['🇹🇲', 'Turkmenistan', r'\bTM\b']),
    ('DE', ['🇩🇪', 'Germany', 'Deutschland', 'Германия', r'\bDE\b']),
    ('FR', ['🇫🇷', 'France', 'Франция', r'\bFR\b']),
    ('GB', ['🇬🇧', 'United Kingdom', 'UK', 'Britain', r'\bGB\b']),
    ('NL', ['🇳🇱', 'Netherlands', 'Holland', r'\bNL\b']),
    ('FI', ['🇫🇮', 'Finland', r'\bFI\b']),
    ('SE', ['🇸🇪', 'Sweden', r'\bSE\b']),
    ('NO', ['🇳🇴', 'Norway', r'\bNO\b']),
    ('PL', ['🇵🇱', 'Poland', r'\bPL\b']),
    ('CZ', ['🇨🇿', 'Czech', r'\bCZ\b']),
    ('AT', ['🇦🇹', 'Austria', r'\bAT\b']),
    ('CH', ['🇨🇭', 'Switzerland', r'\bCH\b']),
    ('BE', ['🇧🇪', 'Belgium', r'\bBE\b']),
    ('DK', ['🇩🇰', 'Denmark', r'\bDK\b']),
    ('ES', ['🇪🇸', 'Spain', r'\bES\b']),
    ('IT', ['🇮🇹', 'Italy', r'\bIT\b']),
    ('PT', ['🇵🇹', 'Portugal', r'\bPT\b']),
    ('HU', ['🇭🇺', 'Hungary', r'\bHU\b']),
    ('RO', ['🇷🇴', 'Romania', r'\bRO\b']),
    ('BG', ['🇧🇬', 'Bulgaria', r'\bBG\b']),
    ('TR', ['🇹🇷', 'Turkey', 'Турция', r'\bTR\b']),
    ('LT', ['🇱🇹', 'Lithuania', r'\bLT\b']),
    ('LV', ['🇱🇻', 'Latvia', r'\bLV\b']),
    ('EE', ['🇪🇪', 'Estonia', r'\bEE\b']),
    ('SK', ['🇸🇰', 'Slovakia', r'\bSK\b']),
    ('SI', ['🇸🇮', 'Slovenia', r'\bSI\b']),
    ('HR', ['🇭🇷', 'Croatia', r'\bHR\b']),
    ('RS', ['🇷🇸', 'Serbia', r'\bRS\b']),
    ('AL', ['🇦🇱', 'Albania', r'\bAL\b']),
    ('ME', ['🇲🇪', 'Montenegro', r'\bME\b']),
    ('MK', ['🇲🇰', 'Macedonia', r'\bMK\b']),
    ('IS', ['🇮🇸', 'Iceland', r'\bIS\b']),
    ('LU', ['🇱🇺', 'Luxembourg', r'\bLU\b']),
    ('MT', ['🇲🇹', 'Malta', r'\bMT\b']),
    ('CY', ['🇨🇾', 'Cyprus', r'\bCY\b']),
    ('JP', ['🇯🇵', 'Japan', 'Япония', r'\bJP\b']),
    ('KR', ['🇰🇷', 'Korea', r'\bKR\b']),
    ('CN', ['🇨🇳', 'China', 'Китай', r'\bCN\b']),
    ('HK', ['🇭🇰', 'Hong Kong', r'\bHK\b']),
    ('TW', ['🇹🇼', 'Taiwan', r'\bTW\b']),
    ('SG', ['🇸🇬', 'Singapore', r'\bSG\b']),
    ('MY', ['🇲🇾', 'Malaysia', r'\bMY\b']),
    ('ID', ['🇮🇩', 'Indonesia', r'\bID\b']),
    ('TH', ['🇹🇭', 'Thailand', r'\bTH\b']),
    ('VN', ['🇻🇳', 'Vietnam', r'\bVN\b']),
    ('IN', ['🇮🇳', 'India', r'\bIN\b']),
    ('PK', ['🇵🇰', 'Pakistan', r'\bPK\b']),
    ('BD', ['🇧🇩', 'Bangladesh', r'\bBD\b']),
    ('MN', ['🇲🇳', 'Mongolia', r'\bMN\b']),
    ('AE', ['🇦🇪', 'Emirates', 'UAE', r'\bAE\b']),
    ('SA', ['🇸🇦', 'Saudi', r'\bSA\b']),
    ('IL', ['🇮🇱', 'Israel', r'\bIL\b']),
    ('IR', ['🇮🇷', 'Iran', r'\bIR\b']),
    ('IQ', ['🇮🇶', 'Iraq', r'\bIQ\b']),
    ('ZA', ['🇿🇦', 'South Africa', r'\bZA\b']),
    ('NG', ['🇳🇬', 'Nigeria', r'\bNG\b']),
    ('EG', ['🇪🇬', 'Egypt', r'\bEG\b']),
    ('US', ['🇺🇸', 'United States', 'USA', r'\bUS\b']),
    ('CA', ['🇨🇦', 'Canada', r'\bCA\b']),
    ('MX', ['🇲🇽', 'Mexico', r'\bMX\b']),
    ('BR', ['🇧🇷', 'Brazil', r'\bBR\b']),
    ('AR', ['🇦🇷', 'Argentina', r'\bAR\b']),
    ('CL', ['🇨🇱', 'Chile', r'\bCL\b']),
    ('CO', ['🇨🇴', 'Colombia', r'\bCO\b']),
    ('AU', ['🇦🇺', 'Australia', r'\bAU\b']),
    ('NZ', ['🇳🇿', 'New Zealand', r'\bNZ\b']),
]

_FLAG_RE = re.compile(r'[\U0001F1E6-\U0001F1FF]{2}')
_BUILT_PATTERNS = []
for cc, aliases in _NAMES:
    flag = _flag(cc)
    for alias in aliases:
        if any(ord(c) > 127 for c in alias):
            try:
                _BUILT_PATTERNS.append((re.compile(re.escape(alias)), cc, flag))
            except re.error:
                pass
        elif re.fullmatch(r'\\b[A-Z]{2}\\b', alias):
            _BUILT_PATTERNS.append((re.compile(alias), cc, flag))
        else:
            try:
                _BUILT_PATTERNS.append((re.compile(alias, re.IGNORECASE), cc, flag))
            except re.error:
                pass

RUSSIA_CC = 'RU'

COUNTRY_RU_NAMES = {
    'RU': 'Россия',
    'UA': 'Украина',
    'BY': 'Беларусь',
    'KZ': 'Казахстан',
    'UZ': 'Узбекистан',
    'AZ': 'Азербайджан',
    'GE': 'Грузия',
    'AM': 'Армения',
    'MD': 'Молдова',
    'KG': 'Киргизия',
    'TJ': 'Таджикистан',
    'TM': 'Туркменистан',
    'DE': 'Германия',
    'FR': 'Франция',
    'GB': 'Великобритания',
    'NL': 'Нидерланды',
    'FI': 'Финляндия',
    'SE': 'Швеция',
    'NO': 'Норвегия',
    'PL': 'Польша',
    'CZ': 'Чехия',
    'AT': 'Австрия',
    'CH': 'Швейцария',
    'BE': 'Бельгия',
    'DK': 'Дания',
    'ES': 'Испания',
    'IT': 'Италия',
    'PT': 'Португалия',
    'HU': 'Венгрия',
    'RO': 'Румыния',
    'BG': 'Болгария',
    'TR': 'Турция',
    'LT': 'Литва',
    'LV': 'Латвия',
    'EE': 'Эстония',
    'SK': 'Словакия',
    'SI': 'Словения',
    'HR': 'Хорватия',
    'RS': 'Сербия',
    'AL': 'Албания',
    'ME': 'Черногория',
    'MK': 'Северная Македония',
    'IS': 'Исландия',
    'LU': 'Люксембург',
    'MT': 'Мальта',
    'CY': 'Кипр',
    'JP': 'Япония',
    'KR': 'Южная Корея',
    'CN': 'Китай',
    'HK': 'Гонконг',
    'TW': 'Тайвань',
    'SG': 'Сингапур',
    'MY': 'Малайзия',
    'ID': 'Индонезия',
    'TH': 'Таиланд',
    'VN': 'Вьетнам',
    'IN': 'Индия',
    'PK': 'Пакистан',
    'BD': 'Бангладеш',
    'MN': 'Монголия',
    'AE': 'ОАЭ',
    'SA': 'Саудовская Аравия',
    'IL': 'Израиль',
    'IR': 'Иран',
    'IQ': 'Ирак',
    'ZA': 'ЮАР',
    'NG': 'Нигерия',
    'EG': 'Египет',
    'US': 'США',
    'CA': 'Канада',
    'MX': 'Мексика',
    'BR': 'Бразилия',
    'AR': 'Аргентина',
    'CL': 'Чили',
    'CO': 'Колумбия',
    'AU': 'Австралия',
    'NZ': 'Новая Зеландия',
}

def detect_country(remark: str) -> tuple[str, str] | None:
    flags = _FLAG_RE.findall(remark)
    if flags:
        flag = flags[0]
        cc_chars = [chr(ord(c) - 0x1F1E6 + ord('A')) for c in flag]
        cc = ''.join(cc_chars)
        return flag, cc
    for pattern, cc, flag in _BUILT_PATTERNS:
        if pattern.search(remark):
            return flag, cc
    return None

def get_remark(config: str) -> str:
    if '#' in config:
        return unquote(config.split('#', 1)[1])
    return ''

def set_remark(config: str, remark: str) -> str:
    base = config.split('#', 1)[0] if '#' in config else config
    return base + '#' + quote(remark, safe='')

def extract_host(config: str) -> str:
    s = config.split('#', 1)[0]
    if '://' in s:
        s = s.split('://', 1)[1]
    if '@' in s:
        s = s.split('@', 1)[1]
    s = s.split('?', 1)[0]
    s = s.split('/', 1)[0]
    if ':' in s:
        if s.startswith('['):
            host = s.split(']', 1)[0][1:]
        else:
            host = s.split(':', 1)[0]
    else:
        host = s
    return host.strip()

def load_local_whitelist(filename: str) -> set[str]:
    values = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                v = line.strip()
                if v:
                    values.add(v)
    except FileNotFoundError:
        print(f"  ✗ Файл белого списка не найден: {filename}")
    return values

def fetch_configs(url: str) -> list[str]:
    try:
        r = requests.get(url, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        text = r.text.strip()
        try:
            decoded = base64.b64decode(text + '==').decode('utf-8', errors='ignore')
            if any(decoded.startswith(p) for p in VALID_PREFIXES):
                text = decoded
        except Exception:
            pass
        configs = [
            line.strip() for line in text.splitlines()
            if line.strip() and any(line.strip().startswith(p) for p in VALID_PREFIXES)
        ]
        print(f"  ✓ ...{url[-45:]}: {len(configs)}")
        return configs
    except Exception as e:
        print(f"  ✗ {url}: {e}")
        return []

def preprocess_pool(pool: list[str], is_bypass: bool, ip_whitelist: set[str], sni_whitelist: set[str], require_transport_allowed: bool = False) -> list[str]:
    valid = []
    for cfg in pool:
        remark = get_remark(cfg)
        if detect_country(remark) is None:
            continue
        if is_bypass:
            host = extract_host(cfg)
            if IP_RE.match(host):
                if host not in ip_whitelist:
                    continue
            else:
                if host not in sni_whitelist:
                    continue
        if require_transport_allowed and not is_transport_allowed(cfg):
            continue
        valid.append(cfg)
    return valid

def random_split(total: int, n: int) -> list[int]:
    weights = [random.random() for _ in range(n)]
    s = sum(weights)
    counts = [max(1, int(w / s * total)) for w in weights]
    diff = total - sum(counts)
    for _ in range(abs(diff)):
        idx = random.randint(0, n - 1)
        counts[idx] = max(1, counts[idx] + (1 if diff > 0 else -1))
    return counts

def sample_from_sources(pools: list[list[str]], total: int) -> list[str]:
    if not pools:
        return []
    counts = random_split(total, len(pools))
    result = []
    for pool, count in zip(pools, counts):
        candidates = random.sample(pool, min(count * 3, len(pool)))
        added = 0
        for cfg in candidates:
            if added >= count:
                break
            result.append(cfg)
            added += 1
    if len(result) < total:
        all_remaining = []
        for pool in pools:
            for cfg in pool:
                if cfg not in result:
                    all_remaining.append(cfg)
        random.shuffle(all_remaining)
        result.extend(all_remaining[:total - len(result)])
    random.shuffle(result)
    return result[:total]

def finalize_configs(configs: list[str], suffix: str) -> list[str]:
    counts = {}
    final_list = []
    for cfg in configs:
        remark = get_remark(cfg)
        res = detect_country(remark)
        if res is None:
            continue
        flag, cc = res
        name = COUNTRY_RU_NAMES.get(cc, cc)

        counts[cc] = counts.get(cc, 0) + 1
        num_str = f" {counts[cc]}" if counts[cc] > 1 else ""

        new_remark = f"{flag} {name}{num_str} | {suffix}"
        final_list.append(set_remark(cfg, new_remark))
    return final_list

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("📥 Загружаю локальные белые списки IP и SNI...")
    ip_whitelist = load_local_whitelist('ip_whitelist.txt')
    sni_whitelist = load_local_whitelist('sni_whitelist.txt')
    print(f"  ✓ IP в белом списке: {len(ip_whitelist)}")
    print(f"  ✓ SNI в белом списке: {len(sni_whitelist)}")

    print("\n📡 Загружаю bypass источники...")
    bypass_pools = []
    bypass_pools_hiddify = []
    for url in BYPASS_SOURCES:
        cfgs = fetch_configs(url)
        if cfgs:
            valid_p = preprocess_pool(cfgs, True, ip_whitelist, sni_whitelist)
            if valid_p:
                bypass_pools.append(valid_p)
            valid_p_hiddify = preprocess_pool(cfgs, True, ip_whitelist, sni_whitelist, require_transport_allowed=True)
            if valid_p_hiddify:
                bypass_pools_hiddify.append(valid_p_hiddify)

    print("\n📡 Формирую bypass конфиги (строго VLESS, 300 штук)...")
    bypass_sampled = sample_from_sources(bypass_pools, 300)
    bypass_final = finalize_configs(bypass_sampled, '@nzea234')

    # ── wl_228.txt (мобилка: только bypass, 300 конфигов) ─────────────────────
    wl_output = '\n'.join([build_header(), '', SEPARATOR_BYPASS, *bypass_final])
    with open('wl_228.txt', 'w', encoding='utf-8') as f:
        f.write(wl_output)

    print(f"\n✅ Готово! wl_228.txt: {len(bypass_final)} (VLESS)")

    # ── hiddify_wl.txt (отдельная подписка для Hiddify, без kcp/domainsocket/tcp/xhttp) ──
    print(f"\n📡 Формирую конфиги для Hiddify (запрещённые транспорты: {', '.join(HIDDIFY_BANNED_TRANSPORTS)})...")
    bypass_sampled_hiddify = sample_from_sources(bypass_pools_hiddify, 300)
    bypass_final_hiddify = finalize_configs(bypass_sampled_hiddify, '@nzea234')

    hiddify_output = '\n'.join([SEPARATOR_BYPASS, *bypass_final_hiddify])
    with open('hiddify_wl.txt', 'w', encoding='utf-8') as f:
        f.write(hiddify_output)

    print(f"✅ Готово! hiddify_wl.txt: {len(bypass_final_hiddify)} (VLESS, без {'/'.join(HIDDIFY_BANNED_TRANSPORTS)})")

if __name__ == '__main__':
    main()
