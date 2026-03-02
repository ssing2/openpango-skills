#!/usr/bin/env python3
"""
message_bus.py - Core message routing for A2A Communication Protocol.

Implements a lightweight message bus using Unix domain sockets for local
agent communication. Supports both fire-and-forget and request-reply patterns.
"""
import argparse
import json
import os
import sys
import time
import uuid
import socket
import threading
import select
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timezone

# Default socket path
DEFAULT_SOCKET_PATH = "/tmp/a2a_message_bus.sock"

# Message types
MSG_TYPES = {
    "ping": "Health check",
    "pong": "Health check response",
    "discover": "Request agent capabilities",
    "discover_response": "Response with capabilities",
    "task_request": "Request task execution",
    "task_response": "Task execution result",
    "event": "Broadcast event",
    "ack": "Acknowledgment"
}


class MessageBus:
    """Message Bus for A2A communication using Unix domain sockets."""
    
    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.server_socket = None
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        self.pending_responses: Dict[str, Any] = {}
        self.response_events: Dict[str, threading.Event] = {}
        self.lock = threading.Lock()
        
    def start_server(self):
        """Start the message bus server."""
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
            
        self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server_socket.bind(self.socket_path)
        self.server_socket.listen(10)
        self.server_socket.setblocking(False)
        self.running = True
        
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()
        
        print(json.dumps({
            "status": "started",
            "socket_path": self.socket_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        
    def _accept_loop(self):
        """Accept incoming connections."""
        while self.running:
            try:
                readable, _, _ = select.select([self.server_socket], [], [], 1.0)
                if readable:
                    conn, _ = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self._handle_client, 
                        args=(conn,), 
                        daemon=True
                    )
                    client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}", file=sys.stderr)
                    
    def _handle_client(self, conn):
        """Handle a client connection."""
        try:
            while self.running:
                data = conn.recv(65536)
                if not data:
                    break
                    
                try:
                    message = json.loads(data.decode('utf-8'))
                    response = self._process_message(message)
                    
                    if response:
                        conn.send(json.dumps(response).encode('utf-8'))
                        
                except json.JSONDecodeError as e:
                    conn.send(json.dumps({
                        "error": "Invalid JSON",
                        "details": str(e)
                    }).encode('utf-8'))
                    
        except Exception as e:
            print(f"Client handler error: {e}", file=sys.stderr)
        finally:
            conn.close()
            
    def _process_message(self, message: Dict) -> Optional[Dict]:
        """Process an incoming message."""
        msg_type = message.get("type")
        correlation_id = message.get("correlation_id")
        
        if correlation_id and correlation_id in self.pending_responses:
            with self.lock:
                self.pending_responses[correlation_id] = message
                if correlation_id in self.response_events:
                    self.response_events[correlation_id].set()
            return None
            
        handler = self.handlers.get(msg_type)
        if handler:
            return handler(message)
            
        return {
            "type": "ack",
            "correlation_id": correlation_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    def register_handler(self, msg_type: str, handler: Callable):
        """Register a handler for a message type."""
        self.handlers[msg_type] = handler
        
    def send_message(self, message: Dict, expect_response: bool = False, 
                     timeout: float = 30.0) -> Optional[Dict]:
        """Send a message through the bus."""
        if not os.path.exists(self.socket_path):
            return {"error": "Message bus not running"}
            
        correlation_id = str(uuid.uuid4())
        message["correlation_id"] = correlation_id
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        if expect_response:
            with self.lock:
                self.pending_responses[correlation_id] = None
                self.response_events[correlation_id] = threading.Event()
                
        try:
            client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client_socket.connect(self.socket_path)
            client_socket.send(json.dumps(message).encode('utf-8'))
            
            if expect_response:
                event = self.response_events[correlation_id]
                if event.wait(timeout):
                    with self.lock:
                        response = self.pending_responses.pop(correlation_id, None)
                        self.response_events.pop(correlation_id, None)
                    return response
                else:
                    with self.lock:
                        self.pending_responses.pop(correlation_id, None)
                        self.response_events.pop(correlation_id, None)
                    return {"error": "Timeout waiting for response"}
            else:
                client_socket.settimeout(5.0)
                try:
                    ack = client_socket.recv(4096)
                    return json.loads(ack.decode('utf-8'))
                except socket.timeout:
                    return {"status": "sent", "ack": False}
                    
        except Exception as e:
            return {"error": str(e)}
        finally:
            client_socket.close()
            
    def stop(self):
        """Stop the message bus server."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        print(json.dumps({"status": "stopped"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A2A Message Bus")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    start_parser = subparsers.add_parser("start", help="Start message bus server")
    start_parser.add_argument("--socket", default=DEFAULT_SOCKET_PATH)
    
    send_parser = subparsers.add_parser("send", help="Send a message")
    send_parser.add_argument("--type", required=True, help="Message type")
    send_parser.add_argument("--to", help="Target agent")
    send_parser.add_argument("--payload", help="JSON payload")
    send_parser.add_argument("--wait", action="store_true", help="Wait for response")
    send_parser.add_argument("--timeout", type=float, default=30.0)
    
    args = parser.parse_args()
    
    if args.command == "start":
        bus = MessageBus(args.socket)
        bus.start_server()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            bus.stop()
    elif args.command == "send":
        bus = MessageBus()
        payload = json.loads(args.payload) if args.payload else {}
        message = {
            "type": args.type,
            "to": args.to,
            "payload": payload
        }
        result = bus.send_message(message, expect_response=args.wait, timeout=args.timeout)
        print(json.dumps(result, indent=2))
