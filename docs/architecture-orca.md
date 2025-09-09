# Orca Architecture Overview

This document provides a comprehensive overview of the Orca ecosystem architecture, focusing on the Orca Checkout Agent and its integration with the broader Orca platform.

## 🐋 Orca Ecosystem

The Orca platform consists of several interconnected components that work together to provide intelligent payment processing and optimization:

### Core Components

#### 1. **Orca Checkout Agent** (This Repository)
- **Purpose**: Decisioning, routing hints, loyalty/risk signals for both in-person and online transactions
- **Responsibilities**:
  - Transaction scoring and risk assessment
  - Card recommendations with explainability
  - Feature attributions for transparency
  - Real-time decision making
  - Integration with merchant systems

#### 2. **Weave Core** (Referenced Service)
- **Purpose**: Processing core for auth/capture/settlement interfaces
- **Responsibilities**:
  - Payment authorization and capture
  - Settlement processing
  - Transaction routing
  - Direct-to-bank experiments (future)
  - Core payment infrastructure

#### 3. **Redemption Agent** (Future Component)
- **Purpose**: Wallet-side interactions and redemption processing
- **Responsibilities**:
  - Reward redemption
  - Loyalty program management
  - Customer wallet operations
  - Points and cashback processing

#### 4. **Interop Layer**
- **Purpose**: Agent-to-agent communication and coordination
- **Responsibilities**:
  - Service discovery and routing
  - Inter-agent messaging
  - Event coordination
  - Health monitoring and failover

## 🏗️ Orca Checkout Agent Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Orca Checkout Agent                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    API      │  │     CLI     │  │   SDKs      │             │
│  │  (FastAPI)  │  │  (Typer)    │  │ (Python/JS) │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Decision   │  │  Scoring    │  │ Composite   │             │
│  │   Engine    │  │   Engine    │  │  Utility    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Preference  │  │  Merchant   │  │  Analytics  │             │
│  │ Weighting   │  │  Penalty    │  │   Engine    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Card      │  │   Risk      │  │  Webhooks   │             │
│  │ Database    │  │  Patterns   │  │   Engine    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### Component Details

#### API Layer
- **FastAPI Application**: RESTful API with automatic OpenAPI schema generation
- **Endpoints**: `/v1/score`, `/v1/explain`, `/v1/healthz`, `/v1/version`
- **Authentication**: API key-based authentication
- **Rate Limiting**: Built-in rate limiting and throttling
- **Monitoring**: Health checks and metrics endpoints

#### CLI Interface
- **Typer-based CLI**: Rich command-line interface
- **Commands**: `checkout`, `score`, `explain`, `health`
- **Interactive Mode**: Guided transaction processing
- **Batch Processing**: File-based transaction processing
- **Configuration**: Environment-based configuration

#### SDK Ecosystem
- **Python SDK**: Full-featured client with async/sync support
- **Node.js SDK**: TypeScript-first implementation
- **Error Handling**: Comprehensive error handling and retry logic
- **Authentication**: Built-in API key management
- **Examples**: Comprehensive usage examples and tutorials

### Intelligence Engine

#### Decision Engine
- **Multi-factor Analysis**: Combines risk, loyalty, and merchant factors
- **Real-time Processing**: Sub-100ms decision latency
- **Explainability**: Detailed feature attributions
- **Confidence Scoring**: Confidence levels for all decisions
- **Fallback Logic**: Graceful degradation on component failures

#### Scoring Engine
- **Two-stage Approval**: Rules layer + calibration layer
- **Risk Assessment**: Multi-level risk scoring (low, medium, high)
- **Velocity Analysis**: Transaction frequency and pattern analysis
- **Location Intelligence**: Geographic and device location analysis
- **Merchant Intelligence**: Category-based risk and reward analysis

#### Composite Utility
- **Multi-factor Utility**: Combines approval probability, rewards, preferences, and penalties
- **Dynamic Weighting**: Context-aware weight adjustments
- **Optimization**: Maximizes expected utility for card recommendations
- **Personalization**: User preference and loyalty tier integration

### Data Layer

#### Card Database
- **7 Major Cards**: Comprehensive coverage of major credit cards
- **Reward Structures**: Detailed reward rate calculations
- **Category Bonuses**: MCC-based reward multipliers
- **Signup Bonuses**: Eligibility and bonus tracking
- **Network Preferences**: Visa, Mastercard, Amex, Discover support

#### Risk Patterns
- **Known Risk Patterns**: Pre-identified fraud patterns
- **Velocity Thresholds**: Transaction frequency limits
- **Location Mismatches**: Device vs. transaction location analysis
- **Amount Patterns**: High-ticket and unusual amount detection
- **Customer History**: Chargeback and dispute tracking

#### Merchant Intelligence
- **Category Detection**: Automatic MCC-based categorization
- **Risk Profiling**: Merchant-specific risk assessment
- **Network Preferences**: Preferred payment networks
- **Penalty System**: Merchant-specific penalty calculations
- **Fuzzy Matching**: Intelligent merchant name matching

## 🔄 Request/Response Flow

### Transaction Processing Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│   Orca      │───▶│  Weave      │
│             │    │  Checkout   │    │   Core      │
│             │    │   Agent     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │  Redemption │
                   │   Agent     │
                   └─────────────┘
```

### Detailed Processing Steps

1. **Request Reception**: API receives transaction context
2. **Context Validation**: Validate cart, merchant, customer, device, and geo data
3. **Risk Assessment**: Analyze risk factors and patterns
4. **Card Scoring**: Score all available cards against transaction context
5. **Utility Calculation**: Calculate composite utility for each card
6. **Recommendation Ranking**: Rank cards by utility score
7. **Explainability Generation**: Generate feature attributions
8. **Response Assembly**: Compile recommendations with metadata
9. **Webhook Dispatch**: Send decision events to configured webhooks
10. **Analytics Logging**: Log decision outcomes for analysis

### Request Schema

```json
{
  "cart": {
    "items": [
      {
        "item": "Product Name",
        "unit_price": "99.99",
        "qty": 1,
        "mcc": "5734",
        "merchant_category": "Electronics"
      }
    ],
    "currency": "USD"
  },
  "merchant": {
    "name": "Merchant Name",
    "mcc": "5734",
    "network_preferences": ["visa", "mc"],
    "location": {
      "city": "San Francisco",
      "country": "US"
    }
  },
  "customer": {
    "id": "customer_123",
    "loyalty_tier": "GOLD",
    "historical_velocity_24h": 3,
    "chargebacks_12m": 0
  },
  "device": {
    "ip": "192.168.1.100",
    "device_id": "device_abc123",
    "ip_distance_km": 5.2,
    "location": {
      "city": "San Francisco",
      "country": "US"
    }
  },
  "geo": {
    "city": "San Francisco",
    "region": "CA",
    "country": "US",
    "lat": 37.7749,
    "lon": -122.4194
  }
}
```

### Response Schema

```json
{
  "transaction_id": "txn_abc123def456",
  "recommendations": [
    {
      "card_id": "chase_sapphire_preferred",
      "card_name": "Chase Sapphire Preferred",
      "rank": 1,
      "p_approval": 0.85,
      "expected_rewards": 0.025,
      "utility": 0.78,
      "explainability": {
        "baseline": 0.50,
        "contributions": [
          {
            "feature": "merchant_category",
            "contribution": 0.15,
            "direction": "positive"
          }
        ],
        "top_drivers": {
          "positive": [
            {
              "feature": "merchant_category",
              "value": "5734",
              "impact": 0.15
            }
          ],
          "negative": []
        }
      },
      "audit": {
        "config_versions": {
          "scoring": "v1.2.0",
          "preferences": "v1.1.0"
        },
        "code_version": "abc123def456",
        "request_id": "req_789ghi012",
        "latency_ms": 45
      }
    }
  ],
  "score": 0.78,
  "status": "completed",
  "metadata": {
    "processing_time_ms": 45,
    "intelligence_version": "1.0.0",
    "algorithm_used": "phase2_intelligence_engine"
  }
}
```

## 🎯 Interchange Optimization

### Where It Lives

Interchange optimization is a key component of the Orca ecosystem and operates at multiple levels:

#### 1. **Card Selection Optimization**
- **Location**: Orca Checkout Agent
- **Function**: Selects cards with optimal interchange rates for the transaction context
- **Factors**: Merchant category, transaction amount, card type, network preferences
- **Output**: Ranked card recommendations with expected interchange rates

#### 2. **Network Routing Optimization**
- **Location**: Weave Core
- **Function**: Routes transactions through optimal payment networks
- **Factors**: Network fees, processing speed, success rates
- **Output**: Network routing decisions and fallback strategies

#### 3. **Settlement Optimization**
- **Location**: Weave Core
- **Function**: Optimizes settlement timing and batching
- **Factors**: Settlement fees, cash flow, risk management
- **Output**: Settlement schedules and batch configurations

### Optimization Algorithms

#### Multi-Objective Optimization
- **Objective 1**: Maximize approval probability
- **Objective 2**: Maximize reward value
- **Objective 3**: Minimize interchange costs
- **Objective 4**: Minimize processing time
- **Constraint**: Maintain risk thresholds

#### Dynamic Weighting
- **Context-Aware**: Weights adjust based on transaction context
- **User Preferences**: Incorporates user preference signals
- **Merchant Requirements**: Respects merchant network preferences
- **Risk Tolerance**: Adjusts based on risk appetite

## 🔗 Integration Points

### Weave Core Integration
- **API Endpoints**: RESTful API for auth/capture/settlement
- **Event Streaming**: Real-time event notifications
- **Health Monitoring**: Service health and availability checks
- **Configuration**: Dynamic configuration updates

### Redemption Agent Integration
- **Reward Processing**: Real-time reward calculations
- **Loyalty Integration**: Customer loyalty tier management
- **Redemption Tracking**: Reward redemption monitoring
- **Customer Communication**: Reward notifications and updates

### Interop Layer Integration
- **Service Discovery**: Dynamic service registration and discovery
- **Load Balancing**: Intelligent request routing
- **Circuit Breakers**: Fault tolerance and failover
- **Monitoring**: Distributed tracing and metrics

## 📊 Monitoring and Observability

### Metrics
- **Transaction Metrics**: Volume, latency, success rates
- **Decision Metrics**: Approval rates, recommendation accuracy
- **Performance Metrics**: Processing time, throughput
- **Business Metrics**: Revenue impact, cost savings

### Logging
- **Structured Logging**: JSON logs with trace IDs
- **Request Tracing**: End-to-end request tracking
- **Error Logging**: Comprehensive error capture
- **Audit Logging**: Decision audit trails

### Alerting
- **Performance Alerts**: Latency and throughput thresholds
- **Error Alerts**: Error rate and failure notifications
- **Business Alerts**: Approval rate and revenue impact
- **Infrastructure Alerts**: Service health and availability

## 🚀 Deployment Architecture

### Deployment Modes

#### 1. **Sidecar Mode**
- **Use Case**: Microservice deployment
- **Benefits**: Independent scaling, fault isolation
- **Requirements**: Service mesh or container orchestration
- **Monitoring**: Distributed tracing, health checks

#### 2. **Inline Mode**
- **Use Case**: Embedded service deployment
- **Benefits**: Low latency, simplified architecture
- **Requirements**: Direct integration with application
- **Monitoring**: Application-level monitoring

#### 3. **Standalone Mode**
- **Use Case**: Independent service deployment
- **Benefits**: Full control, custom configuration
- **Requirements**: Load balancer, service discovery
- **Monitoring**: Service-level monitoring

### Infrastructure Requirements

#### Compute
- **CPU**: 2-4 cores per instance
- **Memory**: 4-8 GB per instance
- **Storage**: 20-50 GB for logs and cache
- **Network**: Low-latency network connectivity

#### Dependencies
- **Redis**: Caching and session storage
- **PostgreSQL**: Configuration and audit data
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

## 🔮 Future Architecture

### Planned Enhancements

#### 1. **Machine Learning Integration**
- **Real-time ML**: Online learning and model updates
- **Feature Engineering**: Automated feature discovery
- **Model Serving**: High-performance model inference
- **A/B Testing**: Experimentation framework

#### 2. **Edge Computing**
- **Edge Deployment**: Regional edge deployments
- **Local Processing**: Reduced latency processing
- **Offline Capability**: Limited offline functionality
- **Sync Mechanisms**: Data synchronization

#### 3. **Blockchain Integration**
- **Smart Contracts**: Automated settlement contracts
- **Tokenization**: Reward token management
- **Decentralized Identity**: Customer identity management
- **Cross-chain**: Multi-blockchain support

### Scalability Roadmap

#### Phase 1: Current (v1.0)
- **Throughput**: 1,000 TPS per instance
- **Latency**: <100ms P95
- **Availability**: 99.9% uptime
- **Geographic**: Single region

#### Phase 2: Enhanced (v2.0)
- **Throughput**: 10,000 TPS per instance
- **Latency**: <50ms P95
- **Availability**: 99.99% uptime
- **Geographic**: Multi-region

#### Phase 3: Global (v3.0)
- **Throughput**: 100,000 TPS per instance
- **Latency**: <25ms P95
- **Availability**: 99.999% uptime
- **Geographic**: Global edge deployment

---

*This architecture document will be updated as the Orca platform evolves and new components are added.*
