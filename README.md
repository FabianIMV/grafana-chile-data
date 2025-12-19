# 🇨🇱 Chile Metrics Collector

![Dashboard Preview](assets/dashboard-preview.png)

Recopilador automático de métricas de Chile para Grafana Cloud.

Este repositorio contiene un sistema automatizado que:
- 📊 Obtiene datos de APIs públicas chilenas cada 5 minutos
- 📤 Envía las métricas a Grafana Cloud Prometheus
- 📈 Permite visualizar datos históricos en dashboards

## 📡 Fuentes de Datos

| Fuente | Datos | API |
|--------|-------|-----|
| 🌤️ Clima | Temperatura, humedad por ciudad | [api.gael.cloud/clima](https://api.gael.cloud/general/public/clima) |
| 🚨 Sismos | Magnitud, profundidad, ubicación | [api.gael.cloud/sismos](https://api.gael.cloud/general/public/sismos) |
| 💱 Monedas | UF, USD, EUR, UTM y más | [api.gael.cloud/monedas](https://api.gael.cloud/general/public/monedas) |

## 📊 Métricas Disponibles

### Clima
- `chile_temperature_celsius` - Temperatura en grados Celsius
- `chile_humidity_percent` - Porcentaje de humedad

### Sismos
- `chile_earthquake_magnitude` - Magnitud del sismo
- `chile_earthquake_depth_km` - Profundidad en kilómetros

### Monedas
- `chile_currency_clp` - Valor en pesos chilenos (UF, USD, EUR, etc.)

## 🚀 Configuración

### 1. Fork este repositorio

### 2. Configura los Secrets en GitHub

Ve a **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Agrega estos 3 secrets:

| Secret Name | Descripción | Ejemplo |
|-------------|-------------|---------|
| `PROMETHEUS_URL` | URL de Grafana Cloud (sin `/api/prom/push`) | `https://prometheus-prod-XX-prod-us-east-0.grafana.net` |
| `PROMETHEUS_USER` | Username/Instance ID | `123456` |
| `PROMETHEUS_PASSWORD` | Token de API | `glc_xxxx...` |

> ⚠️ **Importante**: La URL debe ser solo el dominio base, sin el path `/api/prom/push`

### 3. Activa GitHub Actions

El workflow se ejecutará automáticamente cada 5 minutos.

Para ejecutar manualmente:
1. Ve a **Actions**
2. Selecciona **Chile Metrics Collector**
3. Click **Run workflow**

## 📈 Consultas PromQL para Grafana

### Temperatura actual de Santiago
```promql
chile_temperature_celsius{station="Santiago Centro"}
```

### Promedio de temperatura nacional
```promql
avg(chile_temperature_celsius)
```

### Valor del dólar
```promql
chile_currency_clp{code="USD"}
```

### Valor de la UF
```promql
chile_currency_clp{code="UF"}
```

### Sismos recientes
```promql
chile_earthquake_magnitude
```

## 🔗 Dashboard Público

Puedes ver el dashboard en vivo aquí:
- [Dashboard Chile - Grafana Cloud](https://fabianignaciomv.grafana.net/public-dashboards/1626c4fe9e1f40e987f3a22111c78013)

## 📊 Dashboards Incluidos

Este repo incluye dos dashboards listos para importar:

| Dashboard | Descripción | Archivo |
|-----------|-------------|---------|
| **Chile Metrics - Histórico** | Usa Prometheus, muestra tendencias temporales | [`dashboards/chile-prometheus-dashboard.json`](dashboards/chile-prometheus-dashboard.json) |
| **Chile - Tiempo Real** | Usa Infinity, datos en vivo de APIs | [`dashboards/chile-infinity-dashboard.json`](dashboards/chile-infinity-dashboard.json) |

### Importar un Dashboard

1. Ve a Grafana → **Dashboards** → **New** → **Import**
2. Sube el archivo JSON o pega su contenido
3. Selecciona el datasource correspondiente

## 🛠️ Desarrollo Local

```bash
# Clonar el repo
git clone https://github.com/FabianIMV/grafana-chile-data.git
cd grafana-chile-data

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export PROMETHEUS_URL="https://prometheus-prod-XX-prod-us-east-0.grafana.net"
export PROMETHEUS_USER="123456"
export PROMETHEUS_PASSWORD="glc_xxxx..."

# Ejecutar
python script.py
```

## 📄 Licencia

MIT - Siéntete libre de usar, modificar y distribuir.

## 🙏 Créditos

- Datos proporcionados por [api.gael.cloud](https://api.gael.cloud/)
- Desarrollado con ❤️ para la comunidad chilena