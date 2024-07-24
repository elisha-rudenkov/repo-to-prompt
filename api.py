import os
import fnmatch
import requests
import zipfile
import tempfile
import shutil
from flask import Flask, request, jsonify
from github import Github
from werkzeug.utils import secure_filename

app = Flask(__name__)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB limit for zip files

def should_ignore(file_path, ignore_patterns):
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in ignore_patterns)

def process_github_repo(repo, ignore_patterns):
    output = ""

    def process_directory(path):
        nonlocal output
        contents = repo.get_contents(path)
        for content in contents:
            if content.type == "dir":
                output += f"\n#DIRECTORY: {content.path}\n\n"
                process_directory(content.path)
            elif content.type == "file":
                if should_ignore(content.path, ignore_patterns):
                    continue
                output += f"\n\n+++++ #FILE: {content.name}\n\n"
                try:
                    file_content = content.decoded_content.decode('utf-8')
                    output += file_content + "\n\n"
                except Exception as e:
                    output += f"Error reading file: {str(e)}\n\n"

    process_directory("")
    return output

def process_zip_file(zip_path):
    output = ""
    ignore_patterns = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        gitignore_path = os.path.join(temp_dir, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as gitignore_file:
                ignore_patterns = [line.strip() for line in gitignore_file if line.strip() and not line.startswith('#')]
        
        for root, dirs, files in os.walk(temp_dir):
            rel_path = os.path.relpath(root, temp_dir)
            if rel_path != '.':
                output += f"\n#DIRECTORY: {rel_path}\n\n"
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, temp_dir)
                
                if should_ignore(rel_file_path, ignore_patterns):
                    continue
                
                output += f"\n\n+++++ #FILE: {file}\n\n"
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        output += f.read() + "\n\n"
                except Exception as e:
                    output += f"Error reading file: {str(e)}\n\n"
    
    return output

@app.route('/process_repo', methods=['POST'])
def process_repo():
    if 'file' in request.files:
        # Mode 3: User uploads a zipped repo
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        if not file.filename.endswith('.zip'):
            return jsonify({"error": "Only zip files are allowed"}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        if file_size > MAX_UPLOAD_SIZE:
            return jsonify({"error": f"File size exceeds the limit of {MAX_UPLOAD_SIZE/1024/1024} MB"}), 400
        file.seek(0)
        
        # Save and process the file
        filename = secure_filename(file.filename)
        temp_zip_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_zip_path)
        
        try:
            output = process_zip_file(temp_zip_path)
        finally:
            os.remove(temp_zip_path)
        
        return jsonify({"result": output})
    
    else:
        # Mode 1 & 2: GitHub repo processing
        data = request.json
        repo_url = data.get('repo_url')
        user_token = data.get('token')
        
        if not repo_url:
            return jsonify({"error": "No repo URL provided"}), 400

        try:
            if user_token:
                # Mode 1: Private repo with user-provided token
                g = Github(user_token)
            else:
                # Mode 2: Public repo without token
                g = Github()
            
            repo = g.get_repo(repo_url.split('github.com/')[1])
            
            # Fetch .gitignore contents
            ignore_patterns = []
            try:
                gitignore_content = repo.get_contents('.gitignore').decoded_content.decode('utf-8')
                ignore_patterns = [line.strip() for line in gitignore_content.splitlines() if line.strip() and not line.startswith('#')]
            except:
                pass  # .gitignore not found or couldn't be read

            output = process_github_repo(repo, ignore_patterns)
            
            return jsonify({"result": output})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
