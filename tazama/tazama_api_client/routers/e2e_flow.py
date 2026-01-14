"""
E2E Flow Router - Full ISO 20022 Payment Flow Testing
Routes: pain.001 → pain.013 → pacs.008 → pacs.002
"""
from fastapi import APIRouter, Form
from typing import Optional
from datetime import datetime
import time

from services.tms_client import tms_client
from utils.payload_generator import (
    generate_pain001, 
    generate_pain013, 
    generate_pacs008, 
    generate_pacs002
)

router = APIRouter(prefix="/api/test", tags=["E2E Flow"])

# In-memory storage reference
test_history = []


def set_history_reference(history_list):
    global test_history
    test_history = history_list


@router.post(
    "/pain001",
    summary="Send pain.001 Transaction",
    description="Send pain.001 Customer Credit Transfer Initiation to Tazama TMS"
)
async def test_pain001(
    debtor_account: Optional[str] = Form(None),
    creditor_account: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    debtor_name: Optional[str] = Form(None),
    creditor_name: Optional[str] = Form(None)
):
    """Send pain.001 Customer Credit Transfer Initiation"""
    try:
        payload, message_id, end_to_end_id = generate_pain001(
            debtor_account=debtor_account,
            creditor_account=creditor_account,
            amount=amount,
            debtor_name=debtor_name,
            creditor_name=creditor_name
        )
        
        status_code, response_time, response_data = tms_client.send_pain001(payload)
        
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "pain.001",
            "status": status_code,
            "response_time_ms": response_time,
            "success": status_code == 200,
            "message_id": message_id,
            "end_to_end_id": end_to_end_id
        }
        test_history.append(test_record)
        
        return {
            "status": "success" if status_code == 200 else "error",
            "http_code": status_code,
            "response_time_ms": response_time,
            "message_id": message_id,
            "end_to_end_id": end_to_end_id,
            "payload_sent": payload,
            "tms_response": response_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post(
    "/pain013",
    summary="Send pain.013 Transaction",
    description="Send pain.013 Creditor Payment Activation Request to Tazama TMS"
)
async def test_pain013(
    debtor_account: Optional[str] = Form(None),
    creditor_account: Optional[str] = Form(None),
    amount: Optional[float] = Form(None),
    debtor_name: Optional[str] = Form(None),
    creditor_name: Optional[str] = Form(None)
):
    """Send pain.013 Creditor Payment Activation Request"""
    try:
        payload, message_id, end_to_end_id = generate_pain013(
            debtor_account=debtor_account,
            creditor_account=creditor_account,
            amount=amount,
            debtor_name=debtor_name,
            creditor_name=creditor_name
        )
        
        status_code, response_time, response_data = tms_client.send_pain013(payload)
        
        test_record = {
            "timestamp": datetime.now().isoformat(),
            "type": "pain.013",
            "status": status_code,
            "response_time_ms": response_time,
            "success": status_code == 200,
            "message_id": message_id,
            "end_to_end_id": end_to_end_id
        }
        test_history.append(test_record)
        
        return {
            "status": "success" if status_code == 200 else "error",
            "http_code": status_code,
            "response_time_ms": response_time,
            "message_id": message_id,
            "end_to_end_id": end_to_end_id,
            "payload_sent": payload,
            "tms_response": response_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post(
    "/e2e-flow",
    summary="Full E2E ISO 20022 Flow",
    description="Execute complete payment flow: pain.001 → pain.013 → pacs.008 → pacs.002"
)
async def test_e2e_flow(
    debtor_account: Optional[str] = Form("E2E_DEBTOR_001"),
    creditor_account: Optional[str] = Form("E2E_CREDITOR_001"),
    amount: Optional[float] = Form(1000000),
    final_status: str = Form("ACCC")
):
    """
    Execute full E2E ISO 20022 payment flow.
    Steps: pain.001 → pain.013 → pacs.008 → pacs.002
    """
    start_time = datetime.now()
    
    results = {
        "overall_status": "pending",
        "steps": [],
        "total_time_ms": 0,
        "debtor_account": debtor_account,
        "creditor_account": creditor_account,
        "amount": amount
    }
    
    try:
        # Step 1: pain.001 - Customer Credit Transfer Initiation (OPTIONAL)
        pain001_payload, msg_id_001, e2e_id = generate_pain001(
            debtor_account=debtor_account,
            creditor_account=creditor_account,
            amount=amount
        )
        status_001, time_001, resp_001 = tms_client.send_pain001(pain001_payload)
        
        # Check if endpoint exists (404 = not supported, skip it)
        pain001_skipped = status_001 == 404
        step_001 = {
            "step": 1,
            "type": "pain.001",
            "name": "Customer Credit Transfer Initiation",
            "status": status_001,
            "success": status_001 == 200,
            "skipped": pain001_skipped,
            "response_time_ms": time_001,
            "message_id": msg_id_001,
            "note": "Skipped - endpoint not available in TMS" if pain001_skipped else None
        }
        results["steps"].append(step_001)
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "pain.001 (E2E)" + (" [SKIPPED]" if pain001_skipped else ""),
            "status": status_001,
            "response_time_ms": time_001,
            "success": status_001 == 200 or pain001_skipped,
            "message_id": msg_id_001
        })
        
        # Only fail if error is NOT 404 (not found)
        if status_001 != 200 and status_001 != 404:
            results["overall_status"] = "failed_at_pain001"
            results["total_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            return results
        
        if not pain001_skipped:
            time.sleep(0.3)
        
        # Step 2: pain.013 - Creditor Payment Activation Request (OPTIONAL)
        pain013_payload, msg_id_013, _ = generate_pain013(
            debtor_account=debtor_account,
            creditor_account=creditor_account,
            amount=amount
        )
        status_013, time_013, resp_013 = tms_client.send_pain013(pain013_payload)
        
        # Check if endpoint exists (404 = not supported, skip it)
        pain013_skipped = status_013 == 404
        step_013 = {
            "step": 2,
            "type": "pain.013",
            "name": "Creditor Payment Activation Request",
            "status": status_013,
            "success": status_013 == 200,
            "skipped": pain013_skipped,
            "response_time_ms": time_013,
            "message_id": msg_id_013,
            "note": "Skipped - endpoint not available in TMS" if pain013_skipped else None
        }
        results["steps"].append(step_013)
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "pain.013 (E2E)" + (" [SKIPPED]" if pain013_skipped else ""),
            "status": status_013,
            "response_time_ms": time_013,
            "success": status_013 == 200 or pain013_skipped,
            "message_id": msg_id_013
        })
        
        # Only fail if error is NOT 404 (not found)
        if status_013 != 200 and status_013 != 404:
            results["overall_status"] = "failed_at_pain013"
            results["total_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            return results
        
        if not pain013_skipped:
            time.sleep(0.3)
        
        # Step 3: pacs.008 - FI to FI Customer Credit Transfer
        pacs008_payload = generate_pacs008(
            debtor_account=debtor_account,
            creditor_account=creditor_account,
            amount=amount
        )
        msg_id_008 = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
        e2e_id_008 = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
        
        status_008, time_008, resp_008 = tms_client.send_pacs008(pacs008_payload)
        
        step_008 = {
            "step": 3,
            "type": "pacs.008",
            "name": "FI to FI Customer Credit Transfer",
            "status": status_008,
            "success": status_008 == 200,
            "response_time_ms": time_008,
            "message_id": msg_id_008
        }
        results["steps"].append(step_008)
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "pacs.008 (E2E)",
            "status": status_008,
            "response_time_ms": time_008,
            "success": status_008 == 200,
            "message_id": msg_id_008
        })
        
        if status_008 != 200:
            results["overall_status"] = "failed_at_pacs008"
            results["total_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
            return results
        
        time.sleep(0.3)
        
        # Step 4: pacs.002 - Payment Status Report
        pacs002_payload = generate_pacs002(msg_id_008, e2e_id_008, final_status)
        status_002, time_002, resp_002 = tms_client.send_pacs002(pacs002_payload)
        
        step_002 = {
            "step": 4,
            "type": "pacs.002",
            "name": "Payment Status Report",
            "status": status_002,
            "success": status_002 == 200,
            "response_time_ms": time_002,
            "final_status": final_status
        }
        results["steps"].append(step_002)
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": f"pacs.002 ({final_status}) (E2E)",
            "status": status_002,
            "response_time_ms": time_002,
            "success": status_002 == 200,
            "message_id": msg_id_008
        })
        
        # Final status
        results["total_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        results["overall_status"] = "completed" if status_002 == 200 else "failed_at_pacs002"
        
        return results
        
    except Exception as e:
        results["overall_status"] = "error"
        results["error"] = str(e)
        results["total_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        return results
