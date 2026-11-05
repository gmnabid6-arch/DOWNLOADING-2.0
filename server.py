import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def home():
    return "YouTube & Media Downloader Backend is Running!"

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    file_type = data.get('type', 'MP4').lower()
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
    }

    # Format handling based on user selection
    if file_type in ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'aac']:
        ydl_opts['format'] = 'bestaudio/best'
        codec = 'mp3' if file_type == 'mp3' else ('m4a' if file_type in ['m4a', 'aac'] else file_type)
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': '192',
        }]
    else:
        if file_type == 'webm':
            ydl_opts['format'] = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]'
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=mp4]/best[ext=mp4]'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if file_type in ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'aac']:
                ext = '.mp3' if file_type == 'mp3' else ('.m4a' if file_type in ['m4a', 'aac'] else f'.{file_type}')
                filename = os.path.splitext(filename)[0] + ext

            if not os.path.exists(filename):
                files = os.listdir(DOWNLOAD_DIR)
                if files:
                    filename = max([os.path.join(DOWNLOAD_DIR, f) for f in files], key=os.path.getctime)

            return jsonify({'success': True, 'filename': os.path.basename(filename)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/files/<path:filename>')
def get_file(filename):
    return send_file(os.path.join(DOWNLOAD_DIR, filename), as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
