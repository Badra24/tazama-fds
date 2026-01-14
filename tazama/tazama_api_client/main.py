"""
Tazama API Test Client - Main Application
FastAPI web interface untuk test Tazama TMS Service

Refactored with proper project structure:
- config.py: Environment-based configuration
- routers/: Endpoint handlers organized by feature
- models/: Pydantic schemas for validation
- services/: Reusable business logic
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

# Import routers
from routers.health import router as health_router, set_history_reference as set_health_history
from routers.transactions import router as transactions_router, set_history_reference as set_transactions_history
from routers.attacks import router as attacks_router, set_history_reference as set_attacks_history
from routers.batch import router as batch_router, set_history_reference as set_batch_history
from routers.logs import router as logs_router
from routers.e2e_flow import router as e2e_flow_router, set_history_reference as set_e2e_flow_history

from config import TMS_BASE_URL

# Initialize FastAPI app with OpenAPI docs
app = FastAPI(
    title="Tazama API Test Client",
    description="""
    Interactive web client untuk test Tazama Transaction Monitoring Service.
    
    ## Features
    - 📤 Send pacs.008 payment requests
    - ⚡ Quick status tests (ACCC, ACSC, RJCT)
    - 🔗 Full E2E ISO 20022 Flow (pain.001 → pain.013 → pacs.008 → pacs.002)
    - 🚨 Attack simulations (Velocity, Money Mule, Structuring, High Value)
    - 📊 Dashboard statistics
    - 🔄 Batch testing
    - 📡 Real-time log streaming via WebSocket
    """,
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared test history (in-memory storage)
test_history = []

# Set history reference for all routers
set_health_history(test_history)
set_transactions_history(test_history)
set_attacks_history(test_history)
set_batch_history(test_history)
set_e2e_flow_history(test_history)

# Mount routers

app.include_router(health_router)
app.include_router(transactions_router)
app.include_router(attacks_router)
app.include_router(batch_router)
app.include_router(logs_router)
app.include_router(e2e_flow_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "tms_url": TMS_BASE_URL,
            "history": test_history[-10:]
        }
    )


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_HOST, SERVER_PORT
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
