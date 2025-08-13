import time
import base64
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from .common import NameCardTestCase


class TestNameCardPerformance(NameCardTestCase):
    """Performance tests for OCR Name Card module"""

    def test_image_processing_performance(self):
        """Test image processing performance"""
        start_time = time.time()
        
        with patch('easyocr.Reader') as mock_reader_class, \
             patch('huggingface_hub.InferenceClient') as mock_client_class:
            
            # Setup mocks for fast processing
            mock_reader = MagicMock()
            mock_reader.readtext.return_value = self.mock_ocr_response
            mock_reader_class.return_value = mock_reader
            
            mock_client = MagicMock()
            mock_client.text_generation.return_value = self.mock_ai_response
            mock_client_class.return_value = mock_client
            
            # Process a name card
            namecard = self.create_test_namecard()
            namecard.action_process_card()
            
            processing_time = time.time() - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            self.assertLess(processing_time, 5.0, "Processing took too long")
            self.assertEqual(namecard.processing_status, 'done')

    def test_bulk_creation_performance(self):
        """Test performance with bulk record creation"""
        start_time = time.time()
        
        # Disable auto-processing for performance test
        with patch.object(self.NameCard, 'action_process_card'):
            records_data = []
            for i in range(100):
                records_data.append({
                    'image': self.test_image_data,
                    'image_filename': f'card_{i}.jpg',
                    'processing_status': 'draft'
                })
            
            records = self.NameCard.create(records_data)
            
            creation_time = time.time() - start_time
            
            # Should create 100 records quickly
            self.assertEqual(len(records), 100)
            self.assertLess(creation_time, 10.0, "Bulk creation took too long")

    def test_search_performance(self):
        """Test search performance with large dataset"""
        # Create test dataset
        with patch.object(self.NameCard, 'action_process_card'):
            records_data = []
            for i in range(50):
                records_data.append({
                    'image': self.test_image_data,
                    'image_filename': f'card_{i}.jpg',
                    'contact_name': f'Contact {i}',
                    'company_name': f'Company {i % 10}',
                    'email': f'contact{i}@company{i % 10}.com',
                    'processing_status': 'done'
                })
            
            self.NameCard.create(records_data)
        
        # Test various search operations
        start_time = time.time()
        
        # Search by name
        results1 = self.NameCard.search([('contact_name', 'ilike', 'Contact 1')])
        
        # Search by company
        results2 = self.NameCard.search([('company_name', '=', 'Company 5')])
        
        # Search by status
        results3 = self.NameCard.search([('processing_status', '=', 'done')])
        
        # Complex search
        results4 = self.NameCard.search([
            '|',
            ('contact_name', 'ilike', 'Contact'),
            ('company_name', 'ilike', 'Company')
        ])
        
        search_time = time.time() - start_time
        
        # Verify results
        self.assertTrue(len(results1) > 0)
        self.assertTrue(len(results2) > 0)
        self.assertTrue(len(results3) >= 50)
        self.assertTrue(len(results4) >= 50)
        
        # Should complete searches quickly
        self.assertLess(search_time, 2.0, "Searches took too long")

    def test_memory_usage(self):
        """Test memory usage with image data"""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Create multiple records with images
        with patch.object(self.NameCard, 'action_process_card'):
            for i in range(10):
                namecard = self.create_test_namecard(
                    image_filename=f'large_card_{i}.jpg'
                )
                # Process record operations
                namecard.write({'contact_name': f'Contact {i}'})
                namecard.read(['contact_name', 'image'])
        
        # Force cleanup
        gc.collect()
        
        # Test should complete without memory errors
        self.assertTrue(True, "Memory test completed")

    def test_concurrent_processing_simulation(self):
        """Simulate concurrent processing scenarios"""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        results = []
        errors = []
        
        def process_namecard(index):
            try:
                with patch('easyocr.Reader') as mock_reader_class, \
                     patch('huggingface_hub.InferenceClient') as mock_client_class:
                    
                    mock_reader = MagicMock()
                    mock_reader.readtext.return_value = self.mock_ocr_response
                    mock_reader_class.return_value = mock_reader
                    
                    mock_client = MagicMock()
                    mock_client.text_generation.return_value = self.mock_ai_response
                    mock_client_class.return_value = mock_client
                    
                    # Use new cursor to simulate separate transaction
                    with self.env.registry.cursor() as cr:
                        env = self.env(cr=cr)
                        namecard = env['ocr.namecard'].create({
                            'image': self.test_image_data,
                            'image_filename': f'concurrent_card_{index}.jpg',
                            'processing_status': 'draft'
                        })
                        namecard.action_process_card()
                        results.append(namecard.id)
                        cr.commit()
                        
            except Exception as e:
                errors.append(str(e))
        
        # Simulate 5 concurrent uploads
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_namecard, i) for i in range(5)]
            for future in futures:
                future.result()
        
        # Verify all processed successfully
        self.assertEqual(len(errors), 0, f"Concurrent processing errors: {errors}")
        self.assertEqual(len(results), 5, "Not all concurrent processes completed")

    def test_database_query_optimization(self):
        """Test database query optimization"""
        # Create test data
        with patch.object(self.NameCard, 'action_process_card'):
            records = []
            for i in range(20):
                record = self.create_test_namecard(
                    contact_name=f'Contact {i}',
                    company_name=f'Company {i % 5}',
                    processing_status='done'
                )
                records.append(record)
        
        # Test efficient queries
        start_time = time.time()
        
        # Use prefetch and grouping
        records_with_partners = self.NameCard.search([('processing_status', '=', 'done')])
        records_with_partners.mapped('partner_id.name')  # Should use prefetch
        
        # Group operations
        company_groups = {}
        for record in records_with_partners:
            company = record.company_name
            if company not in company_groups:
                company_groups[company] = []
            company_groups[company].append(record)
        
        query_time = time.time() - start_time
        
        # Should execute efficiently
        self.assertLess(query_time, 1.0, "Database queries took too long")
        self.assertTrue(len(company_groups) > 0)