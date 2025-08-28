# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-12-26

### Added
- **Phase 2 Intelligence Layer**: Complete implementation of intelligent decision-making engine
- **Intelligence Engine**: Main orchestrator for intelligent checkout processing with performance tracking
- **Card Database**: Comprehensive database with 7 major credit cards and detailed rewards structures
- **Merchant Analyzer**: Intelligent merchant categorization and multi-level risk assessment
- **Enhanced Processing**: Multi-factor risk assessment with amount bonuses and merchant bonuses
- **Smart Recommendations**: Context-aware card recommendations with reasoning and confidence scoring
- **Deterministic Testing**: Golden test fixtures for regression testing and output validation
- **Performance Tracking**: Processing time monitoring and optimization strategies
- **Structured Logging**: Enhanced JSON logging with intelligence insights and trace IDs
- **API Usage Examples**: Comprehensive examples for transaction scoring and card recommendations
- **Smoke Test Commands**: Quick health checks and comprehensive testing procedures

### Changed
- **Core Integration**: Integrated intelligence engine into main checkout processing pipeline
- **Fallback Logic**: Graceful fallback to basic processing if intelligence components unavailable
- **Enhanced Models**: Updated data models to support intelligence metadata and explainability
- **Configuration Freezing**: Version-stamped configuration files with detailed release notes
- **Documentation**: Updated README with v0.2.0 features, API examples, and smoke tests

### Technical
- **Comprehensive Testing**: 188 unit tests with pytest coverage (67% overall)
- **Golden Tests**: Deterministic output validation for regression testing
- **Code Quality**: Clear docstrings, type hints, and comprehensive error handling
- **Modular Architecture**: Separated intelligence components for maintainability and scalability

### Performance
- **Fast Processing**: Average processing time <100ms per request
- **Memory Efficient**: Optimized data structures and algorithms
- **Scalable Design**: Modular components ready for horizontal scaling
- **Error Resilience**: Graceful degradation with fallback mechanisms

### Configuration
- **Frozen Configs**: Version 0.2.0 stamped configuration files
- **Approval Scoring**: Enhanced two-stage approval system with MCC-based weights
- **Preference Weighting**: Advanced preference system with loyalty tiers and category boosts
- **Merchant Penalties**: Comprehensive merchant penalty system with fuzzy matching

### Added
- **Phase 2 Intelligence Layer**: Implemented core intelligence engine with advanced decision-making
- **Intelligence Engine**: Main orchestrator for intelligent checkout processing
- **Card Database**: Comprehensive database with 7 major credit cards and rewards data
- **Merchant Analyzer**: Intelligent merchant categorization and risk assessment
- **Enhanced Processing**: Multi-factor risk assessment and transaction scoring
- **Smart Recommendations**: Context-aware card recommendations with reasoning
- **Deterministic Testing**: Golden test fixtures for regression testing
- **Performance Tracking**: Processing time monitoring and statistics
- **Structured Logging**: Enhanced JSON logging with intelligence insights

### Changed
- **Core Integration**: Integrated intelligence engine into main checkout processing
- **Fallback Logic**: Graceful fallback to basic processing if intelligence unavailable
- **Enhanced Models**: Updated data models to support intelligence metadata

### Technical
- **Comprehensive Testing**: 15+ unit tests with pytest coverage
- **Golden Tests**: Deterministic output validation for regression testing
- **Code Quality**: Clear docstrings, type hints, and error handling
- **Modular Architecture**: Separated intelligence components for maintainability

### Performance
- **Fast Processing**: Average processing time <100ms per request
- **Memory Efficient**: Optimized data structures and algorithms
- **Scalable Design**: Modular components ready for horizontal scaling

## [0.1.0] - 2024-12-19
- Initial project setup with AltWallet Merchant Agent CLI
- Core card recommendation engine with deterministic logic
- Typer-based CLI with `recommend` and `demo` commands
- Rich terminal output with beautiful formatting
- Support for 4 popular credit cards (Chase, Citi, Amex)
- Category-specific bonus rewards and annual fee calculations
- Comprehensive test suite with pytest
- VS Code/Cursor configuration and development tools
- PowerShell setup scripts and troubleshooting guide
- Enhancement stubs: `--p-approval` and `--geo-promo` options

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2024-12-19

### Added
- Initial release of AltWallet Merchant Agent CLI
- Basic card recommendation functionality
- Demo command with deterministic output
- Development environment setup
- Comprehensive documentation and examples

---

## Release Types

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Version Format

`MAJOR.MINOR.PATCH` (e.g., 1.2.3)

- **1** = Major version (breaking changes)
- **2** = Minor version (new features, backwards compatible)
- **3** = Patch version (bug fixes, backwards compatible)
