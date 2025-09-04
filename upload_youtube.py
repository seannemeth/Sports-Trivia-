
import base64, json, os, sys
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.upload","https://www.googleapis.com/auth/youtube"]

def get_youtube_client():
    token_b64 = os.getenv("YT_TOKEN_JSON_BASE64")
    if not token_b64:
        raise RuntimeError("Missing YT_TOKEN_JSON_BASE64 secret.")
    info = json.loads(base64.b64decode(token_b64))
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)
    return build("youtube", "v3", credentials=creds)

def upload(video_path, title, description, tags=None, publish_iso=None):
    yt = get_youtube_client()
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:10],
            "categoryId": "17"
        },
        "status": {
            "privacyStatus": "public"
        }
    }
    req = yt.videos().insert(part="snippet,status", body=body, media_body=video_path)
    res = req.execute()
    print("Uploaded video ID:", res.get("id"))

if __name__ == "__main__":
    path = sys.argv[1]
    title = sys.argv[2]
    desc  = sys.argv[3]
    tags  = sys.argv[4].split(",") if len(sys.argv) > 4 else []
    upload(path, title, desc, tags, None)
