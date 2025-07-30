# Anime4K Web UI

A web-based interface for processing images with Anime4K upscaling algorithms.

## Features

- 🖱️ **Drag & Drop Interface**: Simply drag your images into the browser
- 📁 **File Selection**: Choose multiple files at once
- ⚙️ **Configurable Settings**: Adjust scale factor and processing algorithm
- 📊 **Real-time Progress**: Track processing progress with live updates
- 💾 **Batch Download**: Download all processed images as a zip file

## Quick Start

### Option 1: Docker (Recommended)

The easiest way to run the Anime4K Web UI is using Docker:

```bash
cd webapp
./docker-run.sh run
```

Then open your browser to `http://localhost:5000`

Or use the simple server:
```bash
./docker-run.sh simple
```

Then open your browser to `http://localhost:8000`

#### Docker Commands

```bash
# Build and run Flask app
./docker-run.sh run

# Build and run simple server  
./docker-run.sh simple

# Use docker-compose
./docker-run.sh compose

# Production deployment (with Gunicorn)
./docker-run.sh prod

# Stop containers
./docker-run.sh stop

# Clean up everything
./docker-run.sh clean

# View logs
./docker-run.sh logs
```

### Option 2: Manual Docker

```bash
# Build the image
docker build -t anime4k-webapp .

# Run Flask app
docker run -d -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs anime4k-webapp

# Or run simple server
docker run -d -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs anime4k-webapp python simple_server.py
```

### Option 3: Manual Docker

```bash
# Build the image
docker build -t anime4k-webapp .

# Run Flask app
docker run -d -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs anime4k-webapp

# Or run simple server
docker run -d -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs anime4k-webapp python simple_server.py
```

### Option 4: Production Deployment

For production use, there's a separate Dockerfile with Gunicorn:

```bash
# Production with Gunicorn
docker compose -f docker-compose.prod.yml up -d

# Or using the helper script
./docker-run.sh prod
```

This provides:
- Multi-worker Gunicorn WSGI server
- Resource limits and health checks
- Proper logging configuration
- Non-root user for security

### Option 5: Simple Server (Standard Library Only)

```bash
cd webapp
python3 simple_server.py
```

Then open your browser to `http://localhost:8000`

### Option 6: Flask Server (Requires Dependencies)

```bash
cd webapp
pip install -r requirements.txt
python3 app.py
```

Then open your browser to `http://localhost:5000`

## Supported File Formats

- PNG
- JPG/JPEG  
- BMP
- TIFF
- WebP

## How to Use

1. **Upload Files**: Drag and drop images or click "Choose Files"
2. **Configure Settings**: 
   - Select scale factor (1.5x, 2x, 3x, 4x)
   - Choose processing algorithm (more coming soon)
3. **Start Processing**: Click the "Start Processing" button
4. **Monitor Progress**: Watch the real-time progress bar
5. **Download Results**: Download your upscaled images

## Architecture

The web UI consists of:

- **Frontend**: Modern HTML5/CSS3/JavaScript interface
- **Backend**: Python server handling file uploads and processing
- **Processing**: Integration with Anime4K algorithms (placeholder implementation included)

## Current Status

This is a functional demonstration with a placeholder upscaling algorithm. The infrastructure is ready for integration with actual Anime4K processing algorithms.

## Future Enhancements

- Integration with actual Anime4K CNN models
- Support for video files
- Batch processing optimization
- Cloud deployment options
- Advanced algorithm selection