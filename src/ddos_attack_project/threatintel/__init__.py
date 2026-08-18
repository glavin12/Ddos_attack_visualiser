"""Threat intelligence ingestion for the Threat Observatory.

The threatintel package fetches real IOCs from public feeds (abuse.ch
URLhaus / Feodo Tracker / ThreatFox), enriches them with GreyNoise
Community context, geolocates them via MaxMind GeoLite2, and persists them
to the ``threat_indicators`` table. Every indicator has a real source feed
citation and a real observation timestamp — none of it is fabricated.
"""
