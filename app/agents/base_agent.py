"""
Base Agent for Envoyou SEC API

Provides common functionality for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all Envoyou SEC API agents."""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.created_at = datetime.utcnow()
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def process(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Process data and return results."""
        pass
    
    def log_action(self, action: str, data: Optional[Dict[str, Any]] = None):
        """Log agent actions for audit trail."""
        log_entry = {
            "agent": self.name,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data or {}
        }
        self.logger.info(f"Agent action: {action}", extra=log_entry)
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate required input fields."""
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        return True
    
    def create_response(self, status: str, data: Dict[str, Any], 
                      message: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized response format."""
        return {
            "status": status,
            "agent": self.name,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "data": data
        }