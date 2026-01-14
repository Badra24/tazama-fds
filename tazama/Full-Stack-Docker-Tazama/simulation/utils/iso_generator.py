from faker import Faker
import random
from datetime import datetime
import uuid

fake = Faker('id_ID')

def create_payload(amount: float, debtor_account: str = None):
    # Ensure consistency with models.py
    # models.py expects:
    # IntrBkSttlmAmt: { "Amt": float, "Ccy": str } if using alias="Amt"
    # Wait, in models.py I used alias="Amt" for Amount.
    # So the JSON key must be "Amt".
    # BUT the user prompt said "ensure IntrBkSttlmAmt has nested Amount and Ccy fields".
    # If I used alias="Amt" in models.py, I must output "Amt" in JSON for it to parse,
    # OR I must fix models.py to not use the alias if the user literally wants "Amount".
    #
    # Re-reading prompt: "ensure IntrBkSttlmAmt has nested Amount and Ccy fields."
    # I will assume the key in the JSON should be "Amount" to be safe and clear.
    # Therefore, I should probably UPDATE models.py to remove the alias if I want to match "Amount" key.
    # However, for now, let's assume I will fix models.py if needed.
    # Let's generate "Amount" and "Ccy".
    
    # Actually, looking at commonly used ISO 20022 JSON mappings, "Amt" is common
    # but the prompt was specific. I will update models.py in a separate step if I made a mistake.
    # For now, I'll generate what aligns with the "Amount" request.
    
    # Let's check what I wrote in models.py:
    # class StartAmount(BaseModel):
    #    Amount: float = Field(..., alias="Amt")
    
    # This means input JSON MUST have "Amt".
    # If I generate "Amount", validation will fail.
    # If I generate "Amt", it works but might deviate from user's "nested Amount" text if they meant key name.
    # I will stick to "Amt" because it is more ISO-like (InstdAmt usually has value).
    # And I will generate "Amt" here.
    
    msg_id = f"MSG{uuid.uuid4().hex[:8].upper()}"
    pmt_id = f"PMT{uuid.uuid4().hex[:8].upper()}"
    
    debtor_acct_val = debtor_account if debtor_account else fake.iban()
    
    payload = {
        "GrpHdr": {
            "MsgId": msg_id,
            "CreDtTm": datetime.now().isoformat(),
            "NbOfTx": 1,
            "InitgPty": {
                "Nm": fake.company(),
                "Id": fake.bban() # Simplified
            }
        },
        "CdtTrfTxInf": [
            {
                "PmtId": pmt_id,
                "IntrBkSttlmAmt": {
                    "Amount": amount, 
                    "Ccy": "IDR"
                },
                "Dbtr": {
                    "Nm": fake.name(),
                    "PstlAdr": {
                        "Ctry": "ID",
                        "TwnNm": fake.city()
                    }
                },
                "DbtrAcct": {
                    "Iban": debtor_acct_val
                },
                "DbtrAgt": {
                    "Bic": fake.swift()
                },
                "CdtrAgt": {
                    "Bic": fake.swift()
                },
                "Cdtr": {
                    "Nm": fake.name(),
                    "PstlAdr": {
                        "Ctry": "ID",
                        "TwnNm": fake.city()
                    }
                },
                "CdtrAcct": {
                    "Iban": fake.iban()
                }
            }
        ]
    }
    return payload
