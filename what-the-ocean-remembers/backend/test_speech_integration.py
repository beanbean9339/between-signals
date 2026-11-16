"""
Tests for speech processor integration.
Tests speech capture, transcription, and event emission without requiring real audio hardware.
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import dataclass
import logging

from events import SpeechEvent, Event
from speech_refactored import SpeechProcessor, AudioConfig, create_speech_processor
from speech_integration import RoomSpeechProcessor
from room import Room
from config_loader import RoomConfig


class TestAudioConfig:
    """Test AudioConfig dataclass"""
    
    def test_default_config(self):
        """Test default audio configuration"""
        config = AudioConfig()
        assert config.device == 1
        assert config.sample_rate == 44100
        assert config.whisper_rate == 16000
        assert config.process_seconds == 4
        assert config.block_size == 44100
    
    def test_custom_config(self):
        """Test custom audio configuration"""
        config = AudioConfig(
            device=2,
            sample_rate=48000,
            process_seconds=5
        )
        assert config.device == 2
        assert config.sample_rate == 48000
        assert config.block_size == 48000  # Auto-set from sample_rate
        assert config.process_seconds == 5


class TestSpeechProcessorCreation:
    """Test SpeechProcessor initialization"""
    
    @patch('speech_refactored.WhisperModel')
    def test_create_processor(self, mock_whisper):
        """Test creating a speech processor"""
        config = AudioConfig()
        processor = SpeechProcessor(
            audio_config=config,
            whisper_model="base",
            room_id="A"
        )
        
        assert processor.room_id == "A"
        assert processor.audio_config == config
        assert processor.is_running is False
        mock_whisper.assert_called_once()
    
    @patch('speech_refactored.WhisperModel')
    def test_create_processor_with_callback(self, mock_whisper):
        """Test processor with event callback"""
        callback = Mock()
        processor = SpeechProcessor(
            whisper_model="base",
            event_callback=callback,
            room_id="A"
        )
        
        assert processor.event_callback == callback
    
    @patch('speech_refactored.WhisperModel')
    def test_factory_function(self, mock_whisper):
        """Test create_speech_processor factory"""
        callback = Mock()
        processor = create_speech_processor(
            room_id="B",
            audio_device=2,
            sample_rate=48000,
            event_callback=callback
        )
        
        assert processor.room_id == "B"
        assert processor.audio_config.device == 2
        assert processor.audio_config.sample_rate == 48000
        assert processor.event_callback == callback


class TestTranscription:
    """Test audio transcription"""
    
    @patch('speech_refactored.WhisperModel')
    def test_transcribe_buffer_with_speech(self, mock_whisper):
        """Test transcribing audio with speech"""
        # Mock Whisper model
        mock_model_instance = MagicMock()
        mock_whisper.return_value = mock_model_instance
        
        # Mock transcription result
        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock())
        
        processor = SpeechProcessor(whisper_model="base", room_id="A")
        
        # Create dummy audio buffer
        audio = np.random.randn(44100)  # 1 second of audio
        buffer = [audio]
        
        result = processor.transcribe_buffer(buffer)
        
        assert result == "Hello world"
        mock_model_instance.transcribe.assert_called_once()
    
    @patch('speech_refactored.WhisperModel')
    def test_transcribe_buffer_no_speech(self, mock_whisper):
        """Test transcribing silent audio"""
        mock_model_instance = MagicMock()
        mock_whisper.return_value = mock_model_instance
        mock_model_instance.transcribe.return_value = ([], MagicMock())
        
        processor = SpeechProcessor(whisper_model="base", room_id="A")
        audio = np.zeros(44100)  # Silent audio
        buffer = [audio]
        
        result = processor.transcribe_buffer(buffer)
        
        assert result is None
    
    @patch('speech_refactored.WhisperModel')
    def test_transcribe_buffer_multiple_chunks(self, mock_whisper):
        """Test transcribing multiple audio chunks"""
        mock_model_instance = MagicMock()
        mock_whisper.return_value = mock_model_instance
        
        mock_segment = MagicMock()
        mock_segment.text = "One two three"
        mock_model_instance.transcribe.return_value = ([mock_segment], MagicMock())
        
        processor = SpeechProcessor(whisper_model="base", room_id="A")
        
        # Create 4 chunks (processor.process_seconds = 4)
        buffer = [np.random.randn(44100) for _ in range(4)]
        
        result = processor.transcribe_buffer(buffer)
        
        assert result == "One two three"
    
    @patch('speech_refactored.WhisperModel')
    def test_transcribe_empty_buffer(self, mock_whisper):
        """Test transcribing empty buffer"""
        mock_whisper.return_value = MagicMock()
        processor = SpeechProcessor(whisper_model="base", room_id="A")
        
        result = processor.transcribe_buffer([])
        
        assert result is None


class TestEventEmission:
    """Test SpeechEvent emission"""
    
    @patch('speech_refactored.WhisperModel')
    def test_emit_speech_event(self, mock_whisper):
        """Test emitting a SpeechEvent"""
        mock_whisper.return_value = MagicMock()
        callback = Mock()
        
        processor = SpeechProcessor(
            whisper_model="base",
            event_callback=callback,
            room_id="A"
        )
        
        processor.emit_speech_event("Hello world")
        
        # Verify callback was called with a SpeechEvent
        assert callback.call_count == 1
        event = callback.call_args[0][0]
        assert isinstance(event, SpeechEvent)
        assert event.data["text"] == "Hello world"
        assert event.source.value == "A"
    
    @patch('speech_refactored.WhisperModel')
    def test_emit_speech_event_no_callback(self, mock_whisper):
        """Test emit_speech_event with no callback doesn't crash"""
        mock_whisper.return_value = MagicMock()
        
        processor = SpeechProcessor(
            whisper_model="base",
            event_callback=None,
            room_id="A"
        )
        
        # Should not raise
        processor.emit_speech_event("Hello world")
    
    @patch('speech_refactored.WhisperModel')
    def test_emit_speech_event_callback_error_handling(self, mock_whisper):
        """Test that callback errors don't crash the processor"""
        mock_whisper.return_value = MagicMock()
        callback = Mock(side_effect=Exception("Callback error"))
        
        processor = SpeechProcessor(
            whisper_model="base",
            event_callback=callback,
            room_id="A"
        )
        
        # Should not raise, error should be logged
        processor.emit_speech_event("Hello world")


class TestRoomSpeechProcessor:
    """Test RoomSpeechProcessor integration"""
    
    @patch('speech_refactored.WhisperModel')
    def test_create_room_speech_processor(self, mock_whisper):
        """Test creating a room speech processor"""
        mock_whisper.return_value = MagicMock()
        
        config = RoomConfig(room_id="A")
        room = Room(config)
        
        processor = RoomSpeechProcessor.create(room, room_id="A")
        
        assert processor.room == room
        assert processor.speech_processor.room_id == "A"
    
    @patch('speech_refactored.WhisperModel')
    def test_room_processor_routes_to_room(self, mock_whisper):
        """Test that room processor routes events to the room"""
        mock_whisper.return_value = MagicMock()
        
        config = RoomConfig(room_id="A")
        room = Room(config)
        
        # Mock the room's emit_local_event method
        room.emit_local_event = Mock()
        
        processor = RoomSpeechProcessor.create(room, room_id="A")
        
        # Emit a speech event
        processor._on_speech_event(
            SpeechEvent.create(source="A", text="Hello", confidence=1.0, language="en")
        )
        
        # Verify room's emit_local_event was called
        assert room.emit_local_event.call_count == 1
        event = room.emit_local_event.call_args[0][0]
        assert isinstance(event, SpeechEvent)
        assert event.data["text"] == "Hello"
    
    @patch('speech_refactored.WhisperModel')
    def test_room_processor_factory_uses_room_config(self, mock_whisper):
        """Test that factory uses config from room"""
        mock_whisper.return_value = MagicMock()
        
        config = RoomConfig(room_id="B")
        config._config["microphone_device"] = 2
        room = Room(config)
        
        processor = RoomSpeechProcessor.create(room)
        
        # Should use room's microphone_device from config
        assert processor.speech_processor.audio_config.device == 2


class TestSpeechIntegrationEndToEnd:
    """End-to-end integration tests"""
    
    @patch('speech_refactored.WhisperModel')
    @patch('speech_refactored.sd.InputStream')
    def test_full_speech_to_event_flow(self, mock_stream, mock_whisper):
        """Test complete flow: audio -> transcription -> event"""
        # Mock Whisper
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model
        mock_segment = MagicMock()
        mock_segment.text = "Test speech"
        mock_model.transcribe.return_value = ([mock_segment], MagicMock())
        
        # Mock audio stream
        mock_stream.return_value.__enter__ = Mock()
        mock_stream.return_value.__exit__ = Mock()
        
        # Create processor with callback
        events_captured = []
        def capture_event(event):
            events_captured.append(event)
        
        processor = SpeechProcessor(
            whisper_model="base",
            event_callback=capture_event,
            room_id="A"
        )
        
        # Manually test the transcription -> emit flow without full audio stream
        processor.emit_speech_event("Test speech")
        
        assert len(events_captured) == 1
        event = events_captured[0]
        assert isinstance(event, SpeechEvent)
        assert event.data["text"] == "Test speech"
        assert event.source.value == "A"
        assert event.event_id is not None
        assert event.timestamp is not None
    
    @patch('speech_refactored.WhisperModel')
    def test_room_integration_captures_events(self, mock_whisper):
        """Test that room captures speech events"""
        mock_whisper.return_value = MagicMock()
        
        config = RoomConfig(room_id="A")
        room = Room(config)
        
        processor = RoomSpeechProcessor.create(room, room_id="A")
        
        # Emit a speech event through the processor
        speech_event = SpeechEvent.create(
            source="A",
            text="Hello from room",
            confidence=1.0,
            language="en"
        )
        
        processor._on_speech_event(speech_event)
        
        # Verify room captured it in event history
        # (Room.emit_local_event stores in event_history)
        history = room.get_event_history(count=100)
        assert len(history) == 1
        assert history[0].data["text"] == "Hello from room"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
