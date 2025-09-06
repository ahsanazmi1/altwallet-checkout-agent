/**
 * Advanced usage example for the AltWallet Node.js SDK.
 */

const { AltWalletClient, createClient } = require('../dist/index');

class MerchantCheckoutService {
    constructor(config) {
        this.client = new AltWalletClient(config);
        this.initialized = false;
    }

    async initialize() {
        await this.client.initialize();
        this.initialized = true;
        console.log('✅ Merchant checkout service initialized');
    }

    async processCheckout(cartData, customerData, contextData) {
        if (!this.initialized) {
            await this.initialize();
        }

        try {
            const response = await this.client.quote(cartData, customerData, contextData);
            
            const recommendations = response.recommendations.map(rec => ({
                cardId: rec.cardId,
                cardName: rec.cardName,
                issuer: rec.issuer,
                rank: rec.rank,
                approvalProbability: rec.approvalProbability,
                expectedRewards: rec.expectedRewards,
                utilityScore: rec.utilityScore,
                reasoning: rec.reasoning
            }));

            return {
                success: true,
                transactionId: response.transactionId,
                requestId: response.requestId,
                score: response.score,
                recommendations,
                bestCard: recommendations[0] || null,
                processingTimeMs: response.processingTimeMs
            };
        } catch (error) {
            return {
                success: false,
                error: error.name || 'unknown_error',
                message: error.message,
                details: error.details || null,
                statusCode: error.statusCode || null
            };
        }
    }

    async getDecisionDetails(requestId) {
        try {
            const decision = await this.client.decision(requestId);
            return {
                success: true,
                decision: decision.decision,
                confidence: decision.confidence,
                reasoning: decision.reasoning,
                riskFactors: decision.riskFactors
            };
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    async healthCheck() {
        try {
            const health = await this.client.healthCheck();
            const metrics = this.client.getMetrics();
            
            return {
                status: 'healthy',
                apiHealth: health,
                clientMetrics: metrics
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message
            };
        }
    }

    async cleanup() {
        await this.client.cleanup();
        console.log('🧹 Merchant checkout service cleaned up');
    }
}

async function advancedExample() {
    console.log('🚀 AltWallet Node.js SDK - Advanced Usage Example');
    console.log('='.repeat(60));
    
    // Configure SDK with custom settings
    const config = {
        apiEndpoint: 'http://localhost:8000',
        timeout: 60,
        retryAttempts: 5,
        retryDelay: 2.0,
        connectionPoolSize: 20,
        logLevel: 'DEBUG'
    };
    
    // Create merchant service
    const service = new MerchantCheckoutService(config);
    
    try {
        // Initialize service
        await service.initialize();
        
        // Example checkout scenarios
        const scenarios = [
            {
                name: 'Grocery Purchase',
                cart: {
                    items: [
                        {
                            itemId: 'grocery_001',
                            name: 'Organic Groceries',
                            unitPrice: 85.50,
                            quantity: 1,
                            category: 'groceries',
                            mcc: '5411'
                        }
                    ],
                    currency: 'USD',
                    totalAmount: 85.50
                },
                customer: {
                    customerId: 'cust_grocery_001',
                    loyaltyTier: 'GOLD',
                    preferredCards: ['amex_gold', 'chase_sapphire']
                },
                context: {
                    merchantId: 'organic_grocery_123',
                    merchantName: 'Organic Grocery Store',
                    deviceType: 'mobile',
                    ipAddress: '192.168.1.100'
                }
            },
            {
                name: 'Electronics Purchase',
                cart: {
                    items: [
                        {
                            itemId: 'electronics_001',
                            name: 'High-End Laptop',
                            unitPrice: 1299.99,
                            quantity: 1,
                            category: 'electronics',
                            mcc: '5732'
                        }
                    ],
                    currency: 'USD',
                    totalAmount: 1299.99
                },
                customer: {
                    customerId: 'cust_electronics_001',
                    loyaltyTier: 'SILVER',
                    preferredCards: ['chase_freedom', 'citi_double_cash']
                },
                context: {
                    merchantId: 'electronics_store_456',
                    merchantName: 'Electronics Store',
                    deviceType: 'desktop',
                    ipAddress: '192.168.1.200'
                }
            },
            {
                name: 'Gas Station',
                cart: {
                    items: [
                        {
                            itemId: 'gas_001',
                            name: 'Gasoline',
                            unitPrice: 25.00,
                            quantity: 1,
                            category: 'gas',
                            mcc: '5541'
                        }
                    ],
                    currency: 'USD',
                    totalAmount: 25.00
                },
                customer: {
                    customerId: 'cust_gas_001',
                    loyaltyTier: 'BRONZE',
                    preferredCards: ['chase_freedom_unlimited']
                },
                context: {
                    merchantId: 'gas_station_789',
                    merchantName: 'Local Gas Station',
                    deviceType: 'mobile',
                    ipAddress: '192.168.1.300'
                }
            }
        ];
        
        // Process each scenario
        const results = [];
        for (const scenario of scenarios) {
            console.log(`\n🛒 Processing: ${scenario.name}`);
            console.log('-'.repeat(40));
            
            const result = await service.processCheckout(
                scenario.cart,
                scenario.customer,
                scenario.context
            );
            
            results.push({
                scenario: scenario.name,
                result
            });
            
            if (result.success) {
                console.log(`✅ Success! Transaction ID: ${result.transactionId}`);
                console.log(`📊 Score: ${result.score.toFixed(2)}`);
                if (result.bestCard) {
                    const best = result.bestCard;
                    console.log(`🎯 Best Card: ${best.cardName}`);
                    console.log(`   Approval: ${(best.approvalProbability * 100).toFixed(1)}%`);
                    console.log(`   Rewards: ${(best.expectedRewards * 100).toFixed(1)}%`);
                }
                
                // Get decision details
                const decision = await service.getDecisionDetails(result.requestId);
                if (decision.success) {
                    console.log(`🔍 Decision: ${decision.decision} (Confidence: ${(decision.confidence * 100).toFixed(1)}%)`);
                }
            } else {
                console.log(`❌ Failed: ${result.message}`);
            }
        }
        
        // Summary
        console.log('\n📊 Summary');
        console.log('='.repeat(30));
        const successful = results.filter(r => r.result.success).length;
        const total = results.length;
        console.log(`Successful: ${successful}/${total}`);
        
        // Health check
        console.log('\n🏥 Service Health Check');
        console.log('-'.repeat(30));
        const health = await service.healthCheck();
        console.log(`Status: ${health.status}`);
        if (health.status === 'healthy') {
            const metrics = health.clientMetrics;
            console.log(`Requests: ${metrics.requestCount}`);
            console.log(`Error Rate: ${(metrics.errorRate * 100).toFixed(1)}%`);
            console.log(`Avg Latency: ${metrics.averageLatencyMs.toFixed(1)}ms`);
        }
        
    } catch (error) {
        console.error(`❌ Unexpected error: ${error.message}`);
    } finally {
        await service.cleanup();
    }
}

async function batchProcessingExample() {
    console.log('\n🔄 Batch Processing Example');
    console.log('='.repeat(40));
    
    const config = {
        apiEndpoint: 'http://localhost:8000',
        connectionPoolSize: 50, // Higher for batch processing
        timeout: 120
    };
    
    const service = new MerchantCheckoutService(config);
    await service.initialize();
    
    try {
        // Create multiple requests
        const requests = [];
        for (let i = 0; i < 5; i++) {
            requests.push({
                cart: {
                    items: [
                        {
                            itemId: `item_${i.toString().padStart(3, '0')}`,
                            name: `Product ${i}`,
                            unitPrice: 10.0 + i * 5,
                            quantity: 1,
                            category: 'general'
                        }
                    ],
                    currency: 'USD',
                    totalAmount: 10.0 + i * 5
                },
                customer: {
                    customerId: `cust_${i.toString().padStart(3, '0')}`,
                    loyaltyTier: 'SILVER'
                },
                context: {
                    merchantId: `merchant_${i.toString().padStart(3, '0')}`,
                    deviceType: 'mobile'
                }
            });
        }
        
        // Process requests concurrently
        console.log(`🚀 Processing ${requests.length} requests concurrently...`);
        const tasks = requests.map(req => 
            service.processCheckout(req.cart, req.customer, req.context)
        );
        
        const results = await Promise.allSettled(tasks);
        
        // Process results
        let successful = 0;
        results.forEach((result, i) => {
            if (result.status === 'fulfilled' && result.value.success) {
                successful++;
                console.log(`Request ${i}: ✅ Success - Score: ${result.value.score.toFixed(2)}`);
            } else if (result.status === 'rejected') {
                console.log(`Request ${i}: ❌ Error - ${result.reason.message}`);
            } else {
                console.log(`Request ${i}: ❌ Failed - ${result.value.message}`);
            }
        });
        
        console.log(`\n📊 Batch Results: ${successful}/${requests.length} successful`);
        
    } finally {
        await service.cleanup();
    }
}

async function errorHandlingExample() {
    console.log('\n⚠️  Error Handling Example');
    console.log('='.repeat(40));
    
    const service = new MerchantCheckoutService({
        apiEndpoint: 'http://localhost:8000'
    });
    
    try {
        await service.initialize();
        
        // Test validation error
        console.log('Testing validation error...');
        const invalidResult = await service.processCheckout(
            { items: [] }, // Invalid cart
            { customerId: 'test' },
            { merchantId: 'test' }
        );
        
        if (!invalidResult.success) {
            console.log(`✅ Caught validation error: ${invalidResult.message}`);
        }
        
        // Test network error (invalid endpoint)
        console.log('\nTesting network error...');
        const networkService = new MerchantCheckoutService({
            apiEndpoint: 'http://invalid-endpoint:9999'
        });
        
        try {
            await networkService.initialize();
        } catch (error) {
            console.log(`✅ Caught network error: ${error.message}`);
        }
        
    } finally {
        await service.cleanup();
    }
}

// Run examples
if (require.main === module) {
    advancedExample()
        .then(() => batchProcessingExample())
        .then(() => errorHandlingExample())
        .catch(console.error);
}
