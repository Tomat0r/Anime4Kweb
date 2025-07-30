#!/bin/bash
# Test script for the Anime4K Web UI

echo "Starting Anime4K Web UI test..."

# Create a test image for demonstration
cd /home/runner/work/Anime4Kweb/Anime4Kweb/webapp

# Create a simple test image using Python
python3 -c "
from PIL import Image
import os

# Create test image if PIL is available
try:
    # Create a simple colored rectangle
    img = Image.new('RGB', (100, 100), color='red')
    img.save('test_image.png')
    print('Created test_image.png')
except ImportError:
    # Create a dummy file if PIL is not available
    with open('test_image.txt', 'w') as f:
        f.write('This is a test file for the Anime4K Web UI demo')
    print('Created test_image.txt (PIL not available)')
except Exception as e:
    print(f'Could not create test image: {e}')
"

echo "Test setup complete."
echo ""
echo "To test the Web UI:"
echo "1. Run: python3 simple_server.py"
echo "2. Open browser to: http://localhost:8000"
echo "3. Upload the test image created above"
echo "4. Configure settings and start processing"