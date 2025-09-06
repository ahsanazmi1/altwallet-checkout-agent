/**
 * Custom exceptions for the AltWallet Node.js SDK.
 */

export class AltWalletError extends Error {
  public readonly errorCode?: string;
  public readonly requestId?: string;
  public readonly details?: Record<string, any>;

  constructor(
    message: string,
    errorCode?: string,
    requestId?: string,
    details?: Record<string, any>
  ) {
    super(message);
    this.name = 'AltWalletError';
    this.errorCode = errorCode;
    this.requestId = requestId;
    this.details = details || {};

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AltWalletError);
    }
  }

  toString(): string {
    const parts = [this.message];
    if (this.errorCode) {
      parts.push(`(Code: ${this.errorCode})`);
    }
    if (this.requestId) {
      parts.push(`(Request ID: ${this.requestId})`);
    }
    return parts.join(' ');
  }
}

export class ConfigurationError extends AltWalletError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'CONFIGURATION_ERROR', undefined, details);
    this.name = 'ConfigurationError';
  }
}

export class NetworkError extends AltWalletError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'NETWORK_ERROR', undefined, details);
    this.name = 'NetworkError';
  }
}

export class AuthenticationError extends AltWalletError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'AUTHENTICATION_ERROR', undefined, details);
    this.name = 'AuthenticationError';
  }
}

export class ValidationError extends AltWalletError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'VALIDATION_ERROR', undefined, details);
    this.name = 'ValidationError';
  }
}

export class RateLimitError extends AltWalletError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'RATE_LIMIT_ERROR', undefined, details);
    this.name = 'RateLimitError';
  }
}

export class APIError extends AltWalletError {
  public readonly statusCode: number;

  constructor(
    message: string,
    statusCode: number,
    errorCode?: string,
    requestId?: string,
    details?: Record<string, any>
  ) {
    super(message, errorCode, requestId, details);
    this.name = 'APIError';
    this.statusCode = statusCode;
  }

  toString(): string {
    return `${super.toString()} (Status: ${this.statusCode})`;
  }
}
