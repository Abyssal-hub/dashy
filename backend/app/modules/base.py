from abc import ABC, abstractmethod
from typing import Any


class ModuleHandler(ABC):
    """Abstract base class for all module handlers.
    
    Each module type (portfolio, calendar, log) implements this interface
    to provide data and validate configuration.
    """
    
    @property
    @abstractmethod
    def module_type(self) -> str:
        """Return the module type identifier (e.g., 'portfolio', 'calendar')."""
        pass
    
    @abstractmethod
    async def get_data(self, module_id: str, size: str, **kwargs) -> dict[str, Any]:
        """Fetch and return module data based on size preset.
        
        Args:
            module_id: The module instance ID
            size: One of 'small', 'medium', 'large'
            **kwargs: Optional additional arguments (e.g., db_session)
            
        Returns:
            Dict containing the module-specific data payload
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate module configuration.
        
        Args:
            config: User-provided configuration dict
            
        Returns:
            True if config is valid, False otherwise
        """
        pass
