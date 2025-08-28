const CheckoutAgent = require('../src/agent');

describe('CheckoutAgent', () => {
  let agent;

  beforeEach(() => {
    agent = new CheckoutAgent();
  });

  describe('initialization', () => {
    test('should initialize successfully', async () => {
      await expect(agent.initialize()).resolves.toBe(true);
      expect(agent.status).toBe('ready');
    });

    test('should load configuration', async () => {
      await agent.initialize();
      expect(agent.config).toBeDefined();
      expect(agent.config.endpoint).toBeDefined();
    });
  });

  describe('transaction processing', () => {
    beforeEach(async () => {
      await agent.initialize();
    });

    test('should process valid transaction', async () => {
      const transactionData = {
        amount: 100.00,
        currency: 'USD',
        merchantId: 'merchant_123'
      };

      const result = await agent.processCheckout(transactionData);
      
      expect(result.success).toBe(true);
      expect(result.transactionId).toBeDefined();
      expect(result.message).toBe('Payment processed successfully');
    });

    test('should reject invalid transaction data', async () => {
      const invalidData = {
        amount: -50,
        currency: 'USD',
        merchantId: 'merchant_123'
      };

      await expect(agent.processCheckout(invalidData)).rejects.toThrow('Amount must be greater than 0');
    });

    test('should reject transaction with missing fields', async () => {
      const incompleteData = {
        amount: 100,
        currency: 'USD'
        // missing merchantId
      };

      await expect(agent.processCheckout(incompleteData)).rejects.toThrow('Missing required field: merchantId');
    });
  });

  describe('transaction status', () => {
    beforeEach(async () => {
      await agent.initialize();
    });

    test('should return transaction status', async () => {
      const transactionData = {
        amount: 100.00,
        currency: 'USD',
        merchantId: 'merchant_123'
      };

      const result = await agent.processCheckout(transactionData);
      const status = agent.getTransactionStatus(result.transactionId);
      
      expect(status).toBeDefined();
      expect(status.id).toBe(result.transactionId);
      expect(status.status).toBe('completed');
    });

    test('should return null for non-existent transaction', () => {
      const status = agent.getTransactionStatus('non_existent_id');
      expect(status).toBeNull();
    });
  });

  describe('agent status', () => {
    test('should return agent status', () => {
      const status = agent.getStatus();
      
      expect(status).toBeDefined();
      expect(status.status).toBe('idle');
      expect(status.activeTransactions).toBe(0);
      expect(status.uptime).toBeDefined();
    });
  });
});
