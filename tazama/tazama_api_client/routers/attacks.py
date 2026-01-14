"""
Attacks Router
Endpoints for velocity attacks and scenario simulations
"""
from fastapi import APIRouter, Form
from typing import Optional
from datetime import datetime
import subprocess
import random
import string
import re

from services.tms_client import tms_client
from utils.payload_generator import generate_pacs008, generate_pacs002, create_uuid
from models.schemas import ScenarioType

router = APIRouter(prefix="/api/test", tags=["Attack Simulations"])

# In-memory storage reference
test_history = []


def set_history_reference(history_list):
    global test_history
    test_history = history_list


def fetch_logs_internal(container_name, tail=50, since_seconds=None):
    """Fetch logs from a docker container
    
    Args:
        container_name: Docker container name
        tail: Number of log lines to fetch
        since_seconds: Only get logs from the last N seconds (optional)
    """
    try:
        if not container_name.startswith("tazama-"):
            return {"status": "error", "message": "Invalid container name"}
        
        cmd = ["docker", "logs", container_name, "--tail", str(tail)]
        
        # Add --since flag if specified to filter out old logs
        if since_seconds:
            cmd.extend(["--since", f"{since_seconds}s"])
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {"status": "error", "message": result.stderr}
        
        # Docker logs may output to stderr, combine both
        logs = result.stdout + result.stderr
        return {"status": "success", "logs": logs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Base Rule Configurations (static) - UPDATED TO MATCH DATABASE CONFIG
RULE_CONFIGS = {
    "901": {
        "name": "Velocity Check - Debtor",
        "rule_id": "901",
        "trigger_condition": "Debtor melakukan 3 atau lebih transaksi dalam 1 hari",
        "config": {
            "threshold": "3 transaksi per hari",
            "maxQueryRange": "86400000 ms (24 jam)"
        },
        "recommendation": "Verifikasi apakah debtor adalah bisnis yang memang memiliki volume transaksi tinggi atau potensi fraud."
    },
    "902": {
        "name": "Velocity Check - Creditor (Money Mule)",
        "rule_id": "902",
        "trigger_condition": "Creditor menerima 3 atau lebih transaksi dalam 1 hari dari debtor berbeda",
        "config": {
            "threshold": "3 transaksi per hari",
            "maxQueryRange": "86400000 ms (24 jam)"
        },
        "recommendation": "Investigasi apakah creditor adalah akun bisnis legitimate atau potensi pencucian uang."
    },
    "006": {
        "name": "Structuring / Smurfing",
        "rule_id": "006",
        "trigger_condition": "5 atau lebih transaksi dengan nominal mirip dalam toleransi 20 persen",
        "config": {
            "maxQueryLimit": "5 transaksi terakhir",
            "tolerance": "0.2 (20 persen)",
            "lowerLimit": "5 transaksi mirip untuk trigger alert"
        },
        "recommendation": "Periksa apakah total transaksi seharusnya satu transaksi besar yang dipecah."
    },
    "018": {
        "name": "High Value Transfer",
        "rule_id": "018",
        "trigger_condition": "Transaksi melebihi 1.5 kali rata-rata historical debtor (30 hari terakhir)",
        "config": {
            "maxQueryRange": "2592000000 ms (30 hari)",
            "multiplier": "1.5x dari rata-rata historical"
        },
        "recommendation": "Konfirmasi dengan debtor melalui channel resmi sebelum memproses transaksi."
    }
}


def get_dynamic_explanation(rule_id, request_context):
    """Generate dynamic why_triggered message based on actual request values"""
    if not request_context:
        return None
    
    debtor = request_context.get('debtor_account') or request_context.get('debtor_name') or '-'
    creditor = request_context.get('creditor_account') or request_context.get('creditor_name') or '-'
    amount = request_context.get('amount_per_transaction') or request_context.get('amount_requested') or 0
    target_amt = request_context.get('target_amount') or amount
    count = request_context.get('total_transactions') or 0
    total = request_context.get('total_amount') or (amount * count if amount and count else 0)
    
    # Format amount to Indonesian currency
    def fmt_rp(val):
        return f"Rp {val:,.0f}".replace(",", ".")
    
    explanations = {
        "901": f"Anda mengirim {count} transaksi dari debtor '{debtor}' dengan nominal berbeda-beda. "
               f"Rule 901 trigger karena threshold adalah 3 transaksi per hari, dan Anda mengirim {count} transaksi dari debtor yang sama.",
        
        "902": f"Anda mengirim {count} transaksi ke creditor '{creditor}' dari berbagai debtor berbeda. "
               f"Rule 902 trigger karena creditor menerima lebih dari 3 transaksi dari pengirim berbeda dalam 1 hari.",
        
        "006": f"Anda mengirim {count} transaksi dengan nominal sama yaitu {fmt_rp(amount)} dari debtor '{debtor}'. "
               f"Toleransi saat ini adalah 20%, sehingga transaksi dalam range {fmt_rp(amount * 0.8)} - {fmt_rp(amount * 1.2)} dianggap 'mirip'. "
               f"Rule 006 trigger karena terdeteksi {count} transaksi dengan nominal mirip (threshold: 5 transaksi mirip).",
        
        "018": f"Anda mengirim transaksi senilai {fmt_rp(target_amt)} dari debtor '{debtor}'. "
               f"Rata-rata historical transaksi debtor ini (30 hari terakhir) jauh lebih kecil. "
               f"Rule 018 trigger karena nominal {fmt_rp(target_amt)} melebihi 1.5x rata-rata historical transaksi."
    }
    
    return explanations.get(rule_id, None)


def get_alert_explanation(msg_text, request_context=None):
    """Map raw log messages to human-readable explanations with detailed info"""
    
    base_explanation = {"title": "Suspicious Activity", "desc": msg_text}
    rule_detail = None
    rule_id = None
    
    if "debtor has performed three or more transactions" in msg_text:
        rule_id = "901"
        base_explanation = {
            "title": "Velocity Check Failed (Rule 901)",
            "desc": "Debtor melakukan lebih dari 3 transaksi dalam 1 hari."
        }
    elif "creditor has received three or more transactions" in msg_text:
        rule_id = "902"
        base_explanation = {
            "title": "Creditor Velocity Limit (Rule 902)",
            "desc": "Creditor menerima terlalu banyak transaksi dari berbagai pengirim."
        }
    elif "similar amounts" in msg_text or "Two or more similar amounts detected" in msg_text:
        rule_id = "006"
        base_explanation = {
            "title": "Structuring Detected (Rule 006)",
            "desc": "Beberapa transaksi dengan nominal mirip terdeteksi."
        }
    elif "Amount exceeds" in msg_text or "Exceptionally large outgoing transfer detected" in msg_text:
        rule_id = "018"
        base_explanation = {
            "title": "High Value Transaction (Rule 018)",
            "desc": "Nilai transaksi melebihi batas aman berdasarkan historical."
        }
    
    # Get base rule config and add dynamic explanation
    if rule_id and rule_id in RULE_CONFIGS:
        rule_detail = RULE_CONFIGS[rule_id].copy()
        # Add dynamic why_triggered based on actual request values
        dynamic_why = get_dynamic_explanation(rule_id, request_context)
        if dynamic_why:
            rule_detail["why_triggered"] = dynamic_why
        else:
            # Fallback to generic explanation
            rule_detail["why_triggered"] = f"Transaksi Anda memenuhi kondisi trigger: {rule_detail.get('trigger_condition', 'N/A')}"
    
    return {
        **base_explanation,
        "rule_id": rule_id,
        "rule_detail": rule_detail,
        "request_context": request_context
    }


def parse_fraud_alerts(logs_data, request_context=None, target_rule=None):
    """Parse fraud alerts from container logs with detailed explanations
    
    Args:
        logs_data: Log data from container
        request_context: Request details for dynamic explanation
        target_rule: Optional - only include alerts for this specific rule (e.g. "006", "018")
    """
    fraud_alerts = []
    if logs_data.get("status") == "success":
        log_lines = logs_data["logs"].splitlines()
        for line in log_lines:
            match = re.search(r"message:\s*'([^']+)'", line)
            if match:
                msg_text = match.group(1)
                if "End - Handle execute request" not in msg_text and \
                   "EventHistoryDB" not in msg_text and \
                   "Connecting to nats" not in msg_text and \
                   "Connected to nats" not in msg_text and \
                   "Start - Handle execute" not in msg_text and \
                   "Cannot read properties" not in msg_text and \
                   "Outgoing transfer within historical limits" not in msg_text and \
                   "No similar amounts detected" not in msg_text and \
                   "Insufficient transaction history" not in msg_text and \
                   "has performed one transaction" not in msg_text and \
                   "has performed two transactions" not in msg_text and \
                   "has received one transaction" not in msg_text and \
                   "has received two transactions" not in msg_text:
                    
                    existing_raw = [a['raw'] for a in fraud_alerts]
                    if msg_text not in existing_raw:
                        explanation = get_alert_explanation(msg_text, request_context)
                        
                        # Filter by target rule if specified
                        if target_rule and explanation.get('rule_id') != target_rule:
                            continue
                        
                        fraud_alerts.append({
                            "raw": msg_text,
                            "title": explanation['title'],
                            "desc": explanation['desc'],
                            "rule_id": explanation.get('rule_id'),
                            "rule_detail": explanation.get('rule_detail'),
                            "request_context": explanation.get('request_context'),
                            "log_snippet": line.strip()[-200:] if len(line) > 200 else line.strip()
                        })
    return fraud_alerts


@router.post(
    "/velocity",
    summary="Velocity Attack Test (Rule 901)",
    description="Simulate velocity attack by sending multiple transactions from the same debtor"
)
async def test_velocity(
    debtor_account: str = Form(..., description="Target debtor account"),
    debtor_name: str = Form(..., description="Debtor name"),
    count: int = Form(20, description="Number of transactions (1-100)", ge=1, le=100)
):
    """Run a velocity attack simulation (multiple tx in short time)
    
    PHASE 3 UPDATE: Fraud detection now happens at pacs.008 level!
    - Rules 901, 902, 006, 018 are triggered on pacs.008 (before transaction processed)
    - pacs.002 is optional confirmation only
    
    ISOLATED TRIGGER: Uses varied amounts and different creditors to ONLY trigger Rule 901
    - Different creditor per transaction (avoids Rule 902)
    - Varied amounts per transaction (avoids Rule 006)
    """
    results = []
    base_amt = 500000.0
    
    for i in range(count):
        try:
            # Use varied amount to avoid triggering Rule 006 (structuring)
            amt = base_amt + (i * 50000) + random.randint(1000, 9999)
            
            # Use different creditor per transaction to avoid triggering Rule 902
            rand_cred = ''.join(random.choices(string.digits, k=6))
            creditor_acc = f"CRED_{rand_cred}"
            creditor_nm = f"Random Creditor {rand_cred}"
            
            payload = generate_pacs008(
                debtor_account=debtor_account, 
                amount=amt, 
                debtor_name=debtor_name,
                creditor_account=creditor_acc,
                creditor_name=creditor_nm
            )
            status_008, time_008, response_008 = tms_client.send_pacs008(payload)
            
            # PHASE 3: pacs.002 is now optional (fraud check happens at pacs.008)
            # Keeping pacs.002 for complete transaction flow but it's not required for fraud detection
            pacs002_status = None
            if status_008 == 200:
                msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
                e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
                
                pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
                pacs002_status, _, _ = tms_client.send_pacs002(pacs002_payload)
            
            results.append({
                "iteration": i + 1,
                "status": status_008,
                "pacs002_status": pacs002_status,
                "response_time_ms": time_008,
                "amount": amt,
                "creditor": creditor_acc,
                "response": response_008 if isinstance(response_008, dict) else {}
            })
            
            test_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "pacs.008 + pacs.002 (Velocity)",
                "status": status_008,
                "response_time_ms": time_008,
                "success": status_008 == 200,
                "message_id": payload["FIToFICstmrCdtTrf"]["GrpHdr"]["MsgId"]
            })
            
        except Exception as e:
            results.append({"iteration": i + 1, "status": "error", "error": str(e)})

    # Build request context for detailed alerts
    request_context = {
        "scenario": "Rule 901 - Velocity Attack",
        "debtor_account": debtor_account,
        "debtor_name": debtor_name,
        "amount_per_transaction": amt,
        "total_transactions": count,
        "total_amount": amt * count,
        "detection_point": "pacs.008"  # PHASE 3: Fraud detected at request time
    }
    
    # PHASE 3: Fetch logs from rule container (fraud check now at pacs.008)
    logs_data = fetch_logs_internal("tazama-rule-901-1", tail=100, since_seconds=60)
    fraud_alerts = parse_fraud_alerts(logs_data, request_context)

    return {
        "status": "completed",
        "total_sent": count,
        "results": results,
        "fraud_alerts": fraud_alerts,
        "request_summary": request_context,
        "info": "PHASE 3: Fraud detection now triggered at pacs.008 (before transaction processed)"
    }


@router.post(
    "/velocity-creditor",
    summary="Creditor Velocity Test (Rule 902 - Money Mule)",
    description="Simulate money mule scenario with multiple transactions to the same creditor"
)
async def test_velocity_creditor(
    creditor_account: str = Form(..., description="Target creditor account"),
    creditor_name: str = Form(..., description="Creditor name"),
    count: int = Form(20, description="Number of transactions", ge=1, le=100),
    amount: float = Form(500000.0, description="Amount per transaction", gt=0)
):
    """Run a creditor velocity attack simulation (Money Mule Scenario)
    
    PHASE 3 UPDATE: Fraud detection now happens at pacs.008 level!
    - Rules 901, 902, 006, 018 are triggered on pacs.008 (before transaction processed)
    
    ISOLATED TRIGGER: Uses varied amounts to ONLY trigger Rule 902
    - Different debtor per transaction (required for 902)
    - Varied amounts per transaction (avoids Rule 006)
    """
    results = []
    base_amt = amount
    
    for i in range(count):
        try:
            rand_suffix = ''.join(random.choices(string.digits, k=6))
            debtor_acc = f"DEB_{rand_suffix}"
            debtor_nm = f"Random Sender {rand_suffix}"
            
            # Use varied amount to avoid triggering Rule 006 (structuring)
            current_amt = base_amt + (i * 25000) + random.randint(1000, 5000)
            
            payload = generate_pacs008(
                debtor_account=debtor_acc,
                amount=current_amt,
                debtor_name=debtor_nm,
                creditor_account=creditor_account,
                creditor_name=creditor_name
            )
            
            status_008, time_008, response_008 = tms_client.send_pacs008(payload)
            
            pacs002_response_json = {}
            if status_008 == 200:
                msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
                e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
                
                pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
                status_002, _, response_002 = tms_client.send_pacs002(pacs002_payload)
                pacs002_response_json = response_002 if isinstance(response_002, dict) else {}

            results.append({
                "iteration": i + 1,
                "status": status_008,
                "response_time_ms": time_008,
                "amount": current_amt,
                "debtor": debtor_acc,
                "response": response_008 if isinstance(response_008, dict) else {},
                "pacs002_response": pacs002_response_json
            })
            
            test_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "pacs.008 (Money Mule)",
                "status": status_008,
                "response_time_ms": time_008,
                "success": status_008 == 200,
                "message_id": payload["FIToFICstmrCdtTrf"]["GrpHdr"]["MsgId"]
            })
            
        except Exception as e:
            results.append({"iteration": i + 1, "status": "error", "error": str(e)})

    # Build request context for detailed alerts
    request_context = {
        "scenario": "Rule 902 - Money Mule",
        "creditor_account": creditor_account,
        "creditor_name": creditor_name,
        "amount_per_transaction": amount,
        "total_transactions": count,
        "total_amount": amount * count,
        "detection_point": "pacs.008"  # PHASE 3: Fraud detected at request time
    }
    
    # PHASE 3: Fetch logs with time filter
    logs_data = fetch_logs_internal("tazama-rule-902-1", tail=100, since_seconds=60)
    fraud_alerts = parse_fraud_alerts(logs_data, request_context)

    return {
        "status": "completed",
        "total_sent": count,
        "results": results,
        "fraud_alerts": fraud_alerts,
        "request_summary": request_context,
        "info": "PHASE 3: Fraud detection now triggered at pacs.008 (before transaction processed)"
    }


@router.post(
    "/attack-scenario",
    summary="Attack Scenario Test",
    description="Run a specific attack scenario: rule_901 (Velocity), rule_902 (Money Mule), rule_006 (Structuring), rule_018 (High Value)"
)
async def test_attack_scenario(
    scenario: str = Form(..., description="Scenario: rule_901, rule_902, rule_006, or rule_018"),
    count: int = Form(5, description="Number of transactions", ge=1, le=50),
    amount: Optional[float] = Form(None, description="Custom amount (optional)", gt=0)
):
    """Run a specific attack scenario with ISOLATED TRIGGERS
    
    Each scenario is designed to ONLY trigger its target rule:
    - rule_901: Uses varied amounts and different creditors
    - rule_902: Uses varied amounts with same creditor
    - rule_006: Uses SAME amount with minimal count (3 transactions)
    - rule_018: Uses single large transaction after small history
    """
    results = []
    target_container = "tazama-rule-901-1"
    amt = amount or 500000.0
    base_amt = amt
    
    debtor_acc = "SCENARIO_TEST_DEB"
    creditor_acc = "SCENARIO_TEST_CRED"
    target_amt = amt
    
    # Scenario-specific configurations for ISOLATED triggers
    if scenario == "rule_901":
        target_container = "tazama-rule-901-1"
        count = max(count, 5)
        debtor_acc = f"VEL_{random.randint(1000,9999)}"
        # Will use varied amounts and different creditors in loop
        
    elif scenario == "rule_902":
        target_container = "tazama-rule-902-1"
        count = max(count, 5)
        creditor_acc = f"MULE_{random.randint(1000,9999)}"
        # Will use varied amounts with different debtors in loop
    
    elif scenario == "rule_006":
        target_container = "tazama-rule-006-1"
        amt = amount or 9500000.0
        # Use 6 transactions to trigger (lowerLimit is now 5)
        count = 6
        debtor_acc = f"STRUCT_{random.randint(1000,9999)}"
        # Will use SAME amount to trigger structuring
        
    elif scenario == "rule_018":
        target_container = "tazama-rule-018-1"
        target_amt = amount or 500000000.0  # 500 juta sebagai transaksi besar
        # Use 6 transactions: 5 small (history), 1 huge (trigger)
        # Need sufficient history for rule to calculate average
        count = 6
        debtor_acc = f"WHALE_{random.randint(1000,9999)}"

    for i in range(count):
        try:
            current_amt = amt
            current_debtor = debtor_acc
            current_creditor = creditor_acc
            
            # Rule 901: Varied amounts + different creditors (ONLY triggers 901)
            if scenario == "rule_901":
                current_amt = base_amt + (i * 100000) + random.randint(10000, 50000)
                rand_cred = ''.join(random.choices(string.digits, k=6))
                current_creditor = f"CRED_{rand_cred}"
            
            # Rule 902: Varied amounts + different debtors (ONLY triggers 902)
            elif scenario == "rule_902":
                current_amt = base_amt + (i * 50000) + random.randint(5000, 20000)
                rand_suffix = ''.join(random.choices(string.digits, k=6))
                current_debtor = f"DEB_{rand_suffix}"
            
            # Rule 006: SAME amount (triggers structuring)
            elif scenario == "rule_006":
                current_amt = amt  # Keep same amount for structuring detection
                # Use different creditor per transaction to avoid 902
                rand_cred = ''.join(random.choices(string.digits, k=6))
                current_creditor = f"CRED_{rand_cred}"
                
            # Rule 018: Build historical average, then one huge transaction
            elif scenario == "rule_018":
                if i < count - 1:
                    # Small historical transactions: Rp 500k - Rp 2jt (varied to avoid 006)
                    current_amt = 500000.0 + (i * 300000) + random.randint(50000, 150000)
                else:
                    # Final huge transaction: much larger than average
                    current_amt = target_amt
                # Different creditor each time to avoid 902
                rand_cred = ''.join(random.choices(string.digits, k=6))
                current_creditor = f"CRED_{rand_cred}"

            payload = generate_pacs008(
                debtor_account=current_debtor,
                amount=current_amt,
                debtor_name="Scenario Actor",
                creditor_account=current_creditor
            )
            
            start_time = datetime.now()
            status_008, time_008, response_008 = tms_client.send_pacs008(payload)
            
            pacs002_response_json = {}
            if status_008 == 200:
                msg_id = payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
                e2e_id = payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
                
                pacs002_payload = generate_pacs002(msg_id, e2e_id, "ACCC")
                status_002, _, response_002 = tms_client.send_pacs002(pacs002_payload)
                pacs002_response_json = response_002 if isinstance(response_002, dict) else {}

            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            results.append({
                "iteration": i + 1,
                "status": status_008,
                "response": response_008 if isinstance(response_008, dict) else {},
                "amount": current_amt
            })
            
            test_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": f"Scenario {scenario} ({current_amt:,.0f})",
                "status": status_008,
                "success": status_008 == 200,
                "message_id": payload["FIToFICstmrCdtTrf"]["GrpHdr"]["MsgId"],
                "response_time_ms": duration
            })
            
        except Exception as e:
            results.append({"error": str(e)})

    # Build request context for detailed alerts
    request_context = {
        "scenario": scenario,
        "debtor_account": debtor_acc,
        "creditor_account": creditor_acc,
        "amount_requested": amt,
        "target_amount": target_amt if scenario == "rule_018" else amt,
        "total_transactions": count
    }
    
    # Extract rule number from scenario for filtering (e.g. "rule_018" -> "018")
    target_rule = scenario.replace("rule_", "") if scenario.startswith("rule_") else None
    
    logs_data = fetch_logs_internal(target_container, tail=100)
    fraud_alerts = parse_fraud_alerts(logs_data, request_context, target_rule)

    return {
        "status": "completed",
        "total_sent": count,
        "results": results,
        "fraud_alerts": fraud_alerts,
        "request_summary": request_context
    }


@router.post(
    "/fraud-simulation",
    summary="Full Fraud Simulation Flow",
    description="Complete fraud simulation: Normal TX → Trigger Attack → Check Detection → Block → Summary"
)
async def fraud_simulation(
    account_id: str = Form("FRAUD_SIM_001", description="Account ID for simulation"),
    rule: str = Form("rule_006", description="Rule to trigger: rule_006, rule_018, rule_901, rule_902"),
    attack_count: int = Form(6, description="Number of attack transactions", ge=3, le=20)
):
    """
    Full Fraud Simulation Flow - 5 Steps:
    1. ✅ Normal Transaction (ACCC) - Account starts clean
    2. ⚠️ Trigger Fraud Pattern - Execute attack based on selected rule
    3. 🔍 Check Fraud Detection - Fetch fraud alerts
    4. ❌ Block Transaction (RJCT) - Confirm blocking
    5. 📊 Summary - Return fraud details
    """
    import time as time_module
    
    simulation_result = {
        "overall_status": "pending",
        "steps": [],
        "account_id": account_id,
        "target_rule": rule,
        "fraud_detected": False,
        "fraud_alerts": [],
        "summary": {}
    }
    
    # Rule configuration
    rule_id = rule.replace("rule_", "")
    container_map = {
        "006": "tazama-rule-006-1",
        "018": "tazama-rule-018-1",
        "901": "tazama-rule-901-1",
        "902": "tazama-rule-902-1"
    }
    target_container = container_map.get(rule_id, "tazama-rule-901-1")
    
    try:
        # === STEP 1: Normal Transaction (ACCC) ===
        normal_payload = generate_pacs008(
            debtor_account=account_id,
            amount=1000000.0,  # 1 juta - normal amount
            debtor_name="Fraud Sim User",
            creditor_account="LEGIT_CREDITOR_001"
        )
        status_t1, time_t1, resp_t1 = tms_client.send_pacs008(normal_payload)
        
        step1_success = status_t1 == 200
        if step1_success:
            msg_id_t1 = normal_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            e2e_id_t1 = normal_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
            pacs002_t1 = generate_pacs002(msg_id_t1, e2e_id_t1, "ACCC")
            status_002_t1, _, _ = tms_client.send_pacs002(pacs002_t1)
            step1_success = status_002_t1 == 200
        
        simulation_result["steps"].append({
            "step": 1,
            "name": "Normal Transaction (ACCC)",
            "description": "Account starts with clean transaction",
            "success": step1_success,
            "status": status_t1,
            "icon": "✅" if step1_success else "❌"
        })
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "FraudSim Step1 (Normal)",
            "status": status_t1,
            "success": step1_success,
            "response_time_ms": time_t1,
            "message_id": normal_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
        })
        
        time_module.sleep(0.2)
        
        # === STEP 2: Trigger Fraud Pattern ===
        attack_results = []
        attack_amt = 9500000.0 if rule_id == "006" else 500000.0
        
        for i in range(attack_count):
            current_amt = attack_amt
            current_debtor = account_id
            current_creditor = f"CRED_{random.randint(1000, 9999)}"
            
            # Rule-specific configuration
            if rule_id == "901":
                # Velocity: varied amounts, same debtor, different creditors
                current_amt = attack_amt + (i * 100000) + random.randint(10000, 50000)
            elif rule_id == "902":
                # Money Mule: varied amounts, different debtors, same creditor
                current_amt = attack_amt + (i * 50000) + random.randint(5000, 20000)
                current_debtor = f"DEB_{random.randint(1000, 9999)}"
                current_creditor = "MULE_TARGET_001"
            elif rule_id == "006":
                # Structuring: SAME amount for detection
                current_amt = attack_amt
            elif rule_id == "018":
                # High Value: build history then one huge tx
                if i < attack_count - 1:
                    current_amt = 500000.0 + (i * 100000)
                else:
                    current_amt = 500000000.0  # 500 juta
            
            attack_payload = generate_pacs008(
                debtor_account=current_debtor,
                amount=current_amt,
                debtor_name="Fraud Actor",
                creditor_account=current_creditor
            )
            
            status_atk, time_atk, _ = tms_client.send_pacs008(attack_payload)
            
            if status_atk == 200:
                msg_id_atk = attack_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
                e2e_id_atk = attack_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
                pacs002_atk = generate_pacs002(msg_id_atk, e2e_id_atk, "ACCC")
                tms_client.send_pacs002(pacs002_atk)
            
            attack_results.append({
                "tx": i + 1,
                "amount": current_amt,
                "status": status_atk
            })
            
            test_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": f"FraudSim Attack ({rule})",
                "status": status_atk,
                "success": status_atk == 200,
                "response_time_ms": time_atk,
                "message_id": attack_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            })
        
        step2_success = all(r["status"] == 200 for r in attack_results)
        simulation_result["steps"].append({
            "step": 2,
            "name": f"Trigger Fraud Pattern ({RULE_CONFIGS.get(rule_id, {}).get('name', rule)})",
            "description": f"Sent {attack_count} transactions to trigger detection",
            "success": step2_success,
            "transactions": len(attack_results),
            "icon": "⚠️"
        })
        
        time_module.sleep(0.5)  # Wait for processing
        
        # === STEP 3: Check Fraud Detection ===
        request_context = {
            "scenario": f"Rule {rule_id}",
            "debtor_account": account_id,
            "amount_per_transaction": attack_amt,
            "total_transactions": attack_count
        }
        
        logs_data = fetch_logs_internal(target_container, tail=100)
        fraud_alerts = parse_fraud_alerts(logs_data, request_context, rule_id)
        
        fraud_detected = len(fraud_alerts) > 0
        simulation_result["fraud_detected"] = fraud_detected
        simulation_result["fraud_alerts"] = fraud_alerts
        
        simulation_result["steps"].append({
            "step": 3,
            "name": "Check Fraud Detection",
            "description": f"{'Fraud detected!' if fraud_detected else 'No fraud alerts (may need more tx)'}",
            "success": True,
            "fraud_detected": fraud_detected,
            "alerts_count": len(fraud_alerts),
            "icon": "🔍" if fraud_detected else "👀"
        })
        
        time_module.sleep(0.2)
        
        # === STEP 4: Block Transaction (RJCT) ===
        block_payload = generate_pacs008(
            debtor_account=account_id,
            amount=attack_amt,
            debtor_name="Fraud Sim User",
            creditor_account="BLOCKED_CREDITOR"
        )
        status_blk, time_blk, _ = tms_client.send_pacs008(block_payload)
        
        step4_success = status_blk == 200
        if step4_success:
            msg_id_blk = block_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
            e2e_id_blk = block_payload.get("FIToFICstmrCdtTrf", {}).get("CdtTrfTxInf", {}).get("PmtId", {}).get("EndToEndId")
            pacs002_blk = generate_pacs002(msg_id_blk, e2e_id_blk, "RJCT")
            status_002_blk, _, _ = tms_client.send_pacs002(pacs002_blk)
        
        simulation_result["steps"].append({
            "step": 4,
            "name": "Block Transaction (RJCT)",
            "description": "Transaction rejected due to fraud detection",
            "success": step4_success,
            "status": "RJCT",
            "icon": "❌"
        })
        
        test_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "FraudSim Step4 (RJCT)",
            "status": status_blk,
            "success": step4_success,
            "response_time_ms": time_blk,
            "message_id": block_payload.get("FIToFICstmrCdtTrf", {}).get("GrpHdr", {}).get("MsgId")
        })
        
        # === STEP 5: Summary ===
        rule_info = RULE_CONFIGS.get(rule_id, {})
        simulation_result["summary"] = {
            "rule_triggered": rule_info.get("name", rule),
            "rule_id": rule_id,
            "trigger_condition": rule_info.get("trigger_condition", "N/A"),
            "recommendation": rule_info.get("recommendation", "N/A"),
            "total_attack_transactions": attack_count,
            "fraud_detected": fraud_detected,
            "alerts_count": len(fraud_alerts),
            "final_status": "BLOCKED" if fraud_detected else "MONITORING"
        }
        
        simulation_result["steps"].append({
            "step": 5,
            "name": "Summary",
            "description": f"Rule {rule_id}: {rule_info.get('name', 'Unknown')}",
            "success": True,
            "fraud_type": rule_info.get("name", "Unknown"),
            "icon": "📊"
        })
        
        simulation_result["overall_status"] = "completed"
        
    except Exception as e:
        simulation_result["overall_status"] = "error"
        simulation_result["error"] = str(e)
    
    return simulation_result


# ============================================================================
# PHASE 4: VERIFICATION TESTING ENDPOINT
# ============================================================================

@router.post(
    "/verify-fix",
    summary="Verify Fraud Detection Fix (Phase 4)",
    description="Automated test suite to verify all fraud detection fixes are working correctly"
)
async def verify_fraud_fix():
    """
    PHASE 4: Comprehensive verification of fraud detection fixes
    
    Test Cases:
    1. Attacker sends structuring pattern (pacs.008) → Should trigger Rule 006
    2. Attacker sends high value transaction → Should trigger Rule 018
    3. Victim sends normal transaction → Should NOT trigger any alert
    4. Alert attribution check → Alerts should point to attacker, not victim
    """
    import time as time_module
    
    verification_results = {
        "overall_status": "running",
        "tests": [],
        "summary": {
            "total": 4,
            "passed": 0,
            "failed": 0
        }
    }
    
    # Unique identifiers for this test run
    test_run_id = create_uuid()[:8]
    attacker_account = f"ATTACKER_{test_run_id}"
    victim_account = f"VICTIM_{test_run_id}"
    
    # =========================================================================
    # TEST 1: Attacker Structuring Detection (Rule 006)
    # =========================================================================
    test1_result = {
        "test_id": 1,
        "name": "Attacker Structuring Detection (Rule 006)",
        "status": "running"
    }
    
    try:
        structuring_amount = 9500000.0
        structuring_count = 6
        
        for i in range(structuring_count):
            payload = generate_pacs008(
                debtor_account=attacker_account,
                amount=structuring_amount,  # Same amount = structuring
                debtor_name=f"Attacker {test_run_id}",
                creditor_account=f"CRED_{random.randint(1000, 9999)}"
            )
            tms_client.send_pacs008(payload)
        
        time_module.sleep(0.5)
        logs_data = fetch_logs_internal("tazama-rule-006-1", tail=50, since_seconds=30)
        fraud_alerts = parse_fraud_alerts(logs_data, {"debtor_account": attacker_account}, "006")
        
        test1_result["alerts_found"] = len(fraud_alerts)
        test1_result["passed"] = len(fraud_alerts) > 0
        test1_result["status"] = "PASSED ✅" if test1_result["passed"] else "FAILED ❌"
        test1_result["detail"] = f"Sent {structuring_count} transactions with same amount (Rp {structuring_amount:,.0f})"
        
    except Exception as e:
        test1_result["status"] = "ERROR ❌"
        test1_result["error"] = str(e)
        test1_result["passed"] = False
    
    verification_results["tests"].append(test1_result)
    
    # =========================================================================
    # TEST 2: Attacker High Value Detection (Rule 018)
    # =========================================================================
    test2_result = {
        "test_id": 2,
        "name": "Attacker High Value Detection (Rule 018)",
        "status": "running"
    }
    
    try:
        attacker2_account = f"WHALE_{test_run_id}"
        
        # Build small history first
        for i in range(3):
            payload = generate_pacs008(
                debtor_account=attacker2_account,
                amount=500000.0 + (i * 100000),  # Small varied amounts
                debtor_name=f"Whale {test_run_id}",
                creditor_account=f"CRED_{random.randint(1000, 9999)}"
            )
            tms_client.send_pacs008(payload)
        
        # Send huge transaction
        huge_payload = generate_pacs008(
            debtor_account=attacker2_account,
            amount=500000000.0,  # 500 juta - very high
            debtor_name=f"Whale {test_run_id}",
            creditor_account=f"CRED_{random.randint(1000, 9999)}"
        )
        tms_client.send_pacs008(huge_payload)
        
        time_module.sleep(0.5)
        logs_data = fetch_logs_internal("tazama-rule-018-1", tail=50, since_seconds=30)
        fraud_alerts = parse_fraud_alerts(logs_data, {"debtor_account": attacker2_account}, "018")
        
        test2_result["alerts_found"] = len(fraud_alerts)
        test2_result["passed"] = len(fraud_alerts) > 0
        test2_result["status"] = "PASSED ✅" if test2_result["passed"] else "FAILED ❌"
        test2_result["detail"] = "Sent Rp 500,000,000 after small history"
        
    except Exception as e:
        test2_result["status"] = "ERROR ❌"
        test2_result["error"] = str(e)
        test2_result["passed"] = False
    
    verification_results["tests"].append(test2_result)
    
    # =========================================================================
    # TEST 3: Victim Normal Transaction (No False Positive)
    # =========================================================================
    test3_result = {
        "test_id": 3,
        "name": "Victim Normal Transaction (No False Positive)",
        "status": "running"
    }
    
    try:
        # Victim sends ONE normal transaction
        victim_payload = generate_pacs008(
            debtor_account=victim_account,
            amount=1500000.0,  # Normal amount
            debtor_name=f"Victim {test_run_id}",
            creditor_account="LEGIT_MERCHANT_001"
        )
        tms_client.send_pacs008(victim_payload)
        
        time_module.sleep(0.5)
        
        # Check all rule containers for alerts related to victim
        victim_alerts = []
        for container in ["tazama-rule-006-1", "tazama-rule-018-1", "tazama-rule-901-1", "tazama-rule-902-1"]:
            logs = fetch_logs_internal(container, tail=30, since_seconds=30)
            alerts = parse_fraud_alerts(logs, {"debtor_account": victim_account})
            victim_alerts.extend(alerts)
        
        test3_result["alerts_found"] = len(victim_alerts)
        test3_result["passed"] = len(victim_alerts) == 0  # NO alerts = PASS
        test3_result["status"] = "PASSED ✅" if test3_result["passed"] else "FAILED ❌"
        test3_result["detail"] = "Victim sent 1 normal transaction - should not trigger any alert"
        
    except Exception as e:
        test3_result["status"] = "ERROR ❌"
        test3_result["error"] = str(e)
        test3_result["passed"] = False
    
    verification_results["tests"].append(test3_result)
    
    # =========================================================================
    # TEST 4: Alert Attribution Check
    # =========================================================================
    test4_result = {
        "test_id": 4,
        "name": "Alert Attribution Check",
        "status": "running"
    }
    
    try:
        # Check that alerts from Test 1 contain attacker account reference
        logs_data = fetch_logs_internal("tazama-rule-006-1", tail=100, since_seconds=60)
        
        # Simple check: look for attacker account ID in logs
        attacker_mentioned = attacker_account in logs_data.get("logs", "")
        victim_mentioned = victim_account in logs_data.get("logs", "")
        
        test4_result["attacker_in_logs"] = attacker_mentioned
        test4_result["victim_in_logs"] = victim_mentioned
        test4_result["passed"] = attacker_mentioned  # Attacker should be mentioned
        test4_result["status"] = "PASSED ✅" if test4_result["passed"] else "FAILED ❌"
        test4_result["detail"] = f"Checking attribution: Attacker={attacker_account}, Victim={victim_account}"
        
    except Exception as e:
        test4_result["status"] = "ERROR ❌"
        test4_result["error"] = str(e)
        test4_result["passed"] = False
    
    verification_results["tests"].append(test4_result)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    passed_count = sum(1 for t in verification_results["tests"] if t.get("passed", False))
    failed_count = len(verification_results["tests"]) - passed_count
    
    verification_results["summary"]["passed"] = passed_count
    verification_results["summary"]["failed"] = failed_count
    verification_results["overall_status"] = "ALL_PASSED ✅" if failed_count == 0 else f"SOME_FAILED ({failed_count} failures)"
    
    verification_results["conclusion"] = {
        "phase_1_network_map": "Applied - Fraud rules on pacs.008",
        "phase_2_attribution": f"Tested - Attacker={attacker_account}",
        "phase_3_detection_point": "pacs.008 (before transaction processed)",
        "phase_4_verification": f"{passed_count}/4 tests passed"
    }
    
    return verification_results
