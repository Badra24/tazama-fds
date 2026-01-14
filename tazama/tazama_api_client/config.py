
import os

# ============================================================================
# Deployment Configuration
# ============================================================================

# Set to True to use Local PostgreSQL (tazama-local-db - port 3001)
# Set to False to use Full Docker (Full-Stack-Docker-Tazama - port 3000)
USE_LOCAL_POSTGRES = False  # Default: Full Docker

# ============================================================================
# TAZAMA ENDPOINT CONFIGURATION (Auto-configured based on deployment)
# ============================================================================

# Auto-select TMS URL based on deployment
if USE_LOCAL_POSTGRES:
    # Local PostgreSQL deployment (tazama-local-db)
    TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:3001")
else:
    # Full Docker deployment (Full-Stack-Docker-Tazama)
    # Note: TMS container maps 5001:3000 (external:internal)
    TMS_BASE_URL = os.getenv("TMS_BASE_URL", "http://localhost:5001")

# ============================================================================

SOURCE_TENANT_ID = os.getenv("SOURCE_TENANT_ID", "DEFAULT")

# TMS Endpoints
TMS_ENDPOINTS = {
    "health": "/",
    "pain001": "/v1/evaluate/iso20022/pain.001.001.11",
    "pain013": "/v1/evaluate/iso20022/pain.013.001.09",
    "pacs008": "/v1/evaluate/iso20022/pacs.008.001.10",
    "pacs002": "/v1/evaluate/iso20022/pacs.002.001.12"
}

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8080"))

# Timeout Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

# HTTP Status Codes yang dianggap sukses
VALID_STATUS_CODES = [200, 201, 202]

# Company-wide high value threshold
COMPANY_HIGH_VALUE_THRESHOLD = 15000000  # Rp 15 juta

# Rule Timing Configuration
RULE_006_WINDOW_HOURS = 24      # Time window untuk detect structuring
RULE_006_MIN_TRANSACTIONS = 3   # Minimum transaksi untuk trigger
RULE_006_SIMILARITY = 0.8       # Threshold similarity (80%)

# Rule 018 Configuration
RULE_018_MULTIPLIER = 1.5       # Alert jika > 1.5x historical average

