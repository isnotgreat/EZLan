from PyQt6.QtCore import QObject, pyqtSignal
import websockets
import json
import asyncio
import logging

class SignalingService(QObject):
    peer_offer = pyqtSignal(dict)
    peer_answer = pyqtSignal(dict)
    peer_ice_candidate = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("SignalingService")
        self.ws = None
        self.room_id = None
        
    async def connect(self, signaling_server="wss://your-signaling-server.com"):
        try:
            self.ws = await websockets.connect(signaling_server)
            asyncio.create_task(self._message_loop())
        except Exception as e:
            self.logger.error(f"Failed to connect to signaling server: {e}")
            raise

    async def create_room(self):
        await self._send_message({
            'type': 'create_room'
        })
        response = await self._receive_message()
        self.room_id = response['room_id']
        return self.room_id

    async def join_room(self, room_id):
        self.room_id = room_id
        await self._send_message({
            'type': 'join_room',
            'room_id': room_id
        })

    async def send_offer(self, offer):
        await self._send_message({
            'type': 'offer',
            'room_id': self.room_id,
            'offer': offer
        })

    async def send_answer(self, answer):
        await self._send_message({
            'type': 'answer',
            'room_id': self.room_id,
            'answer': answer
        })

    async def _message_loop(self):
        while True:
            try:
                message = await self._receive_message()
                self._handle_message(message)
            except Exception as e:
                self.logger.error(f"Message loop error: {e}")
                break 