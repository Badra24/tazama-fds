"""
Health & Stats Router
Endpoints for system health check and statistics
"""
from fastapi import APIRouter
from services.tms_client import tms_client
from models.schemas import HealthResponse, StatsResponse

router = APIRouter(prefix="/api", tags=["Health & Stats"])

# In-memory storage reference (will be set from main.py)
test_history = []


def set_history_reference(history_list):
    global test_history
    test_history = history_list


@router.get("/health", response_model=HealthResponse)
async def check_tms_health():
    """Check if TMS service is running"""
    result = tms_client.check_health()
    # Add reloaded flag for debugging
    result["reloaded"] = True
    return result


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics"""
    if not test_history:
        return {
            "total_tests": 0,
            "success_count": 0,
            "failure_count": 0,
            "success_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "tests_by_type": {}
        }
    
    total = len(test_history)
    success_count = sum(1 for t in test_history if t.get("success", False))
    failure_count = total - success_count
    
    response_times = [t.get("response_time_ms", 0) for t in test_history if t.get("response_time_ms")]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Group by type
    tests_by_type = {}
    for t in test_history:
        test_type = t.get("type", "unknown")
        if test_type not in tests_by_type:
            tests_by_type[test_type] = {"count": 0, "success": 0}
        tests_by_type[test_type]["count"] += 1
        if t.get("success", False):
            tests_by_type[test_type]["success"] += 1
    
    return {
        "total_tests": total,
        "success_count": success_count,
        "failure_count": failure_count,
        "success_rate": round((success_count / total) * 100, 2) if total > 0 else 0,
        "avg_response_time_ms": round(avg_response_time, 2),
        "tests_by_type": tests_by_type
    }


@router.get("/history")
async def get_test_history():
    """Get test history"""
    return {
        "total_tests": len(test_history),
        "history": test_history[-20:]  # Last 20
    }


@router.delete("/history")
async def clear_history():
    """Clear test history"""
    test_history.clear()
    return {"status": "success", "message": "History cleared"}
