"""
Real-time Status Updates - WebSocket Communication Module
========================================================

Provides real-time updates for invoice generation jobs and dashboard data.
Uses WebSocket connections for instant status notifications.
"""

import json
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Set, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import websockets
    from websockets.server import WebSocketServerProtocol

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    websockets = None
    WebSocketServerProtocol = None
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ WebSockets not available - real-time updates will be limited")


class UpdateType(Enum):
    """Types of real-time updates."""

    JOB_STATUS = "job_status"
    DASHBOARD_DATA = "dashboard_data"
    SYSTEM_STATUS = "system_status"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class RealTimeUpdate:
    """Real-time update message structure."""

    update_type: UpdateType
    data: Dict
    timestamp: datetime
    client_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.update_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "client_id": self.client_id,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class WebSocketManager:
    """Manages WebSocket connections and real-time updates."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize WebSocket manager."""
        self.host = host
        self.port = port
        self.clients: Set = (
            set()
        )  # Use generic Set when WebSocketServerProtocol is None
        self.client_subscriptions: Dict = {}
        self.server = None
        self.is_running = False
        self.update_queue = None

        # Background tasks
        self.server_task = None
        self.broadcast_task = None

        # Initialize queue if asyncio is available
        try:
            self.update_queue = asyncio.Queue()
        except Exception:
            pass

    async def start_server(self):
        """Start the WebSocket server."""
        if not websockets:
            print("⚠️ WebSockets not available - real-time updates disabled")
            return

        try:
            self.server = await websockets.serve(
                self.handle_client, self.host, self.port
            )
            self.is_running = True

            # Start broadcast task
            self.broadcast_task = asyncio.create_task(self.broadcast_loop())

            print(f"🌐 WebSocket server started on ws://{self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Failed to start WebSocket server: {e}")

    async def stop_server(self):
        """Stop the WebSocket server."""
        self.is_running = False

        if self.broadcast_task:
            self.broadcast_task.cancel()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients], return_exceptions=True
            )

        print("🛑 WebSocket server stopped")

    async def handle_client(self, websocket, path: str):
        """Handle new client connection."""
        if not WEBSOCKETS_AVAILABLE or WebSocketServerProtocol is None:
            return

        self.clients.add(websocket)
        self.client_subscriptions[websocket] = set()

        try:
            client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        except Exception:
            client_info = "unknown"

        print(f"👤 New WebSocket client connected: {client_info}")

        try:
            # Send welcome message
            welcome_msg = RealTimeUpdate(
                update_type=UpdateType.NOTIFICATION,
                data={
                    "message": "Connected to real-time updates",
                    "server_time": datetime.now().isoformat(),
                },
                timestamp=datetime.now(),
            )
            await websocket.send(welcome_msg.to_json())

            # Handle incoming messages
            async for message in websocket:
                await self.handle_client_message(websocket, message)

        except Exception as e:
            if "ConnectionClosed" not in str(type(e)):
                print(f"❌ Error handling client {client_info}: {e}")
        finally:
            self.clients.discard(websocket)
            self.client_subscriptions.pop(websocket, None)

    async def handle_client_message(
        self, websocket, message: str
    ):
        """Handle message from client."""
        if not WEBSOCKETS_AVAILABLE:
            return
            
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                # Subscribe to specific update types
                update_types = data.get("types", [])
                for update_type_str in update_types:
                    try:
                        update_type = UpdateType(update_type_str)
                        self.client_subscriptions[websocket].add(update_type)
                    except ValueError:
                        print(f"⚠️ Invalid update type: {update_type_str}")

                # Send confirmation
                response = RealTimeUpdate(
                    update_type=UpdateType.NOTIFICATION,
                    data={
                        "message": f"Subscribed to {len(self.client_subscriptions[websocket])} update types",
                        "subscriptions": [
                            t.value for t in self.client_subscriptions[websocket]
                        ],
                    },
                    timestamp=datetime.now(),
                )
                await websocket.send(response.to_json())

            elif action == "unsubscribe":
                # Unsubscribe from update types
                update_types = data.get("types", [])
                for update_type_str in update_types:
                    try:
                        update_type = UpdateType(update_type_str)
                        self.client_subscriptions[websocket].discard(update_type)
                    except ValueError:
                        pass

            elif action == "ping":
                # Respond to ping
                pong = RealTimeUpdate(
                    update_type=UpdateType.NOTIFICATION,
                    data={"message": "pong", "server_time": datetime.now().isoformat()},
                    timestamp=datetime.now(),
                )
                await websocket.send(pong.to_json())

        except json.JSONDecodeError:
            error_msg = RealTimeUpdate(
                update_type=UpdateType.ERROR,
                data={"message": "Invalid JSON message"},
                timestamp=datetime.now(),
            )
            await websocket.send(error_msg.to_json())
        except Exception as e:
            error_msg = RealTimeUpdate(
                update_type=UpdateType.ERROR,
                data={"message": f"Error processing message: {str(e)}"},
                timestamp=datetime.now(),
            )
            await websocket.send(error_msg.to_json())

    async def broadcast_loop(self):
        """Background task to broadcast updates to clients."""
        while self.is_running:
            try:
                # Wait for updates with timeout
                update = await asyncio.wait_for(self.update_queue.get(), timeout=1.0)
                await self.broadcast_update(update)
            except asyncio.TimeoutError:
                # No updates, continue loop
                continue
            except Exception as e:
                print(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)

    async def broadcast_update(self, update: RealTimeUpdate):
        """Broadcast update to subscribed clients."""
        if not self.clients:
            return

        # Filter clients based on subscriptions
        target_clients = []
        for client in self.clients:
            subscriptions = self.client_subscriptions.get(client, set())
            if not subscriptions or update.update_type in subscriptions:
                target_clients.append(client)

        if target_clients:
            # Send to all target clients
            message = update.to_json()
            results = await asyncio.gather(
                *[self.send_to_client(client, message) for client in target_clients],
                return_exceptions=True,
            )

            # Count successful sends
            successful = sum(1 for result in results if result is True)
            print(
                f"📡 Broadcasted {update.update_type.value} to {successful}/{len(target_clients)} clients"
            )

    async def send_to_client(
        self, client, message: str
    ) -> bool:
        """Send message to specific client."""
        if not WEBSOCKETS_AVAILABLE:
            return False
            
        try:
            await client.send(message)
            return True
        except Exception as e:
            if "ConnectionClosed" in str(type(e)):
                # Client disconnected, remove from active clients
                self.clients.discard(client)
                self.client_subscriptions.pop(client, None)
            else:
                print(f"Error sending to client: {e}")
            return False

    def queue_update(self, update: RealTimeUpdate):
        """Queue an update for broadcasting."""
        if self.is_running and self.update_queue:
            try:
                # Use thread-safe method to add to queue
                asyncio.run_coroutine_threadsafe(
                    self.update_queue.put(update), asyncio.get_event_loop()
                )
            except Exception as e:
                print(f"Error queuing update: {e}")

    def get_client_count(self) -> int:
        """Get number of connected clients."""
        return len(self.clients)

    def get_subscription_stats(self) -> Dict:
        """Get subscription statistics."""
        stats = {}
        for update_type in UpdateType:
            count = sum(
                1
                for subscriptions in self.client_subscriptions.values()
                if update_type in subscriptions
            )
            stats[update_type.value] = count

        return {"total_clients": len(self.clients), "subscriptions": stats}


class RealTimeStatusUpdater:
    """Manages real-time status updates for the application."""

    def __init__(self, websocket_manager: WebSocketManager):
        """Initialize status updater."""
        self.websocket_manager = websocket_manager
        self.update_callbacks: Dict[UpdateType, List[Callable]] = {
            update_type: [] for update_type in UpdateType
        }

        # Periodic update tasks
        self.dashboard_update_interval = 30  # seconds
        self.system_status_interval = 60  # seconds

        self.dashboard_task = None
        self.system_status_task = None
        self.is_running = False

    def start_periodic_updates(self):
        """Start periodic update tasks."""
        if self.is_running:
            return

        self.is_running = True

        # Start background threads for periodic updates
        self.dashboard_task = threading.Thread(
            target=self._dashboard_update_loop, daemon=True
        )
        self.dashboard_task.start()

        self.system_status_task = threading.Thread(
            target=self._system_status_loop, daemon=True
        )
        self.system_status_task.start()

        print("🔄 Started periodic real-time updates")

    def stop_periodic_updates(self):
        """Stop periodic update tasks."""
        self.is_running = False
        print("🛑 Stopped periodic real-time updates")

    def add_update_callback(self, update_type: UpdateType, callback: Callable):
        """Add callback for specific update type."""
        self.update_callbacks[update_type].append(callback)

    def send_job_status_update(
        self,
        job_id: str,
        status: str,
        progress: float = None,
        result: Dict = None,
        error: str = None,
    ):
        """Send job status update."""
        update_data = {
            "job_id": job_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        if progress is not None:
            update_data["progress"] = progress
        if result is not None:
            update_data["result"] = result
        if error is not None:
            update_data["error"] = error

        update = RealTimeUpdate(
            update_type=UpdateType.JOB_STATUS,
            data=update_data,
            timestamp=datetime.now(),
        )

        self.websocket_manager.queue_update(update)
        self._trigger_callbacks(UpdateType.JOB_STATUS, update_data)

    def send_dashboard_update(self, dashboard_data: Dict):
        """Send dashboard data update."""
        update = RealTimeUpdate(
            update_type=UpdateType.DASHBOARD_DATA,
            data=dashboard_data,
            timestamp=datetime.now(),
        )

        self.websocket_manager.queue_update(update)
        self._trigger_callbacks(UpdateType.DASHBOARD_DATA, dashboard_data)

    def send_system_status_update(self, status_data: Dict):
        """Send system status update."""
        update = RealTimeUpdate(
            update_type=UpdateType.SYSTEM_STATUS,
            data=status_data,
            timestamp=datetime.now(),
        )

        self.websocket_manager.queue_update(update)
        self._trigger_callbacks(UpdateType.SYSTEM_STATUS, status_data)

    def send_notification(self, message: str, level: str = "info", data: Dict = None):
        """Send notification to clients."""
        notification_data = {
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
        }

        if data:
            notification_data.update(data)

        update = RealTimeUpdate(
            update_type=UpdateType.NOTIFICATION,
            data=notification_data,
            timestamp=datetime.now(),
        )

        self.websocket_manager.queue_update(update)
        self._trigger_callbacks(UpdateType.NOTIFICATION, notification_data)

    def _trigger_callbacks(self, update_type: UpdateType, data: Dict):
        """Trigger registered callbacks for update type."""
        for callback in self.update_callbacks[update_type]:
            try:
                callback(data)
            except Exception as e:
                print(f"Error in update callback: {e}")

    def _dashboard_update_loop(self):
        """Periodic dashboard update loop."""
        while self.is_running:
            try:
                # Get fresh dashboard data
                from service_manager import get_service_manager

                service_manager = get_service_manager()

                # Get statistics and status
                stats = service_manager.get_statistics()
                status = service_manager.get_service_status_cached()

                # Get queue stats if available
                try:
                    from components.invoice_queue import get_invoice_queue

                    queue = get_invoice_queue()
                    queue_stats = queue.get_queue_stats()
                except Exception:
                    queue_stats = {}

                dashboard_data = {
                    "statistics": stats,
                    "service_status": status,
                    "queue_stats": queue_stats,
                    "last_updated": datetime.now().isoformat(),
                }

                self.send_dashboard_update(dashboard_data)

            except Exception as e:
                print(f"Error in dashboard update loop: {e}")

            # Wait for next update
            time.sleep(self.dashboard_update_interval)

    def _system_status_loop(self):
        """Periodic system status update loop."""
        while self.is_running:
            try:
                from service_manager import get_service_manager

                service_manager = get_service_manager()

                # Get comprehensive system status
                status_data = {
                    "services": service_manager.get_service_status(),
                    "cache_stats": service_manager.get_cache_statistics(),
                    "websocket_stats": self.websocket_manager.get_subscription_stats(),
                    "timestamp": datetime.now().isoformat(),
                }

                self.send_system_status_update(status_data)

            except Exception as e:
                print(f"Error in system status loop: {e}")

            # Wait for next update
            time.sleep(self.system_status_interval)


# Global instances
_websocket_manager = None
_status_updater = None


def get_websocket_manager() -> WebSocketManager:
    """Get global WebSocket manager instance."""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager


def get_status_updater() -> RealTimeStatusUpdater:
    """Get global status updater instance."""
    global _status_updater
    if _status_updater is None:
        websocket_manager = get_websocket_manager()
        _status_updater = RealTimeStatusUpdater(websocket_manager)
    return _status_updater


async def start_realtime_services():
    """Start all real-time services."""
    websocket_manager = get_websocket_manager()
    status_updater = get_status_updater()

    await websocket_manager.start_server()
    status_updater.start_periodic_updates()

    print("🚀 Real-time services started")


async def stop_realtime_services():
    """Stop all real-time services."""
    global _websocket_manager, _status_updater

    if _status_updater:
        _status_updater.stop_periodic_updates()

    if _websocket_manager:
        await _websocket_manager.stop_server()

    _websocket_manager = None
    _status_updater = None

    print("🛑 Real-time services stopped")
 