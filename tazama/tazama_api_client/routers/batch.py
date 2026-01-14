"""
Batch Testing Router
Run multiple test scenarios in sequence
"""
from fastapi import APIRouter, Form
from datetime import datetime
import random
import string

from services.tms_client import tms_client
from utils.payload_generator import generate_pacs008, generate_pacs002
from config import VALID_STATUS_CODES

router = APIRouter(prefix="/api/test", tags=["Batch Testing"])

# In-memory storage reference
test_history = []


def set_history_reference(history_list):
    global test_history
    test_history = history_list


@router.post(
    "/batch",
    summary="Run Batch Tests",
    description="Run multiple test scenarios in sequence. Available: quick_accc, quick_acsc, quick_rjct, rule_901, rule_902, rule_006, rule_018"
)
async def run_batch_test(
    scenarios: str = Form(..., description="Comma-separated scenarios: quick_accc, quick_acsc, quick_rjct, rule_901, rule_902, rule_006, rule_018")
):
    """
    Run multiple test scenarios in batch.
    Available scenarios: quick_accc, quick_acsc, quick_rjct, rule_901, rule_902, rule_006, rule_018
    """
    scenario_list = [s.strip() for s in scenarios.split(",")]
    results = []
    start_time = datetime.now()
    
    for scenario in scenario_list:
        scenario_result = {
            "scenario": scenario,
            "status": "pending",
            "details": None
        }
        
        try:
            if scenario.startswith("quick_"):
                # Quick status test
                status_code = scenario.replace("quick_", "").upper()
                if status_code in VALID_STATUS_CODES:
                    result = await _run_quick_status(status_code)
                    scenario_result["status"] = "success" if result.get("status") == "success" else "error"
                    scenario_result["details"] = {
                        "status_code": status_code,
                        "http_code": result.get("http_code"),
                        "response_time_ms": result.get("response_time_ms")
                    }
                else:
                    scenario_result["status"] = "error"
                    scenario_result["details"] = {"message": f"Invalid status code: {status_code}"}
                    
            elif scenario == "velocity" or scenario == "rule_901":
                # Rule 901 - Velocity Attack
                result = await _run_velocity_test(8)
                success_count = sum(1 for r in result.get("results", []) if r.get("status") == 200)
                scenario_result["status"] = "success" if success_count > 0 else "error"
                scenario_result["details"] = {
                    "rule": "901 - Velocity",
                    "total_sent": result.get("total_sent"),
                    "success_count": success_count,
                    "fraud_alerts": len(result.get("fraud_alerts", []))
                }
                
            elif scenario == "rule_902":
                # Rule 902 - Money Mule (creditor velocity)
                result = await _run_creditor_velocity_test(8)
                success_count = sum(1 for r in result.get("results", []) if r.get("status") == 200)
                scenario_result["status"] = "success" if success_count > 0 else "error"
                scenario_result["details"] = {
                    "rule": "902 - Money Mule",
                    "total_sent": result.get("total_sent"),
                    "success_count": success_count,
                    "fraud_alerts": len(result.get("fraud_alerts", []))
                }
                
            elif scenario in ["rule_006", "rule_018"]:
                # Attack scenario
                result = await _run_attack_scenario(scenario)
                success_count = sum(1 for r in result.get("results", []) if r.get("status") == 200)
                scenario_result["status"] = "success" if success_count > 0 else "error"
                scenario_result["details"] = {
                    "rule": "006 - Structuring" if scenario == "rule_006" else "018 - High Value",
                    "total_sent": result.get("total_sent"),
                    "success_count": success_count,
                    "fraud_alerts": len(result.get("fraud_alerts", []))
                }
                
            else:
                scenario_result["status"] = "error"
                scenario_result["details"] = {"message": f"Unknown scenario: {scenario}"}
                
        except Exception as e:
            scenario_result["status"] = "error"
            scenario_result["details"] = {"message": str(e)}
        
        results.append(scenario_result)
    
    total_time = (datetime.now() - start_time).total_seconds() * 1000
    success_count = sum(1 for r in results if r["status"] == "success")
    
    # Record batch test
    test_history.append({
        "timestamp": start_time.isoformat(),
        "type": f"Batch Test ({len(scenario_list)} scenarios)",
        "status": 200 if success_count == len(scenario_list) else 500,
        "response_time_ms": total_time,
        "success": success_count == len(scenario_list),
        "message_id": f"batch_{start_time.strftime('%H%M%S')}"
    })
    
    return {
        "status": "completed",
        "total_scenarios": len(scenario_list),
        "success_count": success_count,
        "failure_count": len(scenario_list) - success_count,
        "total_time_ms": total_time,
        "results": results
    }


async def _run_quick_status(status_code: str):
    """Helper to run quick status test"""
    import time
    
    pacs008_payload = generate_pacs008(None, None)
    message_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
    end_to_end_id = pacs008_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
    
    start_time = datetime.now()
    status_008, _, _ = tms_client.send_pacs008(pacs008_payload)
    
    if status_008 == 200:
        time.sleep(0.3)
        pacs002_payload = generate_pacs002(message_id, end_to_end_id, status_code)
        status_002, _, response_002 = tms_client.send_pacs002(pacs002_payload)
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "success" if status_002 == 200 else "error",
            "http_code": status_002,
            "response_time_ms": total_time
        }
    else:
        return {"status": "error", "http_code": status_008, "message": "pacs.008 failed"}


async def _run_velocity_test(count: int):
    """Helper to run velocity test (Rule 901)"""
    from routers.attacks import fetch_logs_internal, parse_fraud_alerts
    
    results = []
    debtor_acc = f"BATCH_VEL_{random.randint(1000,9999)}"
    
    for i in range(count):
        payload = generate_pacs008(debtor_acc, 500000.0, "Batch Tester")
        status_008, time_008, _ = tms_client.send_pacs008(payload)
        
        if status_008 == 200:
            msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
            pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
            tms_client.send_pacs002(pacs002_payload)
        
        results.append({"iteration": i + 1, "status": status_008})
    
    logs_data = fetch_logs_internal("tazama-rule-901-1", tail=50)
    fraud_alerts = parse_fraud_alerts(logs_data)
    
    return {"total_sent": count, "results": results, "fraud_alerts": fraud_alerts}


async def _run_creditor_velocity_test(count: int):
    """Helper to run creditor velocity test (Rule 902 - Money Mule)"""
    from routers.attacks import fetch_logs_internal, parse_fraud_alerts
    
    results = []
    creditor_acc = f"MULE_TARGET_{random.randint(1000,9999)}"
    
    for i in range(count):
        rand_suffix = ''.join(random.choices(string.digits, k=6))
        debtor_acc = f"BATCH_DEB_{rand_suffix}"
        
        payload = generate_pacs008(
            debtor_account=debtor_acc,
            amount=500000.0,
            debtor_name=f"Random Sender {rand_suffix}",
            creditor_account=creditor_acc,
            creditor_name="Money Mule Target"
        )
        status_008, time_008, _ = tms_client.send_pacs008(payload)
        
        if status_008 == 200:
            msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
            pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
            tms_client.send_pacs002(pacs002_payload)
        
        results.append({"iteration": i + 1, "status": status_008})
    
    logs_data = fetch_logs_internal("tazama-rule-902-1", tail=50)
    fraud_alerts = parse_fraud_alerts(logs_data)
    
    return {"total_sent": count, "results": results, "fraud_alerts": fraud_alerts}


async def _run_attack_scenario(scenario: str):
    """Helper to run attack scenario"""
    from routers.attacks import fetch_logs_internal, parse_fraud_alerts
    
    results = []
    count = 8 if scenario == "rule_006" else 6
    target_container = "tazama-rule-006-1" if scenario == "rule_006" else "tazama-rule-018-1"
    
    debtor_acc = f"BATCH_{scenario.upper()}_{random.randint(1000,9999)}"
    
    for i in range(count):
        if scenario == "rule_006":
            amt = 9500000.0
        else:
            amt = 50000.0 if i < count - 1 else 900000000000.0
        
        payload = generate_pacs008(debtor_acc, amt, "Batch Actor")
        status_008, _, _ = tms_client.send_pacs008(payload)
        
        if status_008 == 200:
            msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
            pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
            tms_client.send_pacs002(pacs002_payload)
        
        results.append({"iteration": i + 1, "status": status_008, "amount": amt})
    
    logs_data = fetch_logs_internal(target_container, tail=50)
    fraud_alerts = parse_fraud_alerts(logs_data)
    
    return {"total_sent": count, "results": results, "fraud_alerts": fraud_alerts}
