#!/usr/bin/env python3
"""
Chile Metrics Collector
Fetches data from Chilean public APIs and pushes to Grafana Cloud Prometheus.
"""

import os
import time
import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler

# Configuration from environment variables
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "").replace("/api/prom/push", "")
PROMETHEUS_USER = os.environ.get("PROMETHEUS_USER", "")
PROMETHEUS_PASSWORD = os.environ.get("PROMETHEUS_PASSWORD", "")

# API Endpoints
API_CLIMA = "https://api.gael.cloud/general/public/clima"
API_SISMOS = "https://api.gael.cloud/general/public/sismos"
API_MONEDAS = "https://api.gael.cloud/general/public/monedas"


def auth_handler(url, method, timeout, headers, data):
    """Authentication handler for Prometheus push gateway."""
    return basic_auth_handler(url, method, timeout, headers, data, PROMETHEUS_USER, PROMETHEUS_PASSWORD)


def fetch_json(url: str) -> list:
    """Fetch JSON data from an API endpoint."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def collect_weather_metrics(registry: CollectorRegistry):
    """Collect weather metrics from Chilean stations."""
    data = fetch_json(API_CLIMA)
    
    if not data:
        print("No weather data available")
        return
    
    # Create gauges
    temp_gauge = Gauge(
        'chile_weather_temperature_celsius',
        'Temperature in Celsius',
        ['station', 'station_code'],
        registry=registry
    )
    
    humidity_gauge = Gauge(
        'chile_weather_humidity_percent',
        'Humidity percentage',
        ['station', 'station_code'],
        registry=registry
    )
    
    for station in data:
        try:
            station_name = station.get('Estacion', 'Unknown')
            station_code = station.get('Codigo', 'Unknown')
            temp = float(station.get('Temp', 0))
            humidity = float(station.get('Humedad', 0))
            
            temp_gauge.labels(station=station_name, station_code=station_code).set(temp)
            humidity_gauge.labels(station=station_name, station_code=station_code).set(humidity)
            
            print(f"Weather: {station_name} - Temp: {temp}°C, Humidity: {humidity}%")
        except (ValueError, TypeError) as e:
            print(f"Error processing weather station {station}: {e}")


def collect_earthquake_metrics(registry: CollectorRegistry):
    """Collect earthquake metrics."""
    data = fetch_json(API_SISMOS)
    
    if not data:
        print("No earthquake data available")
        return
    
    # Create gauges for the most recent earthquakes
    magnitude_gauge = Gauge(
        'chile_earthquake_magnitude',
        'Earthquake magnitude',
        ['location', 'date'],
        registry=registry
    )
    
    depth_gauge = Gauge(
        'chile_earthquake_depth_km',
        'Earthquake depth in kilometers',
        ['location', 'date'],
        registry=registry
    )
    
    # Only process the 10 most recent earthquakes
    for quake in data[:10]:
        try:
            location = quake.get('RefGeografica', 'Unknown')
            date = quake.get('Fecha', 'Unknown')
            magnitude = float(quake.get('Magnitud', 0))
            depth = float(quake.get('Profundidad', 0))
            
            # Clean location for label (remove special chars)
            location_clean = location[:50].replace('"', '').replace("'", "")
            
            magnitude_gauge.labels(location=location_clean, date=date).set(magnitude)
            depth_gauge.labels(location=location_clean, date=date).set(depth)
            
            print(f"Earthquake: {magnitude} - {location_clean}")
        except (ValueError, TypeError) as e:
            print(f"Error processing earthquake {quake}: {e}")


def collect_currency_metrics(registry: CollectorRegistry):
    """Collect currency/economic indicator metrics."""
    data = fetch_json(API_MONEDAS)
    
    if not data:
        print("No currency data available")
        return
    
    currency_gauge = Gauge(
        'chile_currency_value_clp',
        'Currency value in Chilean Pesos',
        ['code', 'name'],
        registry=registry
    )
    
    # Important currencies to track
    important_currencies = ['UF', 'USD', 'EUR', 'UTM', 'GBP', 'CAD', 'AUD', 'BRL', 'ARS', 'MXN']
    
    for currency in data:
        try:
            code = currency.get('Codigo', '').strip()
            name = currency.get('Nombre', 'Unknown').strip()
            
            # Only process important currencies
            if code not in important_currencies:
                continue
            
            # Handle comma as decimal separator
            value_str = currency.get('Valor', '0').replace(',', '.')
            value = float(value_str)
            
            currency_gauge.labels(code=code, name=name).set(value)
            
            print(f"Currency: {code} ({name}) = {value} CLP")
        except (ValueError, TypeError) as e:
            print(f"Error processing currency {currency}: {e}")


def push_metrics():
    """Collect all metrics and push to Grafana Cloud."""
    print(f"Starting metrics collection at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Pushing to: {PROMETHEUS_URL}")
    
    # Create a new registry for this run
    registry = CollectorRegistry()
    
    # Collect all metrics
    collect_weather_metrics(registry)
    collect_earthquake_metrics(registry)
    collect_currency_metrics(registry)
    
    # Push to Grafana Cloud
    try:
        # For Grafana Cloud, we use the /api/prom/push endpoint
        gateway_url = PROMETHEUS_URL.rstrip('/')
        
        push_to_gateway(
            gateway=gateway_url,
            job='chile_metrics',
            registry=registry,
            handler=auth_handler
        )
        print("✅ Metrics pushed successfully!")
    except Exception as e:
        print(f"❌ Error pushing metrics: {e}")
        raise


if __name__ == "__main__":
    if not all([PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASSWORD]):
        print("Error: Missing environment variables")
        print("Required: PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASSWORD")
        exit(1)
    
    push_metrics()
