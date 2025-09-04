#!/usr/bin/env python3
"""Test script for AltWallet Checkout Agent API."""

import json
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8080"


def test_health():
    """Test health endpoint."""
    print("Testing /v1/healthz...")
    response = requests.get(f"{BASE_URL}/v1/healthz")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_version():
    """Test version endpoint."""
    print("Testing /v1/version...")
    response = requests.get(f"{BASE_URL}/v1/version")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_score():
    """Test scoring endpoint."""
    print("Testing /v1/score...")

    # Sample context data
    context_data = {
        "cart": {
            "items": [
                {
                    "item": "Wireless Headphones",
                    "unit_price": "199.99",
                    "qty": 1,
                    "mcc": "5734",
                    "merchant_category": "Computer Software Stores",
                }
            ],
            "currency": "USD",
        },
        "merchant": {
            "name": "Best Buy",
            "mcc": "5734",
            "network_preferences": ["visa", "mc"],
            "location": {"city": "San Francisco", "country": "US"},
        },
        "customer": {
            "id": "cust_12345",
            "loyalty_tier": "GOLD",
            "historical_velocity_24h": 3,
            "chargebacks_12m": 0,
        },
        "device": {
            "ip": "192.168.1.100",
            "device_id": "dev_abc123",
            "ip_distance_km": 5.2,
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

    payload = {"context_data": context_data}
    response = requests.post(f"{BASE_URL}/v1/score", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_explain():
    """Test explain endpoint."""
    print("Testing /v1/explain...")

    # Sample context data
    context_data = {
        "cart": {
            "items": [
                {
                    "item": "Gaming Console",
                    "unit_price": "499.99",
                    "qty": 1,
                    "mcc": "5734",
                }
            ],
            "currency": "USD",
        },
        "merchant": {
            "name": "Online Electronics Store",
            "mcc": "5734",
            "network_preferences": ["visa"],
        },
        "customer": {
            "id": "cust_67890",
            "loyalty_tier": "NONE",
            "historical_velocity_24h": 15,
            "chargebacks_12m": 2,
        },
        "device": {
            "ip": "10.0.0.1",
            "device_id": "dev_xyz789",
            "ip_distance_km": 1500.0,
            "location": {"city": "New York", "country": "US"},
        },
        "geo": {
            "city": "Los Angeles",
            "region": "CA",
            "country": "US",
            "lat": 34.0522,
            "lon": -118.2437,
        },
    }

    payload = {"context_data": context_data}
    response = requests.post(f"{BASE_URL}/v1/explain", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def main():
    """Run all tests."""
    print("AltWallet Checkout Agent API Tests")
    print("=" * 40)

    try:
        test_health()
        test_version()
        test_score()
        test_explain()
        print("All tests completed successfully!")
    except requests.exceptions.ConnectionError:
        print(
            "Error: Could not connect to API server. Make sure it's running on localhost:8080"
        )
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
