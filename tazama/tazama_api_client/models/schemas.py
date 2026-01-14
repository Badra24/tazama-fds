"""
Pydantic Schemas for Request/Response Validation
All models used across the Tazama API Client
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ============ ENUMS ============

class StatusCode(str, Enum):
    """Valid pacs.002 status codes"""
    ACCC = "ACCC"  # Accepted Customer Credit
    ACSC = "ACSC"  # Accepted Settlement Completed
    RJCT = "RJCT"  # Rejected


class ScenarioType(str, Enum):
    """Available attack scenario types"""
    RULE_901 = "rule_901"  # Velocity Attack (multiple tx from same debtor)
    RULE_902 = "rule_902"  # Money Mule (multiple tx to same creditor)
    RULE_006 = "rule_006"  # Structuring (amounts just under threshold)
    RULE_018 = "rule_018"  # High Value Transfer


# ============ REQUEST MODELS ============

class Pacs008Request(BaseModel):
    """Request model for pacs.008 test"""
    debtor_account: Optional[str] = Field(None, description="Debtor account ID")
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount (must be positive)")
    debtor_name: Optional[str] = Field(None, description="Debtor name")


class QuickStatusRequest(BaseModel):
    """Request model for quick status test"""
    status_code: StatusCode = Field(StatusCode.ACCC, description="Final status code")
    debtor_account: Optional[str] = Field(None, description="Debtor account ID")
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount")


class FullTransactionRequest(BaseModel):
    """Request model for full transaction test"""
    debtor_account: Optional[str] = Field(None, description="Debtor account ID")
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount")


class VelocityTestRequest(BaseModel):
    """Request model for velocity attack test (Rule 901)"""
    debtor_account: str = Field(..., min_length=1, description="Target debtor account")
    debtor_name: str = Field(..., min_length=1, description="Debtor name")
    count: int = Field(20, ge=1, le=100, description="Number of transactions to send")


class CreditorTestRequest(BaseModel):
    """Request model for creditor velocity test (Rule 902 - Money Mule)"""
    creditor_account: str = Field(..., min_length=1, description="Target creditor account")
    creditor_name: str = Field(..., min_length=1, description="Creditor name")
    count: int = Field(20, ge=1, le=100, description="Number of transactions")
    amount: float = Field(500000.0, gt=0, description="Amount per transaction")


class AttackScenarioRequest(BaseModel):
    """Request model for attack scenario test"""
    scenario: ScenarioType = Field(..., description="Attack scenario type")
    count: int = Field(5, ge=1, le=50, description="Number of transactions")
    amount: Optional[float] = Field(None, gt=0, description="Optional custom amount")


class BatchTestRequest(BaseModel):
    """Request model for batch testing"""
    scenarios: str = Field(..., description="Comma-separated scenario names")


# ============ RESPONSE MODELS ============

class TestRecord(BaseModel):
    """Record of a single test execution"""
    timestamp: str
    type: str
    status: int
    response_time_ms: float
    success: bool
    message_id: str
    end_to_end_id: Optional[str] = None


class Pacs008Response(BaseModel):
    """Response model for pacs.008 test"""
    status: str
    http_code: int
    response_time_ms: float
    payload_sent: Dict[str, Any]
    tms_response: Dict[str, Any]
    test_record: TestRecord


class QuickStatusResponse(BaseModel):
    """Response model for quick status test"""
    status: str
    http_code: int
    response_time_ms: float
    payload_sent: Dict[str, Any]
    tms_response: Dict[str, Any]
    test_record: TestRecord


class FullTransactionResponse(BaseModel):
    """Response model for full transaction test"""
    pacs008: Optional[Dict[str, Any]] = None
    pacs002: Optional[Dict[str, Any]] = None
    overall_status: str


class FraudAlert(BaseModel):
    """Fraud alert extracted from logs"""
    raw: str
    title: str
    desc: str


class AttackResult(BaseModel):
    """Result of a single attack iteration"""
    iteration: int
    status: int
    response_time_ms: Optional[float] = None
    response: Optional[Dict[str, Any]] = None
    pacs002_response: Optional[Dict[str, Any]] = None
    amount: Optional[float] = None
    error: Optional[str] = None


class AttackResponse(BaseModel):
    """Response model for attack simulations"""
    status: str
    total_sent: int
    results: List[AttackResult]
    fraud_alerts: List[FraudAlert]


class BatchScenarioResult(BaseModel):
    """Result of a single batch scenario"""
    scenario: str
    status: str
    details: Optional[Dict[str, Any]] = None


class BatchResponse(BaseModel):
    """Response model for batch testing"""
    status: str
    total_scenarios: int
    success_count: int
    failure_count: int
    total_time_ms: float
    results: List[BatchScenarioResult]


class StatsResponse(BaseModel):
    """Response model for statistics"""
    total_tests: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_response_time_ms: float
    tests_by_type: Dict[str, Any]  # Contains {"count": int, "success": int} per type


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    tms_status: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    http_code: Optional[int] = None
    message: Optional[str] = None


class LogsResponse(BaseModel):
    """Response model for container logs"""
    container: str
    status: str
    logs: Optional[str] = None
    message: Optional[str] = None


class FraudAlertsResponse(BaseModel):
    """Response model for fraud alerts aggregation"""
    status: str
    fraud_alerts: List[FraudAlert]
    checked_containers: List[str]


class ErrorResponse(BaseModel):
    """Standard error response"""
    status: str = "error"
    message: str
