#!/usr/bin/env python3
"""
Simple Anime4K Web UI using only standard library
"""

import os
import sys
import json
import uuid
import shutil
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import mimetypes
from pathlib import Path

# Configuration
PORT = 8000
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# Global job tracking
jobs = {}
job_lock = threading.Lock()

def ensure_directories():
    """Ensure all required directories exist"""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        os.makedirs(folder, exist_ok=True)

class ProcessingJob:
    def __init__(self, job_id, files, settings):
        self.job_id = job_id
        self.files = files
        self.settings = settings
        self.status = 'pending'
        self.progress = 0
        self.total_files = len(files)
        self.processed_files = 0
        self.current_file = None
        self.error = None
        self.start_time = time.time()
        self.output_files = []

def simple_upscale_placeholder(input_path, output_path, scale_factor=2):
    """
    Placeholder upscaling function - just copies the file for demonstration
    In a real implementation, this would use the Anime4K algorithms
    """
    try:
        # For now, just copy the file to demonstrate the workflow
        shutil.copy2(input_path, output_path)
        return True
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def process_job(job_id):
    """Process a job in a separate thread"""
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            return
        
    try:
        job.status = 'processing'
        
        for i, file_info in enumerate(job.files):
            job.current_file = file_info['original_name']
            
            # Create output filename
            base_name = os.path.splitext(file_info['original_name'])[0]
            ext = os.path.splitext(file_info['original_name'])[1]
            output_filename = f"{base_name}_anime4k{ext}"
            output_path = os.path.join(OUTPUT_FOLDER, output_filename)
            
            # Simulate processing time
            time.sleep(1)
            
            # Process the image (placeholder)
            success = simple_upscale_placeholder(
                file_info['path'], 
                output_path, 
                scale_factor=job.settings.get('scale_factor', 2)
            )
            
            if success:
                job.output_files.append({
                    'original': file_info['original_name'],
                    'processed': output_filename,
                    'path': output_path
                })
            
            job.processed_files += 1
            job.progress = int((job.processed_files / job.total_files) * 100)
            
        job.status = 'completed'
        
    except Exception as e:
        job.status = 'error'
        job.error = str(e)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.serve_file('templates/index.html', 'text/html')
        elif path.startswith('/static/'):
            # Serve static files
            file_path = path[1:]  # Remove leading slash
            if os.path.exists(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                self.serve_file(file_path, mime_type or 'text/plain')
            else:
                print(f"Static file not found: {file_path}")
                self.send_error(404)
        elif path.startswith('/status/'):
            job_id = path.split('/')[-1]
            self.get_job_status(job_id)
        elif path.startswith('/download/'):
            job_id = path.split('/')[-1]
            self.download_results(job_id)
        elif path == '/settings':
            self.get_settings()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            self.upload_files()
        else:
            self.send_error(404)
    
    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
    
    def send_json(self, data, status=200):
        response = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def upload_files(self):
        try:
            # Parse multipart form data
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            if ctype == 'multipart/form-data':
                pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
                form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
                
                # Get settings
                settings = {}
                if 'scale_factor' in form:
                    try:
                        settings['scale_factor'] = float(form['scale_factor'].value)
                    except ValueError:
                        settings['scale_factor'] = 2
                
                # Get files
                files = form.getlist('files') if 'files' in form else []
                
                if not files:
                    self.send_json({'error': 'No files provided'}, 400)
                    return
                
                # Generate job ID
                job_id = str(uuid.uuid4())
                
                # Save uploaded files
                saved_files = []
                for file_field in files:
                    if hasattr(file_field, 'filename') and file_field.filename:
                        filename = file_field.filename
                        timestamp = str(int(time.time()))
                        unique_filename = f"{timestamp}_{filename}"
                        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(file_field.file.read())
                        
                        saved_files.append({
                            'original_name': filename,
                            'path': file_path
                        })
                
                if not saved_files:
                    self.send_json({'error': 'No valid files uploaded'}, 400)
                    return
                
                # Create job
                job = ProcessingJob(job_id, saved_files, settings)
                
                with job_lock:
                    jobs[job_id] = job
                
                # Start processing in background
                thread = threading.Thread(target=process_job, args=(job_id,))
                thread.daemon = True
                thread.start()
                
                self.send_json({'job_id': job_id})
            else:
                self.send_json({'error': 'Invalid content type'}, 400)
                
        except Exception as e:
            print(f"Upload error: {e}")
            self.send_json({'error': str(e)}, 500)
    
    def get_job_status(self, job_id):
        with job_lock:
            job = jobs.get(job_id)
            if not job:
                self.send_json({'error': 'Job not found'}, 404)
                return
            
            self.send_json({
                'status': job.status,
                'progress': job.progress,
                'total_files': job.total_files,
                'processed_files': job.processed_files,
                'current_file': job.current_file,
                'error': job.error,
                'output_files': len(job.output_files) if job.output_files else 0
            })
    
    def download_results(self, job_id):
        with job_lock:
            job = jobs.get(job_id)
            if not job or job.status != 'completed':
                self.send_json({'error': 'Job not found or not completed'}, 404)
                return
        
        # For now, just return a success message
        # In a full implementation, you'd create and serve a zip file
        self.send_json({'message': 'Download feature coming soon'})
    
    def get_settings(self):
        self.send_json({
            'scale_factors': [1.5, 2, 3, 4],
            'algorithms': ['Placeholder'],
            'default_scale_factor': 2,
            'default_algorithm': 'Placeholder'
        })

def main():
    ensure_directories()
    
    # Change to webapp directory
    webapp_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(webapp_dir)
    
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print(f"Starting Anime4K Web UI on http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    main()