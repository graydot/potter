#!/usr/bin/env python3
"""
Configuration Sources
Abstract interface and implementations for configuration sources
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)


class ConfigurationSource(ABC):
    """Abstract base class for configuration sources"""
    
    def __init__(self, name: str, priority: int = 100):
        self.name = name
        self.priority = priority
        self.logger = logging.getLogger(f"config.source.{name}")
        self._change_callbacks: List[Callable] = []
        self._is_watching = False
    
    @abstractmethod
    def load_configuration(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    def watch_changes(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
        if not self._is_watching:
            return self._start_watching()
        return True
    
    def stop_watching(self):
        self._is_watching = False
        self._stop_watching()
    
    def _start_watching(self) -> bool:
        self._is_watching = True
        return True
    
    def _stop_watching(self):
        pass
    
    def _notify_change(self, new_config: Dict[str, Any]):
        for callback in self._change_callbacks:
            try:
                callback(new_config)
            except Exception as e:
                self.logger.error(f"Error in change callback: {e}")
    
    def get_source_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'priority': self.priority,
            'available': self.is_available(),
            'watching': self._is_watching,
            'callbacks': len(self._change_callbacks)
        }


class FileConfigurationSource(ConfigurationSource):
    """File-based configuration source"""
    
    def __init__(self, file_path: str, format: str = 'auto', 
                 create_if_missing: bool = True, priority: int = 100):
        super().__init__(f"file:{os.path.basename(file_path)}", priority)
        self.file_path = Path(file_path)
        self.format = format
        self.create_if_missing = create_if_missing
        self._last_modified = None
        self._file_watcher = None
        
        if self.format == 'auto':
            self.format = self._detect_format()
        
        if create_if_missing and not self.file_path.exists():
            self._create_empty_file()
    
    def load_configuration(self) -> Dict[str, Any]:
        if not self.file_path.exists():
            self.logger.warning(f"Configuration file not found: {self.file_path}")
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                if not content:
                    return {}
                
                if self.format == 'json':
                    config = json.loads(content)
                elif self.format == 'yaml' and YAML_AVAILABLE:
                    config = yaml.safe_load(content)
                else:
                    raise ValueError(f"Unsupported format: {self.format}")
                
                self._last_modified = self.file_path.stat().st_mtime
                return config or {}
                
        except Exception as e:
            self.logger.error(f"Error loading configuration from {self.file_path}: {e}")
            return {}
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.format == 'json':
                    json.dump(config, f, indent=2, ensure_ascii=False)
                elif self.format == 'yaml' and YAML_AVAILABLE:
                    yaml.dump(config, f, default_flow_style=False, 
                            allow_unicode=True, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {self.format}")
            
            self._last_modified = self.file_path.stat().st_mtime
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration to {self.file_path}: {e}")
            return False
    
    def is_available(self) -> bool:
        try:
            if self.file_path.exists():
                return self.file_path.is_file() and os.access(self.file_path, os.R_OK)
            else:
                parent = self.file_path.parent
                return parent.exists() and os.access(parent, os.W_OK)
        except Exception:
            return False
    
    def _detect_format(self) -> str:
        suffix = self.file_path.suffix.lower()
        if suffix in ['.json']:
            return 'json'
        elif suffix in ['.yaml', '.yml']:
            return 'yaml'
        else:
            return 'json'
    
    def _create_empty_file(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.format == 'json':
                with open(self.file_path, 'w') as f:
                    json.dump({}, f)
            elif self.format == 'yaml' and YAML_AVAILABLE:
                with open(self.file_path, 'w') as f:
                    yaml.dump({}, f)
            
        except Exception as e:
            self.logger.error(f"Error creating configuration file: {e}")


class EnvironmentConfigurationSource(ConfigurationSource):
    """Environment variable configuration source"""
    
    def __init__(self, prefix: str = "POTTER_", priority: int = 50):
        super().__init__("environment", priority)
        self.prefix = prefix.upper()
    
    def load_configuration(self) -> Dict[str, Any]:
        config = {}
        
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                config_key = key[len(self.prefix):].lower()
                config = self._set_nested_value(config, config_key, self._parse_value(value))
        
        return config
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        try:
            flattened = self._flatten_config(config)
            
            for key, value in flattened.items():
                env_key = f"{self.prefix}{key.upper()}"
                os.environ[env_key] = str(value)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting environment variables: {e}")
            return False
    
    def is_available(self) -> bool:
        return True
    
    def _parse_value(self, value: str) -> Any:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> Dict[str, Any]:
        parts = key.split('_')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        return config
    
    def _flatten_config(self, config: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        result = {}
        
        for key, value in config.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, dict):
                result.update(self._flatten_config(value, new_key))
            else:
                result[new_key] = value
        
        return result


class MemoryConfigurationSource(ConfigurationSource):
    """In-memory configuration source"""
    
    def __init__(self, initial_config: Dict[str, Any] = None, priority: int = 10):
        super().__init__("memory", priority)
        self._config = initial_config or {}
    
    def load_configuration(self) -> Dict[str, Any]:
        return self._config.copy()
    
    def save_configuration(self, config: Dict[str, Any]) -> bool:
        old_config = self._config.copy()
        self._config = config.copy()
        
        if old_config != self._config:
            self._notify_change(self._config)
        
        return True
    
    def is_available(self) -> bool:
        return True
    
    def update_value(self, key: str, value: Any):
        self._set_nested_value(self._config, key, value)
        self._notify_change(self._config)
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        parts = key.split('.')
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value 