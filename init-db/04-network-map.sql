\connect configuration;

insert into
    network_map (configuration)
    -- NOTE: To add more rules, append them to the 'rules' array inside the JSON 'typologies' object below.
values (
        '{
  "active": true,
  "name": "Public Network Map",
  "cfg": "1.0.0",
  "tenantId": "DEFAULT",
  "messages": [
    {
      "id": "004@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.002.001.12",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999-901@1.0.0",
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
            },
            {
              "id": "903@1.0.0",
              "cfg": "1.0.0"
            }
          ]
        }
      ]
    },
    {
      "id": "008@1.0.0",
      "cfg": "1.0.0",
      "txTp": "pacs.008.001.10",
      "typologies": [
        {
          "id": "typology-processor@1.0.0",
          "cfg": "999-901@1.0.0",
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
            },
            {
              "id": "903@1.0.0",
              "cfg": "1.0.0"
            }
          ]
        }
      ]
    }
  ]
}'
    );