import asyncio
import json
from functools import partial
from unittest.mock import Mock, patch

import pytest

from langflow.events.event_manager import EventManager


@pytest.fixture
def client():
    pass


class TestEventManager:
    # Registering an event without specifying an event type should default to using send_event
    def test_register_event_without_event_type_defaults_to_send_event(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event")

        assert "test_event" in event_manager.events
        assert event_manager.events["test_event"] == event_manager.send_event

    # Registering an event with an empty string as the name
    def test_register_event_with_empty_string_name(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("")

        assert "" in event_manager.events
        assert event_manager.events[""] == event_manager.send_event

    # Registering an event with a specific event type should use a partial function of send_event
    def test_register_event_with_specific_event_type_uses_partial_function(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event", "specific_type")

        assert "test_event" in event_manager.events
        assert isinstance(event_manager.events["test_event"], partial)

    # Registering a custom event function should store it correctly in the events dictionary using a mock with the correct import
    def test_register_custom_event_function_stored_correctly_with_mock_with_mock_import(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        custom_event_function = Mock()
        event_manager.register_event_function("custom_event", custom_event_function)

        assert "custom_event" in event_manager.events
        assert event_manager.events["custom_event"] == custom_event_function

    # Accessing an unregistered event should return the noop function
    def test_accessing_unregistered_event_returns_noop_function(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)

        result = event_manager.unregistered_event

        assert result == event_manager.noop

    # Accessing a registered event should return the corresponding function
    def test_accessing_registered_event_returns_corresponding_function(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event")

        assert "test_event" in event_manager.events
        assert event_manager.events["test_event"] == event_manager.send_event

    # Sending an event should correctly format the event data as JSON and add it to the queue
    def test_send_event_correctly_formats_data_and_adds_to_queue(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event")

        event_type = "test_type"
        data = {"key": "value"}
        event_manager.send_event(event_type, data)

        event_id, str_data, timestamp = queue.get_nowait()
        decoded_data = json.loads(str_data.decode("utf-8"))

        assert decoded_data["event"] == event_type
        assert decoded_data["data"] == data

    # Accessing an event with a name that has not been registered
    def test_accessing_unregistered_event(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)

        result = event_manager.unknown_event

        assert result == event_manager.noop

    # Asserting the registration of a partial function for an event with an empty string as the event type
    def test_assert_partial_function_for_empty_string_event_type(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event", "")

        assert "test_event" in event_manager.events
        assert (
            isinstance(event_manager.events["test_event"], partial)
            and event_manager.events["test_event"].func == event_manager.send_event
            and event_manager.events["test_event"].args == ("",)
        )

    # Sending an event with an empty dictionary as data
    def test_sending_event_with_empty_data(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event")

        event_manager.send_event("test_event", {})

        # Check if the event was sent with the correct data
        assert not queue.empty()
        event_id, data, timestamp = queue.get_nowait()
        decoded_data = json.loads(data.decode("utf-8"))
        assert decoded_data["event"] == "test_event"
        assert decoded_data["data"] == {}

    # Registering an event with None as the event type
    def test_register_event_with_none_event_type_defaults_to_send_event(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event", None)

        assert "test_event" in event_manager.events
        assert event_manager.events["test_event"] == event_manager.send_event

    # Registering multiple events with the same name should overwrite the previous event
    def test_registering_multiple_events_overwrite_previous_fixed(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event", "type1")
        event_manager.register_event("test_event", "type2")

        assert "test_event" in event_manager.events
        assert event_manager.events["test_event"].args == ("type2",)

    # The queue should handle events with large data payloads
    def test_handle_large_data_payloads(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        event_manager.register_event("test_event")

        large_data = {"key": "value" * 1000}  # Creating a large data payload
        event_manager.send_event("test_event", large_data)

        event_id, str_data, timestamp = queue.get_nowait()
        decoded_data = json.loads(str_data.decode("utf-8"))

        assert decoded_data["event"] == "test_event"
        assert decoded_data["data"] == large_data

    # The noop function should handle any data without raising exceptions
    def test_noop_handles_any_data(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        data = {"key": "value"}

        event_manager.noop(data)
        # No exceptions should be raised

    # Implementing the Recommended Fix for handling JSON serialization error during event sending
    def mock_json_dumps_error(self, *args, **kwargs):
        raise ValueError("Mock JSON serialization error")

    def test_send_event_json_serialization_error_with_patch_fixed_replica(self):
        queue = asyncio.Queue()
        event_manager = EventManager(queue)
        with patch("json.dumps", side_effect=self.mock_json_dumps_error):
            try:
                event_manager.send_event("test_event", {"key": "value"})
            except Exception:
                pass
            assert queue.empty()  # Queue should be empty due to error handling
