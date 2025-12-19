#!/usr/bin/env python3
"""
Chile Metrics Collector
Fetches data from Chilean public APIs and pushes to Grafana Cloud using Remote Write.
"""

import os
import time
import requests

# Configuration from environment variables
PROMETHEUS_URL = os.environ.get("PROMETHEUS_URL", "")
PROMETHEUS_USER = os.environ.get("PROMETHEUS_USER", "")
PROMETHEUS_PASSWORD = os.environ.get("PROMETHEUS_PASSWORD", "")

# API Endpoints
API_CLIMA = "https://api.gael.cloud/general/public/clima"
API_SISMOS = "https://api.gael.cloud/general/public/sismos"
API_MONEDAS = "https://api.gael.cloud/general/public/monedas"


def fetch_json(url: str) -> list:
    """Fetch JSON data from an API endpoint."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def build_write_request(metrics: list) -> bytes:
    """
    Build a Prometheus Remote Write request.
    Uses the protobuf format expected by Grafana Cloud.
    """
    # Import here to avoid issues if not installed
    from prometheus_pb2 import WriteRequest, TimeSeries, Label, Sample
    
    write_request = WriteRequest()
    timestamp_ms = int(time.time() * 1000)
    
    for metric in metrics:
        ts = write_request.timeseries.add()
        
        # Add __name__ label
        label = ts.labels.add()
        label.name = "__name__"
        label.value = metric["name"]
        
        # Add other labels
        for label_name, label_value in metric.get("labels", {}).items():
            l = ts.labels.add()
            l.name = label_name
            l.value = str(label_value)
        
        # Add sample
        sample = ts.samples.add()
        sample.value = float(metric["value"])
        sample.timestamp = timestamp_ms
    
    return write_request.SerializeToString()


def push_metrics_simple(metrics: list):
    """
    Push metrics to Grafana Cloud using the Influx line protocol.
    This is a simpler approach that works with Grafana Cloud.
    """
    # Build metrics in Prometheus exposition format
    lines = []
    timestamp_ms = int(time.time() * 1000)
    
    for metric in metrics:
        name = metric["name"]
        value = metric["value"]
        labels = metric.get("labels", {})
        
        if labels:
            label_str = ",".join([f'{k}="{v}"' for k, v in labels.items()])
            lines.append(f"{name}{{{label_str}}} {value}")
        else:
            lines.append(f"{name} {value}")
    
    body = "\n".join(lines)
    
    # Push to Grafana Cloud Prometheus
    url = f"{PROMETHEUS_URL}/api/v1/push"
    
    headers = {
        "Content-Type": "text/plain",
    }
    
    try:
        response = requests.post(
            url,
            data=body,
            headers=headers,
            auth=(PROMETHEUS_USER, PROMETHEUS_PASSWORD),
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ Pushed {len(metrics)} metrics successfully!")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text if e.response else 'No response'}")
        return False
    except Exception as e:
        print(f"❌ Error pushing metrics: {e}")
        return False


def push_metrics_influx(metrics: list):
    """
    Push metrics using Influx line protocol (supported by Grafana Cloud).
    """
    timestamp_ns = int(time.time() * 1e9)
    lines = []
    
    for metric in metrics:
        name = metric["name"]
        value = metric["value"]
        labels = metric.get("labels", {})
        
        # Build tags string
        if labels:
            tags = ",".join([f'{k}={v.replace(" ", "_").replace(",", "")}' for k, v in labels.items()])
            line = f"{name},{tags} value={value} {timestamp_ns}"
        else:
            line = f"{name} value={value} {timestamp_ns}"
        
        lines.append(line)
    
    body = "\n".join(lines)
    
    # Grafana Cloud Influx endpoint
    url = f"{PROMETHEUS_URL}/api/v1/push/influx/write"
    
    try:
        response = requests.post(
            url,
            data=body,
            auth=(PROMETHEUS_USER, PROMETHEUS_PASSWORD),
            timeout=30
        )
        response.raise_for_status()
        print(f"✅ Pushed {len(metrics)} metrics successfully!")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error {e.response.status_code}: {e}")
        if e.response:
            print(f"Response: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def collect_all_metrics() -> list:
    """Collect all metrics from Chilean APIs."""
    metrics = []
    
    # Weather metrics
    weather_data = fetch_json(API_CLIMA)
    for station in weather_data:
        try:
            station_name = station.get('Estacion', 'Unknown')
            station_code = station.get('Codigo', 'Unknown')
            temp = float(station.get('Temp', 0))
            humidity = float(station.get('Humedad', 0))
            
            metrics.append({
                "name": "chile_temperature_celsius",
                "value": temp,
                "labels": {"station": station_name, "code": station_code}
            })
            
            metrics.append({
                "name": "chile_humidity_percent",
                "value": humidity,
                "labels": {"station": station_name, "code": station_code}
            })
            
            print(f"Weather: {station_name} - {temp}°C, {humidity}%")
        except (ValueError, TypeError) as e:
            print(f"Error processing weather: {e}")
    
    # Earthquake metrics
    quake_data = fetch_json(API_SISMOS)
    for i, quake in enumerate(quake_data[:10]):
        try:
            location = quake.get('RefGeografica', 'Unknown')[:40]
            location = location.replace('"', '').replace("'", "").replace(",", "")
            magnitude = float(quake.get('Magnitud', 0))
            depth = float(quake.get('Profundidad', 0))
            
            metrics.append({
                "name": "chile_earthquake_magnitude",
                "value": magnitude,
                "labels": {"location": location, "index": str(i)}
            })
            
            metrics.append({
                "name": "chile_earthquake_depth_km",
                "value": depth,
                "labels": {"location": location, "index": str(i)}
            })
            
            print(f"Earthquake: {magnitude} - {location}")
        except (ValueError, TypeError) as e:
            print(f"Error processing earthquake: {e}")
    
    # Currency metrics
    currency_data = fetch_json(API_MONEDAS)
    important = ['UF', 'USD', 'EUR', 'UTM', 'GBP', 'CAD', 'AUD', 'BRL', 'ARS', 'MXN']
    
    for currency in currency_data:
        try:
            code = currency.get('Codigo', '').strip()
            if code not in important:
                continue
            
            name = currency.get('Nombre', 'Unknown').strip()
            value_str = currency.get('Valor', '0').replace(',', '.')
            value = float(value_str)
            
            metrics.append({
                "name": "chile_currency_clp",
                "value": value,
                "labels": {"code": code, "name": name}
            })
            
            print(f"Currency: {code} = {value} CLP")
        except (ValueError, TypeError) as e:
            print(f"Error processing currency: {e}")
    
    return metrics


def main():
    print(f"🇨🇱 Chile Metrics Collector")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {PROMETHEUS_URL}")
    print("-" * 50)
    
    if not all([PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASSWORD]):
        print("❌ Missing environment variables!")
        exit(1)
    
    # Collect metrics
    metrics = collect_all_metrics()
    print("-" * 50)
    print(f"Collected {len(metrics)} metrics")
    
    # Try Influx protocol first
    if push_metrics_influx(metrics):
        return
    
    # Fallback to simple push
    print("Trying alternative push method...")
    push_metrics_simple(metrics)


if __name__ == "__main__":
    main()
