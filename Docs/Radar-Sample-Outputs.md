# Cloudflare Radar Sample Outputs

This document records one successful sample response for every Cloudflare Radar endpoint currently used by the project.

The complete raw JSON responses are stored in [`../radar-samples/`](../radar-samples/). The examples below show the response shape and representative values without duplicating the full 167-point timeseries payloads.

## Collection

The samples were collected with:

```text
Top, location, and summary endpoints: dateRange=1d
Timeseries endpoints: dateRange=7d&aggInterval=1h
Collected: 2026-08-15
```

All 11 sample responses returned:

```json
{
  "success": true,
  "errors": [],
  "result": {}
}
```

## Endpoint Inventory

| Sample file | Endpoint | Result key | Sample size | Normalization | Units |
| --- | --- | --- | ---: | --- | --- |
| `layer3-top-attacks.json` | `/attacks/layer3/top/attacks?limit=100&dateRange=1d` | `top_0` | 100 | `PERCENTAGE` | bytes |
| `layer7-top-attacks.json` | `/attacks/layer7/top/attacks?limit=100&dateRange=1d` | `top_0` | 100 | `PERCENTAGE` | requests |
| `layer3-top-origin.json` | `/attacks/layer3/top/locations/origin?limit=50&dateRange=1d` | `top_0` | 50 | `PERCENTAGE` | bytes |
| `layer3-top-target.json` | `/attacks/layer3/top/locations/target?limit=50&dateRange=1d` | `top_0` | 50 | `PERCENTAGE` | bytes |
| `layer7-top-origin.json` | `/attacks/layer7/top/locations/origin?limit=50&dateRange=1d` | `top_0` | 50 | `PERCENTAGE` | requests |
| `layer7-top-target.json` | `/attacks/layer7/top/locations/target?limit=50&dateRange=1d` | `top_0` | 50 | `PERCENTAGE` | requests |
| `layer3-summary-protocol.json` | `/attacks/layer3/summary/protocol?dateRange=1d` | `summary_0` | 4 | `PERCENTAGE` | bytes |
| `layer3-summary-vector.json` | `/attacks/layer3/summary/vector?dateRange=1d` | `summary_0` | 10 | `PERCENTAGE` | bytes |
| `layer7-summary-http-method.json` | `/attacks/layer7/summary/http_method?dateRange=1d` | `summary_0` | 10 | `PERCENTAGE` | requests |
| `layer3-timeseries.json` | `/attacks/layer3/timeseries?dateRange=7d&aggInterval=1h` | `serie_0` | 167 | `MIN0_MAX` | bytes |
| `layer7-timeseries.json` | `/attacks/layer7/timeseries?dateRange=7d&aggInterval=1h` | `serie_0` | 167 | `MIN0_MAX` | requests |

## Top Attack Pairs

These are the most useful responses for generating source-country to target-country visualization arcs.

### Layer 3

File: [`layer3-top-attacks.json`](../radar-samples/layer3-top-attacks.json)

The response contains 100 records. The sample records do not contain `rank`.

```json
[
  {
    "originCountryAlpha2": "BR",
    "originCountryName": "Brazil",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "6.844203"
  },
  {
    "originCountryAlpha2": "US",
    "originCountryName": "United States",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "4.639382"
  },
  {
    "originCountryAlpha2": "US",
    "originCountryName": "United States",
    "targetCountryName": "China",
    "targetCountryAlpha2": "CN",
    "value": "4.425545"
  },
  {
    "originCountryAlpha2": "BR",
    "originCountryName": "Brazil",
    "targetCountryName": "Hong Kong",
    "targetCountryAlpha2": "HK",
    "value": "3.073432"
  },
  {
    "originCountryAlpha2": "DE",
    "originCountryName": "Germany",
    "targetCountryName": "China",
    "targetCountryAlpha2": "CN",
    "value": "2.811189"
  }
]
```

Metadata:

```json
{
  "normalization": "PERCENTAGE",
  "units": [{ "name": "*", "value": "bytes" }],
  "dateRange": [{
    "startTime": "2026-08-14T09:00:00Z",
    "endTime": "2026-08-15T09:00:00Z"
  }],
  "lastUpdated": "2026-08-15T08:15:00Z"
}
```

### Layer 7

File: [`layer7-top-attacks.json`](../radar-samples/layer7-top-attacks.json)

The response contains 100 records and includes `rank`.

```json
[
  {
    "originCountryAlpha2": "US",
    "originCountryName": "United States",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "16.027051",
    "rank": 1
  },
  {
    "originCountryAlpha2": "CN",
    "originCountryName": "China",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "10.476354",
    "rank": 2
  },
  {
    "originCountryAlpha2": "SG",
    "originCountryName": "Singapore",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "2.850384",
    "rank": 3
  },
  {
    "originCountryAlpha2": "JP",
    "originCountryName": "Japan",
    "targetCountryName": "United States",
    "targetCountryAlpha2": "US",
    "value": "2.717078",
    "rank": 4
  },
  {
    "originCountryAlpha2": "US",
    "originCountryName": "United States",
    "targetCountryName": "Canada",
    "targetCountryAlpha2": "CA",
    "value": "2.709118",
    "rank": 5
  }
]
```

Metadata uses `PERCENTAGE` normalization and `requests` as the unit.

## Top Origin Countries

These responses describe origin-country distributions. They do not identify source-to-target pairs.

### Layer 3 Origins

File: [`layer3-top-origin.json`](../radar-samples/layer3-top-origin.json)

```json
[
  { "originCountryAlpha2": "US", "originCountryName": "United States", "value": "16.49431", "rank": 1 },
  { "originCountryAlpha2": "BR", "originCountryName": "Brazil", "value": "14.733838", "rank": 2 },
  { "originCountryAlpha2": "CL", "originCountryName": "Chile", "value": "5.311455", "rank": 3 },
  { "originCountryAlpha2": "DE", "originCountryName": "Germany", "value": "4.35855", "rank": 4 },
  { "originCountryAlpha2": "FR", "originCountryName": "France", "value": "4.217471", "rank": 5 }
]
```

The complete response contains 50 records, with `PERCENTAGE` normalization and `bytes` as the unit.

### Layer 7 Origins

File: [`layer7-top-origin.json`](../radar-samples/layer7-top-origin.json)

```json
[
  { "originCountryAlpha2": "US", "originCountryName": "United States", "value": "24.313896", "rank": 1 },
  { "originCountryAlpha2": "CN", "originCountryName": "China", "value": "6.411565", "rank": 2 },
  { "originCountryAlpha2": "ID", "originCountryName": "Indonesia", "value": "5.847621", "rank": 3 },
  { "originCountryAlpha2": "DE", "originCountryName": "Germany", "value": "4.911142", "rank": 4 },
  { "originCountryAlpha2": "SG", "originCountryName": "Singapore", "value": "4.200095", "rank": 5 }
]
```

The complete response contains 50 records, with `PERCENTAGE` normalization and `requests` as the unit.

## Top Target Countries

These responses describe target-country distributions. They do not identify source-to-target pairs.

### Layer 3 Targets

File: [`layer3-top-target.json`](../radar-samples/layer3-top-target.json)

```json
[
  { "targetCountryAlpha2": "US", "targetCountryName": "United States", "value": "44.568155", "rank": 1 },
  { "targetCountryAlpha2": "CN", "targetCountryName": "China", "value": "24.092388", "rank": 2 },
  { "targetCountryAlpha2": "HK", "targetCountryName": "Hong Kong", "value": "22.491364", "rank": 3 },
  { "targetCountryAlpha2": "BR", "targetCountryName": "Brazil", "value": "4.880554", "rank": 4 },
  { "targetCountryAlpha2": "DE", "targetCountryName": "Germany", "value": "2.175515", "rank": 5 }
]
```

The complete response contains 50 records, with `PERCENTAGE` normalization and `bytes` as the unit.

### Layer 7 Targets

File: [`layer7-top-target.json`](../radar-samples/layer7-top-target.json)

```json
[
  { "targetCountryAlpha2": "US", "targetCountryName": "United States", "value": "50.889206", "rank": 1 },
  { "targetCountryAlpha2": "CA", "targetCountryName": "Canada", "value": "8.296641", "rank": 2 },
  { "targetCountryAlpha2": "KE", "targetCountryName": "Kenya", "value": "2.913623", "rank": 3 },
  { "targetCountryAlpha2": "CN", "targetCountryName": "China", "value": "2.862284", "rank": 4 },
  { "targetCountryAlpha2": "CY", "targetCountryName": "Cyprus", "value": "2.741767", "rank": 5 }
]
```

The complete response contains 50 records, with `PERCENTAGE` normalization and `requests` as the unit.

## Layer 3 Summaries

### Protocol Summary

File: [`layer3-summary-protocol.json`](../radar-samples/layer3-summary-protocol.json)

```json
{
  "UDP": "76.322904",
  "TCP": "23.578538",
  "GRE": "0.080067",
  "ICMP": "0.018011"
}
```

The values are percentages of observed Layer 3 attack bytes for the one-day window.

### Attack Vector Summary

File: [`layer3-summary-vector.json`](../radar-samples/layer3-summary-vector.json)

```json
{
  "Mirai (UDP) Flood": "49.223582",
  "SYN Flood": "22.255776",
  "UDP Flood": "21.771216",
  "DNS Flood": "1.565201",
  "SFU Flood": "1.420612",
  "DNS Amplification": "1.094607",
  "ACK Flood": "0.593283",
  "Mirai (TCP) Flood": "0.343232",
  "QUIC Flood": "0.309615",
  "other": "1.422876"
}
```

The values are percentages of observed Layer 3 attack bytes for the one-day window.

## Layer 7 Summary

### HTTP Method Summary

File: [`layer7-summary-http-method.json`](../radar-samples/layer7-summary-http-method.json)

```json
{
  "GET": "83.428205",
  "POST": "12.93838",
  "HEAD": "2.605425",
  "OPTIONS": "0.401941",
  "PATCH": "0.205649",
  "PUT": "0.17063",
  "DELETE": "0.163636",
  "UNKNOWN": "0.085916",
  "ACL": "0.000204",
  "other": "1.4e-05"
}
```

The values are percentages of observed Layer 7 attack requests for the one-day window.

## Timeseries Responses

Timeseries responses contain 167 hourly points for the seven-day request. The complete timestamp and value arrays remain in the raw JSON files.

### Layer 3 Timeseries

File: [`layer3-timeseries.json`](../radar-samples/layer3-timeseries.json)

```json
{
  "serie_0": {
    "timestamps": [
      "2026-08-08T09:00:00Z",
      "2026-08-08T10:00:00Z",
      "2026-08-08T11:00:00Z"
    ],
    "values": ["0.06777", "0.197944", "0.42822"]
  },
  "meta": {
    "normalization": "MIN0_MAX",
    "aggInterval": "ONE_HOUR",
    "units": [{ "name": "*", "value": "bytes" }]
  }
}
```

Last three points in the collected response:

```text
2026-08-15T05:00:00Z = 0.112243
2026-08-15T06:00:00Z = 0.596707
2026-08-15T07:00:00Z = 0.519944
```

### Layer 7 Timeseries

File: [`layer7-timeseries.json`](../radar-samples/layer7-timeseries.json)

```json
{
  "serie_0": {
    "timestamps": [
      "2026-08-08T09:00:00Z",
      "2026-08-08T10:00:00Z",
      "2026-08-08T11:00:00Z"
    ],
    "values": ["0.790072", "0.791859", "0.854627"]
  },
  "meta": {
    "normalization": "MIN0_MAX",
    "aggInterval": "ONE_HOUR",
    "units": [{ "name": "*", "value": "requests" }]
  }
}
```

Last three points in the collected response:

```text
2026-08-15T05:00:00Z = 0.820236
2026-08-15T06:00:00Z = 0.848321
2026-08-15T07:00:00Z = 0.854864
```

## Backend Parsing Notes

### Percentage conversion

Radar returns percentage values as strings on the `0` to `100` scale:

```text
"6.844203" -> 6.844203 percent -> 0.06844203 share
```

The backend should parse values as `Decimal` or validated floats, then divide by `100` before storing them in the database field defined as `attack_share` in the `0` to `1` range.

### Layer units

Layer 3 and Layer 7 values must not be combined without preserving their units:

```text
L3: bytes
L7: requests
```

The values are percentages, not absolute bytes, requests, Mbps, or packets per second.

### Timeseries interpretation

The timeseries responses use `MIN0_MAX` normalization. These values are useful for relative chart intensity, but they must not be presented as real traffic volume. Do not label them as Mbps or absolute request counts.

### Pair versus country distributions

Use the `top/attacks` responses to create source-to-target visualization samples. The origin-only and target-only responses are useful for country rankings and analytics, but they cannot reconstruct source-to-target pairs.

### Optional fields

The Layer 3 pair response does not include `rank` in this sample, while the Layer 7 pair response does. The parser should therefore treat `rank` as optional for pair records.

### Data attribution

These responses are real Cloudflare Radar aggregate telemetry. A generated visualization event sampled from these distributions should be marked:

```json
{
  "real": true,
  "source": "cloudflare_radar"
}
```

The generated event is still a representative visualization sample, not an individually observed packet or exact attack location.

## Raw Samples

- [`layer3-top-attacks.json`](../radar-samples/layer3-top-attacks.json)
- [`layer7-top-attacks.json`](../radar-samples/layer7-top-attacks.json)
- [`layer3-top-origin.json`](../radar-samples/layer3-top-origin.json)
- [`layer3-top-target.json`](../radar-samples/layer3-top-target.json)
- [`layer7-top-origin.json`](../radar-samples/layer7-top-origin.json)
- [`layer7-top-target.json`](../radar-samples/layer7-top-target.json)
- [`layer3-summary-protocol.json`](../radar-samples/layer3-summary-protocol.json)
- [`layer3-summary-vector.json`](../radar-samples/layer3-summary-vector.json)
- [`layer7-summary-http-method.json`](../radar-samples/layer7-summary-http-method.json)
- [`layer3-timeseries.json`](../radar-samples/layer3-timeseries.json)
- [`layer7-timeseries.json`](../radar-samples/layer7-timeseries.json)
