"""
Single-Flag Configuration Demo
Demonstrates how ONE flag controls ALL deployment settings
"""

from config import USE_LOCAL_POSTGRES, TMS_BASE_URL

print("=" * 60)
print("🎯 TAZAMA API CLIENT - DEPLOYMENT CONFIGURATION")
print("=" * 60)
print()

# Show current configuration
if USE_LOCAL_POSTGRES:
    print("✅ ACTIVE DEPLOYMENT: Local PostgreSQL (tazama-local-db)")
    print()
    print("📊 Configuration:")
    print("   • TMS Endpoint:      http://localhost:3001")
    print("   • Database Strategy: LocalPostgresStrategy")
    print("   • PostgreSQL:        localhost:5430")
    print("   • Database:          event_history (4 separate DBs)")
    print()
    print("🔗 Services Required:")
    print("   • PostgreSQL (Postgres.app on port 5430)")
    print("   • tazama-local-db containers (port 3001)")
    print()
    print("💡 Start with:")
    print("   cd tazama-local-db && ./start.sh")
else:
    print("✅ ACTIVE DEPLOYMENT: Full Docker Stack")
    print()
    print("📊 Configuration:")
    print("   • TMS Endpoint:      http://localhost:3000")
    print("   • Database Strategy: FullDockerStrategy")
    print("   • PostgreSQL:        Docker container (tazama-postgres-1)")
    print("   • Database:          event_history (in container)")
    print()
    print("🔗 Services Required:")
    print("   • Full-Stack-Docker-Tazama (all in Docker)")
    print()
    print("💡 Start with:")
    print("   cd Full-Stack-Docker-Tazama && docker-compose up -d")

print()
print("=" * 60)
print("🔄 TO SWITCH:")
print("   Edit config.py → Change USE_LOCAL_POSTGRES")
print("   Then restart: python -m uvicorn main:app --reload")
print("=" * 60)
print()

# Verify TMS URL is correct
print(f"🌐 TMS URL configured: {TMS_BASE_URL}")
print()
