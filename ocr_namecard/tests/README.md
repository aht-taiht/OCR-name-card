# OCR Name Card Tests

Comprehensive test suite for the OCR Name Card module.

## Test Structure

```
tests/
├── __init__.py              # Test module initialization  
├── common.py               # Base test classes and utilities
├── test_namecard_model.py  # Model unit tests
├── test_namecard_controller.py  # Controller/HTTP tests  
├── test_namecard_integration.py  # Integration tests
├── test_performance.py     # Performance tests
└── README.md              # This file
```

## Test Categories

### 1. Unit Tests (`test_namecard_model.py`)

Tests individual model methods and functionality:

- **Model Creation**: Basic record creation and validation
- **Name Computation**: Dynamic name field computation logic
- **OCR Processing**: Text extraction from images using EasyOCR
- **AI Processing**: HuggingFace API integration and fallback parsing
- **Data Processing**: Updating records from structured AI responses
- **Partner Creation**: Converting name cards to Odoo contacts
- **Validation**: Email format and other data validation
- **Error Handling**: Graceful failure handling

**Key Test Methods:**
- `test_create_namecard_basic()`
- `test_extract_text_from_image_success()`
- `test_process_with_ai_success()`
- `test_action_create_partner_basic()`
- `test_email_validation_valid()`

### 2. Controller Tests (`test_namecard_controller.py`)

Tests HTTP endpoints and web controllers:

- **File Upload**: Single and bulk image uploads
- **API Responses**: JSON response formatting
- **Export Functions**: JSON and vCard export functionality
- **Error Handling**: HTTP error responses
- **File Validation**: File type and size validation
- **Authentication**: Access control testing

**Key Test Methods:**
- `test_upload_namecard_success()`
- `test_bulk_upload_success()`
- `test_export_namecard_json()`
- `test_generate_vcard()`

### 3. Integration Tests (`test_namecard_integration.py`)

Tests complete workflows and module integration:

- **Full Workflow**: End-to-end processing from upload to contact creation
- **Error Recovery**: Handling failures with fallback mechanisms
- **Partner Integration**: Integration with Odoo contacts
- **Mail Integration**: Activity and message tracking
- **Search & Filtering**: Advanced search capabilities
- **Access Rights**: Security and permissions
- **Data Consistency**: Constraint validation

**Key Test Methods:**
- `test_full_processing_workflow()`
- `test_partner_creation_scenarios()`
- `test_mail_integration()`
- `test_access_rights()`

### 4. Performance Tests (`test_performance.py`)

Tests system performance and scalability:

- **Processing Speed**: Image processing performance
- **Bulk Operations**: Large dataset handling
- **Search Performance**: Query optimization
- **Memory Usage**: Memory efficiency
- **Concurrent Processing**: Multi-user scenarios
- **Database Optimization**: Query efficiency

**Key Test Methods:**
- `test_image_processing_performance()`
- `test_bulk_creation_performance()`
- `test_search_performance()`
- `test_concurrent_processing_simulation()`

## Running Tests

### Command Line

```bash
# Run all tests
odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init

# Run specific test file
odoo-bin -d test_db -i ocr_namecard --test-enable --test-tags ocr_namecard.test_namecard_model --stop-after-init

# Run with verbose output
odoo-bin -d test_db -i ocr_namecard --test-enable --log-level=test --stop-after-init
```

### From Odoo Interface

1. Enable developer mode
2. Go to Settings → Technical → Tests
3. Select OCR Name Card module
4. Run tests

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Odoo Tests
  run: |
    odoo-bin -d ${POSTGRES_DB} -i ocr_namecard --test-enable --stop-after-init
```

## Test Data

### Mock Data Used

- **Test Images**: Minimal PNG image data for upload tests
- **OCR Responses**: Predefined text extraction results
- **AI Responses**: Sample JSON responses from AI processing
- **Contact Data**: Sample business card information

### Test Configuration

Tests use mocked external dependencies:
- **EasyOCR**: Mocked to return predictable results
- **HuggingFace API**: Mocked to avoid API calls during testing
- **File System**: Temporary files for image processing tests

## Best Practices

### Writing Tests

1. **Use Base Classes**: Extend `NameCardTestCase` for model tests
2. **Mock External APIs**: Never make real API calls in tests
3. **Clean Test Data**: Use `TransactionCase` for automatic rollback
4. **Test Edge Cases**: Include error scenarios and validation failures
5. **Performance Awareness**: Set reasonable time limits for performance tests

### Test Coverage

Aim for comprehensive coverage of:
- ✅ All public methods
- ✅ Error handling paths
- ✅ Integration points
- ✅ User workflows
- ✅ Security checks

### Debugging Tests

```python
# Add debug prints
import logging
_logger = logging.getLogger(__name__)
_logger.info("Debug info: %s", variable)

# Use pdb for breakpoints
import pdb; pdb.set_trace()

# Check SQL queries
self.env.cr.execute("SELECT query FROM pg_stat_activity")
```

## Common Issues

### 1. Mock Configuration
- Ensure mocks are properly configured before test execution
- Reset mocks between tests to avoid interference

### 2. Database State
- Use `TransactionCase` for automatic rollback
- Be careful with `commit()` in tests

### 3. External Dependencies
- All external APIs should be mocked
- Install required Python packages in test environment

### 4. Performance Tests
- Performance thresholds may need adjustment based on hardware
- Use relative performance comparisons when possible

## Coverage Reports

Generate coverage reports:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source=ocr_namecard odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init

# Generate report
coverage report -m
coverage html  # HTML report in htmlcov/
```

## Continuous Integration

Example test configuration for CI:

```yaml
test:
  stage: test
  script:
    - pip install -r requirements.txt
    - createdb test_db
    - odoo-bin -d test_db -i ocr_namecard --test-enable --stop-after-init
  coverage: '/TOTAL.*\s+(\d+%)$/'
```