# upload_youtube.py
import os, sys, json, base64, time
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_client():
    token_b64 = os.environ.get("YT_TOKEN_JSON_BASE64", "")
    if not token_b64:
        print("Missing env YT_TOKEN_JSON_BASE64", file=sys.stderr)
        sys.exit(2)
    info = json.loads(base64.b64decode(token_b64))
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)
    return build("youtube", "v3", credentials=creds, cache_discovery=False)

def upload(path, title, desc, tags_csv, privacy="public"):
    yt = get_youtube_client()
    tags = [t.strip() for t in (tags_csv or "").split(",") if t.strip()]
    body = {
        "snippet": {
            "title": title[:100],
            "description": desc[:5000],
            "tags": tags,
            "categoryId": "17",  # Sports (tweak if you want)
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }
    media = MediaFileUpload(
        path, mimetype="video/mp4",
        chunksize=8 * 1024 * 1024,  # 8MB chunks
        resumable=True
    )

    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    last_print = 0
    try:
        while response is None:
            status, response = request.next_chunk()
            # status is a MediaUploadProgress object, may be None between chunks
            if status and (time.time() - last_print > 1.5):
                pct = int(status.progress() * 100)
                print(f"  progress: {pct}%", flush=True)
                last_print = time.time()
    except HttpError as e:
        print("YouTube API error:", e, file=sys.stderr)
        if e.resp is not None:
            print("Status:", e.resp.status, file=sys.stderr)
        sys.exit(3)

    vid = response.get("id")
    print("Upload complete. videoId:", vid, flush=True)
    return vid

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python upload_youtube.py <path.mp4> <title> <description> <tags_csv>", file=sys.stderr)
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
