\connect configuration;

-- ============================================================================
-- RULE 006: STRUCTURING / SMURFING DETECTION
-- ============================================================================

delete from rule where ruleid = '006@1.0.0' and tenantid = 'DEFAULT';

insert into rule (configuration) values (
'{
    "id": "006@1.0.0",
    "cfg": "1.0.0",
    "tenantId": "DEFAULT",
    "desc": "Outgoing transfer similarity - amounts",
    "config": {
      "parameters": {
        "maxQueryLimit": 5,
        "tolerance": 0.2
      },
      "exitConditions": [
        {
          "subRuleRef": ".x00",
          "reason": "Incoming transaction is unsuccessful"
        },
        {
          "subRuleRef": ".x01",
          "reason": "Insufficient transaction history"
        }
      ],
      "bands": [
        {
          "subRuleRef": ".01",
          "upperLimit": 5,
          "reason": "No similar amounts detected in the most recent transactions from the debtor"
        },
        {
          "subRuleRef": ".02",
          "lowerLimit": 5,
          "reason": "Two or more similar amounts detected in the most recent transactions from the debtor"
        }
      ]
    }
}');

-- ============================================================================
-- RULE 018: HIGH VALUE TRANSFER DETECTION
-- ============================================================================

delete from rule where ruleid = '018@1.0.0' and tenantid = 'DEFAULT';

insert into rule (configuration) values (
'{
    "id": "018@1.0.0",
    "cfg": "1.0.0",
    "tenantId": "DEFAULT",
    "desc": "Exceptionally large outgoing transfer - debtor",
    "config": {
      "parameters": {
        "maxQueryRange": 2592000000
      },
      "exitConditions": [
        {
          "subRuleRef": ".x00",
          "reason": "Incoming transaction is unsuccessful"
        },
        {
          "subRuleRef": ".x01",
          "reason": "Insufficient transaction history"
        }
      ],
      "bands": [
        {
          "subRuleRef": ".01",
          "upperLimit": 1.5,
          "reason": "Outgoing transfer within historical limits"
        },
        {
          "subRuleRef": ".02",
          "lowerLimit": 1.5,
          "reason": "Exceptionally large outgoing transfer detected"
        }
      ]
    }
}');

-- ============================================================================
-- NETWORK MAP: pacs.008 + pacs.002 dengan semua fraud rules
-- ============================================================================

delete from network_map;

insert into network_map (configuration) values (
'{
  "active": true,
  "cfg": "1.0.1",
  "name": "Public Network Map with Extra Rules",
  "tenantId": "DEFAULT",
  "messages": [
    {
      "id": "008@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.008.001.10",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999@1.0.0",
          "tenantId": "DEFAULT",
          "rules": [
            {
              "id": "EFRuP@1.0.0",
              "cfg": "none"
            },
            {
              "id": "901@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "902@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "006@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "018@1.0.0",
              "cfg": "1.0.0"
            }
          ]
        }
      ]
    },
    {
      "id": "004@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.002.001.12",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999@1.0.0",
          "tenantId": "DEFAULT",
          "rules": [
            {
              "id": "EFRuP@1.0.0",
              "cfg": "none"
            },
            {
              "id": "901@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "902@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "006@1.0.0",
              "cfg": "1.0.0"
            },
            {
              "id": "018@1.0.0",
              "cfg": "1.0.0"
            }
          ]
        }
      ]
    }
  ]
}');