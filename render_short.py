
import json, sys, os, textwrap
from pathlib import Path
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip, AudioFileClip

W, H = 1080, 1920

def render_short(json_path, index=1, out_path=None, music_path=None, font="assets/fonts/Inter-Bold.ttf"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    q = data["questions"][index-1]
    question = q["question"]
    options = q["options"]
    duration = 18

    bg = ImageClip("assets/bg.jpg").set_duration(duration).resize((W,H))

    def txt(s, size, y):
        t = TextClip(s, fontsize=size, color="white", font=font, method="caption", size=(W-160,None), align="center")
        return t.set_position(("center", y)).set_duration(duration)

    lines = "\n".join(textwrap.wrap(question, 26))
    qclip = txt(lines, 72, H*0.20)

    opt_text = "\n".join([f"{i+1}. {options[i]}" for i in range(len(options))])
    oclip = txt(opt_text, 60, H*0.45)

    final = CompositeVideoClip([bg, qclip, oclip], size=(W,H))

    if music_path and os.path.exists(music_path):
        music = AudioFileClip(music_path).volumex(0.12)
        final = final.set_audio(music)

    if not out_path:
        out_path = Path(json_path).with_suffix("").as_posix() + f"_q{index:02d}.mp4"

    final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac", preset="medium", threads=4)
    final.close()
    print("Wrote", out_path)
    return out_path

if __name__ == "__main__":
    render_short(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1, sys.argv[3] if len(sys.argv) > 3 else None, "assets/soft_loop.mp3")
