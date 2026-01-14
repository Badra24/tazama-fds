"""
Database Query Service - Strategy Pattern
Supports switching between Full Docker and Local PostgreSQL
"""

import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class DatabaseQueryStrategy(ABC):
    """Abstract base class for database query strategies"""
    
    @abstractmethod
    def execute_query(self, query: str, format_csv: bool = False) -> subprocess.CompletedProcess:
        """Execute a query and return the result"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name for logging"""
        pass


class FullDockerStrategy(DatabaseQueryStrategy):
    """Query PostgreSQL inside Docker container (Full-Stack-Docker-Tazama)"""
    
    def __init__(self, container_name: str = "tazama-postgres-1", 
                 database: str = "event_history"):
        self.container_name = container_name
        self.database = database
    
    def execute_query(self, query: str, format_csv: bool = False) -> subprocess.CompletedProcess:
        """Execute query via docker exec"""
        cmd = ["docker", "exec", "-i", self.container_name, 
               "psql", "-U", "postgres", "-d", self.database]
        
        if format_csv:
            cmd.extend(["-t", "-A", "-F", ","])
        else:
            cmd.extend(["-t", "-A"])
        
        cmd.extend(["-c", query])
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
    
    def get_name(self) -> str:
        return f"FullDocker({self.container_name}:{self.database})"


class LocalPostgresStrategy(DatabaseQueryStrategy):
    """Query local PostgreSQL directly (tazama-local-db)"""
    
    def __init__(self, host: str = "localhost", port: int = 5430, 
                 user: str = "badraaji", database: str = "event_history"):
        self.host = host
        self.port = port
        self.user = user
        self.database = database
    
    def execute_query(self, query: str, format_csv: bool = False) -> subprocess.CompletedProcess:
        """Execute query via psql"""
        cmd = ["psql", "-h", self.host, "-p", str(self.port), 
               "-U", self.user, "-d", self.database]
        
        if format_csv:
            cmd.extend(["-t", "-A", "-F", ","])
        else:
            cmd.extend(["-t", "-A"])
        
        cmd.extend(["-c", query])
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
    
    def get_name(self) -> str:
        return f"LocalPostgres({self.host}:{self.port}/{self.database})"


class DatabaseQueryService:
    """Service for querying Tazama database with switchable strategies"""
    
    def __init__(self, strategy: DatabaseQueryStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: DatabaseQueryStrategy):
        """Switch database query strategy at runtime"""
        self.strategy = strategy
    
    def get_transaction_summary(self) -> Dict:
        """Get transaction summary grouped by debtor and creditor"""
        try:
            # Query debtor (source) summary
            debtor_query = """
            SELECT source as account, COUNT(*) as tx_count, SUM(amt) as total_amount
            FROM transaction 
            WHERE source IS NOT NULL AND source != ''
            GROUP BY source 
            ORDER BY tx_count DESC 
            LIMIT 20;
            """
            
            # Query creditor (destination) summary
            creditor_query = """
            SELECT destination as account, COUNT(*) as tx_count, SUM(amt) as total_amount
            FROM transaction 
            WHERE destination IS NOT NULL AND destination != ''
            GROUP BY destination 
            ORDER BY tx_count DESC 
            LIMIT 20;
            """
            
            # Total count
            total_query = "SELECT COUNT(*) as total FROM transaction;"
            
            # Execute queries
            result_debtor = self.strategy.execute_query(debtor_query, format_csv=True)
            
            if result_debtor.returncode != 0:
                return {
                    "status": "error", 
                    "message": f"Debtor query failed: {result_debtor.stderr}",
                    "strategy": self.strategy.get_name()
                }
            
            result_creditor = self.strategy.execute_query(creditor_query, format_csv=True)
            
            if result_creditor.returncode != 0:
                return {
                    "status": "error", 
                    "message": f"Creditor query failed: {result_creditor.stderr}",
                    "strategy": self.strategy.get_name()
                }
            
            result_total = self.strategy.execute_query(total_query)
            
            if result_total.returncode != 0:
                return {
                    "status": "error", 
                    "message": f"Total query failed: {result_total.stderr}",
                    "strategy": self.strategy.get_name()
                }
            
            # Parse results
            debtors = self._parse_csv_result(result_debtor.stdout)
            creditors = self._parse_csv_result(result_creditor.stdout)
            total = int(result_total.stdout.strip()) if result_total.stdout.strip() else 0
            
            return {
                "status": "success",
                "total_transactions": total,
                "debtors": debtors,
                "creditors": creditors,
                "strategy": self.strategy.get_name()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error", 
                "message": "Database query timeout (>10s)",
                "strategy": self.strategy.get_name()
            }
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "strategy": self.strategy.get_name()
            }
    
    def _parse_csv_result(self, csv_data: str) -> List[Dict]:
        """Parse CSV formatted query result"""
        results = []
        for line in csv_data.strip().split('\n'):
            if line and ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    results.append({
                        "account": parts[0],
                        "tx_count": int(parts[1]) if parts[1] else 0,
                        "total_amount": float(parts[2]) if len(parts) > 2 and parts[2] else 0
                    })
        return results


# Factory function for easy creation
def create_database_service(use_local: bool = False) -> DatabaseQueryService:
    """
    Factory function to create DatabaseQueryService with appropriate strategy
    
    Args:
        use_local: If True, use LocalPostgresStrategy. If False, use FullDockerStrategy.
    
    Returns:
        Configured DatabaseQueryService instance
    """
    if use_local:
        strategy = LocalPostgresStrategy(
            host="localhost",
            port=5430,
            user="badraaji",
            database="event_history"
        )
    else:
        strategy = FullDockerStrategy(
            container_name="tazama-postgres-1",
            database="event_history"
        )
    
    return DatabaseQueryService(strategy)
