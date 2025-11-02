"""
Sendly Sandbox Magic Numbers

These phone numbers provide predictable behaviors for testing
with test API keys (sl_test_*). Use these constants to ensure
consistent testing across your application.
"""

# Test numbers organized by category
MAGIC_NUMBERS = {
    # Success scenarios - Messages that will be delivered successfully
    'success': {
        'instant': '+15550001234',  # Instant delivery success
        'delay_5s': '+15550001235',  # Success with 5 second delay
        'verizon_carrier': '+15550001236',  # Success with Verizon carrier simulation
    },
    
    # Error scenarios - Messages that will fail with specific errors
    'errors': {
        'invalid_number': '+15550001001',  # Invalid phone number format (400)
        'carrier_rejection': '+15550001002',  # Carrier content rejection (400)
        'rate_limit': '+15550001003',  # Rate limit exceeded (429)
        'timeout': '+15550001004',  # Request timeout (500)
        'insufficient_balance': '+15550001005',  # Insufficient account balance (402)
    },
    
    # Delay testing - Messages with various delivery delays
    'delays': {
        '10_seconds': '+15550001010',  # 10 second delivery delay
        '30_seconds': '+15550001030',  # 30 second delivery delay
        '60_seconds': '+15550001060',  # 60 second delivery delay
    },
    
    # Carrier simulations - Test carrier-specific behaviors
    'carriers': {
        'verizon': '+15550002001',  # Verizon network behavior
        'att': '+15550002002',  # AT&T network behavior
        'tmobile': '+15550002003',  # T-Mobile network behavior
    },
    
    # Webhook testing - Test webhook delivery scenarios
    'webhooks': {
        'success': '+15550003001',  # Successful webhook delivery
        'timeout': '+15550003002',  # Webhook timeout simulation
        'error_500': '+15550003003',  # Webhook 500 error with retry
    }
}

# Test number metadata for documentation
MAGIC_NUMBER_INFO = {
    # Success scenarios
    '+15550001234': {
        'number': '+15550001234',
        'category': 'success',
        'description': 'Instant delivery success',
    },
    '+15550001235': {
        'number': '+15550001235',
        'category': 'success',
        'description': 'Success with 5 second delay',
        'delay': 5000,
    },
    '+15550001236': {
        'number': '+15550001236',
        'category': 'success',
        'description': 'Verizon carrier simulation',
    },
    
    # Error scenarios
    '+15550001001': {
        'number': '+15550001001',
        'category': 'error',
        'description': 'Invalid phone number format',
        'http_status': 400,
        'error': 'invalid_number',
    },
    '+15550001002': {
        'number': '+15550001002',
        'category': 'error',
        'description': 'Carrier content rejection',
        'http_status': 400,
        'error': 'carrier_rejection',
    },
    '+15550001003': {
        'number': '+15550001003',
        'category': 'error',
        'description': 'Rate limit exceeded',
        'http_status': 429,
        'error': 'rate_limit_exceeded',
    },
    '+15550001004': {
        'number': '+15550001004',
        'category': 'error',
        'description': 'Request timeout',
        'http_status': 500,
        'error': 'timeout_error',
    },
    '+15550001005': {
        'number': '+15550001005',
        'category': 'error',
        'description': 'Insufficient account balance',
        'http_status': 402,
        'error': 'insufficient_balance',
    },
    
    # Delay scenarios
    '+15550001010': {
        'number': '+15550001010',
        'category': 'delay',
        'description': '10 second delivery delay',
        'delay': 10000,
    },
    '+15550001030': {
        'number': '+15550001030',
        'category': 'delay',
        'description': '30 second delivery delay',
        'delay': 30000,
    },
    '+15550001060': {
        'number': '+15550001060',
        'category': 'delay',
        'description': '60 second delivery delay',
        'delay': 60000,
    },
    
    # Carrier scenarios
    '+15550002001': {
        'number': '+15550002001',
        'category': 'carrier',
        'description': 'Verizon network simulation',
    },
    '+15550002002': {
        'number': '+15550002002',
        'category': 'carrier',
        'description': 'AT&T network simulation',
    },
    '+15550002003': {
        'number': '+15550002003',
        'category': 'carrier',
        'description': 'T-Mobile network simulation',
    },
    
    # Webhook scenarios
    '+15550003001': {
        'number': '+15550003001',
        'category': 'webhook',
        'description': 'Successful webhook delivery',
    },
    '+15550003002': {
        'number': '+15550003002',
        'category': 'webhook',
        'description': 'Webhook timeout simulation',
    },
    '+15550003003': {
        'number': '+15550003003',
        'category': 'webhook',
        'description': 'Webhook 500 error with retry',
    },
}


def is_magic_number(phone_number: str) -> bool:
    """
    Check if a phone number is a test number.
    
    Args:
        phone_number: The phone number to check
        
    Returns:
        True if the number is a test number, False otherwise
    """
    return phone_number in MAGIC_NUMBER_INFO


def get_magic_number_info(phone_number: str) -> dict:
    """
    Get test number information.
    
    Args:
        phone_number: The test number to get info for
        
    Returns:
        Test number information dictionary or None if not found
    """
    return MAGIC_NUMBER_INFO.get(phone_number)


def get_magic_numbers_by_category(category: str) -> list:
    """
    Get all test numbers by category.
    
    Args:
        category: The category to filter by ('success', 'error', 'delay', 'carrier', 'webhook')
        
    Returns:
        List of test numbers in the specified category
    """
    return [
        info['number'] 
        for info in MAGIC_NUMBER_INFO.values() 
        if info.get('category') == category
    ]


def get_error_magic_numbers() -> list:
    """
    Get all test numbers that produce errors.
    
    Returns:
        List of error-producing test numbers
    """
    return get_magic_numbers_by_category('error')


def get_success_magic_numbers() -> list:
    """
    Get all test numbers that succeed.
    
    Returns:
        List of success test numbers
    """
    return get_magic_numbers_by_category('success')