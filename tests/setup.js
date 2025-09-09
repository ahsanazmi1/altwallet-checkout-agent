// Test setup file
process.env.NODE_ENV = 'test';

// Set default environment variables for testing
process.env.ALTWALLET_API_KEY = 'test_api_key';
process.env.ORCA_ENDPOINT = 'https://test-api.orca.com';
process.env.REQUEST_TIMEOUT = '5000';

// Increase timeout for async operations
jest.setTimeout(10000);
