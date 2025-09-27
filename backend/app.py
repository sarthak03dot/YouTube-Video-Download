from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import io
import tempfile
import yt_dlp

app = Flask(__name__)
CORS(app)

def get_format_string(quality: str):
    """Return yt-dlp format string based on requested quality"""
    quality = quality.lower()
    if quality == '1080p':
        return 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best[height<=1080][ext=mp4]'
    elif quality == '720p':
        return 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best[height<=720][ext=mp4]'
    elif quality == '360p':
        return 'best[height<=360][ext=mp4]'
    return 'best[ext=mp4]'  # fallback progressive MP4

@app.route("/", methods=["GET"])
def home():
    return "YouTube Downloader Backend Running!"

# Folder to save downloaded videos temporarily
DOWNLOADS_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

@app.route("/download", methods=["POST"])
def download_video():
    try:
        data = request.json
        if not data or "url" not in data:
            return jsonify({"error": "URL is required"}), 400

        url = data["url"].strip()
        quality = data.get("quality", "360p").lower()
        format_code = get_format_string(quality)

        # Extract video info for a safe filename
        ydl_opts_meta = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            from yt_dlp.utils import sanitize_filename
            filename = sanitize_filename(info_dict.get('title', 'video')) + f'-{quality}.mp4'

        file_path = os.path.join(DOWNLOADS_DIR, filename)

        # --- Handle cookies ---
        cookies_content = os.environ.get("YOUTUBE_COOKIES")
        cookie_file_path = None

        if cookies_content:
            # Write env var content to a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(cookies_content.encode())
                cookie_file_path = tmp.name
        else:
            # Fallback to local cookies.txt
            local_cookies = os.path.join(os.path.dirname(__file__), "../cookies.txt")
            if os.path.exists(local_cookies):
                cookie_file_path = local_cookies
            else:
                cookie_file_path = None  # No cookies

        # yt-dlp options
        ydl_opts_final = {
            'quiet': True,
            'no_warnings': True,
            'outtmpl': file_path,
            'format': format_code,
            'merge_output_format': 'mp4',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'geo_bypass': True,
        }

        if cookie_file_path:
            ydl_opts_final['cookiefile'] = cookie_file_path

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts_final) as ydl:
            ydl.download([url])

        # Send video to frontend
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="video/mp4"
        )

    except yt_dlp.utils.DownloadError as e:
        print("DownloadError:", e)
        error_msg = f"Download failed: {str(e).split(': ')[-1].split(';')[0].strip()}"
        if "HTTP Error 403" in str(e):
            error_msg += ". Video may be restricted/geo-blocked. Check cookies."
        return jsonify({"error": error_msg}), 500

    except Exception as e:
        print("Exception:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Use PORT env variable for Render; fallback to 5000 for local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
