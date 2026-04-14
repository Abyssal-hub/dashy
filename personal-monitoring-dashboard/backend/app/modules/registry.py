from typing import Type

from app.modules.base import ModuleHandler


_registry: dict[str, Type[ModuleHandler]] = {}


def register(module_type: str):
    """Decorator to register a module handler class.
    
    Usage:
        @register("portfolio")
        class PortfolioHandler(ModuleHandler):
            ...
    """
    def decorator(cls: Type[ModuleHandler]) -> Type[ModuleHandler]:
        if not issubclass(cls, ModuleHandler):
            raise TypeError(f"{cls.__name__} must inherit from ModuleHandler")
        _registry[module_type] = cls
        return cls
    return decorator


def get_handler(module_type: str) -> Type[ModuleHandler] | None:
    """Get the handler class for a module type.
    
    Args:
        module_type: The module type identifier
        
    Returns:
        The handler class or None if not found
    """
    return _registry.get(module_type)


def list_module_types() -> list[str]:
    """List all registered module types."""
    return list(_registry.keys())
