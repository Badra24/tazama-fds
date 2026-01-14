"""
Transactions Router
Endpoints for pacs.008, pacs.002 quick-status, and full-transaction
"""
from fastapi import APIRouter, Form
from typing import Optional
from datetime import datetime
import time

from services.tms_client import tms_client
from utils.payload_generator import generate_pacs008, generate_pacs002
from config import VALID_STATUS_CODES
from routers.attacks import fetch_logs_internal, parse_fraud_alerts


router = APIRouter(prefix="/api/test", tags=["Transactions"])

# In-memory storage reference
test_history = []


def set_history_reference(history_list):
    global test_history
    test_history = history_list


@router.post(
    "/pacs008",
    summary="Send pacs.008 Transaction",
    description="Send a test pacs.008 (Credit Transfer) message to Tazama TMS"
)
async def test_pacs008(
    debtor_account: Optional[str] = Form(None, description="Debtor account ID"),
    creditor_account: Optional[str] = Form(None, description="Creditor account ID"),
    amount: Optional[str] = Form(None, description="Transaction amount"),
    debtor_name: Optional[str] = Form(None, description="Debtor name")
):
    """Send test pacs.008 transaction with pacs.002 confirmation to trigger Rule 901/902"""
    try:
        amt = float(amount) if amount else None
        if debtor_account and not debtor_account.strip():
            debtor_account = None
        if creditor_account and not creditor_account.strip():
            creditor_account = None
        if debtor_name and not debtor_name.strip():
            debtor_name = None

        # Step 1: Send pacs.008 (Credit Transfer)
        payload = generate_pacs008(debtor_account, amt, debtor_name, creditor_account=creditor_account)
        status_code, response_time, response_data = tms_client.send_pacs008(payload)
        
        # Get actual values from payload for context
        actual_debtor = debtor_account or payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("DbtrAcct", {}).get("Id", {}).get("Othr", [{}])[0].get("Id", "UNKNOWN")
        actual_amount = amt or float(payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("IntrBkSttlmAmt", {}).get("Amt", {}).get("Amt", 0))
        actual_name = debtor_name or payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("Dbtr", {}).get("Nm", "Unknown")
        
        msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
        e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
        
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "pacs.008",
            "status": status_code,
            "response_time_ms": response_time,
            "success": status_code == 200,
            "message_id": msg_id,
            "end_to_end_id": e2e_id,
            "debtor_account": actual_debtor,
            "amount": actual_amount
        }
        test_history.append(test_record)
        
        # Step 2: Send pacs.002 confirmation (REQUIRED for Rule 901/902)
        # Rule 901/902 expect FIToFIPmtSts (pacs.002 format), not pacs.008
        pacs002_status = None
        if status_code == 200 and msg_id and e2e_id:
            pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
            pacs002_status, _, _ = tms_client.send_pacs002(pacs002_payload)
        
        # Wait for Tazama to process both transactions
        time.sleep(0.5)
        
        # Build request context for detailed alerts
        request_context = {
            "scenario": "pacs.008 + pacs.002 Transaction",
            "debtor_account": actual_debtor,
            "debtor_name": actual_name,
            "amount_per_transaction": actual_amount,
            "total_transactions": 1
        }
        
        # Fetch fraud alerts from Tazama container logs ONLY
        fraud_alerts = []
        for container in ["tazama-rule-901-1", "tazama-rule-902-1", "tazama-rule-006-1", "tazama-rule-018-1"]:
            try:
                logs_data = fetch_logs_internal(container, tail=10, since_seconds=5)
                alerts = parse_fraud_alerts(logs_data, request_context)
                fraud_alerts.extend(alerts)
            except Exception as e:
                pass  # Ignore container fetch errors
        
        # Remove duplicates based on rule_id (show one alert per rule)
        seen_rules = set()
        unique_alerts = []
        for alert in fraud_alerts:
            if alert.get('rule_id') and alert['rule_id'] not in seen_rules:
                seen_rules.add(alert['rule_id'])
                unique_alerts.append(alert)
        
        return {
            "status": "success" if status_code == 200 else "error",
            "http_code": status_code,
            "pacs002_status": pacs002_status,
            "response_time_ms": response_time,
            "payload_sent": payload,
            "tms_response": response_data,
            "test_record": test_record,
            "fraud_alerts": unique_alerts,
            "request_summary": request_context
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post(
    "/quick-status",
    summary="Quick Status Test",
    description="Send pacs.008 + pacs.002 with selectable status code (ACCC/ACSC/RJCT)"
)
async def test_quick_status(
    status_code: str = Form("ACCC", description="Status code: ACCC, ACSC, or RJCT"),
    debtor_account: Optional[str] = Form(None, description="Debtor account ID"),
    amount: Optional[float] = Form(None, description="Transaction amount")
):
    """
    Quick Test: Send pacs.008 + pacs.002 with selectable status code.
    Supports ACCC (Accepted), ACSC (Settled), RJCT (Rejected)
    """
    if status_code not in VALID_STATUS_CODES:
        return {
            "status": "error",
            "message": f"Invalid status code. Must be one of: {', '.join(VALID_STATUS_CODES)}"
        }
    
    pacs008_payload = generate_pacs008(debtor_account, amount)
    message_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
    end_to_end_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
    
    try:
        start_time = datetime.now()
        
        # Send pacs.008
        status_008, _, _ = tms_client.send_pacs008(pacs008_payload)
        
        if status_008 == 200:
            time.sleep(0.3)
            
            pacs002_payload = generate_pacs002(message_id, end_to_end_id, status_code)
            status_002, pacs002_time, response_002 = tms_client.send_pacs002(pacs002_payload)
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            test_record = {
                "timestamp": start_time.isoformat(),
                "type": f"Quick Test ({status_code})",
                "status": status_002,
                "response_time_ms": total_time,
                "success": status_002 == 200,
                "message_id": message_id
            }
            test_history.append(test_record)
            
            return {
                "status": "success" if status_002 == 200 else "error",
                "http_code": status_002,
                "response_time_ms": total_time,
                "payload_sent": pacs002_payload,
                "tms_response": response_002,
                "test_record": test_record
            }
        else:
            return {
                "status": "error",
                "http_code": status_008,
                "message": "pacs.008 failed"
            }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post(
    "/full-transaction",
    summary="Full Transaction Test",
    description="Send complete transaction flow: pacs.008 followed by pacs.002 ACCC"
)
async def test_full_transaction(
    debtor_account: Optional[str] = Form(None, description="Debtor account ID"),
    amount: Optional[float] = Form(None, description="Transaction amount")
):
    """Send complete transaction (pacs.008 + pacs.002 ACCC)"""
    results = {
        "pacs008": None,
        "pacs002": None,
        "overall_status": "pending"
    }
    
    pacs008_payload = generate_pacs008(debtor_account, amount)
    message_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
    end_to_end_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
    
    try:
        status_008, time_008, response_008 = tms_client.send_pacs008(pacs008_payload)
        
        results["pacs008"] = {
            "status": status_008,
            "success": status_008 == 200,
            "response": response_008
        }
        
        if status_008 == 200:
            time.sleep(0.5)
            
            pacs002_payload = generate_pacs002(message_id, end_to_end_id, "ACCC")
            status_002, time_002, response_002 = tms_client.send_pacs002(pacs002_payload)
            
            results["pacs002"] = {
                "status": status_002,
                "success": status_002 == 200,
                "response": response_002
            }
            
            results["overall_status"] = "success" if status_002 == 200 else "partial"
        else:
            results["overall_status"] = "failed"
        
        return results
        
    except Exception as e:
        results["overall_status"] = "error"
        results["error"] = str(e)
        return results


@router.get(
    "/db-summary",
    summary="Get Database Transaction Summary",
    description="Get summary of transactions in Tazama database (supports Full Docker and Local PostgreSQL)"
)
async def get_db_summary():
    """
    Get transaction summary from Tazama PostgreSQL database
    
    Automatically switches between:
    - Full Docker: queries tazama-postgres-1 container
    - Local PostgreSQL: queries localhost:5430
    
    Configure via config.USE_LOCAL_POSTGRES
    """
    from services.database_query_service import create_database_service
    from config import USE_LOCAL_POSTGRES
    
    # Create service with appropriate strategy based on config
    db_service = create_database_service(use_local=USE_LOCAL_POSTGRES)
    
    # Execute query and return result
    return db_service.get_transaction_summary()
