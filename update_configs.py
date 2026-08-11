#!/usr/bin/env python3
import requests
import random
import base64
import re
from datetime import datetime, timezone
from urllib.parse import unquote, quote, urlparse, parse_qs

# ─── Заголовок файла ──────────────────────────────────────────────────────────
def build_header():
    now = datetime.now(timezone.utc).strftime('%H:%M %d.%m.%Y UTC')
    return f"""\
#profile-title: nzea234vpnツ
#announce: Последний апдейт на GitHub: {now} | Не работает — обнови подписку на две стрелочки
#support-url: https://t.me/nzea_tri_bykvi
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

VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://', 'ssr://', 'hysteria2://', 'hy2://', 'tuic://')
ALLOWED_PREFIXES = ('vless://', 'hysteria2://', 'hy2://')

# ─── GeoIP-распознавание стран через API ─────────────────────────────────────
# Страна определяется по IP сервера, а не по названию/флагу в remark.
# Используется бесплатный batch API ip-api.com: до 100 IP за один запрос.
# Результаты кэшируются, чтобы не делать повторные запросы для одинаковых хостов.
RUSSIA_CC = 'RU'
GEOIP_API_URL = 'http://ip-api.com/batch'
GEOIP_BATCH_SIZE = 100

def extract_endpoint_host(config: str) -> str:
    """Возвращает host/IP из адреса конфигурации."""
    try:
        parsed = urlparse(config.split('#', 1)[0])
        return (parsed.hostname or '').strip().lower()
    except Exception:
        return ''

def resolve_host(host: str) -> str | None:
    """Резолвит доменное имя в IPv4. IPv6 здесь намеренно не используется."""
    if not host:
        return None
    try:
        import ipaddress
        ipaddress.ip_address(host)
        return host if ipaddress.ip_address(host).version == 4 else None
    except ValueError:
        pass

    try:
        import socket
        infos = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        for info in infos:
            ip = info[4][0]
            if ip:
                return ip
    except Exception:
        pass
    return None

class GeoIPResolver:
    def __init__(self):
        self.cache: dict[str, tuple[str, str] | None] = {}

    def resolve_configs(self, configs: list[str]) -> None:
        """Определяет страну всех конфигов одним/несколькими batch-запросами."""
        host_to_ip = {}
        for cfg in configs:
            host = extract_endpoint_host(cfg)
            if not host or host in self.cache or host in host_to_ip:
                continue
            ip = resolve_host(host)
            host_to_ip[host] = ip

        ips = list(dict.fromkeys(ip for ip in host_to_ip.values() if ip))
        if not ips:
            return

        print(f"  🌍 GeoIP: определяю страны для {len(ips)} IP через API...")

        for i in range(0, len(ips), GEOIP_BATCH_SIZE):
            batch = ips[i:i + GEOIP_BATCH_SIZE]
            try:
                response = requests.post(
                    GEOIP_API_URL,
                    json=[
                        {
                            'query': ip,
                            'fields': 'status,countryCode,country',
                        }
                        for ip in batch
                    ],
                    timeout=20,
                    headers={'User-Agent': 'nzea234vpn-geoip/1.0'},
                )
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, list):
                    raise ValueError("GeoIP API вернул неожиданный ответ")

                for item in data:
                    ip = item.get('query')
                    if item.get('status') == 'success' and item.get('countryCode'):
                        self.cache[ip] = (
                            item['countryCode'].upper(),
                            item.get('country', ''),
                        )
                    else:
                        self.cache[ip] = None

            except Exception as e:
                print(f"  ✗ GeoIP API: {e}")
                for ip in batch:
                    self.cache.setdefault(ip, None)

        # Привязываем результат IP обратно к hostname.
        for host, ip in host_to_ip.items():
            self.cache[host] = self.cache.get(ip)

        ok = sum(1 for host in host_to_ip if self.cache.get(host))
        print(f"  ✓ GeoIP: распознано {ok}/{len(host_to_ip)} хостов.")

    def detect_country(self, config: str) -> tuple[str, str] | None:
        host = extract_endpoint_host(config)
        if not host:
            return None

        result = self.cache.get(host)
        if not result:
            return None

        cc, _country_name = result
        return _flag(cc), cc

def _flag(cc: str) -> str:
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in cc.upper())

def get_remark(config: str) -> str:
    if '#' in config:
        return unquote(config.split('#', 1)[1])
    return ''

def set_remark(config: str, remark: str) -> str:
    base = config.split('#', 1)[0] if '#' in config else config
    return base + '#' + quote(remark, safe='')

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

def load_sni_whitelist(path: str = 'sni_list.txt') -> set[str]:
    allowed = set()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                domain = line.strip().lower()
                if domain:
                    allowed.add(domain)
    except FileNotFoundError:
        print(f"  ✗ Файл {path} не найден, SNI-фильтр отключён.")
    return allowed

def extract_sni(config: str) -> str:
    s = config.split('#', 1)[0]
    try:
        parsed = urlparse(s)
        qs = parse_qs(parsed.query)
        for key in ('sni', 'peer', 'host'):
            if key in qs and qs[key][0]:
                return qs[key][0].strip().lower()
    except Exception:
        pass
    return ''

def preprocess_pool(
    pool: list[str],
    sni_whitelist: set[str],
    geoip: GeoIPResolver,
) -> list[str]:
    valid = []
    for cfg in pool:
        if geoip.detect_country(cfg) is None:
            continue
        sni = extract_sni(cfg)
        if not sni or sni not in sni_whitelist:
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

def finalize_configs(
    configs: list[str],
    suffix: str,
    geoip: GeoIPResolver,
) -> list[str]:
    counts = {}
    final_list = []
    for cfg in configs:
        res = geoip.detect_country(cfg)
        if res is None:
            continue
        flag, cc = res
        is_foreign = (cc != RUSSIA_CC)
        ai_tag = ' (ai)' if is_foreign else ''
        
        counts[cc] = counts.get(cc, 0) + 1
        num_str = f" {counts[cc]}" if counts[cc] > 1 else ""
        
        new_remark = f"{flag}{ai_tag} {cc}{num_str} | {suffix}"
        final_list.append(set_remark(cfg, new_remark))
    return final_list

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("📥 Загружаю белый список SNI...")
    sni_whitelist = load_sni_whitelist()
    print(f"  ✓ Загружено {len(sni_whitelist)} разрешённых SNI.")

    print("\n📡 Загружаю bypass источники...")
    raw_pools = []
    all_candidates = []

    for url in BYPASS_SOURCES:
        cfgs = fetch_configs(url)
        if cfgs:
            # Отбираем только vless:// и hysteria2:// для мобилки (bypass / БС)
            cfgs_filtered = [cfg for cfg in cfgs if cfg.startswith(ALLOWED_PREFIXES)]
            if cfgs_filtered:
                raw_pools.append(cfgs_filtered)
                all_candidates.extend(cfgs_filtered)

    # Новый распознаватель: GeoIP по реальному endpoint IP.
    # В отличие от старого варианта, страна больше не берётся из remark.
    geoip = GeoIPResolver()
    geoip.resolve_configs(all_candidates)

    bypass_pools = []
    for pool in raw_pools:
        valid_p = preprocess_pool(pool, sni_whitelist, geoip)
        if valid_p:
            bypass_pools.append(valid_p)

    print("\n📡 Формирую bypass конфиги (VLESS + Hysteria2, 300 штук)...")
    bypass_sampled = sample_from_sources(bypass_pools, 300)
    bypass_final = finalize_configs(bypass_sampled, 'обход бс', geoip)

    # ── wl_228.txt (только bypass/whitelist, 300 конфигов) ────────────────────
    wl_output = '\n'.join([build_header(), '', SEPARATOR_BYPASS, *bypass_final])
    with open('wl_228.txt', 'w', encoding='utf-8') as f:
        f.write(wl_output)

    print(f"\n✅ Готово! wl_228.txt: {len(bypass_final)} (VLESS + Hysteria2)")

if __name__ == '__main__':
    main()
