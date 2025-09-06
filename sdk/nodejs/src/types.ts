/**
 * Type definitions for the AltWallet Node.js SDK.
 * These types match the OpenAPI specification for consistency.
 */

export interface SDKConfig {
  /** AltWallet API endpoint URL */
  apiEndpoint?: string;
  /** API key for authentication */
  apiKey?: string;
  /** Request timeout in seconds */
  timeout?: number;
  /** Number of retry attempts for failed requests */
  retryAttempts?: number;
  /** Delay between retry attempts in seconds */
  retryDelay?: number;
  /** HTTP connection pool size */
  connectionPoolSize?: number;
  /** Enable HTTP keep-alive */
  keepAlive?: boolean;
  /** Logging level */
  logLevel?: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  /** Enable SDK logging */
  enableLogging?: boolean;
}

export interface CartItem {
  /** Unique item identifier */
  itemId: string;
  /** Item name */
  name: string;
  /** Unit price of the item */
  unitPrice: number;
  /** Quantity of the item */
  quantity: number;
  /** Item category */
  category?: string;
  /** Merchant category code */
  mcc?: string;
}

export interface Cart {
  /** List of cart items */
  items: CartItem[];
  /** Currency code */
  currency?: string;
  /** Total cart amount */
  totalAmount?: number;
  /** Tax amount */
  taxAmount?: number;
  /** Shipping amount */
  shippingAmount?: number;
}

export interface Customer {
  /** Unique customer identifier */
  customerId: string;
  /** Customer loyalty tier */
  loyaltyTier?: string;
  /** Preferred card IDs */
  preferredCards?: string[];
  /** Customer risk profile */
  riskProfile?: string;
  /** Customer location */
  location?: {
    city?: string;
    state?: string;
    country?: string;
  };
}

export interface Context {
  /** Merchant identifier */
  merchantId: string;
  /** Merchant name */
  merchantName?: string;
  /** Device type (mobile, desktop, etc.) */
  deviceType?: string;
  /** User agent string */
  userAgent?: string;
  /** Customer IP address */
  ipAddress?: string;
  /** Session identifier */
  sessionId?: string;
  /** Referrer URL */
  referrer?: string;
  /** Marketing campaign ID */
  campaignId?: string;
}

export interface QuoteRequest {
  /** Shopping cart information */
  cart: Cart;
  /** Customer information */
  customer: Customer;
  /** Transaction context */
  context: Context;
  /** Unique request identifier */
  requestId?: string;
}

export interface Recommendation {
  /** Unique card identifier */
  cardId: string;
  /** Card name */
  cardName: string;
  /** Card issuer */
  issuer: string;
  /** Recommendation rank (1 = best) */
  rank: number;
  /** Probability of approval (0.0-1.0) */
  approvalProbability: number;
  /** Expected rewards rate */
  expectedRewards: number;
  /** Overall utility score */
  utilityScore: number;
  /** Human-readable reasoning */
  reasoning?: string;
  /** Feature attributions */
  features?: Record<string, any>;
}

export interface QuoteResponse {
  /** Unique request identifier */
  requestId: string;
  /** Transaction identifier */
  transactionId: string;
  /** Overall transaction score */
  score: number;
  /** Processing status */
  status: string;
  /** Card recommendations */
  recommendations: Recommendation[];
  /** Processing time in milliseconds */
  processingTimeMs: number;
  /** Response timestamp */
  timestamp: string;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

export interface DecisionRequest {
  /** Request identifier to look up */
  requestId: string;
}

export interface DecisionResponse {
  /** Request identifier */
  requestId: string;
  /** Transaction identifier */
  transactionId: string;
  /** Decision result */
  decision: string;
  /** Decision confidence (0.0-1.0) */
  confidence: number;
  /** Decision reasoning */
  reasoning: string;
  /** Identified risk factors */
  riskFactors?: string[];
  /** Decision timestamp */
  timestamp: string;
  /** Additional metadata */
  metadata?: Record<string, any>;
}

export interface ErrorResponse {
  /** Error code */
  errorCode: string;
  /** Error message */
  errorMessage: string;
  /** Request identifier */
  requestId?: string;
  /** Error timestamp */
  timestamp: string;
  /** Additional error details */
  details?: Record<string, any>;
}

export interface HealthResponse {
  /** Health status */
  status: string;
  /** Service version */
  version?: string;
  /** Timestamp */
  timestamp: string;
  /** Additional health information */
  details?: Record<string, any>;
}

export interface Metrics {
  /** Number of requests made */
  requestCount: number;
  /** Number of errors encountered */
  errorCount: number;
  /** Error rate (0.0-1.0) */
  errorRate: number;
  /** Average latency in milliseconds */
  averageLatencyMs: number;
  /** Whether client is initialized */
  initialized: boolean;
}

export interface RequestOptions {
  /** Request timeout in milliseconds */
  timeout?: number;
  /** Custom headers */
  headers?: Record<string, string>;
  /** Request ID for tracing */
  requestId?: string;
}
