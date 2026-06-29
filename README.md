# context-checker

Belirli Slack kanalına düşen bug raporlarını denetleyen Slack botu.
Bir mesaj bug raporu ise ve zorunlu alanlar eksikse, kişiyi etiketleyip aynı
thread'e tek bir soru atar.

**Zorunlu alanlar**
1. **Ortam** — bug Canlı/yayında mı yoksa özel bir build'de mi görüldü?
2. **Build numarası** — özel build ise (Canlı ise gerekmez).

**Mimari:** Slack **Socket Mode** (public endpoint yok) → her üst-seviye mesaj
yerel **`claude` CLI** (Claude Code, Max aboneliği) üzerinden **Haiku** ile
değerlendirilir → eksikse threaded reply. **Anthropic API anahtarı gerekmez.**

---

## 1. Slack App kurulumu (bir kez)

[api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → *From scratch*.

1. **Socket Mode** → *Enable Socket Mode* → açılan ekranda bir **App-Level
   Token** üret (`connections:write` scope) → `xapp-...` → `SLACK_APP_TOKEN`.
2. **OAuth & Permissions** → *Bot Token Scopes* (izlenen kanallar public):
   - `channels:history`
   - `chat:write`
3. **Event Subscriptions** → *Enable Events* → *Subscribe to bot events*:
   - `message.channels`
4. **Install App** → workspace'e kur → *Bot User OAuth Token* `xoxb-...` →
   `SLACK_BOT_TOKEN`.
5. Botu kanala ekle: `#qa-polygunarena` içinde `/invite @<bot-adı>`.
6. **Kanal ID'si:** kanal adına sağ tık → *View channel details* → en altta
   `C...` → `QA_CHANNEL_ID`.

> **Kapsam:** `message.channels` workspace genelinde tanımlıdır ama Slack bu
> eventleri yalnızca botun **üye olduğu** kanallar için gönderir. Botu sadece
> izlemek istediğin kanal(lar)a `/invite` et. Ayrıca kod `QA_CHANNEL_ID`
> dışındaki her kanalı yok sayar (ikinci kilit).

## 2. Claude Code motorunu hazırla (Max — API key yok)

Bot, Anthropic API yerine yerel `claude` CLI'ı kullanır. Önce CLI kurulu ve
abonelikle yetkili olmalı:

```bash
claude --version          # kurulu mu? değilse: npm i -g @anthropic-ai/claude-code
claude setup-token        # Max hesabınla giriş → uzun ömürlü token basar
```

`setup-token` çıktısındaki `sk-ant-oat-...` token'ını `.env` içine
`CLAUDE_CODE_OAUTH_TOKEN=` olarak yazacaksın (aşağıda).

Hızlı sağlık testi (token'ı bir kez elle vererek):
```bash
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat-... \
  claude --print --model claude-haiku-4-5-20251001 "merhaba de"
# "Not logged in" yerine bir yanıt görmelisin.
```

## 3. Lokal kurulum

```bash
cd "context-checker"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env'in yoksa .env.example'dan oluştur, sonra içini doldur.

python app.py              # "context-checker başlıyor..."
```

Kanala eksik bilgili bir test mesajı at (örn. "şu ekranda crash oluyor") → bot
thread'e soru atmalı. Tam bir mesaj at (örn. "Canlıda crash oluyor") → bot
sessiz kalmalı.