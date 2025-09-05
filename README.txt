
Guess-The-Team Starter (NBA / NFL / Soccer)
===========================================

1) Drag this whole folder into your repo root.
2) Add repo secret: YT_TOKEN_JSON_BASE64 (base64 of token.json).
3) Run the workflow: Actions → Daily Guess-The-Team → Run workflow.

Files
-----
- render_guess_team.py        : Renders one Short from a JSON lineup.
- fetch_assets.py             : Pulls soccer flags and builds college placeholders.
- upload_youtube.py           : Uploads MP4 to YouTube using your token secret.
- assets/backgrounds/*.png    : Your Canva backgrounds (1080x1920).
- assets/college_logos/       : Optional real logos (slugged names) override placeholders.
- assets/flags/               : Auto-downloaded soccer flags land here.
- data/lineup_*.json          : Example inputs for each sport.
- .github/workflows/daily_guess_team.yml : Renders all 3 + uploads, staggered.

Run locally
-----------
python render_guess_team.py data/lineup_basketball.json
python render_guess_team.py data/lineup_football.json
python render_guess_team.py data/lineup_soccer.json

Customize
---------
- Edit the JSONs (colleges/flags, year, title, handle).
- Drop real college logos into assets/college_logos/<slug>.png (e.g., ohio-state.png).
- Flags will auto-download for common ISO3 codes (USA,FRA,BRA,ARG,ENG,GER,ESP,PORT,NED,ITA,BEL,URU,MEX,POL,JPN,KOR).

Safe uploading
--------------
The workflow uploads three Shorts/day and sleeps ~15–35 minutes between uploads to avoid spam signals.
Each MP4 uses different metadata per sport.
