import json
import base64
import logging
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger(__name__)


class NameCardController(http.Controller):

    @http.route('/namecard/upload', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_namecard(self, **kwargs):
        """Upload name card image via HTTP"""
        try:
            if 'image' not in request.httprequest.files:
                return json.dumps({'error': 'No image file provided'})
            
            image_file = request.httprequest.files['image']
            if not image_file.filename:
                return json.dumps({'error': 'No image file selected'})
            
            # Validate file type
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
            file_ext = image_file.filename.lower().split('.')[-1]
            if file_ext not in allowed_extensions:
                return json.dumps({'error': 'Invalid file type. Allowed: ' + ', '.join(allowed_extensions)})
            
            # Read and encode image
            image_data = image_file.read()
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create name card record
            namecard = request.env['ocr.namecard'].create({
                'image': image_b64,
                'image_filename': image_file.filename,
                'processing_model': kwargs.get('model', 'microsoft/DialoGPT-medium'),
            })
            
            return json.dumps({
                'success': True,
                'namecard_id': namecard.id,
                'message': 'Name card uploaded successfully and processing started'
            })
            
        except Exception as e:
            _logger.error(f"Error uploading name card: {e}")
            return json.dumps({'error': str(e)})

    @http.route('/namecard/status/<int:namecard_id>', type='json', auth='user')
    def get_processing_status(self, namecard_id):
        """Get processing status of a name card"""
        try:
            namecard = request.env['ocr.namecard'].browse(namecard_id)
            if not namecard.exists():
                return {'error': 'Name card not found'}
            
            return {
                'status': namecard.processing_status,
                'error': namecard.processing_error,
                'contact_name': namecard.contact_name,
                'company_name': namecard.company_name,
                'email': namecard.email,
                'phone': namecard.phone,
                'confidence': namecard.extraction_confidence,
            }
            
        except Exception as e:
            _logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

    @http.route('/namecard/export/<int:namecard_id>', type='http', auth='user')
    def export_namecard(self, namecard_id, format='json'):
        """Export name card data"""
        try:
            namecard = request.env['ocr.namecard'].browse(namecard_id)
            if not namecard.exists():
                return request.not_found()
            
            if format == 'json':
                data = {
                    'name': namecard.contact_name,
                    'title': namecard.job_title,
                    'company': namecard.company_name,
                    'email': namecard.email,
                    'phone': namecard.phone,
                    'mobile': namecard.mobile,
                    'website': namecard.website,
                    'address': namecard.address,
                    'other': namecard.other_info,
                    'extracted_text': namecard.extracted_text,
                    'confidence': namecard.extraction_confidence,
                }
                
                filename = f"namecard_{namecard.id}.json"
                response = request.make_response(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    headers=[
                        ('Content-Type', 'application/json'),
                        ('Content-Disposition', content_disposition(filename))
                    ]
                )
                return response
                
            elif format == 'vcard':
                vcard_data = self._generate_vcard(namecard)
                filename = f"namecard_{namecard.id}.vcf"
                response = request.make_response(
                    vcard_data,
                    headers=[
                        ('Content-Type', 'text/vcard'),
                        ('Content-Disposition', content_disposition(filename))
                    ]
                )
                return response
                
            else:
                return request.not_found()
                
        except Exception as e:
            _logger.error(f"Error exporting name card: {e}")
            return request.not_found()

    def _generate_vcard(self, namecard):
        """Generate vCard format from name card data"""
        vcard_lines = ['BEGIN:VCARD', 'VERSION:3.0']
        
        if namecard.contact_name:
            vcard_lines.append(f'FN:{namecard.contact_name}')
            # Split name for N field (Last;First;Middle;Prefix;Suffix)
            name_parts = namecard.contact_name.split()
            if len(name_parts) >= 2:
                vcard_lines.append(f'N:{name_parts[-1]};{" ".join(name_parts[:-1])};;;')
            else:
                vcard_lines.append(f'N:{namecard.contact_name};;;;')
        
        if namecard.company_name:
            vcard_lines.append(f'ORG:{namecard.company_name}')
        
        if namecard.job_title:
            vcard_lines.append(f'TITLE:{namecard.job_title}')
        
        if namecard.email:
            vcard_lines.append(f'EMAIL:{namecard.email}')
        
        if namecard.phone:
            vcard_lines.append(f'TEL;TYPE=WORK:{namecard.phone}')
        
        if namecard.mobile:
            vcard_lines.append(f'TEL;TYPE=CELL:{namecard.mobile}')
        
        if namecard.website:
            vcard_lines.append(f'URL:{namecard.website}')
        
        if namecard.address:
            # Format: ADR:;;street;city;state;postal;country
            vcard_lines.append(f'ADR;TYPE=WORK:;;{namecard.address};;;;')
        
        if namecard.other_info:
            vcard_lines.append(f'NOTE:{namecard.other_info}')
        
        vcard_lines.append('END:VCARD')
        return '\n'.join(vcard_lines)

    @http.route('/namecard/bulk_upload', type='http', auth='user', methods=['POST'], csrf=False)
    def bulk_upload_namecards(self, **kwargs):
        """Bulk upload multiple name cards"""
        try:
            files = request.httprequest.files.getlist('images')
            if not files:
                return json.dumps({'error': 'No image files provided'})
            
            results = []
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
            
            for image_file in files:
                try:
                    if not image_file.filename:
                        continue
                    
                    # Validate file type
                    file_ext = image_file.filename.lower().split('.')[-1]
                    if file_ext not in allowed_extensions:
                        results.append({
                            'filename': image_file.filename,
                            'success': False,
                            'error': 'Invalid file type'
                        })
                        continue
                    
                    # Read and encode image
                    image_data = image_file.read()
                    image_b64 = base64.b64encode(image_data).decode('utf-8')
                    
                    # Create name card record
                    namecard = request.env['ocr.namecard'].create({
                        'image': image_b64,
                        'image_filename': image_file.filename,
                        'processing_model': kwargs.get('model', 'microsoft/DialoGPT-medium'),
                    })
                    
                    results.append({
                        'filename': image_file.filename,
                        'success': True,
                        'namecard_id': namecard.id
                    })
                    
                except Exception as e:
                    results.append({
                        'filename': image_file.filename,
                        'success': False,
                        'error': str(e)
                    })
            
            return json.dumps({
                'success': True,
                'results': results,
                'total_files': len(files),
                'successful_uploads': len([r for r in results if r['success']])
            })
            
        except Exception as e:
            _logger.error(f"Error in bulk upload: {e}")
            return json.dumps({'error': str(e)})