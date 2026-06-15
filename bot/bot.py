import os
import json
import time
import requests
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime
import schedule

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "IL_TUO_TOKEN_QUI")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "IL_TUO_CHAT_ID_QUI")
KRAKEN_API_KEY  = os.environ.get("KRAKEN_API_KEY", "")
KRAKEN_SECRET   = os.environ.get("KRAKEN_SECRET", "")
ALERT_THRESHOLD = float(os.environ.get("ALERT_THRESHOLD", "-10"))  # % calo per alert
DATA_FILE       = "data/portfolio.json"

# ── Kraken API ───────────────────────────────────────────────────────────────
def kraken_request(endpoint, data={}):
    url = f"https://api.kraken.com{endpoint}"
    nonce = str(int(time.time() * 1000))
    data["nonce"] = nonce
    post_data = urllib.parse.urlencode(data)
    encoded = (nonce + post_data).encode()
    message = endpoint.encode() + hashlib.sha256(encoded).digest()
    secret = base64.b64decode(KRAKEN_SECRET)
    signature = hmac.new(secret, message, hashlib.sha512)
    sig_digest = base64.b64encode(signature.digest()).decode()
    headers = {"API-Key": KRAKEN_API_KEY, "API-Sign": sig_digest}
    r = requests.post(url, headers=headers, data=data, timeout=10)
    return r.json()

def get_balance():
    result = kraken_request("/0/private/Balance")
    if result.get("error"):
        return None
    return result.get("result", {})

def get_prices(pairs=["XETHZEUR", "DOTEUR"]):
    url = "https://api.kraken.com/0/public/Ticker"
    r = requests.get(url, params={"pair": ",".join(pairs)}, timeout=10)
    data = r.json().get("result", {})
    prices = {}
    for pair, info in data.items():
        prices[pair] = float(info["c"][0])
    return prices

def get_staking_rewards():
    result = kraken_request("/0/private/Ledgers", {
        "type": "staking",
        "start": int(time.time()) - 86400
    })
    rewards = {}
    for entry in result.get("result", {}).get("ledger", {}).values():
        asset = entry.get("asset", "")
        amount = float(entry.get("amount", 0))
        if amount > 0:
            rewards[asset] = rewards.get(asset, 0) + amount
    return rewards

# ── Portfolio helpers ────────────────────────────────────────────────────────
def load_data():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"history": [], "total_rewards": {}, "initial_value": 100.0}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def calc_portfolio_value(balance, prices):
    mapping = {
        "XETH": "XETHZEUR",
        "DOT":  "DOTEUR",
    }
    total = 0.0
    breakdown = {}
    for asset, pair in mapping.items():
        amount = float(balance.get(asset, 0))
        price  = prices.get(pair, 0)
        value  = amount * price
        total += value
        breakdown[asset] = {"amount": round(amount, 6), "price": round(price, 2), "value": round(value, 2)}
    return round(total, 2), breakdown

# ── Telegram ─────────────────────────────────────────────────────────────────
def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ── Daily report ─────────────────────────────────────────────────────────────
def daily_report():
    data    = load_data()
    balance = get_balance()
    prices  = get_prices()

    if not balance or not prices:
        send_telegram("⚠️ Errore nel recuperare i dati da Kraken. Riprovo domani.")
        return

    total, breakdown = calc_portfolio_value(balance, prices)
    rewards = get_staking_rewards()

    # Salva storico
    entry = {"date": datetime.now().isoformat(), "total": total, "breakdown": breakdown}
    data["history"].append(entry)
    for asset, amount in rewards.items():
        data["total_rewards"][asset] = data["total_rewards"].get(asset, 0) + amount
    save_data(data)

    # Calcola variazione
    initial = data.get("initial_value", 100.0)
    change_pct = ((total - initial) / initial) * 100

    # Reward ultimi 24h
    reward_lines = ""
    for asset, amount in rewards.items():
        reward_lines += f"  • {asset}: +{amount:.6f}\n"
    if not reward_lines:
        reward_lines = "  Nessuno ancora oggi\n"

    # Alert prezzi
    alerts = ""
    eth_price = prices.get("XETHZEUR", 0)
    dot_price = prices.get("DOTEUR", 0)

    # Messaggio finale
    emoji_change = "📈" if change_pct >= 0 else "📉"
    msg = (
        f"<b>📊 Report giornaliero — {datetime.now().strftime('%d/%m/%Y')}</b>\n\n"
        f"{emoji_change} <b>Valore portfolio:</b> €{total:.2f}\n"
        f"   Variazione da inizio: {change_pct:+.2f}%\n\n"
        f"<b>🪙 Posizioni:</b>\n"
    )
    for asset, info in breakdown.items():
        msg += f"  • {asset}: {info['amount']} @ €{info['price']} = <b>€{info['value']}</b>\n"

    msg += f"\n<b>🎁 Reward 24h:</b>\n{reward_lines}"
    msg += f"\n<b>💰 Reward totali accumulati:</b>\n"
    for asset, amount in data["total_rewards"].items():
        msg += f"  • {asset}: {amount:.6f}\n"

    if alerts:
        msg += f"\n⚠️ <b>Alert prezzi:</b>\n{alerts}"

    msg += "\n📲 <i>Dashboard: <a href='https://tuousername.github.io/kraken-staking-bot'>apri</a></i>"
    send_telegram(msg)
    print(f"[{datetime.now()}] Report inviato. Portfolio: €{total}")

# ── Alert prezzi (ogni ora) ──────────────────────────────────────────────────
def price_alert_check():
    prices = get_prices()
    if not prices:
        return
    # Qui puoi aggiungere logica per confrontare con prezzi precedenti
    print(f"[{datetime.now()}] Prezzi: {prices}")

# ── Scheduler ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Bot avviato!")
    send_telegram("✅ <b>Kraken Staking Bot avviato!</b>\nRiceverai il report ogni mattina alle 08:00.")
    daily_report()  # Report immediato all'avvio

    schedule.every().day.at("08:00").do(daily_report)
    schedule.every(1).hours.do(price_alert_check)

    while True:
        schedule.run_pending()
        time.sleep(60)
