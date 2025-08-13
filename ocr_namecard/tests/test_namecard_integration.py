import json
import base64
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase, HttpCase
from .common import NameCardTestCase, NameCardHttpTestCase


class TestNameCardIntegration(NameCardTestCase):
    """Integration tests for OCR Name Card module"""

    @patch('pytesseract.image_to_data')
    @patch('cv2.imread')
    @patch('huggingface_hub.InferenceClient')
    def test_full_processing_workflow(self, mock_client_class, mock_imread, mock_tesseract):
        """Test complete workflow from image upload to contact creation"""
        # Setup mocks
        mock_image = MagicMock()
        mock_imread.return_value = mock_image
        
        mock_tesseract_data = {
            'level': [5, 5, 5, 5, 5],
            'conf': [95, 92, 88, 93, 90],
            'text': ['John Smith', 'Senior Developer', 'Tech Corp Inc.', 
                    'john.smith@techcorp.com', '+1-555-0123'],
            'left': [100, 100, 100, 100, 100],
            'top': [50, 90, 120, 150, 180],
            'width': [100, 150, 180, 200, 100],
            'height': [30, 20, 20, 20, 20]
        }
        mock_tesseract.return_value = mock_tesseract_data
        
        mock_client = MagicMock()
        mock_client.text_generation.return_value = self.mock_ai_response
        mock_client_class.return_value = mock_client
        
        # Create name card with image
        namecard = self.create_test_namecard()
        
        # Verify initial state
        self.assertEqual(namecard.processing_status, 'draft')
        self.assertFalse(namecard.contact_name)
        
        # Process the card (this should happen automatically on create, but let's be explicit)
        namecard.action_process_card()
        
        # Verify processing completed successfully
        self.assertEqual(namecard.processing_status, 'done')
        self.assertEqual(namecard.contact_name, 'John Smith')
        self.assertEqual(namecard.job_title, 'Senior Developer')
        self.assertEqual(namecard.company_name, 'Tech Corp Inc.')
        self.assertEqual(namecard.email, 'john.smith@techcorp.com')
        self.assertEqual(namecard.phone, '+1-555-0123')
        self.assertGreater(namecard.extraction_confidence, 0.9)
        
        # Create partner from name card
        result = namecard.action_create_partner()
        
        # Verify partner creation
        self.assertTrue(namecard.partner_id.exists())
        partner = namecard.partner_id
        self.assertEqual(partner.name, 'John Smith')
        self.assertEqual(partner.email, 'john.smith@techcorp.com')
        self.assertEqual(partner.function, 'Senior Developer')
        
        # Verify company creation
        company = partner.parent_id
        self.assertTrue(company.exists())
        self.assertEqual(company.name, 'Tech Corp Inc.')
        self.assertTrue(company.is_company)
        
        # Verify return action
        self.assertEqual(result['res_model'], 'res.partner')
        self.assertEqual(result['res_id'], partner.id)

    @patch('pytesseract.image_to_data')
    def test_processing_with_ocr_failure(self, mock_tesseract):
        """Test workflow when OCR fails"""
        mock_tesseract.side_effect = Exception("OCR service unavailable")
        
        namecard = self.create_test_namecard()
        namecard.action_process_card()
        
        # Verify error handling
        self.assertEqual(namecard.processing_status, 'error')
        self.assertIn('OCR service unavailable', namecard.processing_error)

    @patch('pytesseract.image_to_data')
    @patch('cv2.imread')
    @patch('huggingface_hub.InferenceClient')
    def test_processing_with_ai_failure_fallback(self, mock_client_class, mock_imread, mock_tesseract):
        """Test workflow when AI fails but fallback works"""
        # Setup OCR to work
        mock_image = MagicMock()
        mock_imread.return_value = mock_image
        
        mock_tesseract_data = {
            'level': [5, 5],
            'conf': [93, 90],
            'text': ['john.smith@techcorp.com', '+1-555-0123'],
            'left': [100, 100],
            'top': [150, 180],
            'width': [200, 100],
            'height': [20, 20]
        }
        mock_tesseract.return_value = mock_tesseract_data
        
        # Setup AI to fail
        mock_client_class.side_effect = Exception("AI service unavailable")
        
        namecard = self.create_test_namecard()
        namecard.action_process_card()
        
        # Verify fallback worked
        self.assertEqual(namecard.processing_status, 'done')
        self.assertEqual(namecard.email, 'john.smith@techcorp.com')
        self.assertEqual(namecard.phone, '+1-555-0123')

    def test_partner_creation_scenarios(self):
        """Test various partner creation scenarios"""
        # Scenario 1: Individual contact only
        namecard1 = self.create_test_namecard(
            contact_name='Jane Doe',
            email='jane@example.com'
        )
        namecard1.action_create_partner()
        
        partner1 = namecard1.partner_id
        self.assertEqual(partner1.name, 'Jane Doe')
        self.assertFalse(partner1.parent_id)
        self.assertFalse(partner1.is_company)
        
        # Scenario 2: Company only
        namecard2 = self.create_test_namecard(
            company_name='Solo Corp',
            email='info@solocorp.com'
        )
        namecard2.action_create_partner()
        
        partner2 = namecard2.partner_id
        self.assertEqual(partner2.name, 'Solo Corp')
        self.assertFalse(partner2.parent_id)
        
        # Scenario 3: Contact with existing company
        existing_company = self.Partner.create({
            'name': 'Existing Corp',
            'is_company': True
        })
        
        namecard3 = self.create_test_namecard(
            contact_name='Bob Wilson',
            company_name='Existing Corp',
            email='bob@existing.com'
        )
        namecard3.action_create_partner()
        
        partner3 = namecard3.partner_id
        self.assertEqual(partner3.parent_id, existing_company)

    def test_reprocessing_workflow(self):
        """Test reprocessing name cards"""
        namecard = self.create_test_namecard(processing_status='error')
        
        # Mock successful processing on retry
        with patch.object(namecard, '_extract_text_from_image') as mock_ocr, \
             patch.object(namecard, '_process_with_ai') as mock_ai:
            
            mock_ocr.return_value = self.mock_ocr_response
            mock_ai.return_value = json.loads(self.mock_ai_response)
            
            namecard.action_reprocess()
            
            # Verify reprocessing worked
            self.assertEqual(namecard.processing_status, 'done')
            self.assertEqual(namecard.contact_name, 'John Smith')

    def test_mail_integration(self):
        """Test mail/activity integration"""
        namecard = self.create_test_namecard()
        
        # Test tracking changes
        namecard.write({
            'contact_name': 'Updated Name',
            'processing_status': 'done'
        })
        
        # Check messages were created
        messages = namecard.message_ids
        self.assertTrue(messages.exists())
        
        # Test adding followers
        user = self.env.user
        namecard.message_subscribe([user.partner_id.id])
        self.assertIn(user.partner_id, namecard.message_follower_ids.mapped('partner_id'))

    def test_search_and_filtering(self):
        """Test search and filtering capabilities"""
        # Create test data
        namecard1 = self.create_test_namecard(
            contact_name='Alice Johnson',
            company_name='Alpha Corp',
            processing_status='done'
        )
        namecard2 = self.create_test_namecard(
            contact_name='Bob Smith',
            company_name='Beta Inc',
            processing_status='error'
        )
        namecard3 = self.create_test_namecard(
            contact_name='Charlie Brown',
            company_name='Alpha Corp',
            processing_status='processing'
        )
        
        # Test search by name
        results = self.NameCard.search([('contact_name', 'ilike', 'alice')])
        self.assertEqual(len(results), 1)
        self.assertEqual(results.contact_name, 'Alice Johnson')
        
        # Test search by company
        results = self.NameCard.search([('company_name', '=', 'Alpha Corp')])
        self.assertEqual(len(results), 2)
        
        # Test filtering by status
        done_cards = self.NameCard.search([('processing_status', '=', 'done')])
        error_cards = self.NameCard.search([('processing_status', '=', 'error')])
        
        self.assertIn(namecard1, done_cards)
        self.assertIn(namecard2, error_cards)

    def test_access_rights(self):
        """Test access rights and security"""
        # Create regular user
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]
        })
        
        # Test user can create and access name cards
        namecard = self.NameCard.with_user(user).create({
            'image': self.test_image_data,
            'image_filename': 'test.jpg'
        })
        
        self.assertTrue(namecard.exists())
        
        # Test user can read their own records
        read_access = self.NameCard.with_user(user).search([('id', '=', namecard.id)])
        self.assertTrue(read_access.exists())

    def test_data_consistency(self):
        """Test data consistency and constraints"""
        # Test email validation
        namecard = self.create_test_namecard(email='invalid-email')
        
        with self.assertRaises(Exception):
            namecard._check_email_format()
        
        # Test name computation consistency
        namecard = self.create_test_namecard()
        original_name = namecard.name
        
        namecard.write({'contact_name': 'New Name'})
        self.assertNotEqual(namecard.name, original_name)

    def test_performance_bulk_operations(self):
        """Test performance with bulk operations"""
        # Create multiple name cards
        namecards_data = []
        for i in range(10):
            namecards_data.append({
                'image': self.test_image_data,
                'image_filename': f'test_card_{i}.jpg',
                'processing_status': 'draft'
            })
        
        # Disable auto-processing for this test
        with patch.object(self.NameCard, 'action_process_card'):
            namecards = self.NameCard.create(namecards_data)
        
        self.assertEqual(len(namecards), 10)
        
        # Test bulk operations
        namecards.write({'processing_status': 'done'})
        for namecard in namecards:
            self.assertEqual(namecard.processing_status, 'done')


class TestNameCardHttpIntegration(NameCardHttpTestCase):
    """HTTP integration tests"""

    def test_complete_http_workflow(self):
        """Test complete HTTP workflow"""
        # This would test the full HTTP workflow but requires more complex setup
        # For now, we'll test basic HTTP functionality
        pass

    def test_api_authentication(self):
        """Test API authentication requirements"""
        # Test that unauthenticated requests are rejected
        pass

    def test_concurrent_uploads(self):
        """Test handling concurrent uploads"""
        # Test that multiple simultaneous uploads work correctly
        pass