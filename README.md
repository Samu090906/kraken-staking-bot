# 🪙 Kraken Staking Monitor

Bot Telegram + Dashboard web per monitorare il tuo portfolio in staking su Kraken.

**Demo dashboard →** https://tuousername.github.io/kraken-staking-bot/dashboard/

---

## Cosa fa

- 📊 **Dashboard web** visualizzabile da browser (GitHub Pages, gratis)
- 📲 **Notifiche Telegram** ogni mattina alle 08:00
- 📈 Report giornaliero con valore portfolio, reward ricevuti e variazione prezzi
- ⚠️ Alert automatico se un asset cala oltre il 10%
- 🔒 Solo lettura — nessun acquisto o vendita automatica

---

## Setup in 4 passi

### 1. Crea il bot Telegram

1. Apri Telegram e cerca `@BotFather`
2. Scrivi `/newbot` e scegli un nome
3. Copia il **token API** che ti viene dato

Per trovare il tuo **Chat ID**:
- Scrivi qualcosa al tuo bot
- Vai su: `https://api.telegram.org/bot<IL_TUO_TOKEN>/getUpdates`
- Copia il valore `"id"` dentro `"chat"`

### 2. Crea le API key di Kraken (sola lettura)

1. Vai su Kraken → Account → Security → API
2. Crea una nuova chiave con **solo questi permessi**:
   - ✅ Query Funds
   - ✅ Query Ledgers
3. Copia **API Key** e **Secret**

### 3. Configura le variabili

```bash
git clone https://github.com/tuousername/kraken-staking-bot
cd kraken-staking-bot
cp .env.example .env
```

Apri `.env` e inserisci i tuoi dati:

```
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
KRAKEN_API_KEY=...
KRAKEN_SECRET=...
```

### 4. Avvia il bot

```bash
pip install -r requirements.txt
python bot/bot.py
```

---

## Deploy gratuito su Railway

1. Vai su [railway.app](https://railway.app) e collegati con GitHub
2. Crea un nuovo progetto → Deploy from GitHub repo
3. Vai in **Variables** e aggiungi le stesse variabili del file `.env`
4. Il bot parte automaticamente e rimane attivo 24/7

---

## Dashboard su GitHub Pages

1. Vai nelle impostazioni del tuo repo GitHub
2. Settings → Pages → Source: `main` branch, cartella `/dashboard`
3. La dashboard sarà disponibile su `https://tuousername.github.io/kraken-staking-bot/dashboard/`

---

## Struttura del progetto

```
kraken-staking-bot/
├── bot/
│   └── bot.py          # Bot Telegram principale
├── dashboard/
│   └── index.html      # Dashboard web (GitHub Pages)
├── data/               # Generata dal bot (non su GitHub)
│   └── portfolio.json
├── .env.example        # Template variabili d'ambiente
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚠️ Sicurezza

- **Non caricare mai il file `.env` su GitHub** — è già in `.gitignore`
- Le API key di Kraken devono avere solo permessi di lettura
- Il bot non esegue mai acquisti o vendite

---

*Progetto personale — non è consulenza finanziaria.*
