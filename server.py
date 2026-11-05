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
    return "Media Downloader Backend is Running!"

@app.route('/download', methods=['POST'])
def download_media():
    data = request.get_json()
    url = data.get('url')
    file_format = data.get('format', 'mp4').lower()
    quality = data.get('quality', 'best')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'noplaylist': True,
    }

    # Audio format handling
    if file_format in ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'aac']:
        ydl_opts['format'] = 'bestaudio/best'
        codec = 'mp3' if file_format == 'mp3' else ('m4a' if file_format in ['m4a', 'aac'] else file_format)
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': codec,
            'preferredquality': '192',
        }]
    else:
        # Video quality and format selection
        if quality == '1080':
            v_res = '[height<=1080]'
        elif quality == '720':
            v_res = '[height<=720]'
        elif quality == '480':
            v_res = '[height<=480]'
        else:
            v_res = ''

        if file_format == 'webm':
            ydl_opts['format'] = f'bestvideo{v_res}[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best'
            ydl_opts['merge_output_format'] = 'webm'
        else:
            ydl_opts['format'] = f'bestvideo{v_res}[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if file_format in ['mp3', 'm4a', 'wav', 'ogg', 'flac', 'aac']:
                ext = '.mp3' if file_format == 'mp3' else ('.m4a' if file_format in ['m4a', 'aac'] else f'.{file_format}')
                filename = os.path.splitext(filename)[0] + ext
            else:
                ext = '.webm' if file_format == 'webm' else '.mp4'
                filename = os.path.splitext(filename)[0] + ext

            if not os.path.exists(filename):
                files = os.listdir(DOWNLOAD_DIR)
                if files:
                    filename = max([os.path.join(DOWNLOAD_DIR, f) for f in files], key=os.path.getctime)

            return send_file(filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
