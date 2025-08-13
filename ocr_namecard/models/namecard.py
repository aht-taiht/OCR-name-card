import os
import json
import base64
import tempfile
import logging
import shutil
import platform
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

try:
    from paddleocr import PaddleOCR
    from huggingface_hub import InferenceClient
    from PIL import Image
    import numpy as np
    import cv2
except ImportError as e:
    logging.getLogger(__name__).warning(f"Missing dependencies: {e}")

_logger = logging.getLogger(__name__)


# Global PaddleOCR readers cache
_readers = {}

def get_paddleocr_readers():
    """Get or initialize PaddleOCR readers for different languages"""
    global _readers
    
    if not _readers:
        try:
            import os
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            
            _logger.info("Initializing PaddleOCR readers...")
            
            # Initialize English OCR
            try:
                _readers['en'] = PaddleOCR(use_angle_cls=True, lang='en')
                _logger.info("✅ English OCR initialized")
            except Exception as e:
                _logger.warning(f"English OCR failed: {e}")
                _readers['en'] = None
            
            # Initialize Japanese OCR
            try:
                _readers['japan'] = PaddleOCR(use_angle_cls=True, lang='japan')
                _logger.info("✅ Japanese OCR initialized")
            except Exception as e:
                _logger.warning(f"Japanese OCR failed: {e}")
                _readers['japan'] = None
            
            # Initialize Vietnamese OCR
            try:
                _readers['vi'] = PaddleOCR(use_angle_cls=True, lang='vi')
                _logger.info("✅ Vietnamese OCR initialized")
            except Exception as e:
                _logger.warning(f"Vietnamese OCR failed: {e}")
                _readers['vi'] = None
                
        except Exception as e:
            _logger.error(f"Failed to initialize PaddleOCR readers: {e}")
    
    return _readers


class NameCard(models.Model):
    _name = 'ocr.namecard'
    _description = 'Name Card OCR'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Card Name', compute='_compute_name', store=True)
    image = fields.Binary(string='Name Card Image', required=True)
    image_filename = fields.Char(string='Filename')
    
    # Extracted raw text
    extracted_text = fields.Text(string='Extracted Text (Raw)')
    extraction_confidence = fields.Float(string='Average Confidence', digits=(3, 2))
    
    # Structured contact information
    contact_name = fields.Char(string='Full Name', tracking=True)
    job_title = fields.Char(string='Job Title', tracking=True)
    company_name = fields.Char(string='Company', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    mobile = fields.Char(string='Mobile', tracking=True)
    website = fields.Char(string='Website', tracking=True)
    address = fields.Text(string='Address', tracking=True)
    other_info = fields.Text(string='Other Information')
    
    # Processing information
    processing_model = fields.Char(string='AI Model Used', default='openai/gpt-oss-20b')
    processing_status = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('done', 'Completed'),
        ('error', 'Error')
    ], string='Status', default='draft', tracking=True)
    processing_error = fields.Text(string='Processing Error')
    raw_ai_response = fields.Text(string='Raw AI Response')
    
    # Partner linking
    partner_id = fields.Many2one('res.partner', string='Linked Contact')
    
    @api.depends('contact_name', 'company_name')
    def _compute_name(self):
        for record in self:
            if record.contact_name and record.company_name:
                record.name = f"{record.contact_name} ({record.company_name})"
            elif record.contact_name:
                record.name = record.contact_name
            elif record.company_name:
                record.name = record.company_name
            else:
                record.name = record.image_filename or 'Name Card'

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if record.image and record.processing_status == 'draft':
            record.action_process_card()
        return record

    def action_process_card(self):
        """Process the name card image with OCR and AI"""
        for record in self:
            if not record.image:
                raise UserError(_("No image uploaded"))
            
            record.processing_status = 'processing'
            try:
                # Extract text using OCR
                extracted_data = record._extract_text_from_image()
                
                if not extracted_data:
                    record.processing_status = 'error'
                    record.processing_error = "No text could be extracted from the image"
                    continue
                
                # Process with AI
                structured_data = record._process_with_ai(extracted_data)
                
                # Update record with structured data
                record._update_from_structured_data(structured_data)
                record.processing_status = 'done'
                
            except Exception as e:
                _logger.error(f"Error processing name card: {e}")
                record.processing_status = 'error'
                record.processing_error = str(e)

    def _extract_text_from_image(self):
        """Extract text from image using PaddleOCR with multiple languages"""
        try:
            # Get PaddleOCR readers
            readers = get_paddleocr_readers()
            
            if not any(readers.values()):
                raise UserError(_(
                    "PaddleOCR is not properly initialized. "
                    "Please ensure PaddleOCR and its dependencies are installed:\n\n"
                    "pip install paddlepaddle paddleocr"
                ))
            
            # Decode base64 image
            image_data = base64.b64decode(self.image)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_file.flush()
                
                results = []
                
                # Try English OCR
                if readers.get('en'):
                    try:
                        _logger.info("🇺🇸 Trying English OCR...")
                        en_results = readers['en'].ocr(temp_file.name)
                        if en_results and en_results[0]:
                            en_processed = self._process_paddleocr_results(en_results[0], 'en')
                            if en_processed:
                                results.append(('en', en_processed))
                                _logger.info(f"✅ English: {len(en_processed)} texts found")
                    except Exception as e:
                        _logger.warning(f"❌ English OCR failed: {e}")
                
                # Try Japanese OCR
                if readers.get('japan'):
                    try:
                        _logger.info("🇯🇵 Trying Japanese OCR...")
                        jp_results = readers['japan'].ocr(temp_file.name)
                        if jp_results and jp_results[0]:
                            jp_processed = self._process_paddleocr_results(jp_results[0], 'japan')
                            if jp_processed:
                                results.append(('japan', jp_processed))
                                _logger.info(f"✅ Japanese: {len(jp_processed)} texts found")
                    except Exception as e:
                        _logger.warning(f"❌ Japanese OCR failed: {e}")
                
                # Try Vietnamese OCR
                if readers.get('vi'):
                    try:
                        _logger.info("🇻🇳 Trying Vietnamese OCR...")
                        vi_results = readers['vi'].ocr(temp_file.name)
                        if vi_results and vi_results[0]:
                            vi_processed = self._process_paddleocr_results(vi_results[0], 'vi')
                            if vi_processed:
                                results.append(('vi', vi_processed))
                                _logger.info(f"✅ Vietnamese: {len(vi_processed)} texts found")
                    except Exception as e:
                        _logger.warning(f"❌ Vietnamese OCR failed: {e}")
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                # Combine all results from different languages
                if not results:
                    _logger.warning("No OCR results found")
                    return []
                
                combined_results = self._combine_all_language_results(results)
                _logger.info(f"🔗 Combined results: {len(combined_results)} total texts from {len(results)} languages")
                
                # Store raw extracted text
                self.extracted_text = " ".join([item['text'] for item in combined_results])
                
                # Calculate average confidence
                if combined_results:
                    total_confidence = sum(item['confidence'] for item in combined_results)
                    self.extraction_confidence = total_confidence / len(combined_results)
                else:
                    self.extraction_confidence = 0
                
                return combined_results
                
        except Exception as e:
            _logger.error(f"OCR extraction error: {e}")
            raise UserError(_("Failed to extract text from image: %s") % str(e))
    
    def _process_paddleocr_results(self, raw_results, lang_combo):
        """Process raw PaddleOCR results into standardized format"""
        processed_results = []
        
        # Handle PaddleOCR format: list of [bbox, (text, confidence)] or dict format
        if isinstance(raw_results, dict) and 'rec_texts' in raw_results:
            # Handle dict format with rec_texts, rec_scores, rec_boxes
            for i in range(len(raw_results['rec_texts'])):
                try:
                    bbox = raw_results['rec_boxes'][i]
                    text_conf = raw_results['rec_texts'][i]
                    confidence = raw_results['rec_scores'][i]

                    if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                        text = str(text_conf[0])
                        confidence = float(text_conf[1])
                    else:
                        text = str(text_conf)
                        confidence = float(confidence)

                    # Convert numpy array to float if needed
                    if hasattr(confidence, 'item'):
                        confidence = confidence.item()

                    if confidence > 0.3 and text.strip():  # Filter low confidence and empty text
                        processed_results.append({
                            'text': text.strip(),
                            'confidence': confidence,
                            'bbox': bbox,
                            'lang_combo': lang_combo
                        })
                except Exception as e:
                    _logger.warning(f"⚠️ Error processing OCR item: {e}")
                    continue
        else:
            # Handle list format: [[bbox, (text, confidence)], ...]
            for item in raw_results:
                try:
                    if len(item) >= 2:
                        bbox = item[0]
                        text_conf = item[1]

                        if isinstance(text_conf, (list, tuple)) and len(text_conf) >= 2:
                            text = str(text_conf[0])
                            confidence = float(text_conf[1])
                        else:
                            text = str(text_conf)
                            confidence = 1.0

                        # Convert numpy array to float if needed
                        if hasattr(confidence, 'item'):
                            confidence = confidence.item()

                        if confidence > 0.3 and text.strip():  # Filter low confidence and empty text
                            processed_results.append({
                                'text': text.strip(),
                                'confidence': confidence,
                                'bbox': bbox,
                                'lang_combo': lang_combo
                            })
                except Exception as e:
                    _logger.warning(f"⚠️ Error processing OCR item: {e}")
                    continue
                
        return processed_results
    
    def _combine_all_language_results(self, results):
        """Combine results from all languages and remove duplicates"""
        combined_results = []
        seen_texts = set()
        
        for lang_combo, processed_results in results:
            if not processed_results:
                continue
            
            _logger.info(f"📊 {lang_combo}: {len(processed_results)} texts")
            
            for item in processed_results:
                text = item['text'].strip().lower()
                
                # Check for duplicate text (case insensitive)
                if text not in seen_texts and text:
                    seen_texts.add(text)
                    combined_results.append(item)
                    _logger.info(f"  ✅ Added: {item['text']} (confidence: {item['confidence']:.3f})")
                else:
                    _logger.info(f"  ⚠️ Duplicate skipped: {item['text']}")
        
        # Sort by confidence (highest first)
        combined_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        return combined_results

    def _preprocess_image(self, image):
        """Preprocess image to improve OCR accuracy"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Optional: Apply morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
            
            return processed
        except Exception as e:
            _logger.warning(f"Image preprocessing failed, using original: {e}")
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _process_with_ai(self, extracted_text):
        """Process extracted text with HuggingFace AI"""
        if not extracted_text:
            return {}
            
        # Combine all extracted text
        text_content = " ".join([item['text'] for item in extracted_text])
        
        prompt = f"""
        Please analyze the following text extracted from a business card and structure it into JSON format.
        Extract and organize the following information if available:
        - name (full name of the person)
        - title (job title/position)
        - company (company name)
        - email (email address)
        - phone (phone number)
        - mobile (mobile number)
        - address (physical address)
        - website (website URL)
        - other (any other relevant information)
        
        Text from business card: {text_content}
        
        Return only valid JSON format without any additional explanation or markdown formatting.
        """
        
        try:
            # Get HuggingFace token from system parameters
            hf_token = self.env['ir.config_parameter'].sudo().get_param('ocr_namecard.hf_token', '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')
            model_name = self.env['ir.config_parameter'].sudo().get_param('ocr_namecard.hf_model', 'openai/gpt-oss-20b')
            
            client = InferenceClient(
                provider="fireworks-ai",
                api_key=hf_token,
            )
            
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            response_content = response.choices[0].message.content
            self.raw_ai_response = response_content
            
            try:
                # Try to parse the response as JSON
                structured_data = json.loads(response_content)
                return structured_data
            except json.JSONDecodeError:
                # If not valid JSON, try to extract information manually
                return self._fallback_text_parsing(text_content)
                
        except Exception as e:
            _logger.error(f"AI processing error: {e}")
            # Fallback to simple text parsing
            return self._fallback_text_parsing(text_content)

    def _fallback_text_parsing(self, text_content):
        """Fallback method to parse text without AI"""
        import re
        
        result = {}
        
        # Simple email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        if emails:
            result['email'] = emails[0]
        
        # Simple phone extraction
        phone_pattern = r'[\+]?[1-9]?[0-9]{7,15}'
        phones = re.findall(phone_pattern, text_content)
        if phones:
            result['phone'] = phones[0]
        
        # Simple website extraction
        website_pattern = r'www\.[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}'
        websites = re.findall(website_pattern, text_content)
        if websites:
            result['website'] = websites[0]
        
        result['other'] = text_content
        return result

    def _update_from_structured_data(self, structured_data):
        """Update record fields from structured data"""
        field_mapping = {
            'name': 'contact_name',
            'title': 'job_title',
            'company': 'company_name',
            'email': 'email',
            'phone': 'phone',
            'mobile': 'mobile',
            'website': 'website',
            'address': 'address',
            'other': 'other_info'
        }
        
        for ai_field, odoo_field in field_mapping.items():
            if ai_field in structured_data and structured_data[ai_field]:
                setattr(self, odoo_field, structured_data[ai_field])

    def action_create_partner(self):
        """Create a partner from the name card data"""
        for record in self:
            if record.partner_id:
                raise UserError(_("A contact is already linked to this name card"))
            
            partner_vals = {
                'name': record.contact_name or record.company_name or 'Unknown',
                'email': record.email,
                'phone': record.phone,
                'mobile': record.mobile,
                'website': record.website,
                'street': record.address,
                'function': record.job_title,
                'comment': record.other_info,
            }
            
            # Create company contact if company name exists
            if record.company_name and record.contact_name:
                # First create/find company
                company = self.env['res.partner'].search([
                    ('name', '=', record.company_name),
                    ('is_company', '=', True)
                ], limit=1)
                
                if not company:
                    company = self.env['res.partner'].create({
                        'name': record.company_name,
                        'is_company': True,
                        'website': record.website,
                    })
                
                partner_vals['parent_id'] = company.id
                partner_vals['is_company'] = False
            
            partner = self.env['res.partner'].create(partner_vals)
            record.partner_id = partner.id
            
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': record.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reprocess(self):
        """Reprocess the name card"""
        for record in self:
            record.processing_status = 'draft'
            record.processing_error = False
            record.action_process_card()

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email:
                import re
                email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
                if not re.match(email_pattern, record.email):
                    raise ValidationError(_("Invalid email format: %s") % record.email)