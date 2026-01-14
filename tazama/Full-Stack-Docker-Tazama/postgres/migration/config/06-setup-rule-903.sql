
-- ============================================================================
-- RULE 903: GEO-LOCATION RISK DETECTION
-- ============================================================================
--
-- FUNGSI:
--   Mendeteksi transaksi dari lokasi geografis dengan tingkat risiko berbeda.
--   Tazama akan menentukan risk level berdasarkan city/region dari transaksi.
--
-- PARAMETER:
--   - riskZones: Definisi zona high/medium/low risk berdasarkan city/region
--
-- BANDS (Risk Levels):
--   - .01: High Risk Zone    → 🔴 STRICT (Jakarta, Tangerang, Surabaya)
--   - .02: Medium Risk Zone  → 🟡 WARNING (Bandung, Semarang, Bali)
--   - .03: Low Risk Zone     → 🟢 NORMAL (other cities)
--
-- CONTOH KASUS:
--   1. Transaksi dari Jakarta → Rule 903 return .01 (high risk)
--   2. Transaksi dari Bandung → Rule 903 return .02 (medium risk)
--   3. Transaksi dari Yogyakarta → Rule 903 return .03 (low risk)
--
--
-- Rule 903: Geographic Risk Detection
-- This rule analyzes transaction geo-location data to determine risk levels
-- based on configured high, medium, and low risk zones.

\connect configuration;

-- Create required helper function for tenant-aware queries
-- This function is used by @tazama-lf/frms-coe-lib to set tenant context
CREATE OR REPLACE FUNCTION public.set_tenant_id(tenant_id TEXT)
RETURNS VOID AS $$
BEGIN
  PERFORM set_config('app.current_tenant', tenant_id, true);
END;
$$ LANGUAGE plpgsql;

-- Insert Rule 903 configuration
INSERT INTO rule (configuration)
VALUES (
    '{
  "id": "903@1.0.0",
  "cfg": "1.0.0",
  "tenantId": "DEFAULT",
  "desc": "Geographic Risk Detection - City/Region-based risk scoring",
  "config": {
    "parameters": {
      "riskZones": {
        "high": [
          "Jakarta",
          "Tangerang",
          "Surabaya"
        ],
        "medium": [
          "Bandung",
          "Semarang",
          "Bali",
          "Denpasar"
        ],
        "low": []
      }
    },
    "exitConditions": [
      {
        "subRuleRef": ".x00",
        "reason": "Geo-location data not available"
      }
    ],
    "bands": [
      {
        "subRuleRef": ".01",
        "reason": "Transaction from HIGH RISK zone"
      },
      {
        "subRuleRef": ".02",
        "reason": "Transaction from MEDIUM RISK zone"
      },
      {
        "subRuleRef": ".03",
        "reason": "Transaction from LOW RISK zone"
      }
    ]
  }
}'
)
ON CONFLICT (id) DO UPDATE
SET configuration = EXCLUDED.configuration;

-- Update network map to include Rule 903 for pacs.008 (Credit Transfer)
DELETE FROM network_map 
WHERE messages LIKE '%"pacs.008.001.10"%' 
AND rules::text LIKE '%"903@1.0.0"%';

INSERT INTO network_map (messages, rules)
SELECT 
    messages,
    (rules::jsonb || '["903@1.0.0"]'::jsonb)::text::json
FROM network_map
WHERE messages LIKE '%"pacs.008.001.10"%'
AND NOT (rules::text LIKE '%"903@1.0.0"%')
ON CONFLICT (messages) DO UPDATE
SET rules = (
    SELECT (EXCLUDED.rules::jsonb || '["903@1.0.0"]'::jsonb)::text::json
    WHERE NOT (network_map.rules::text LIKE '%"903@1.0.0"%')
);

-- Update network map to include Rule 903 for pacs.002 (Payment Status)
DELETE FROM network_map 
WHERE messages LIKE '%"pacs.002.001.12"%' 
AND rules::text LIKE '%"903@1.0.0"%';

INSERT INTO network_map (messages, rules)
SELECT 
    messages,
    (rules::jsonb || '["903@1.0.0"]'::jsonb)::text::json
FROM network_map
WHERE messages LIKE '%"pacs.002.001.12"%'
AND NOT (rules::text LIKE '%"903@1.0.0"%')
ON CONFLICT (messages) DO UPDATE
SET rules = (
    SELECT (EXCLUDED.rules::jsonb || '["903@1.0.0"]'::jsonb)::text::json
    WHERE NOT (network_map.rules::text LIKE '%"903@1.0.0"%')
);

-- Create Typology 999 for Rule 903 (Geographic Risk Scoring)
INSERT INTO typology (configuration)
VALUES (
    '{
  "id": "typology-processor@1.0.0",
  "cfg": "999-903@1.0.0",
  "rules": [
    {
      "id": "903@1.0.0",
      "cfg": "1.0.0",
      "wghts": [
        {"ref": ".x00", "wght": "0"},
        {"ref": ".01", "wght": "100"},
        {"ref": ".02", "wght": "50"},
        {"ref": ".03", "wght": "10"}
      ],
      "termId": "v903at100at100"
    },
    {
      "id": "EFRuP@1.0.0",
      "cfg": "none",
      "wghts": [
        {"ref": ".err", "wght": "0"},
        {"ref": "override", "wght": "0"},
        {"ref": "non-overridable-block", "wght": "0"},
        {"ref": "overridable-block", "wght": "0"},
        {"ref": "none", "wght": "0"}
      ],
      "termId": "vEFRuPat100atnone"
    }
  ],
  "tenantId": "DEFAULT",
  "workflow": {
    "flowProcessor": "EFRuP@1.0.0",
    "alertThreshold": 50,
    "interdictionThreshold": 100
  },
  "expression": ["Add", "v903at100at100"],
  "typology_name": "Typology-999-Geographic-Risk"
}'
)
ON CONFLICT (typologyid, typologycfg, tenantid) DO UPDATE
SET configuration = EXCLUDED.configuration;

-- Verify Rule 903 installation
SELECT 'Rule 903 Configuration:' as info;
SELECT id, cfg, description, tenantid 
FROM rule 
WHERE id = '903@1.0.0';

SELECT 'Network Map for pacs.008:' as info;
SELECT messages, rules 
FROM network_map 
WHERE messages LIKE '%"pacs.008.001.10"%';

SELECT 'Network Map for pacs.002:' as info;
SELECT messages, rules 
FROM network_map 
WHERE messages LIKE '%"pacs.002.001.12"%';
