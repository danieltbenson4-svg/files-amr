
from flask import Flask
    
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from check_generate import check_and_generate

load_dotenv()


import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return app.send_static_file("upload.html")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_files():
    # Validate files
    required_files = ["question", "answer_key", "student_answer"]
    for f in required_files:
        if f not in request.files:
            return jsonify({"error": f"Missing file: {f}"}), 400

    saved_paths = []

    try:
        for key in required_files:
            file = request.files[key]
            if file.filename == "":
                return jsonify({"error": f"Empty filename for {key}"}), 400

            # Avoid filename collisions
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            filepath = os.path.join(UPLOAD_DIR, filename)

            file.save(filepath)
            saved_paths.append(filepath)

        # Call your existing function
        result = check_and_generate(
            saved_paths[0],
            saved_paths[1],
            saved_paths[2],
        )

        return jsonify({
            "status": "success",
            "result": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(port=5001)
