import json
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from .common import NameCardTestCase


class TestNameCardModel(NameCardTestCase):
    """Test cases for ocr.namecard model"""

    def test_create_namecard_basic(self):
        """Test basic name card creation"""
        namecard = self.create_test_namecard()
        
        self.assertTrue(namecard.exists())
        self.assertEqual(namecard.processing_status, 'draft')
        self.assertEqual(namecard.image_filename, 'test_card.jpg')
        self.assertTrue(namecard.image)

    def test_compute_name_with_contact_and_company(self):
        """Test name computation with both contact and company"""
        namecard = self.create_test_namecard(
            contact_name='John Smith',
            company_name='Tech Corp'
        )
        
        self.assertEqual(namecard.name, 'John Smith (Tech Corp)')

    def test_compute_name_contact_only(self):
        """Test name computation with contact only"""
        namecard = self.create_test_namecard(
            contact_name='John Smith'
        )
        
        self.assertEqual(namecard.name, 'John Smith')

    def test_compute_name_company_only(self):
        """Test name computation with company only"""
        namecard = self.create_test_namecard(
            company_name='Tech Corp'
        )
        
        self.assertEqual(namecard.name, 'Tech Corp')

    def test_compute_name_fallback(self):
        """Test name computation fallback to filename"""
        namecard = self.create_test_namecard()
        
        self.assertEqual(namecard.name, 'test_card.jpg')

    @patch('ocr_namecard.models.namecard.get_easyocr_readers')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_extract_text_from_image_success(self, mock_unlink, mock_tempfile, mock_get_readers):
        """Test successful text extraction from image"""
        # Setup mocks
        mock_temp = MagicMock()
        mock_temp.name = '/tmp/test_image.jpg'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        # Mock EasyOCR readers
        mock_reader_ja_en = MagicMock()
        mock_reader_ja_en.readtext.return_value = [
            ([[100, 50], [200, 50], [200, 80], [100, 80]], 'John Smith', 0.95),
            ([[100, 90], [250, 90], [250, 110], [100, 110]], 'Developer', 0.88),
        ]
        
        mock_reader_vi_en = MagicMock()
        mock_reader_vi_en.readtext.return_value = [
            ([[100, 50], [200, 50], [200, 80], [100, 80]], 'John Smith', 0.92),
        ]
        
        mock_get_readers.return_value = {
            'ja_en': mock_reader_ja_en,
            'vi_en': mock_reader_vi_en
        }
        
        namecard = self.create_test_namecard()
        result = namecard._extract_text_from_image()
        
        # Assertions (should select ja+en as it has better score)
        self.assertGreater(len(result), 0)
        self.assertEqual(namecard.extracted_text.strip(), 'John Smith Developer')
        self.assertGreater(namecard.extraction_confidence, 0.8)

    @patch('ocr_namecard.models.namecard.get_easyocr_readers')
    def test_extract_text_from_image_failure(self, mock_get_readers):
        """Test text extraction failure"""
        mock_get_readers.return_value = {
            'ja_en': None,
            'vi_en': None
        }
        
        namecard = self.create_test_namecard()
        
        with self.assertRaises(UserError) as context:
            namecard._extract_text_from_image()
        
        self.assertIn("EasyOCR is not properly initialized", str(context.exception))

    @patch('huggingface_hub.InferenceClient')
    def test_process_with_ai_success(self, mock_client_class):
        """Test successful AI processing"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.text_generation.return_value = self.mock_ai_response
        mock_client_class.return_value = mock_client
        
        namecard = self.create_test_namecard()
        result = namecard._process_with_ai(self.mock_ocr_response)
        
        # Assertions
        self.assertEqual(result['name'], 'John Smith')
        self.assertEqual(result['company'], 'Tech Corp Inc.')
        self.assertEqual(result['email'], 'john.smith@techcorp.com')
        self.assertEqual(namecard.raw_ai_response, self.mock_ai_response)

    @patch('huggingface_hub.InferenceClient')
    def test_process_with_ai_invalid_json(self, mock_client_class):
        """Test AI processing with invalid JSON response"""
        # Setup mock to return invalid JSON
        mock_client = MagicMock()
        mock_client.text_generation.return_value = "This is not valid JSON"
        mock_client_class.return_value = mock_client
        
        namecard = self.create_test_namecard()
        result = namecard._process_with_ai(self.mock_ocr_response)
        
        # Should fallback to simple text parsing
        self.assertIn('email', result)
        self.assertEqual(result['email'], 'john.smith@techcorp.com')

    @patch('huggingface_hub.InferenceClient')
    def test_process_with_ai_failure(self, mock_client_class):
        """Test AI processing failure"""
        mock_client_class.side_effect = Exception("AI processing failed")
        
        namecard = self.create_test_namecard()
        result = namecard._process_with_ai(self.mock_ocr_response)
        
        # Should fallback to simple text parsing
        self.assertIsInstance(result, dict)

    def test_fallback_text_parsing(self):
        """Test fallback text parsing functionality"""
        namecard = self.create_test_namecard()
        text_content = "John Smith john.smith@techcorp.com +1-555-0123 www.techcorp.com Other info"
        
        result = namecard._fallback_text_parsing(text_content)
        
        self.assertEqual(result['email'], 'john.smith@techcorp.com')
        self.assertEqual(result['phone'], '+1-555-0123')
        self.assertEqual(result['website'], 'www.techcorp.com')
        self.assertIn('Other info', result['other'])

    def test_update_from_structured_data(self):
        """Test updating record from structured data"""
        namecard = self.create_test_namecard()
        structured_data = {
            'name': 'Jane Doe',
            'title': 'Manager',
            'company': 'Example Corp',
            'email': 'jane@example.com',
            'phone': '+1-555-9999'
        }
        
        namecard._update_from_structured_data(structured_data)
        
        self.assertEqual(namecard.contact_name, 'Jane Doe')
        self.assertEqual(namecard.job_title, 'Manager')
        self.assertEqual(namecard.company_name, 'Example Corp')
        self.assertEqual(namecard.email, 'jane@example.com')
        self.assertEqual(namecard.phone, '+1-555-9999')

    @patch.object(NameCardTestCase.NameCard, '_extract_text_from_image')
    @patch.object(NameCardTestCase.NameCard, '_process_with_ai')
    def test_action_process_card_success(self, mock_ai, mock_ocr):
        """Test successful card processing"""
        # Setup mocks
        mock_ocr.return_value = self.mock_ocr_response
        mock_ai.return_value = json.loads(self.mock_ai_response)
        
        namecard = self.create_test_namecard()
        namecard.action_process_card()
        
        # Assertions
        self.assertEqual(namecard.processing_status, 'done')
        self.assertEqual(namecard.contact_name, 'John Smith')
        self.assertEqual(namecard.company_name, 'Tech Corp Inc.')
        mock_ocr.assert_called_once()
        mock_ai.assert_called_once()

    def test_action_process_card_no_image(self):
        """Test processing card without image"""
        namecard = self.NameCard.create({
            'image_filename': 'test.jpg',
            'processing_status': 'draft'
        })
        
        with self.assertRaises(UserError) as context:
            namecard.action_process_card()
        
        self.assertIn("No image uploaded", str(context.exception))

    @patch.object(NameCardTestCase.NameCard, '_extract_text_from_image')
    def test_action_process_card_no_text_extracted(self, mock_ocr):
        """Test processing when no text is extracted"""
        mock_ocr.return_value = []
        
        namecard = self.create_test_namecard()
        namecard.action_process_card()
        
        self.assertEqual(namecard.processing_status, 'error')
        self.assertIn("No text could be extracted", namecard.processing_error)

    def test_action_create_partner_basic(self):
        """Test creating partner from name card"""
        namecard = self.create_test_namecard(
            contact_name='John Smith',
            company_name='Tech Corp',
            email='john@techcorp.com',
            phone='+1-555-0123',
            job_title='Developer'
        )
        
        result = namecard.action_create_partner()
        
        # Check partner was created
        self.assertTrue(namecard.partner_id.exists())
        self.assertEqual(namecard.partner_id.name, 'John Smith')
        self.assertEqual(namecard.partner_id.email, 'john@techcorp.com')
        self.assertEqual(namecard.partner_id.function, 'Developer')
        
        # Check return action
        self.assertEqual(result['res_model'], 'res.partner')
        self.assertEqual(result['res_id'], namecard.partner_id.id)

    def test_action_create_partner_already_linked(self):
        """Test creating partner when already linked"""
        partner = self.Partner.create({'name': 'Existing Partner'})
        namecard = self.create_test_namecard(partner_id=partner.id)
        
        with self.assertRaises(UserError) as context:
            namecard.action_create_partner()
        
        self.assertIn("already linked", str(context.exception))

    def test_action_create_partner_with_company(self):
        """Test creating partner with company structure"""
        namecard = self.create_test_namecard(
            contact_name='John Smith',
            company_name='Tech Corp Inc',
            email='john@techcorp.com'
        )
        
        namecard.action_create_partner()
        
        # Check company was created
        company = self.Partner.search([('name', '=', 'Tech Corp Inc'), ('is_company', '=', True)])
        self.assertTrue(company.exists())
        
        # Check contact is linked to company
        self.assertEqual(namecard.partner_id.parent_id, company)
        self.assertFalse(namecard.partner_id.is_company)

    def test_action_reprocess(self):
        """Test reprocessing name card"""
        namecard = self.create_test_namecard(processing_status='done')
        
        with patch.object(namecard, 'action_process_card') as mock_process:
            namecard.action_reprocess()
            
            self.assertEqual(namecard.processing_status, 'draft')
            self.assertFalse(namecard.processing_error)
            mock_process.assert_called_once()

    def test_email_validation_valid(self):
        """Test valid email validation"""
        namecard = self.create_test_namecard(email='test@example.com')
        # Should not raise any exception
        namecard._check_email_format()

    def test_email_validation_invalid(self):
        """Test invalid email validation"""
        namecard = self.create_test_namecard(email='invalid-email')
        
        with self.assertRaises(ValidationError) as context:
            namecard._check_email_format()
        
        self.assertIn("Invalid email format", str(context.exception))

    def test_create_triggers_processing(self):
        """Test that creating a record triggers processing"""
        with patch.object(self.NameCard, 'action_process_card') as mock_process:
            namecard = self.create_test_namecard()
            mock_process.assert_called_once()

    def test_mail_tracking(self):
        """Test that mail tracking works for important fields"""
        namecard = self.create_test_namecard()
        
        # Change tracked field
        namecard.write({'contact_name': 'New Name'})
        
        # Check that message was posted
        messages = namecard.message_ids
        self.assertTrue(any('contact_name' in msg.body for msg in messages if msg.body))