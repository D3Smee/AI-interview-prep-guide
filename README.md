# Interview Prep — Launch Instructions

## Setup (one-time)
Copy both files to the same folder on your Desktop:
- `Interview prep.html`
- `proxy.py`

## Launch

**Step 1** — Start the proxy (in Terminal):
```bash
cd ~/Desktop
python3 proxy.py
```

**Step 2** — Open in Chrome:
```
http://localhost:3000
```

Enter your Anthropic API key in the ⚙ settings panel and you're ready to go.

---

> The proxy runs entirely on your machine. Your API key is never stored — it travels only from your browser to `localhost:3000` and then to Anthropic's API.
