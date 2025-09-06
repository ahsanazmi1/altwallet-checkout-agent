/**
 * AltWallet Checkout Agent Node.js SDK
 * 
 * This SDK provides a Node.js client for integrating with the AltWallet Checkout Agent
 * to get intelligent card recommendations and transaction scoring.
 */

export { AltWalletClient, createClient, quote, decision } from './client';
export {
  SDKConfig,
  CartItem,
  Cart,
  Customer,
  Context,
  QuoteRequest,
  QuoteResponse,
  DecisionRequest,
  DecisionResponse,
  Recommendation,
  ErrorResponse,
  HealthResponse,
  Metrics,
  RequestOptions,
} from './types';
export {
  AltWalletError,
  ConfigurationError,
  NetworkError,
  AuthenticationError,
  ValidationError,
  RateLimitError,
  APIError,
} from './exceptions';

// Version information
export const VERSION = '1.0.0';
export const SDK_NAME = 'altwallet-nodejs-sdk';