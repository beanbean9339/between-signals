"""
Configuration management for Between Signals.

Loads and validates room-specific configuration from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class RoomConfig:
    """
    Configuration for a single room (Environment A or B).
    
    Loads settings from JSON file and provides access to configuration values.
    """

    def __init__(self, room_id: str, config_path: Optional[str] = None):
        """
        Initialize room configuration.
        
        Args:
            room_id: Room identifier ("A" or "B")
            config_path: Path to JSON config file. If None, looks for 
                        config/{room_id.lower()}.json
        """
        self.room_id = room_id
        self.config_path = config_path or self._default_config_path(room_id)
        self._config: Dict[str, Any] = {}
        
        self._load_config()
        self._validate_config()

    def _default_config_path(self, room_id: str) -> Path:
        """Generate default config path based on room ID."""
        config_dir = Path(__file__).parent.parent / "config"
        return config_dir / f"room_{room_id.lower()}.json"

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            logger.warning(
                f"Config file not found: {config_file}. "
                "Using default values."
            )
            self._config = self._default_config()
            return

        try:
            with open(config_file, 'r') as f:
                self._config = json.load(f)
            logger.info(f"Loaded config from {config_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_file}: {e}")
            self._config = self._default_config()
        except IOError as e:
            logger.error(f"Cannot read {config_file}: {e}")
            self._config = self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "room_id": self.room_id,
            "environment": "unknown",
            "mode": "simulation",
            "backend_port": 8000,
            "osc_output_host": "127.0.0.1",
            "osc_output_port": 7001 if self.room_id == "A" else 7002,
            "microphone_device": -1,  # -1 means auto-detect
            "whisper_model": "base",
            "whisper_device": "cpu",
            "whisper_compute_type": "int8",
            "audio_sample_rate": 44100,
            "whisper_sample_rate": 16000,
            "audio_process_seconds": 4,
            "enable_vad": False,  # Voice Activity Detection
        }

    def _validate_config(self) -> None:
        """Validate that required keys are present."""
        required_keys = ["room_id", "environment"]
        
        for key in required_keys:
            if key not in self._config:
                logger.warning(
                    f"Missing required config key: {key}. "
                    "Using default."
                )
                self._config[key] = self._default_config()[key]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return key in self._config

    def __str__(self) -> str:
        """String representation showing key settings."""
        return (
            f"RoomConfig(id={self.room_id}, "
            f"env={self.get('environment')}, "
            f"mode={self.get('mode')}, "
            f"osc_port={self.get('osc_output_port')})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


# Default configuration values (used when no JSON file exists)
DEFAULT_CONFIG = {
    "room_id": "A",
    "environment": "grass",
    "mode": "simulation",
    "backend_port": 8000,
    "osc_output_host": "127.0.0.1",
    "osc_output_port": 7001,
    "microphone_device": -1,
    "whisper_model": "base",
    "whisper_device": "cpu",
    "whisper_compute_type": "int8",
    "audio_sample_rate": 44100,
    "whisper_sample_rate": 16000,
    "audio_process_seconds": 4,
    "enable_vad": False,
}

# Legacy constants for backward compatibility
ENV_A_PORT = 7001
ENV_B_PORT = 7002
BACKEND_PORT = 8000
LOCAL_HOST = "127.0.0.1"
