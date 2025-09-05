# AltWallet Node.js SDK

The AltWallet Node.js SDK provides a simple and powerful way to integrate with the AltWallet Checkout Agent to get intelligent card recommendations and transaction scoring.

## Features

- 🚀 **Easy Integration**: Simple API for getting card recommendations
- 🔄 **Async/Await Support**: Full async/await support for modern Node.js applications
- 🛡️ **Error Handling**: Comprehensive error handling with custom exceptions
- 📊 **Metrics**: Built-in performance metrics and monitoring
- 🔧 **Configurable**: Flexible configuration options for different environments
- 📝 **TypeScript Support**: Full TypeScript definitions and type safety
- 🔍 **Logging**: Structured logging with configurable levels

## Installation

```bash
npm install altwallet-sdk
```

## Quick Start

### Basic Usage

```javascript
const { AltWalletClient } = require('altwallet-sdk');

async function main() {
    // Configure the SDK
    const config = {
        apiEndpoint: 'http://localhost:8000',
        apiKey: 'your-api-key-here', // Optional
        timeout: 30
    };
    
    // Create and initialize client
    const client = new AltWalletClient(config);
    await client.initialize();
    
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
    const response = await client.quote(cart, customer, context);
    
    console.log(`Received ${response.recommendations.length} recommendations`);
    console.log(`Transaction Score: ${response.score.toFixed(2)}`);
    
    // Display top recommendations
    response.recommendations.slice(0, 3).forEach((rec, i) => {
        console.log(`${i + 1}. ${rec.cardName} (${rec.issuer})`);
        console.log(`   Approval: ${(rec.approvalProbability * 100).toFixed(1)}%`);
        console.log(`   Rewards: ${(rec.expectedRewards * 100).toFixed(1)}%`);
    });
    
    // Get decision details
    const decision = await client.decision(response.requestId);
    console.log(`Decision: ${decision.decision} (Confidence: ${(decision.confidence * 100).toFixed(1)}%)`);
    
    // Cleanup
    await client.cleanup();
}

main().catch(console.error);
```

### TypeScript Usage

```typescript
import { AltWalletClient, SDKConfig, QuoteRequest, QuoteResponse } from 'altwallet-sdk';

async function main(): Promise<void> {
    const config: SDKConfig = {
        apiEndpoint: 'http://localhost:8000',
        apiKey: 'your-api-key-here',
        timeout: 30
    };
    
    const client = new AltWalletClient(config);
    await client.initialize();
    
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
        loyaltyTier: 'SILVER'
    };
    
    const context = {
        merchantId: 'grocery_store_123',
        deviceType: 'mobile'
    };
    
    const response: QuoteResponse = await client.quote(cart, customer, context);
    console.log(`Score: ${response.score}`);
    
    await client.cleanup();
}
```

### Convenience Functions

```javascript
const { quote, decision } = require('altwallet-sdk');

// Simple quote request
const response = await quote(cart, customer, context);

// Get decision details
const decisionResponse = await decision(response.requestId);
```

## API Reference

### AltWalletClient

The main client class for interacting with the AltWallet API.

#### Constructor

```javascript
const client = new AltWalletClient(config: SDKConfig);
```

#### Methods

##### `initialize(): Promise<void>`

Initialize the client and test the connection to the API.

```javascript
await client.initialize();
```

##### `quote(cart, customer, context, requestId?): Promise<QuoteResponse>`

Get card recommendations for a transaction.

**Parameters:**
- `cart`: Shopping cart information
- `customer`: Customer information  
- `context`: Transaction context
- `requestId`: Optional request identifier

**Returns:** `Promise<QuoteResponse>` with card recommendations

##### `decision(requestId): Promise<DecisionResponse>`

Get decision details for a previous request.

**Parameters:**
- `requestId`: Request identifier to look up

**Returns:** `Promise<DecisionResponse>` with decision details

##### `healthCheck(): Promise<HealthResponse>`

Check API health status.

**Returns:** `Promise<HealthResponse>` with health status information

##### `getMetrics(): Metrics`

Get client performance metrics.

**Returns:** `Metrics` object with performance metrics including request count, error rate, and latency

##### `cleanup(): Promise<void>`

Cleanup client resources.

```javascript
await client.cleanup();
```

### Data Models

#### Cart

```typescript
interface Cart {
    items: CartItem[];
    currency?: string;
    totalAmount?: number;
    taxAmount?: number;
    shippingAmount?: number;
}

interface CartItem {
    itemId: string;
    name: string;
    unitPrice: number;
    quantity: number;
    category?: string;
    mcc?: string;
}
```

#### Customer

```typescript
interface Customer {
    customerId: string;
    loyaltyTier?: string;
    preferredCards?: string[];
    riskProfile?: string;
    location?: {
        city?: string;
        state?: string;
        country?: string;
    };
}
```

#### Context

```typescript
interface Context {
    merchantId: string;
    merchantName?: string;
    deviceType?: string;
    userAgent?: string;
    ipAddress?: string;
    sessionId?: string;
    referrer?: string;
    campaignId?: string;
}
```

#### QuoteResponse

```typescript
interface QuoteResponse {
    requestId: string;
    transactionId: string;
    score: number;
    status: string;
    recommendations: Recommendation[];
    processingTimeMs: number;
    timestamp: string;
    metadata?: Record<string, any>;
}

interface Recommendation {
    cardId: string;
    cardName: string;
    issuer: string;
    rank: number;
    approvalProbability: number;
    expectedRewards: number;
    utilityScore: number;
    reasoning?: string;
    features?: Record<string, any>;
}
```

#### DecisionResponse

```typescript
interface DecisionResponse {
    requestId: string;
    transactionId: string;
    decision: string;
    confidence: number;
    reasoning: string;
    riskFactors?: string[];
    timestamp: string;
    metadata?: Record<string, any>;
}
```

### Configuration

#### SDKConfig

```typescript
interface SDKConfig {
    apiEndpoint?: string;        // Default: 'http://localhost:8000'
    apiKey?: string;            // Optional
    timeout?: number;           // Default: 30 seconds
    retryAttempts?: number;     // Default: 3
    retryDelay?: number;        // Default: 1.0 seconds
    connectionPoolSize?: number; // Default: 10
    keepAlive?: boolean;        // Default: true
    logLevel?: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR'; // Default: 'INFO'
    enableLogging?: boolean;    // Default: true
}
```

### Error Handling

The SDK provides custom exceptions for different error types:

```javascript
const {
    AltWalletError,
    ConfigurationError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    APIError
} = require('altwallet-sdk');

try {
    const response = await client.quote(cart, customer, context);
} catch (error) {
    if (error instanceof ValidationError) {
        console.log(`Validation error: ${error.message}`);
        console.log(`Details:`, error.details);
    } else if (error instanceof NetworkError) {
        console.log(`Network error: ${error.message}`);
    } else if (error instanceof APIError) {
        console.log(`API error: ${error.message} (Status: ${error.statusCode})`);
    } else if (error instanceof AltWalletError) {
        console.log(`AltWallet error: ${error.message}`);
    }
}
```

## Advanced Usage

### Batch Processing

```javascript
async function processMultipleRequests() {
    const client = new AltWalletClient(config);
    await client.initialize();
    
    try {
        // Create multiple requests
        const requests = [
            { cart: cart1, customer: customer1, context: context1 },
            { cart: cart2, customer: customer2, context: context2 },
            { cart: cart3, customer: customer3, context: context3 }
        ];
        
        // Process concurrently
        const tasks = requests.map(req => 
            client.quote(req.cart, req.customer, req.context)
        );
        
        const responses = await Promise.allSettled(tasks);
        
        // Process results
        responses.forEach((response, i) => {
            if (response.status === 'fulfilled') {
                console.log(`Request ${i} success: ${response.value.score}`);
            } else {
                console.log(`Request ${i} failed: ${response.reason.message}`);
            }
        });
        
    } finally {
        await client.cleanup();
    }
}
```

### Custom Retry Logic

```javascript
const config = {
    retryAttempts: 5,
    retryDelay: 2.0, // Exponential backoff starts at 2 seconds
    timeout: 60
};
```

### Logging Configuration

```javascript
const config = {
    logLevel: 'DEBUG', // DEBUG, INFO, WARN, ERROR
    enableLogging: true
};
```

### Performance Monitoring

```javascript
// Get metrics after processing requests
const metrics = client.getMetrics();
console.log(`Requests: ${metrics.requestCount}`);
console.log(`Error Rate: ${(metrics.errorRate * 100).toFixed(1)}%`);
console.log(`Avg Latency: ${metrics.averageLatencyMs.toFixed(1)}ms`);
```

### Express.js Integration

```javascript
const express = require('express');
const { AltWalletClient } = require('altwallet-sdk');

const app = express();
app.use(express.json());

// Initialize client once
const client = new AltWalletClient({
    apiEndpoint: process.env.ALTWALLET_API_ENDPOINT,
    apiKey: process.env.ALTWALLET_API_KEY
});

await client.initialize();

// API endpoint
app.post('/api/checkout', async (req, res) => {
    try {
        const { cart, customer, context } = req.body;
        const response = await client.quote(cart, customer, context);
        res.json(response);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(3000);
```

## Examples

See the `examples/` directory for complete working examples:

- `basic_usage.js` - Simple integration example
- `advanced_usage.js` - Advanced features and error handling

## Requirements

- Node.js 16.0+
- axios >= 1.6.0
- uuid >= 9.0.0

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/altwallet/checkout-agent.git
cd checkout-agent/sdk/nodejs

# Install dependencies
npm install

# Build the project
npm run build

# Run tests
npm test

# Run linting
npm run lint
```

### TypeScript

The SDK is written in TypeScript and includes full type definitions. You can use it in TypeScript projects without additional type packages.

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- Issues: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- Email: team@altwallet.com
