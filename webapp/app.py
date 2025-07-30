#!/usr/bin/env python3
"""
Anime4K Web UI - A web interface for processing images with Anime4K algorithms
"""

import os
import sys
import uuid
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import threading
import json
import time

# Add parent directory to path to import tensorflow utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tensorflow'))

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
TEMP_FOLDER = 'temp'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'webp'}

# Global job tracking
jobs = {}
job_lock = threading.Lock()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_directories():
    """Ensure all required directories exist"""
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, TEMP_FOLDER]:
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

def process_image_simple(input_path, output_path, scale_factor=2):
    """
    Simple image upscaling using OpenCV as fallback
    This is a placeholder - in a full implementation, you'd use the Anime4K algorithms
    """
    try:
        # Read image
        img = cv2.imread(input_path)
        if img is None:
            raise ValueError("Could not read image")
        
        # Get original dimensions
        height, width = img.shape[:2]
        
        # Calculate new dimensions
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        # Upscale using INTER_CUBIC for better quality
        upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Save result
        cv2.imwrite(output_path, upscaled)
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
            
            # Process the image
            success = process_image_simple(
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    settings = request.form.to_dict()
    
    # Convert settings to appropriate types
    try:
        settings['scale_factor'] = float(settings.get('scale_factor', 2))
    except ValueError:
        settings['scale_factor'] = 2
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded files
    saved_files = []
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            timestamp = str(int(time.time()))
            unique_filename = f"{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)
            
            saved_files.append({
                'original_name': filename,
                'path': file_path
            })
    
    if not saved_files:
        return jsonify({'error': 'No valid files uploaded'}), 400
    
    # Create job
    job = ProcessingJob(job_id, saved_files, settings)
    
    with job_lock:
        jobs[job_id] = job
    
    # Start processing in background
    thread = threading.Thread(target=process_job, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def get_job_status(job_id):
    """Get job status"""
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'status': job.status,
            'progress': job.progress,
            'total_files': job.total_files,
            'processed_files': job.processed_files,
            'current_file': job.current_file,
            'error': job.error,
            'output_files': len(job.output_files) if job.output_files else 0
        })

@app.route('/download/<job_id>')
def download_results(job_id):
    """Download processed files as a zip"""
    with job_lock:
        job = jobs.get(job_id)
        if not job or job.status != 'completed':
            return jsonify({'error': 'Job not found or not completed'}), 404
    
    # Create zip file with results
    import zipfile
    zip_filename = f"anime4k_output_{job_id}.zip"
    zip_path = os.path.join(TEMP_FOLDER, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_info in job.output_files:
            zipf.write(file_info['path'], file_info['processed'])
    
    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

@app.route('/settings')
def get_settings():
    """Get available processing settings"""
    return jsonify({
        'scale_factors': [1.5, 2, 3, 4],
        'algorithms': ['Simple', 'CNN_S', 'CNN_M', 'CNN_L'],  # Placeholder for future
        'default_scale_factor': 2,
        'default_algorithm': 'Simple'
    })

if __name__ == '__main__':
    ensure_directories()
    app.run(debug=True, host='0.0.0.0', port=5000)