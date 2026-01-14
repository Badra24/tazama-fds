from fastapi import FastAPI
from models import Pacs008Message
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TazamaMockTMS")

app = FastAPI(title="Tazama Mock TMS")

@app.post("/v1/evaluate/iso20022/pacs.008.001.10")
async def evaluate_transaction(message: Pacs008Message):
    # Extract relevant details for logging
    # Assuming batch of 1 for simplicity as per generator
    if message.CdtTrfTxInf:
        tx_info = message.CdtTrfTxInf[0]
        end_to_end_id = tx_info.PmtId
        amount = tx_info.IntrBkSttlmAmt.Amount
        
        # Log as requested
        print(f"💰 Received Transaction: EndToEndId={end_to_end_id}, Amount={amount}")
    
    return {"status": "ACTC", "reason": "Passed Validation"}
