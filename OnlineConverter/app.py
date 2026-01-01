import os
import io
import uuid
import threading
from flask import Flask, render_template, request, send_file, after_this_request, jsonify
from flask_cors import CORS
from pydub import AudioSegment

app = Flask(__name__)
CORS(app) # Enable Cross-Origin requests so WordPress can talk to this API
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

# Ensure upload dir exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def cleanup_file(filepath, delay=60):
    """Deletes a file after a delay to ensure it's sent before deletion."""
    def _delete():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Cleaned up {filepath}")
        except Exception as e:
            print(f"Error cleaning up {filepath}: {e}")
    
    timer = threading.Timer(delay, _delete)
    timer.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    target_format = request.form.get('format', 'mp3')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        # Generate unique filename to avoid collisions
        unique_id = str(uuid.uuid4())
        original_ext = os.path.splitext(file.filename)[1]
        input_filename = f"{unique_id}{original_ext}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
        
        output_filename = f"{os.path.splitext(file.filename)[0]}.{target_format}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}.{target_format}")
        
        try:
            # Save uploaded file
            file.save(input_path)
            
            # Convert
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format=target_format)
            
            # Cleanup input immediately
            cleanup_file(input_path, delay=1)
            
            # Send file and cleanup output after
            @after_this_request
            def remove_output_file(response):
                cleanup_file(output_path, delay=5)
                return response

            return send_file(
                output_path, 
                as_attachment=True, 
                download_name=output_filename
            )
            
        except Exception as e:
            # Cleanup on error
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
