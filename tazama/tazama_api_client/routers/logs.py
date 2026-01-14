"""
Logs Router
Container logs and WebSocket for real-time streaming
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import subprocess
import asyncio

from models.schemas import LogsResponse, FraudAlertsResponse

router = APIRouter(tags=["Logs"])


@router.get(
    "/api/logs/{container_name}",
    response_model=LogsResponse,
    summary="Get Container Logs",
    description="Fetch logs from a Tazama docker container"
)
async def get_container_logs(container_name: str, tail: int = 50):
    """Fetch logs from a docker container"""
    try:
        if not container_name.startswith("tazama-"):
            return {"container": container_name, "status": "error", "message": "Invalid container name"}
            
        result = subprocess.run(
            ["docker", "logs", container_name, "--tail", str(tail)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return {"container": container_name, "status": "error", "message": result.stderr}
            
        return {"container": container_name, "status": "success", "logs": result.stdout}
    except Exception as e:
        return {"container": container_name, "status": "error", "message": str(e)}


@router.websocket("/ws/logs/{container_name}")
async def websocket_logs(websocket: WebSocket, container_name: str):
    """
    WebSocket endpoint for real-time log streaming.
    Streams docker logs continuously to connected clients.
    """
    await websocket.accept()
    
    if not container_name.startswith("tazama-"):
        await websocket.send_json({"error": "Invalid container name"})
        await websocket.close()
        return
    
    try:
        # Start docker logs with follow
        process = await asyncio.create_subprocess_exec(
            "docker", "logs", container_name, "--follow", "--tail", "20",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        async def read_logs():
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                try:
                    await websocket.send_text(line.decode('utf-8').strip())
                except:
                    break
        
        async def check_disconnect():
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                process.terminate()
        
        # Run both tasks concurrently
        await asyncio.gather(
            read_logs(),
            check_disconnect(),
            return_exceptions=True
        )
        
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@router.get(
    "/api/fraud-alerts",
    response_model=FraudAlertsResponse,
    summary="Get Fraud Alerts",
    description="Get latest fraud alerts from all rule containers (901, 902, 006, 018)"
)
async def get_fraud_alerts():
    """Get latest fraud alerts from all rule containers"""
    from routers.attacks import fetch_logs_internal, parse_fraud_alerts
    
    all_alerts = []
    containers = [
        "tazama-rule-901-1",
        "tazama-rule-902-1",
        "tazama-rule-006-1",
        "tazama-rule-018-1"
    ]
    
    for container in containers:
        logs_data = fetch_logs_internal(container, tail=50)
        alerts = parse_fraud_alerts(logs_data)
        all_alerts.extend(alerts)
    
    # Deduplicate
    seen = set()
    unique_alerts = []
    for alert in all_alerts:
        if alert['raw'] not in seen:
            seen.add(alert['raw'])
            unique_alerts.append(alert)
    
    return {
        "status": "success",
        "fraud_alerts": unique_alerts,
        "checked_containers": containers
    }
