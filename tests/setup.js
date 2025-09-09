// Test setup file
process.env.NODE_ENV = 'test';

// Set default environment variables for testing (using new ORCA_ prefix)
process.env.ORCA_API_KEY = 'test_orca_api_key';
process.env.ORCA_ENDPOINT = 'https://test-api.orca.com';
process.env.ORCA_TIMEOUT = '5000';
process.env.ORCA_LOG_LEVEL = 'WARNING';
process.env.ORCA_ENVIRONMENT = 'test';

// Legacy variables for backward compatibility testing
process.env.ALTWALLET_API_KEY = 'test_legacy_api_key';
process.env.ALTWALLET_ENDPOINT = 'https://test-api.altwallet.com';
process.env.REQUEST_TIMEOUT = '5000';

// Increase timeout for async operations
jest.setTimeout(10000);
