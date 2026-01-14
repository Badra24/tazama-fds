"""
TMS Client - Centralized API calls to Tazama TMS Service
"""
import requests
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from config  import TMS_BASE_URL, TMS_ENDPOINTS, SOURCE_TENANT_ID, REQUEST_TIMEOUT

class TMSClient:
    """Client for interacting with Tazama TMS Service"""
    
    def __init__(self):
        self.base_url = TMS_BASE_URL
        self.endpoints = TMS_ENDPOINTS
        self.tenant_id = SOURCE_TENANT_ID
        self.timeout = REQUEST_TIMEOUT
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "SourceTenantId": self.tenant_id
        }
    
    def check_health(self, check_docker=True) -> Dict[str, Any]:
        """Check TMS service health
        
        Args:
            check_docker: If HTTP fails, try checking Docker container status
        """
        import subprocess
        
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['health']}",
                timeout=5
            )
            return {
                "status": "success",
                "tms_status": response.json(),
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "http_code": response.status_code
            }
        except requests.exceptions.ConnectionError:
            # Fallback: Check Docker container status
            if check_docker:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "--filter", "name=tazama-tms", "--format", "{{.Status}}"],
                        capture_output=True, text=True, timeout=5
                    )
                    container_status = result.stdout.strip()
                    if "Up" in container_status:
                        return {
                            "status": "success",
                            "message": "TMS container is running (HTTP endpoint may be internal only)",
                            "container_status": container_status,
                            "tms_url": self.base_url,
                            "note": "TMS Fastify listens on 127.0.0.1 inside container"
                        }
                except Exception:
                    pass
            
            return {
                "status": "error",
                "message": "Cannot connect to TMS service. Is it running?",
                "tms_url": self.base_url
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def send_pacs008(self, payload: dict) -> Tuple[int, float, Any]:
        """
        Send pacs.008 payment request
        Returns: (status_code, response_time_ms, response_data)
        """
        start_time = datetime.now()
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoints['pacs008']}",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return response.status_code, response_time, response.json()
            else:
                return response.status_code, response_time, response.text
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return 0, response_time, str(e)
    
    def send_pacs002(self, payload: dict) -> Tuple[int, float, Any]:
        """
        Send pacs.002 confirmation
        Returns: (status_code, response_time_ms, response_data)
        """
        start_time = datetime.now()
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoints['pacs002']}",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return response.status_code, response_time, response.json()
            else:
                return response.status_code, response_time, response.text
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return 0, response_time, str(e)
    
    def send_pain001(self, payload: dict) -> Tuple[int, float, Any]:
        """
        Send pain.001 Customer Credit Transfer Initiation
        Returns: (status_code, response_time_ms, response_data)
        """
        start_time = datetime.now()
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoints['pain001']}",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return response.status_code, response_time, response.json()
            else:
                return response.status_code, response_time, response.text
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return 0, response_time, str(e)
    
    def send_pain013(self, payload: dict) -> Tuple[int, float, Any]:
        """
        Send pain.013 Creditor Payment Activation Request
        Returns: (status_code, response_time_ms, response_data)
        """
        start_time = datetime.now()
        try:
            response = requests.post(
                f"{self.base_url}{self.endpoints['pain013']}",
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                return response.status_code, response_time, response.json()
            else:
                return response.status_code, response_time, response.text
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return 0, response_time, str(e)


# Singleton instance
tms_client = TMSClient()
