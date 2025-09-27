import asyncio
import websockets
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChatServer")

class ChatServer:
    def __init__(self):
        self.connected_clients = set()
    
    async def register(self, websocket):
        """Регистрация нового клиента"""
        self.connected_clients.add(websocket)
        logger.info(f"Новый клиент подключен. Всего клиентов: {len(self.connected_clients)}")
        
        # Уведомляем всех о новом пользователе
        join_message = {
            "type": "system",
            "user": "System",
            "text": "Новый пользователь присоединился к чату",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "clients_count": len(self.connected_clients)
        }
        await self.broadcast(join_message)
    
    async def unregister(self, websocket):
        """Удаление клиента"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
            logger.info(f"Клиент отключен. Осталось клиентов: {len(self.connected_clients)}")
            
            # Уведомляем всех об уходе пользователя
            leave_message = {
                "type": "system",
                "user": "System",
                "text": "Пользователь покинул чат",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "clients_count": len(self.connected_clients)
            }
            await self.broadcast(leave_message)
    
    async def broadcast(self, message):
        """Рассылка сообщения всем подключенным клиентам"""
        if self.connected_clients:
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.connected_clients],
                return_exceptions=True
            )
    
    async def handle_message(self, websocket, message_data):
        """Обработка входящего сообщения"""
        try:
            message = json.loads(message_data)
            message["timestamp"] = datetime.now().strftime("%H:%M:%S")
            
            logger.info(f"Сообщение от {message.get('user', 'Unknown')}: {message.get('text', '')}")
            
            # Рассылаем сообщение всем клиентам
            await self.broadcast(message)
            
        except json.JSONDecodeError:
            error_message = {
                "type": "error",
                "text": "Ошибка формата сообщения",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            await websocket.send(json.dumps(error_message))
    
    async def handle_client(self, websocket, path):
        """Обработка подключения клиента"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def start_server(self, host='localhost', port=8765):
        """Запуск WebSocket сервера"""
        logger.info(f"Запуск WebSocket чат-сервера на {host}:{port}")
        async with websockets.serve(self.handle_client, host, port):
            await asyncio.Future()  # Бесконечное ожидание

if __name__ == "__main__":
    server = ChatServer()
    asyncio.run(server.start_server())