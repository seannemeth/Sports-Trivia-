
# Add to your GitHub Actions workflow steps (before rendering):

- name: Install deps (requests + pillow)
  run: |
    python -m pip install --upgrade pip wheel setuptools
    python -m pip install "Pillow<10" "moviepy==1.0.3" imageio-ffmpeg google-api-python-client google-auth requests

- name: Fetch logos & flags (on-demand, with manifest)
  run: |
    python fetch_assets_v4.py data/lineup_basketball.json data/lineup_football.json data/lineup_soccer.json
