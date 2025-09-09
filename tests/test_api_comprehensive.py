"""Comprehensive tests for FastAPI application."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from altwallet_agent.api import app


class TestAPIModels:
    """Test API request/response models."""

    def test_health_response_model(self):
        """Test HealthResponse model."""
        from altwallet_agent.api import HealthResponse

        health = HealthResponse(
            status="healthy",
            uptime_seconds=100,
            version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        assert health.status == "healthy"
        assert health.uptime_seconds == 100
        assert health.version == "1.0.0"
        assert health.timestamp == "2024-01-01T00:00:00Z"
        assert health.error is None

    def test_version_response_model(self):
        """Test VersionResponse model."""
        from altwallet_agent.api import VersionResponse

        version = VersionResponse(
            version="1.0.0",
            build_date="2024-01-01T00:00:00Z",
            git_sha="abc123",
            components={"scoring_engine": "v1.2.0"},
            api_spec_version="3.0.3",
        )

        assert version.version == "1.0.0"
        assert version.build_date == "2024-01-01T00:00:00Z"
        assert version.git_sha == "abc123"
        assert version.components["scoring_engine"] == "v1.2.0"
        assert version.api_spec_version == "3.0.3"

    def test_score_request_model(self):
        """Test ScoreRequest model."""
        from altwallet_agent.api import ScoreRequest

        request = ScoreRequest(context_data={"merchant": {"id": "test"}})

        assert request.context_data["merchant"]["id"] == "test"

    def test_score_response_model(self):
        """Test ScoreResponse model."""
        from altwallet_agent.api import ScoreResponse

        response = ScoreResponse(
            transaction_id="test_txn",
            recommendations=[{"card_id": "test_card"}],
            score=0.85,
            status="completed",
            metadata={"processing_time_ms": 100},
        )

        assert response.transaction_id == "test_txn"
        assert len(response.recommendations) == 1
        assert response.score == 0.85
        assert response.status == "completed"
        assert response.metadata["processing_time_ms"] == 100

    def test_explain_request_model(self):
        """Test ExplainRequest model."""
        from altwallet_agent.api import ExplainRequest

        request = ExplainRequest(context_data={"merchant": {"id": "test"}})

        assert request.context_data["merchant"]["id"] == "test"

    def test_explain_response_model(self):
        """Test ExplainResponse model."""
        from altwallet_agent.api import ExplainResponse

        response = ExplainResponse(
            transaction_id="test_txn",
            request_id="test_req",
            attributions={"risk_factors": {}},
            metadata={"processing_time_ms": 100},
        )

        assert response.transaction_id == "test_txn"
        assert response.request_id == "test_req"
        assert "risk_factors" in response.attributions
        assert response.metadata["processing_time_ms"] == 100

    def test_decision_request_model(self):
        """Test DecisionRequest model."""
        from altwallet_agent.api import DecisionRequest

        request = DecisionRequest(context_data={"merchant": {"id": "test"}})

        assert request.context_data["merchant"]["id"] == "test"

    def test_decision_response_model(self):
        """Test DecisionResponse model."""
        from altwallet_agent.api import DecisionResponse
        from altwallet_agent.decisioning import (
            ActionType,
            BusinessRule,
            Decision,
            DecisionContract,
            DecisionReason,
            RoutingHint,
        )

        decision_contract = DecisionContract(
            decision=Decision.APPROVE,
            actions=[
                BusinessRule(
                    rule_id="test",
                    action_type=ActionType.LOYALTY_BOOST,
                    description="Test",
                )
            ],
            reasons=[
                DecisionReason(
                    feature_name="test",
                    value="good",
                    threshold=0.5,
                    weight=0.8,
                    description="Test",
                )
            ],
            routing_hint=RoutingHint(),
            transaction_id="test_txn",
        )

        response = DecisionResponse(
            decision_contract=decision_contract,
            transaction_id="test_txn",
            status="completed",
            metadata={"processing_time_ms": 100},
        )

        assert response.transaction_id == "test_txn"
        assert response.status == "completed"
        assert response.decision_contract.decision == Decision.APPROVE
        assert response.metadata["processing_time_ms"] == 100


class TestAPIMiddleware:
    """Test API middleware functionality."""

    def test_trace_id_middleware(self):
        """Test trace ID middleware adds trace ID to requests."""
        client = TestClient(app)

        with patch("altwallet_agent.api.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            response = client.get("/v1/healthz")

            assert response.status_code == 200
            assert "X-Trace-Id" in response.headers
            assert response.headers["X-Trace-Id"] is not None

            # Verify logging was called
            assert mock_log.info.call_count >= 2  # Request and response logging

    def test_trace_id_middleware_with_existing_trace_id(self):
        """Test trace ID middleware uses existing trace ID from headers."""
        client = TestClient(app)

        custom_trace_id = "custom-trace-123"

        with patch("altwallet_agent.api.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            response = client.get(
                "/v1/healthz", headers={"X-Trace-Id": custom_trace_id}
            )

            assert response.status_code == 200
            assert response.headers["X-Trace-Id"] == custom_trace_id

    def test_trace_id_middleware_logging(self):
        """Test trace ID middleware logs request and response."""
        client = TestClient(app)

        with patch("altwallet_agent.api.get_logger") as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log

            response = client.get("/v1/healthz")

            assert response.status_code == 200

            # Check that request and response were logged
            log_calls = mock_log.info.call_args_list
            assert len(log_calls) >= 2

            # Check request logging
            request_log = log_calls[0][1]
            assert "method" in request_log
            assert "url" in request_log
            assert "trace_id" in request_log

            # Check response logging
            response_log = log_calls[1][1]
            assert "method" in response_log
            assert "url" in response_log
            assert "status_code" in response_log
            assert "trace_id" in response_log


class TestAPIEndpoints:
    """Test API endpoints."""

    @pytest.fixture
    def sample_context_data(self):
        """Sample context data for testing."""
        return {
            "cart": {
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "100.00",
                        "qty": 1,
                        "mcc": "4511",
                    }
                ],
                "currency": "USD",
            },
            "merchant": {
                "id": "test_merchant",
                "name": "Test Merchant",
                "mcc": "4511",
                "region": "US",
            },
            "customer": {
                "id": "test_customer",
                "loyalty_tier": "GOLD",
                "risk_score": 0.2,
                "chargebacks_12m": 0,
            },
            "device": {
                "ip": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "network_preferences": [],
            },
            "geo": {
                "city": "New York",
                "region": "NY",
                "country": "US",
                "lat": 40.7128,
                "lon": -74.0060,
            },
        }

    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        client = TestClient(app)

        response = client.get("/v1/healthz")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_version_endpoint(self):
        """Test version endpoint."""
        client = TestClient(app)

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"abc123def456"

            response = client.get("/v1/version")

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "1.0.0"
            assert data["git_sha"] == "abc123def456"
            assert data["api_spec_version"] == "3.0.3"
            assert "components" in data
            assert "build_date" in data

    def test_version_endpoint_git_error(self):
        """Test version endpoint when git command fails."""
        client = TestClient(app)

        with patch("subprocess.check_output", side_effect=Exception("Git not found")):
            response = client.get("/v1/version")

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "1.0.0"
            assert data["git_sha"] == "unknown"
            assert data["api_spec_version"] == "3.0.3"

    def test_score_endpoint_success(self, sample_context_data):
        """Test score endpoint with valid data."""
        client = TestClient(app)

        with patch("altwallet_agent.api.composite_utility") as mock_utility:
            with patch(
                "altwallet_agent.data.card_database.CardDatabase"
            ) as mock_card_db:
                # Mock card database
                mock_db_instance = Mock()
                mock_db_instance.get_all_cards.return_value = {
                    "card1": {
                        "card_id": "card1",
                        "card_name": "Test Card",
                        "components": {"p_approval": 0.85, "expected_rewards": 0.02},
                        "utility_score": 0.75,
                    }
                }
                mock_card_db.return_value = mock_db_instance

                # Mock composite utility
                mock_utility.rank_cards_by_utility.return_value = [
                    {
                        "card_id": "card1",
                        "card_name": "Test Card",
                        "components": {"p_approval": 0.85, "expected_rewards": 0.02},
                        "utility_score": 0.75,
                    }
                ]

                response = client.post(
                    "/v1/score", json={"context_data": sample_context_data}
                )

                assert response.status_code == 200
                data = response.json()
                assert "transaction_id" in data
                assert "recommendations" in data
                assert "score" in data
                assert data["status"] == "completed"
                assert "metadata" in data
                assert len(data["recommendations"]) == 1

    def test_score_endpoint_invalid_context(self):
        """Test score endpoint with invalid context data."""
        client = TestClient(app)

        response = client.post("/v1/score", json={"context_data": {"invalid": "data"}})

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_explain_endpoint_success(self, sample_context_data):
        """Test explain endpoint with valid data."""
        client = TestClient(app)

        with patch("altwallet_agent.api.score_transaction") as mock_score:
            with patch("altwallet_agent.api.Context.from_json_payload") as mock_context:
                # Create a mock context object
                mock_context_obj = Mock()
                mock_context_obj.flags.return_value = {
                    "mismatch_location": False,
                    "velocity_24h_flag": False,
                }
                mock_context_obj.customer.chargebacks_12m = 0
                mock_context_obj.cart.total = Decimal("100.00")
                mock_context_obj.merchant.mcc = "4511"
                mock_context_obj.customer.loyalty_tier.value = "GOLD"
                mock_context_obj.device.ip_distance_km = 5.0
                mock_context_obj.dict.return_value = {"test": "data"}
                mock_context.return_value = mock_context_obj

                mock_score.return_value = Mock(
                    risk_score=0.2,
                    loyalty_boost=0.1,
                    final_score=0.75,
                    routing_hint="VISA",
                )

                response = client.post(
                    "/v1/explain", json={"context_data": sample_context_data}
                )

                assert response.status_code == 200
                data = response.json()
                assert "transaction_id" in data
                assert "request_id" in data
                assert "attributions" in data
                assert "metadata" in data
                assert "risk_factors" in data["attributions"]
                assert "feature_contributions" in data["attributions"]
                assert "composite_scores" in data["attributions"]

    def test_explain_endpoint_invalid_context(self):
        """Test explain endpoint with invalid context data."""
        client = TestClient(app)

        response = client.post(
            "/v1/explain", json={"context_data": {"invalid": "data"}}
        )

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_decision_endpoint_success(self, sample_context_data):
        """Test decision endpoint with valid data."""
        client = TestClient(app)

        with patch("altwallet_agent.api.decision_engine") as mock_engine:
            from altwallet_agent.decisioning import (
                ActionType,
                BusinessRule,
                Decision,
                DecisionContract,
                DecisionReason,
                RoutingHint,
            )

            mock_contract = DecisionContract(
                decision=Decision.APPROVE,
                actions=[
                    BusinessRule(
                        rule_id="test",
                        action_type=ActionType.LOYALTY_BOOST,
                        description="Test",
                    )
                ],
                reasons=[
                    DecisionReason(
                        feature_name="test",
                        value="good",
                        threshold=0.5,
                        weight=0.8,
                        description="Test",
                    )
                ],
                routing_hint=RoutingHint(),
                transaction_id="test_txn",
            )
            mock_engine.make_decision.return_value = mock_contract

            response = client.post(
                "/v1/decision", json={"context_data": sample_context_data}
            )

            assert response.status_code == 200
            data = response.json()
            assert "decision_contract" in data
            assert "transaction_id" in data
            assert data["status"] == "completed"
            assert "metadata" in data
            assert data["decision_contract"]["decision"] == "APPROVE"

    def test_decision_endpoint_invalid_context(self):
        """Test decision endpoint with invalid context data."""
        client = TestClient(app)

        response = client.post(
            "/v1/decision", json={"context_data": {"invalid": "data"}}
        )

        assert response.status_code == 500
        assert "detail" in response.json()

    def test_legacy_health_endpoint(self):
        """Test legacy health endpoint."""
        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_legacy_score_endpoint(self, sample_context_data):
        """Test legacy score endpoint."""
        client = TestClient(app)

        with patch("altwallet_agent.api.composite_utility") as mock_utility:
            with patch(
                "altwallet_agent.data.card_database.CardDatabase"
            ) as mock_card_db:
                # Mock card database
                mock_db_instance = Mock()
                mock_db_instance.get_all_cards.return_value = {
                    "card1": {
                        "card_id": "card1",
                        "card_name": "Test Card",
                        "components": {"p_approval": 0.85, "expected_rewards": 0.02},
                        "utility_score": 0.75,
                    }
                }
                mock_card_db.return_value = mock_db_instance

                # Mock composite utility
                mock_utility.rank_cards_by_utility.return_value = [
                    {
                        "card_id": "card1",
                        "card_name": "Test Card",
                        "components": {"p_approval": 0.85, "expected_rewards": 0.02},
                        "utility_score": 0.75,
                    }
                ]

                response = client.post(
                    "/score", json={"context_data": sample_context_data}
                )

                assert response.status_code == 200
                data = response.json()
                assert "transaction_id" in data
                assert "recommendations" in data

    def test_legacy_decision_endpoint(self, sample_context_data):
        """Test legacy decision endpoint."""
        client = TestClient(app)

        with patch("altwallet_agent.api.decision_engine") as mock_engine:
            from altwallet_agent.decisioning import (
                ActionType,
                BusinessRule,
                Decision,
                DecisionContract,
                DecisionReason,
                RoutingHint,
            )

            mock_contract = DecisionContract(
                decision=Decision.APPROVE,
                actions=[
                    BusinessRule(
                        rule_id="test",
                        action_type=ActionType.LOYALTY_BOOST,
                        description="Test",
                    )
                ],
                reasons=[
                    DecisionReason(
                        feature_name="test",
                        value="good",
                        threshold=0.5,
                        weight=0.8,
                        description="Test",
                    )
                ],
                routing_hint=RoutingHint(),
                transaction_id="test_txn",
            )
            mock_engine.make_decision.return_value = mock_contract

            response = client.post(
                "/decision", json={"context_data": sample_context_data}
            )

            assert response.status_code == 200
            data = response.json()
            assert "decision_contract" in data
            assert "transaction_id" in data


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_score_endpoint_processing_error(self):
        """Test score endpoint handles processing errors."""
        client = TestClient(app)

        with patch(
            "altwallet_agent.api.Context.from_json_payload",
            side_effect=Exception("Processing error"),
        ):
            response = client.post(
                "/v1/score", json={"context_data": {"valid": "data"}}
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Processing error" in data["detail"]

    def test_explain_endpoint_processing_error(self):
        """Test explain endpoint handles processing errors."""
        client = TestClient(app)

        with patch(
            "altwallet_agent.api.Context.from_json_payload",
            side_effect=Exception("Processing error"),
        ):
            response = client.post(
                "/v1/explain", json={"context_data": {"valid": "data"}}
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Processing error" in data["detail"]

    def test_decision_endpoint_processing_error(self):
        """Test decision endpoint handles processing errors."""
        client = TestClient(app)

        with patch(
            "altwallet_agent.api.Context.from_json_payload",
            side_effect=Exception("Processing error"),
        ):
            response = client.post(
                "/v1/decision", json={"context_data": {"valid": "data"}}
            )

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Processing error" in data["detail"]


class TestAPIStartup:
    """Test API startup functionality."""

    def test_startup_event(self):
        """Test startup event generates OpenAPI schema."""
        with patch("altwallet_agent.api.Path") as mock_path:
            with patch("builtins.open", mock_open()):
                with patch("json.dump") as mock_json_dump:
                    with patch("altwallet_agent.api.get_logger") as mock_logger:
                        mock_log = Mock()
                        mock_logger.return_value = mock_log

                        # Mock the Path object
                        mock_dir = Mock()
                        mock_schema_path = Mock()
                        mock_path.return_value = mock_dir
                        mock_dir.mkdir.return_value = None
                        mock_dir.__truediv__ = Mock(return_value=mock_schema_path)
                        mock_schema_path.__str__ = Mock(
                            return_value="openapi/openapi.json"
                        )

                        # Import and call startup event
                        import asyncio

                        from altwallet_agent.api import startup_event

                        asyncio.run(startup_event())

                        # Verify OpenAPI schema was written
                        mock_json_dump.assert_called_once()
                        mock_log.info.assert_called_once()

    def test_app_initialization(self):
        """Test FastAPI app initialization."""
        from altwallet_agent.api import app

        assert app.title == "Orca Checkout Agent API"
        assert app.version == "1.1.0"
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

    def test_cors_middleware(self):
        """Test CORS middleware is configured."""
        from altwallet_agent.api import app

        # Check that CORS middleware is added
        middleware_names = [
            middleware.cls.__name__ for middleware in app.user_middleware
        ]
        assert "CORSMiddleware" in middleware_names


class TestAPIIntegration:
    """Test API integration scenarios."""

    def test_full_workflow_score_explain_decision(self):
        """Test full workflow: score -> explain -> decision."""
        client = TestClient(app)

        context_data = {
            "cart": {
                "items": [
                    {
                        "item": "Test Item",
                        "unit_price": "100.00",
                        "qty": 1,
                        "mcc": "4511",
                    }
                ],
                "currency": "USD",
            },
            "merchant": {
                "id": "test_merchant",
                "name": "Test Merchant",
                "mcc": "4511",
                "region": "US",
            },
            "customer": {
                "id": "test_customer",
                "loyalty_tier": "GOLD",
                "risk_score": 0.2,
                "chargebacks_12m": 0,
            },
            "device": {
                "ip": "192.168.1.1",
                "user_agent": "Mozilla/5.0",
                "network_preferences": [],
            },
            "geo": {
                "city": "New York",
                "region": "NY",
                "country": "US",
                "lat": 40.7128,
                "lon": -74.0060,
            },
        }

        with patch("altwallet_agent.api.composite_utility") as mock_utility:
            with patch(
                "altwallet_agent.data.card_database.CardDatabase"
            ) as mock_card_db:
                with patch("altwallet_agent.api.score_transaction") as mock_score:
                    with patch("altwallet_agent.api.decision_engine") as mock_engine:
                        # Mock card database
                        mock_db_instance = Mock()
                        mock_db_instance.get_all_cards.return_value = {
                            "card1": {
                                "card_id": "card1",
                                "card_name": "Test Card",
                                "components": {
                                    "p_approval": 0.85,
                                    "expected_rewards": 0.02,
                                },
                                "utility_score": 0.75,
                            }
                        }
                        mock_card_db.return_value = mock_db_instance

                        # Mock composite utility
                        mock_utility.rank_cards_by_utility.return_value = [
                            {
                                "card_id": "card1",
                                "card_name": "Test Card",
                                "components": {
                                    "p_approval": 0.85,
                                    "expected_rewards": 0.02,
                                },
                                "utility_score": 0.75,
                            }
                        ]

                        # Mock scoring
                        mock_score.return_value = Mock(
                            risk_score=0.2,
                            loyalty_boost=0.1,
                            final_score=0.75,
                            routing_hint="VISA",
                        )

                        # Mock decision engine
                        from altwallet_agent.decisioning import (
                            ActionType,
                            BusinessRule,
                            Decision,
                            DecisionContract,
                            DecisionReason,
                            RoutingHint,
                        )

                        mock_contract = DecisionContract(
                            decision=Decision.APPROVE,
                            actions=[
                                BusinessRule(
                                    rule_id="test",
                                    action_type=ActionType.LOYALTY_BOOST,
                                    description="Test",
                                )
                            ],
                            reasons=[
                                DecisionReason(
                                    feature_name="test",
                                    value="good",
                                    threshold=0.5,
                                    weight=0.8,
                                    description="Test",
                                )
                            ],
                            routing_hint=RoutingHint(),
                            transaction_id="test_txn",
                        )
                        mock_engine.make_decision.return_value = mock_contract

                        # Test score endpoint
                        score_response = client.post(
                            "/v1/score", json={"context_data": context_data}
                        )
                        assert score_response.status_code == 200

                        # Test explain endpoint with Context mocking
                        with patch(
                            "altwallet_agent.api.Context.from_json_payload"
                        ) as mock_context:
                            # Create a mock context object
                            mock_context_obj = Mock()
                            mock_context_obj.flags.return_value = {
                                "mismatch_location": False,
                                "velocity_24h_flag": False,
                            }
                            mock_context_obj.customer.chargebacks_12m = 0
                            mock_context_obj.cart.total = Decimal("100.00")
                            mock_context_obj.merchant.mcc = "4511"
                            mock_context_obj.customer.loyalty_tier.value = "GOLD"
                            mock_context_obj.device.ip_distance_km = 5.0
                            mock_context_obj.dict.return_value = {"test": "data"}
                            mock_context.return_value = mock_context_obj

                            explain_response = client.post(
                                "/v1/explain", json={"context_data": context_data}
                            )
                            assert explain_response.status_code == 200

                        # Test decision endpoint
                        decision_response = client.post(
                            "/v1/decision", json={"context_data": context_data}
                        )
                        assert decision_response.status_code == 200

                        # Verify all responses have required fields
                        score_data = score_response.json()
                        explain_data = explain_response.json()
                        decision_data = decision_response.json()

                        assert "transaction_id" in score_data
                        assert "recommendations" in score_data
                        assert "score" in score_data

                        assert "transaction_id" in explain_data
                        assert "attributions" in explain_data

                        assert "decision_contract" in decision_data
                        assert "transaction_id" in decision_data


def mock_open():
    """Mock open function for testing."""
    from unittest.mock import mock_open as _mock_open

    return _mock_open()
