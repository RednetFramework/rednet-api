import websockets
import asyncio
import json
from typing import Optional, Dict, Any, Callable
import threading
import queue
import logging

class WebSocketConnection:
    """Manages WebSocket connections with automatic reconnection and message queuing"""

    def __init__(self, url: str):
        self._url = url
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._connected = False
        self._should_reconnect = True
        self._reconnect_delay = 1  # Initial delay in seconds
        self._max_reconnect_delay = 30
        self._message_queue = queue.Queue()
        self._send_thread = None
        self._receive_thread = None
        self._headers: Dict[str, str] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self._event_loop = None

    def set_header(self, name: str, value: str):
        """Set a header for the WebSocket connection"""
        self._headers[name] = value

    def connect(self):
        """Initialize connection to WebSocket server"""
        self._should_reconnect = True
        self._start_event_loop()
        self._ensure_send_thread()
        self._ensure_receive_thread()

    def disconnect(self):
        """Disconnect from WebSocket server"""
        self._should_reconnect = False
        if self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._event_loop)

    def send_message(self, message: Any):
        """Queue a message to be sent
        Args:
            message: Can be string or dict (will be converted to JSON)
        """
        try:
            if isinstance(message, dict):
                message = json.dumps(message)
            self._message_queue.put(message)
        except Exception as e:
            logging.error(f"Error queueing message: {e}")

    def add_callback(self, event_type: str, callback: Callable):
        """Add a callback for a specific event type"""
        self._callbacks[event_type] = callback

    def _start_event_loop(self):
        """Start the asyncio event loop in a separate thread"""
        def run_event_loop():
            self._event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()

        thread = threading.Thread(target=run_event_loop, daemon=True)
        thread.start()

    def _ensure_send_thread(self):
        """Ensure the send thread is running"""
        if not self._send_thread or not self._send_thread.is_alive():
            self._send_thread = threading.Thread(
                target=self._message_sender,
                daemon=True
            )
            self._send_thread.start()

    def _ensure_receive_thread(self):
        """Ensure the receive thread is running"""
        if not self._receive_thread or not self._receive_thread.is_alive():
            self._receive_thread = threading.Thread(
                target=self._message_receiver,
                daemon=True
            )
            self._receive_thread.start()

    async def _connect(self):
        """Establish WebSocket connection"""
        try:
            extra_headers = [(k, v) for k, v in self._headers.items()]
            self._ws = await websockets.connect(
                self._url,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=20
            )
            self._connected = True
            logging.info("WebSocket connected")
            return True
        except Exception as e:
            logging.error(f"WebSocket connection error: {e}")
            return False

    def _message_sender(self):
        """Background thread for sending messages"""
        while self._should_reconnect or not self._message_queue.empty():
            try:
                message = self._message_queue.get(timeout=1.0)
                if self._ws and self._connected:
                    future = asyncio.run_coroutine_threadsafe(
                        self._ws.send(message),
                        self._event_loop
                    )
                    future.result()  # Wait for the send to complete
                self._message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error in message sender: {e}")
                # Put the message back in the queue if send failed
                try:
                    self._message_queue.put(message)
                except:
                    pass

    def _message_receiver(self):
        """Background thread for receiving messages"""
        while self._should_reconnect:
            try:
                if not self._connected:
                    future = asyncio.run_coroutine_threadsafe(
                        self._connect(),
                        self._event_loop
                    )
                    if not future.result():
                        # Connection failed, wait before retry
                        delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                        threading.Event().wait(delay)
                        continue

                # Start receiving messages
                while self._connected and self._ws:
                    try:
                        future = asyncio.run_coroutine_threadsafe(
                            self._ws.recv(),
                            self._event_loop
                        )
                        message = future.result()
                        self._handle_message(message)
                    except Exception as e:
                        logging.error(f"Error receiving message: {e}")
                        self._connected = False
                        break

            except Exception as e:
                logging.error(f"Error in message receiver: {e}")
                self._connected = False

    def _handle_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            event_type = data.get("type")
            if event_type and event_type in self._callbacks:
                self._callbacks[event_type](data)
        except Exception as e:
            logging.error(f"Error handling message: {e}")

    def __del__(self):
        """Cleanup when object is destroyed"""
        self.disconnect()
        if self._event_loop:
            self._event_loop.stop()