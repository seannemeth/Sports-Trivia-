# Sports Trivia Agent (Hands-off)

This repo generates **daily sports trivia** automatically with GitHub Actions. It creates:
- 10 multiple-choice questions (JSON)
- Polished vertical PNG cards (1080x1920) for each question
- A 9:16 MP4 Short for the first question (with quiet music placeholder)
- A static `/public` site showing the latest day (serve via GitHub Pages)

## Setup (quick)
1) Create a GitHub repo and upload these files.
2) Settings → Pages → set Source to `Deploy from a branch` → Branch `main` → Folder `/public`.
3) Go to Actions and enable workflows if prompted.
4) You're done. It will run daily around 08:10 ET and commit new trivia to `/public/YYYY-MM-DD/`.

Optional: YouTube auto-upload
- Create an OAuth `token.json` for your channel (YouTube Data API v3).
- Base64 encode it and save as secret `YT_TOKEN_JSON_BASE64`.
- (Then use `upload_youtube.py` in the workflow if you want to auto-post.)

Local test:
```bash
pip install -r requirements.txt
python daily_agent.py
```
