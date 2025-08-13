/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class NameCardUploadWidget extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.fileInputRef = useRef("fileInput");
        
        this.state = useState({
            uploading: false,
            processing: false,
            dragover: false,
            results: null,
            error: null,
        });
    }

    onDragOver(ev) {
        ev.preventDefault();
        this.state.dragover = true;
    }

    onDragLeave(ev) {
        ev.preventDefault();
        this.state.dragover = false;
    }

    onDrop(ev) {
        ev.preventDefault();
        this.state.dragover = false;
        
        const files = ev.dataTransfer.files;
        if (files.length > 0) {
            this.uploadFiles(files);
        }
    }

    onFileSelect(ev) {
        const files = ev.target.files;
        if (files.length > 0) {
            this.uploadFiles(files);
        }
    }

    async uploadFiles(files) {
        this.state.uploading = true;
        this.state.error = null;
        this.state.results = null;

        try {
            const formData = new FormData();
            
            if (files.length === 1) {
                formData.append('image', files[0]);
                const response = await fetch('/namecard/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.notification.add(result.message, { type: 'success' });
                    this.monitorProcessing(result.namecard_id);
                } else {
                    this.state.error = result.error;
                }
            } else {
                // Bulk upload
                for (let file of files) {
                    formData.append('images', file);
                }
                
                const response = await fetch('/namecard/bulk_upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.notification.add(
                        `${result.successful_uploads}/${result.total_files} files uploaded successfully`,
                        { type: 'success' }
                    );
                    
                    // Monitor all successful uploads
                    const successfulIds = result.results
                        .filter(r => r.success)
                        .map(r => r.namecard_id);
                    
                    for (let id of successfulIds) {
                        this.monitorProcessing(id);
                    }
                } else {
                    this.state.error = result.error;
                }
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.state.error = 'Upload failed: ' + error.message;
        } finally {
            this.state.uploading = false;
        }
    }

    async monitorProcessing(namecardId) {
        this.state.processing = true;
        
        const checkStatus = async () => {
            try {
                const result = await this.rpc('/namecard/status/' + namecardId, {});
                
                if (result.error) {
                    this.state.error = result.error;
                    this.state.processing = false;
                    return;
                }
                
                if (result.status === 'done') {
                    this.state.results = result;
                    this.state.processing = false;
                    this.notification.add('Name card processed successfully!', { type: 'success' });
                } else if (result.status === 'error') {
                    this.state.error = result.error || 'Processing failed';
                    this.state.processing = false;
                } else {
                    // Still processing, check again in 2 seconds
                    setTimeout(checkStatus, 2000);
                }
            } catch (error) {
                console.error('Status check error:', error);
                this.state.error = 'Failed to check processing status';
                this.state.processing = false;
            }
        };
        
        checkStatus();
    }

    browseFiles() {
        this.fileInputRef.el.click();
    }

    exportResults(format = 'json') {
        if (this.state.results && this.state.results.namecard_id) {
            window.open(`/namecard/export/${this.state.results.namecard_id}?format=${format}`);
        }
    }

    reset() {
        this.state.uploading = false;
        this.state.processing = false;
        this.state.results = null;
        this.state.error = null;
        if (this.fileInputRef.el) {
            this.fileInputRef.el.value = '';
        }
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'high';
        if (confidence >= 0.6) return 'medium';
        return 'low';
    }

    formatConfidence(confidence) {
        return Math.round(confidence * 100) + '%';
    }
}

NameCardUploadWidget.template = "ocr_namecard.UploadWidget";

// Register the widget
registry.category("public_widgets").add("namecard_upload", NameCardUploadWidget);