/**
 * Basic usage example for the AltWallet Node.js SDK.
 */

const { AltWalletClient, createClient, quote, decision } = require('../dist/index');

async function main() {
    console.log('🚀 AltWallet Node.js SDK - Basic Usage Example');
    console.log('='.repeat(50));
    
    // Configure the SDK
    const config = {
        apiEndpoint: 'http://localhost:8000',
        apiKey: 'your-api-key-here', // Optional
        timeout: 30,
        retryAttempts: 3,
        logLevel: 'INFO'
    };
    
    // Create client
    const client = new AltWalletClient(config);
    
    try {
        // Initialize the client
        console.log('📡 Initializing client...');
        await client.initialize();
        console.log('✅ Client initialized successfully');
        
        // Prepare request data
        const cart = {
            items: [
                {
                    itemId: 'item_123',
                    name: 'Grocery Items',
                    unitPrice: 45.99,
                    quantity: 1,
                    category: 'groceries',
                    mcc: '5411'
                }
            ],
            currency: 'USD',
            totalAmount: 45.99
        };
        
        const customer = {
            customerId: 'cust_12345',
            loyaltyTier: 'SILVER',
            preferredCards: ['amex_gold', 'chase_freedom']
        };
        
        const context = {
            merchantId: 'grocery_store_123',
            merchantName: 'Local Grocery Store',
            deviceType: 'mobile',
            ipAddress: '192.168.1.100'
        };
        
        // Get card recommendations
        console.log('\n💳 Getting card recommendations...');
        const response = await client.quote(cart, customer, context);
        
        console.log(`✅ Received ${response.recommendations.length} recommendations`);
        console.log(`📊 Transaction Score: ${response.score.toFixed(2)}`);
        console.log(`⏱️  Processing Time: ${response.processingTimeMs}ms`);
        
        // Display recommendations
        console.log('\n🎯 Top Recommendations:');
        response.recommendations.slice(0, 3).forEach((rec, i) => {
            console.log(`${i + 1}. ${rec.cardName} (${rec.issuer})`);
            console.log(`   Approval Probability: ${(rec.approvalProbability * 100).toFixed(1)}%`);
            console.log(`   Expected Rewards: ${(rec.expectedRewards * 100).toFixed(1)}%`);
            console.log(`   Utility Score: ${rec.utilityScore.toFixed(2)}`);
            if (rec.reasoning) {
                console.log(`   Reasoning: ${rec.reasoning}`);
            }
            console.log();
        });
        
        // Get decision details
        console.log('🔍 Getting decision details...');
        const decisionResponse = await client.decision(response.requestId);
        
        console.log(`✅ Decision: ${decisionResponse.decision}`);
        console.log(`🎯 Confidence: ${(decisionResponse.confidence * 100).toFixed(1)}%`);
        console.log(`💭 Reasoning: ${decisionResponse.reasoning}`);
        
        // Health check
        console.log('\n🏥 Checking API health...');
        const health = await client.healthCheck();
        console.log(`Status: ${health.status || 'unknown'}`);
        
        // Get metrics
        console.log('\n📈 Client Metrics:');
        const metrics = client.getMetrics();
        console.log(`Requests: ${metrics.requestCount}`);
        console.log(`Errors: ${metrics.errorCount}`);
        console.log(`Error Rate: ${(metrics.errorRate * 100).toFixed(1)}%`);
        console.log(`Avg Latency: ${metrics.averageLatencyMs.toFixed(1)}ms`);
        
    } catch (error) {
        console.error(`❌ Error: ${error.message}`);
        if (error.details) {
            console.error('Details:', error.details);
        }
    } finally {
        // Cleanup
        await client.cleanup();
        console.log('\n🧹 Client cleaned up');
    }
}

// Convenience function example
async function convenienceExample() {
    console.log('\n🔄 Convenience Function Example');
    console.log('='.repeat(40));
    
    try {
        const cart = {
            items: [
                {
                    itemId: 'item_456',
                    name: 'Electronics',
                    unitPrice: 299.99,
                    quantity: 1,
                    category: 'electronics',
                    mcc: '5732'
                }
            ],
            currency: 'USD',
            totalAmount: 299.99
        };
        
        const customer = {
            customerId: 'cust_67890',
            loyaltyTier: 'GOLD'
        };
        
        const context = {
            merchantId: 'electronics_store_456',
            deviceType: 'desktop'
        };
        
        // Use convenience function
        const response = await quote(cart, customer, context, {
            apiEndpoint: 'http://localhost:8000'
        });
        
        console.log(`✅ Quote received: ${response.recommendations.length} recommendations`);
        console.log(`Best card: ${response.recommendations[0]?.cardName}`);
        
        // Get decision using convenience function
        const decisionResponse = await decision(response.requestId, {
            apiEndpoint: 'http://localhost:8000'
        });
        
        console.log(`Decision: ${decisionResponse.decision}`);
        
    } catch (error) {
        console.error(`❌ Convenience function error: ${error.message}`);
    }
}

// Run examples
if (require.main === module) {
    main()
        .then(() => convenienceExample())
        .catch(console.error);
}
