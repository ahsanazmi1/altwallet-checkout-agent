# AltWallet Checkout Agent API - OpenAPI 3.0.3 Specification

## Overview

This directory contains the OpenAPI 3.0.3 specification for the AltWallet Checkout Agent API, which provides intelligent checkout processing and card recommendations.

## Files

- `openapi.yaml` - Complete OpenAPI 3.0.3 specification
- `README.md` - This documentation file

## API Endpoints

### Core Endpoints

#### POST /v1/score
Process a checkout request and return scored card recommendations with:
- Approval probabilities (p_approval)
- Expected rewards rates
- Utility scores
- Explainability information
- Audit trails

**Input**: Context object containing cart items, merchant info, customer data, device context, and geographic location
**Output**: Ranked card recommendations with detailed metrics

#### POST /v1/explain
Get full feature attributions for transaction transparency:
- Risk factor analysis
- Feature contribution breakdown
- Composite scoring components
- No card ranking (focus on explainability)

**Input**: Same Context object as /v1/score
**Output**: Detailed feature attributions and scoring breakdown

### Health & Monitoring

#### GET /v1/healthz
Health check endpoint returning:
- Service status
- Uptime information
- Version details
- Error information (if unhealthy)

#### GET /v1/version
Version information endpoint returning:
- API version
- Build date and git SHA
- Component versions
- OpenAPI specification version

### Documentation

#### GET /docs
Interactive API documentation (Swagger UI)

#### GET /openapi.json
OpenAPI specification in JSON format

## Data Models

### Core Schemas

- **Context**: Complete transaction context with cart, merchant, customer, device, and geo information
- **Cart**: Shopping cart with items and currency
- **CartItem**: Individual cart items with pricing and category information
- **Merchant**: Merchant information including MCC and network preferences
- **Customer**: Customer data including loyalty tier and transaction history
- **Device**: Device information including IP and location
- **Geo**: Geographic location data

### Response Schemas

- **ScoreResponse**: Card recommendations with utility scores and explainability
- **Recommendation**: Individual card recommendation with detailed metrics
- **ExplainResponse**: Feature attributions and scoring breakdown
- **HealthResponse**: Health check response
- **VersionResponse**: Version information response

### Supporting Schemas

- **ExplainabilityInfo**: Explainability data with baseline, contributions, and drivers
- **AuditInfo**: Audit trail information
- **Attribution**: Feature contribution details
- **Driver**: Top feature drivers
- **RiskFactor**: Risk factor analysis
- **FeatureContribution**: Feature contribution analysis
- **CompositeScores**: Composite scoring components

## Usage Examples

### Basic Scoring Request

```bash
curl -X POST "http://localhost:8080/v1/score" \
  -H "Content-Type: application/json" \
  -d '{
    "context_data": {
      "cart": {
        "items": [
          {
            "item": "Wireless Headphones",
            "unit_price": "199.99",
            "qty": 1,
            "mcc": "5734"
          }
        ],
        "currency": "USD"
      },
      "merchant": {
        "name": "Best Buy",
        "mcc": "5734",
        "network_preferences": ["visa", "mc"]
      },
      "customer": {
        "id": "cust_12345",
        "loyalty_tier": "GOLD",
        "historical_velocity_24h": 3,
        "chargebacks_12m": 0
      },
      "device": {
        "ip": "192.168.1.100",
        "device_id": "dev_abc123"
      },
      "geo": {
        "city": "San Francisco",
        "country": "US"
      }
    }
  }'
```

### Explainability Request

```bash
curl -X POST "http://localhost:8080/v1/explain" \
  -H "Content-Type: application/json" \
  -d '{
    "context_data": {
      // Same context structure as scoring request
    }
  }'
```

## Validation

The OpenAPI specification has been validated using `@apidevtools/swagger-cli`:

```bash
swagger-cli validate openapi/openapi.yaml
```

## Implementation Status

✅ **Completed**:
- OpenAPI 3.0.3 specification with info.version: "1.0.0"
- POST /v1/score endpoint with full Context input and Recommendation output
- POST /v1/explain endpoint with feature attributions
- GET /v1/healthz and GET /v1/version endpoints
- Complete component schemas for all data models
- /docs and /openapi.json endpoints served
- Specification validation passed
- API implementation with FastAPI
- Test script demonstrating all endpoints

## Key Features

1. **Comprehensive Data Models**: All schemas are fully defined with examples and validation rules
2. **Explainability**: Built-in transparency with feature attributions and scoring breakdown
3. **Audit Trail**: Complete audit information for compliance and debugging
4. **Health Monitoring**: Robust health and version endpoints
5. **Interactive Documentation**: Swagger UI for easy API exploration
6. **Validation**: OpenAPI specification validated and tested

## Testing

Run the test script to verify all endpoints:

```bash
python test_api.py
```

This will test all endpoints with sample data and display the responses.

## Server

The API server runs on `http://localhost:8080` and provides:

- Interactive documentation at `/docs`
- OpenAPI JSON at `/openapi.json`
- All v1 endpoints as specified in the OpenAPI specification
