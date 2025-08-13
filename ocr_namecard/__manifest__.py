{
    'name': 'OCR Name Card Reader',
    'version': '18.0.1.0.0',
    'category': 'Tools',
    'summary': 'Extract and structure contact information from name card images using OCR and AI',
    'description': """
OCR Name Card Reader
===================
This module allows you to:
* Upload name card images
* Extract text using EasyOCR (Japanese + English, Vietnamese + English)
* Structure contact information using HuggingFace AI models
* Store and manage contact data
* Export results to various formats
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'web'],
    'external_dependencies': {
        'python': ['easyocr', 'huggingface_hub', 'PIL', 'numpy', 'cv2', 'torch']
    },
    'test_depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/namecard_views.xml',
        'views/namecard_menus.xml',
        'data/namecard_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ocr_namecard/static/src/css/namecard.css',
            'ocr_namecard/static/src/js/namecard_upload.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}