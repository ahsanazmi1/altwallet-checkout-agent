/**
 * Main client for the AltWallet Node.js SDK.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { v4 as uuidv4 } from 'uuid';

import {
  SDKConfig,
  QuoteRequest,
  QuoteResponse,
  DecisionRequest,
  DecisionResponse,
  HealthResponse,
  Metrics,
  RequestOptions,
} from './types';

import {
  AltWalletError,
  ConfigurationError,
  NetworkError,
  AuthenticationError,
  ValidationError,
  RateLimitError,
  APIError,
} from './exceptions';

export class AltWalletClient {
  private config: Required<SDKConfig>;
  private client: AxiosInstance;
  private initialized: boolean = false;
  private requestCount: number = 0;
  private totalLatencyMs: number = 0;
  private errorCount: number = 0;

  constructor(config: SDKConfig = {}) {
    // Set default configuration
    this.config = {
      apiEndpoint: config.apiEndpoint || 'http://localhost:8000',
      apiKey: config.apiKey || '',
      timeout: config.timeout || 30,
      retryAttempts: config.retryAttempts || 3,
      retryDelay: config.retryDelay || 1.0,
      connectionPoolSize: config.connectionPoolSize || 10,
      keepAlive: config.keepAlive !== false,
      logLevel: config.logLevel || 'INFO',
      enableLogging: config.enableLogging !== false,
    };

    this.validateConfig();
    this.setupLogging();
    this.createHttpClient();

    this.log('info', 'AltWallet client initialized', {
      apiEndpoint: this.config.apiEndpoint,
      timeout: this.config.timeout,
    });
  }

  private validateConfig(): void {
    if (!this.config.apiEndpoint) {
      throw new ConfigurationError('API endpoint is required');
    }

    if (!this.config.apiEndpoint.startsWith('http://') && !this.config.apiEndpoint.startsWith('https://')) {
      throw new ConfigurationError('API endpoint must be a valid HTTP/HTTPS URL');
    }

    if (this.config.timeout <= 0) {
      throw new ConfigurationError('Timeout must be positive');
    }

    if (this.config.retryAttempts < 0) {
      throw new ConfigurationError('Retry attempts must be non-negative');
    }
  }

  private setupLogging(): void {
    if (!this.config.enableLogging) {
      return;
    }

    // Simple logging implementation
    // In production, you might want to use a proper logging library
    this.log = (level: string, message: string, data?: any) => {
      const timestamp = new Date().toISOString();
      const logEntry = {
        timestamp,
        level: level.toUpperCase(),
        message,
        ...(data && { data }),
      };

      if (level === 'error') {
        console.error(JSON.stringify(logEntry));
      } else if (level === 'warn') {
        console.warn(JSON.stringify(logEntry));
      } else if (level === 'info' && ['DEBUG', 'INFO'].includes(this.config.logLevel)) {
        console.log(JSON.stringify(logEntry));
      } else if (level === 'debug' && this.config.logLevel === 'DEBUG') {
        console.log(JSON.stringify(logEntry));
      }
    };
  }

  private log(level: string, message: string, data?: any): void {
    // Default no-op logger
  }

  private createHttpClient(): void {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': 'altwallet-nodejs-sdk/1.0.0',
      'Accept': 'application/json',
    };

    if (this.config.apiKey) {
      headers['Authorization'] = `Bearer ${this.config.apiKey}`;
    }

    this.client = axios.create({
      baseURL: this.config.apiEndpoint,
      timeout: this.config.timeout * 1000, // Convert to milliseconds
      headers,
      maxRedirects: 5,
      validateStatus: (status) => status < 500, // Don't throw for 4xx errors
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        this.log('debug', 'Making API request', {
          method: config.method?.toUpperCase(),
          url: config.url,
          requestId: config.headers['X-Request-ID'],
        });
        return config;
      },
      (error) => {
        this.log('error', 'Request interceptor error', { error: error.message });
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and metrics
    this.client.interceptors.response.use(
      (response) => {
        const latency = response.config.metadata?.endTime - response.config.metadata?.startTime;
        this.log('debug', 'API request completed', {
          status: response.status,
          latency: latency ? `${latency}ms` : 'unknown',
          requestId: response.config.headers['X-Request-ID'],
        });
        return response;
      },
      (error) => {
        this.log('error', 'API request failed', {
          error: error.message,
          status: error.response?.status,
          requestId: error.config?.headers['X-Request-ID'],
        });
        return Promise.reject(error);
      }
    );
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      await this.testConnection();
      this.initialized = true;
      this.log('info', 'AltWallet client initialized successfully');
    } catch (error) {
      this.log('error', 'Failed to initialize AltWallet client', { error: (error as Error).message });
      throw new ConfigurationError(`Failed to initialize client: ${(error as Error).message}`);
    }
  }

  private async testConnection(): Promise<void> {
    try {
      const response = await this.client.get('/health');
      if (response.status !== 200) {
        throw new NetworkError(`Health check failed with status ${response.status}`);
      }
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new NetworkError(`Failed to connect to API: ${error.message}`);
      }
      throw error;
    }
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST',
    endpoint: string,
    data?: any,
    options: RequestOptions = {}
  ): Promise<T> {
    if (!this.initialized) {
      await this.initialize();
    }

    const requestId = options.requestId || uuidv4();
    const startTime = Date.now();
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const config: AxiosRequestConfig = {
          method,
          url: endpoint,
          headers: {
            'X-Request-ID': requestId,
            ...options.headers,
          },
          ...(data && { data }),
          metadata: {
            startTime,
          },
        };

        this.log('info', 'Making API request', {
          method,
          endpoint,
          attempt: attempt + 1,
          requestId,
        });

        const response: AxiosResponse<T> = await this.client.request(config);

        // Update metrics
        const latency = Date.now() - startTime;
        this.requestCount++;
        this.totalLatencyMs += latency;

        // Handle response
        if (response.status === 200) {
          this.log('info', 'API request successful', {
            status: response.status,
            latency: `${latency}ms`,
            requestId,
          });
          return response.data;
        } else if (response.status === 401) {
          this.errorCount++;
          throw new AuthenticationError('Authentication failed');
        } else if (response.status === 422) {
          this.errorCount++;
          const errorData = response.data as any;
          throw new ValidationError(
            errorData.errorMessage || 'Validation failed',
            errorData.details
          );
        } else if (response.status === 429) {
          this.errorCount++;
          throw new RateLimitError('Rate limit exceeded');
        } else {
          this.errorCount++;
          const errorData = response.data as any;
          throw new APIError(
            errorData.errorMessage || `API error: ${response.status}`,
            response.status,
            errorData.errorCode,
            requestId,
            errorData.details
          );
        }
      } catch (error) {
        lastError = error as Error;

        // Don't retry certain errors
        if (
          error instanceof AuthenticationError ||
          error instanceof ValidationError ||
          error instanceof RateLimitError
        ) {
          throw error;
        }

        if (attempt < this.config.retryAttempts) {
          const delay = this.config.retryDelay * Math.pow(2, attempt); // Exponential backoff
          this.log('warn', 'Request failed, retrying', {
            attempt: attempt + 1,
            delay: `${delay}s`,
            error: lastError.message,
            requestId,
          });
          await this.sleep(delay * 1000);
        } else {
          this.log('error', 'All request attempts failed', {
            attempts: this.config.retryAttempts + 1,
            error: lastError.message,
            requestId,
          });
        }
      }
    }

    // If we get here, all retries failed
    if (axios.isAxiosError(lastError)) {
      throw new NetworkError(`Network error: ${lastError.message}`);
    } else {
      throw new AltWalletError(`Request failed: ${lastError?.message || 'Unknown error'}`);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async quote(
    cart: any,
    customer: any,
    context: any,
    requestId?: string
  ): Promise<QuoteResponse> {
    try {
      const quoteRequest: QuoteRequest = {
        cart,
        customer,
        context,
        requestId,
      };

      const response = await this.makeRequest<QuoteResponse>(
        'POST',
        '/v1/quote',
        quoteRequest,
        { requestId }
      );

      return response;
    } catch (error) {
      if (error instanceof AltWalletError) {
        throw error;
      }
      throw new AltWalletError(`Quote request failed: ${(error as Error).message}`);
    }
  }

  async decision(requestId: string): Promise<DecisionResponse> {
    try {
      const response = await this.makeRequest<DecisionResponse>(
        'GET',
        `/v1/decision/${requestId}`,
        undefined,
        { requestId }
      );

      return response;
    } catch (error) {
      if (error instanceof AltWalletError) {
        throw error;
      }
      throw new AltWalletError(`Decision request failed: ${(error as Error).message}`);
    }
  }

  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await this.makeRequest<HealthResponse>('GET', '/health');
      return response;
    } catch (error) {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        details: {
          error: (error as Error).message,
        },
      };
    }
  }

  getMetrics(): Metrics {
    return {
      requestCount: this.requestCount,
      errorCount: this.errorCount,
      errorRate: this.requestCount > 0 ? this.errorCount / this.requestCount : 0,
      averageLatencyMs: this.requestCount > 0 ? this.totalLatencyMs / this.requestCount : 0,
      initialized: this.initialized,
    };
  }

  async cleanup(): Promise<void> {
    // Cleanup any resources if needed
    this.initialized = false;
    this.log('info', 'AltWallet client cleaned up');
  }
}

// Convenience functions for easy usage
export async function createClient(config?: SDKConfig): Promise<AltWalletClient> {
  const client = new AltWalletClient(config);
  await client.initialize();
  return client;
}

export async function quote(
  cart: any,
  customer: any,
  context: any,
  config?: SDKConfig
): Promise<QuoteResponse> {
  const client = new AltWalletClient(config);
  await client.initialize();
  try {
    return await client.quote(cart, customer, context);
  } finally {
    await client.cleanup();
  }
}

export async function decision(
  requestId: string,
  config?: SDKConfig
): Promise<DecisionResponse> {
  const client = new AltWalletClient(config);
  await client.initialize();
  try {
    return await client.decision(requestId);
  } finally {
    await client.cleanup();
  }
}
