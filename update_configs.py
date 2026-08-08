import asyncio
import base64
import json
import socket
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

ALLOWED_SNI_FILE = "wl_sni.txt"
RAW_CONFIGS_FILE = "all_source_configs.txt"
OUTPUT_FILE = "wl_228.json"


def load_allowed_snis(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return {
                line.strip().lower()
                for line in f
                if line.strip() and not line.startswith("#")
            }
    except FileNotFoundError:
        return set()


def decode_base64_if_needed(text):
    text = text.strip()
    if text.startswith("vless://"):
        return text
    try:
        padded = text + "=" * (-len(text) % 4)
        return base64.b64decode(padded).decode("utf-8", errors="ignore")
    except Exception:
        return text


def fetch_subscription_links(url):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (v2rayN)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            decoded = decode_base64_if_needed(content)
            return [
                line.strip()
                for line in decoded.splitlines()
                if line.strip().startswith("vless://")
            ]
    except Exception as e:
        print(f"Ошибка при загрузке подписки {url}: {e}")
        return []


def load_all_vless_urls():
    vless_urls = []
    try:
        with open(RAW_CONFIGS_FILE, "r", encoding="utf-8") as f:
            lines = [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]
    except FileNotFoundError:
        print(f"Файл {RAW_CONFIGS_FILE} не найден.")
        return []

    for line in lines:
        if line.startswith("http://") or line.startswith("https://"):
            vless_urls.extend(fetch_subscription_links(line))
        elif line.startswith("vless://"):
            vless_urls.append(line)

    return vless_urls


def parse_vless(url):
    if not url.startswith("vless://"):
        return None
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)

        uuid = parsed.username or "00000000-0000-0000-0000-000000000000"
        host = parsed.hostname
        port = parsed.port or 443

        if not host:
            return None

        sni = (
            query.get("sni", [""])[0]
            or query.get("host", [""])[0]
            or host
        )

        return {
            "uuid": uuid,
            "host": host,
            "port": int(port),
            "sni": sni.lower() if sni else "",
            "net_type": query.get("type", ["tcp"])[0],
            "security": query.get("security", ["none"])[0],
            "path": query.get("path", [""])[0],
            "service_name": query.get("serviceName", [""])[0],
            "pbk": query.get("pbk", [""])[0],
            "sid": query.get("sid", [""])[0],
            "fp": query.get("fp", ["chrome"])[0],
            "flow": query.get("flow", [""])[0],
        }
    except Exception:
        return None


async def measure_ping(host, port, timeout=2.0):
    start = time.time()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return round((time.time() - start) * 1000, 1)
    except Exception:
        return float("inf")


async def get_countries_batch(hosts):
    unique_hosts = list(set(hosts))
    ip_map = {}

    for i in range(0, len(unique_hosts), 100):
        chunk = unique_hosts[i : i + 100]
        batch_data = [{"query": h} for h in chunk]
        try:
            req = urllib.request.Request(
                "http://ip-api.com/batch?fields=country,countryCode,query",
                data=json.dumps(batch_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                results = json.loads(resp.read().decode("utf-8"))
                for item in results:
                    if item.get("countryCode"):
                        ip_map[item["query"]] = (
                            item["countryCode"],
                            item["country"],
                        )
        except Exception:
            pass
    return ip_map


def get_country_flag(code):
    if len(code) == 2 and code.isalpha():
        return "".join(chr(127397 + ord(c)) for c in code.upper())
    return "🌐"


def build_singbox_vless_outbound(cfg, tag):
    outbound = {
        "type": "vless",
        "tag": tag,
        "server": cfg["host"],
        "server_port": cfg["port"],
        "uuid": cfg["uuid"],
    }
    if cfg["flow"]:
        outbound["flow"] = cfg["flow"]

    if cfg["security"] in ["tls", "reality"]:
        tls_config = {
            "enabled": True,
            "server_name": cfg["sni"],
            "utls": {"enabled": True, "fingerprint": cfg["fp"]},
        }
        if cfg["security"] == "reality":
            tls_config["reality"] = {
                "enabled": True,
                "public_key": cfg["pbk"],
                "short_id": cfg["sid"],
            }
        outbound["tls"] = tls_config

    if cfg["net_type"] == "ws":
        outbound["transport"] = {"type": "ws", "path": cfg["path"]}
    elif cfg["net_type"] == "grpc":
        outbound["transport"] = {
            "type": "grpc",
            "service_name": cfg["service_name"],
        }

    return outbound


async def main():
    allowed_snis = load_allowed_snis(ALLOWED_SNI_FILE)
    raw_vless_links = load_all_vless_urls()

    if not raw_vless_links:
        print("Нет VLESS ссылок для обработки.")
        return

    filtered_configs = []
    for raw in raw_vless_links:
        cfg = parse_vless(raw)
        if cfg and (not allowed_snis or cfg["sni"] in allowed_snis):
            filtered_configs.append(cfg)

    ping_tasks = [
        measure_ping(cfg["host"], cfg["port"]) for cfg in filtered_configs
    ]
    pings = await asyncio.gather(*ping_tasks)

    valid_configs = []
    active_hosts = []
    for cfg, ping in zip(filtered_configs, pings):
        if ping < float("inf"):
            cfg["ping"] = ping
            valid_configs.append(cfg)
            active_hosts.append(cfg["host"])

    country_map = await get_countries_batch(active_hosts)
    for cfg in valid_configs:
        code, name = country_map.get(cfg["host"], ("XX", "Unknown"))
        cfg["country_code"] = code
        cfg["country_name"] = name

    country_best = {}
    for cfg in valid_configs:
        cc = cfg["country_code"]
        if cc not in country_best or cfg["ping"] < country_best[cc]["ping"]:
            country_best[cc] = cfg

    top_20 = sorted(country_best.values(), key=lambda x: x["ping"])[:20]

    if not top_20:
        print("Нет рабочих серверов.")
        return

    outbound_tags = []
    server_outbounds = []

    for cfg in top_20:
        flag = get_country_flag(cfg["country_code"])
        tag_name = f"{flag} {cfg['country_name']} | {int(cfg['ping'])}ms"
        outbound_tags.append(tag_name)
        server_outbounds.append(build_singbox_vless_outbound(cfg, tag_name))

    now_msk = datetime.now(timezone(timedelta(hours=3))).strftime(
        "%d.%m.%Y %H:%M MSK"
    )

    info_outbound = {
        "type": "vless",
        "tag": "Для обхода белых списков🏳️👇",
        "server": "0.0.0.0",
        "server_port": 443,
        "uuid": "00000000-0000-0000-0000-000000000000",
    }

    auto_selector = {
        "type": "urltest",
        "tag": "⚡ Авто обход LTE",
        "outbounds": outbound_tags,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "3m",
        "tolerance": 50,
    }

    final_json = {
        "#profile-title": "nzea234vpnツ 2.0",
        "#profile-update-interval": 1,
        "#announce": f"Последний апдейт на GitHub: {now_msk} | Версия: 2.0 | Не работает — обнови подписку на две стрелочки 👇",
        "#support-url": "https://t.me/nzea234",
        "#profile-web-page-url": "http://t.me/send?start=IV9P4rO9112W",
        "#hide-settings": 1,
        "outbounds": [info_outbound, auto_selector] + server_outbounds,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_json, f, indent=2, ensure_ascii=False)

    print(f"Подписка успешно сохранена в {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
