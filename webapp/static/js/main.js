// Anime4K Web UI JavaScript

class Anime4KWebUI {
    constructor() {
        this.selectedFiles = [];
        this.currentJobId = null;
        this.pollInterval = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
    }

    initializeElements() {
        // Get DOM elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileList = document.getElementById('fileList');
        this.selectedFilesList = document.getElementById('selectedFiles');
        this.processBtn = document.getElementById('processBtn');
        this.progressSection = document.getElementById('progressSection');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.currentFileText = document.getElementById('currentFile');
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsText = document.getElementById('resultsText');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.errorSection = document.getElementById('errorSection');
        this.errorText = document.getElementById('errorText');
        this.retryBtn = document.getElementById('retryBtn');
        this.scaleFactorSelect = document.getElementById('scaleFactorSelect');
        this.algorithmSelect = document.getElementById('algorithmSelect');
    }

    setupEventListeners() {
        // File input events
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        
        // Drag and drop events
        this.dropZone.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropZone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e));
        this.dropZone.addEventListener('click', () => this.fileInput.click());
        
        // Button events
        this.processBtn.addEventListener('click', () => this.startProcessing());
        this.downloadBtn.addEventListener('click', () => this.downloadResults());
        this.resetBtn.addEventListener('click', () => this.reset());
        this.retryBtn.addEventListener('click', () => this.reset());
    }

    async loadSettings() {
        try {
            const response = await fetch('/settings');
            const settings = await response.json();
            
            // Populate scale factor options
            this.scaleFactorSelect.innerHTML = '';
            settings.scale_factors.forEach(factor => {
                const option = document.createElement('option');
                option.value = factor;
                option.textContent = `${factor}x`;
                option.selected = factor === settings.default_scale_factor;
                this.scaleFactorSelect.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.dropZone.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.addFiles(files);
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.addFiles(files);
    }

    addFiles(files) {
        // Filter valid image files
        const validFiles = files.filter(file => {
            const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/bmp', 'image/tiff', 'image/webp'];
            return validTypes.includes(file.type);
        });

        if (validFiles.length === 0) {
            this.showError('No valid image files selected. Please select PNG, JPG, BMP, TIFF, or WebP files.');
            return;
        }

        // Add to selected files (avoid duplicates)
        validFiles.forEach(file => {
            const exists = this.selectedFiles.some(existing => 
                existing.name === file.name && existing.size === file.size
            );
            
            if (!exists) {
                this.selectedFiles.push(file);
            }
        });

        this.updateFileList();
    }

    updateFileList() {
        if (this.selectedFiles.length === 0) {
            this.fileList.style.display = 'none';
            this.processBtn.disabled = true;
            return;
        }

        this.fileList.style.display = 'block';
        this.processBtn.disabled = false;

        // Clear existing list
        this.selectedFilesList.innerHTML = '';

        // Add files to list
        this.selectedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${file.name} (${this.formatFileSize(file.size)})</span>
                <button onclick="ui.removeFile(${index})" style="float: right; background: #e53e3e; color: white; border: none; border-radius: 4px; padding: 2px 8px; cursor: pointer;">×</button>
            `;
            this.selectedFilesList.appendChild(li);
        });
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateFileList();
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async startProcessing() {
        if (this.selectedFiles.length === 0) {
            this.showError('Please select files to process.');
            return;
        }

        // Prepare form data
        const formData = new FormData();
        
        this.selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        formData.append('scale_factor', this.scaleFactorSelect.value);
        formData.append('algorithm', this.algorithmSelect.value);

        try {
            // Show progress section
            this.hideAllSections();
            this.progressSection.style.display = 'block';
            this.progressText.textContent = 'Uploading files...';
            this.progressFill.style.width = '0%';

            // Upload files and start processing
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }

            this.currentJobId = result.job_id;
            this.startPolling();

        } catch (error) {
            console.error('Processing failed:', error);
            this.showError(`Processing failed: ${error.message}`);
        }
    }

    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }

        this.pollInterval = setInterval(() => {
            this.checkJobStatus();
        }, 1000);
    }

    async checkJobStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`/status/${this.currentJobId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const status = await response.json();
            
            if (status.error) {
                throw new Error(status.error);
            }

            // Update progress
            this.progressFill.style.width = `${status.progress}%`;
            
            if (status.current_file) {
                this.progressText.textContent = `Processing: ${status.current_file}`;
                this.currentFileText.textContent = `File ${status.processed_files + 1} of ${status.total_files}`;
            } else {
                this.progressText.textContent = `${status.status}...`;
                this.currentFileText.textContent = '';
            }

            // Check if completed
            if (status.status === 'completed') {
                this.stopPolling();
                this.showResults(status);
            } else if (status.status === 'error') {
                this.stopPolling();
                this.showError(status.error || 'Processing failed');
            }

        } catch (error) {
            console.error('Status check failed:', error);
            this.stopPolling();
            this.showError(`Status check failed: ${error.message}`);
        }
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }

    showResults(status) {
        this.hideAllSections();
        this.resultsSection.style.display = 'block';
        this.resultsText.textContent = `Successfully processed ${status.output_files} file(s) with ${this.scaleFactorSelect.value}x upscaling.`;
    }

    showError(message) {
        this.hideAllSections();
        this.errorSection.style.display = 'block';
        this.errorText.textContent = message;
    }

    hideAllSections() {
        this.progressSection.style.display = 'none';
        this.resultsSection.style.display = 'none';
        this.errorSection.style.display = 'none';
    }

    async downloadResults() {
        if (!this.currentJobId) return;

        try {
            window.open(`/download/${this.currentJobId}`, '_blank');
        } catch (error) {
            console.error('Download failed:', error);
            this.showError(`Download failed: ${error.message}`);
        }
    }

    reset() {
        this.stopPolling();
        this.selectedFiles = [];
        this.currentJobId = null;
        this.fileInput.value = '';
        this.updateFileList();
        this.hideAllSections();
    }
}

// Initialize the UI when the page loads
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new Anime4KWebUI();
});