"""
Load test for Orca Checkout Agent API using Locust.

This file provides basic load testing capabilities for the Orca Checkout Agent API.
It simulates realistic transaction scenarios to validate performance under load.
"""

import random

from locust import HttpUser, between, task


class OrcaCheckoutUser(HttpUser):
    """Simulates a user interacting with the Orca Checkout Agent API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Initialize the user session."""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Orca-LoadTest/1.0",
        }

    @task(3)
    def health_check(self):
        """Check API health - most common operation."""
        self.client.get("/v1/healthz", headers=self.headers)

    @task(2)
    def version_check(self):
        """Check API version."""
        self.client.get("/v1/version", headers=self.headers)

    @task(5)
    def score_transaction(self):
        """Score a transaction - core functionality."""
        # Generate realistic transaction data
        transaction_data = self._generate_transaction_data()

        self.client.post(
            "/v1/score",
            json=transaction_data,
            headers=self.headers,
            name="score_transaction",
        )

    @task(1)
    def explain_transaction(self):
        """Explain a transaction - less frequent but important."""
        transaction_data = self._generate_transaction_data()

        self.client.post(
            "/v1/explain",
            json=transaction_data,
            headers=self.headers,
            name="explain_transaction",
        )

    def _generate_transaction_data(self):
        """Generate realistic transaction data for testing."""
        # Sample merchant categories
        merchants = [
            {"name": "Amazon", "mcc": "5999", "category": "Miscellaneous"},
            {"name": "Best Buy", "mcc": "5734", "category": "Electronics"},
            {"name": "Whole Foods", "mcc": "5411", "category": "Grocery"},
            {"name": "Shell", "mcc": "5541", "category": "Gas Station"},
            {"name": "Starbucks", "mcc": "5814", "category": "Restaurant"},
        ]

        # Sample loyalty tiers
        loyalty_tiers = ["NONE", "SILVER", "GOLD", "PLATINUM", "DIAMOND"]

        # Sample cities
        cities = [
            {
                "city": "San Francisco",
                "region": "CA",
                "country": "US",
                "lat": 37.7749,
                "lon": -122.4194,
            },
            {
                "city": "New York",
                "region": "NY",
                "country": "US",
                "lat": 40.7128,
                "lon": -74.0060,
            },
            {
                "city": "Los Angeles",
                "region": "CA",
                "country": "US",
                "lat": 34.0522,
                "lon": -118.2437,
            },
            {
                "city": "Chicago",
                "region": "IL",
                "country": "US",
                "lat": 41.8781,
                "lon": -87.6298,
            },
            {
                "city": "Seattle",
                "region": "WA",
                "country": "US",
                "lat": 47.6062,
                "lon": -122.3321,
            },
        ]

        merchant = random.choice(merchants)
        city = random.choice(cities)

        # Generate realistic transaction amounts
        amount = round(random.uniform(10.00, 500.00), 2)

        return {
            "cart": {
                "items": [
                    {
                        "item": f"Product from {merchant['name']}",
                        "unit_price": str(amount),
                        "qty": random.randint(1, 3),
                        "mcc": merchant["mcc"],
                        "merchant_category": merchant["category"],
                    }
                ],
                "currency": "USD",
            },
            "merchant": {
                "name": merchant["name"],
                "mcc": merchant["mcc"],
                "network_preferences": random.choice(
                    [["visa", "mc"], ["visa"], ["mc"], ["amex"]]
                ),
                "location": {"city": city["city"], "country": city["country"]},
            },
            "customer": {
                "id": f"customer_{random.randint(10000, 99999)}",
                "loyalty_tier": random.choice(loyalty_tiers),
                "historical_velocity_24h": random.randint(0, 10),
                "chargebacks_12m": random.randint(0, 2),
            },
            "device": {
                "ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "device_id": f"device_{random.randint(100000, 999999)}",
                "ip_distance_km": round(random.uniform(0.1, 100.0), 1),
                "location": {"city": city["city"], "country": city["country"]},
            },
            "geo": city,
        }


class OrcaCheckoutAdminUser(HttpUser):
    """Simulates an admin user with different access patterns."""

    wait_time = between(5, 10)  # Less frequent requests

    def on_start(self):
        """Initialize the admin user session."""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Orca-Admin/1.0",
        }

    @task(1)
    def health_check(self):
        """Admin health checks."""
        self.client.get("/v1/healthz", headers=self.headers)

    @task(1)
    def version_check(self):
        """Admin version checks."""
        self.client.get("/v1/version", headers=self.headers)

    @task(3)
    def score_high_value_transaction(self):
        """Score high-value transactions."""
        transaction_data = self._generate_high_value_transaction()

        self.client.post(
            "/v1/score",
            json=transaction_data,
            headers=self.headers,
            name="score_high_value",
        )

    def _generate_high_value_transaction(self):
        """Generate high-value transaction data."""
        return {
            "cart": {
                "items": [
                    {
                        "item": "High-Value Product",
                        "unit_price": str(round(random.uniform(1000.00, 10000.00), 2)),
                        "qty": 1,
                        "mcc": "5734",
                        "merchant_category": "Electronics",
                    }
                ],
                "currency": "USD",
            },
            "merchant": {
                "name": "Premium Electronics Store",
                "mcc": "5734",
                "network_preferences": ["visa", "mc"],
                "location": {"city": "San Francisco", "country": "US"},
            },
            "customer": {
                "id": f"vip_customer_{random.randint(1000, 9999)}",
                "loyalty_tier": random.choice(["PLATINUM", "DIAMOND"]),
                "historical_velocity_24h": random.randint(0, 5),
                "chargebacks_12m": 0,
            },
            "device": {
                "ip": f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "device_id": f"vip_device_{random.randint(10000, 99999)}",
                "ip_distance_km": round(random.uniform(0.1, 10.0), 1),
                "location": {"city": "San Francisco", "country": "US"},
            },
            "geo": {
                "city": "San Francisco",
                "region": "CA",
                "country": "US",
                "lat": 37.7749,
                "lon": -122.4194,
            },
        }
