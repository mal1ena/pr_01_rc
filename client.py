import asyncio
import websockets
import json
import threading
from datetime import datetime

class ChatClient:
    def __init__(self):
        self.websocket = None
        self.username = None
        self.is_connected = False
    
    async def connect(self, uri):
        """Подключение к WebSocket серверу"""
        try:
            self.websocket = await websockets.connect(uri)
            self.is_connected = True
            print("✅ Подключение к чату установлено!")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False
    
    async def receive_messages(self):
        """Прием сообщений от сервера"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                
                if data.get("type") == "system":
                    print(f"\n🔔 {data['text']} (Пользователей онлайн: {data.get('clients_count', 0)})")
                elif data.get("type") == "error":
                    print(f"\n❌ Ошибка: {data['text']}")
                else:
                    user = data.get("user", "Unknown")
                    text = data.get("text", "")
                    timestamp = data.get("timestamp", "")
                    print(f"\n[{timestamp}] {user}: {text}")
                
                print("Введите сообщение: ", end="", flush=True)
                
        except websockets.exceptions.ConnectionClosed:
            print("\n❌ Соединение с сервером разорвано")
            self.is_connected = False
    
    async def send_message(self, text):
        """Отправка сообщения на сервер"""
        if self.is_connected and self.websocket:
            message = {
                "type": "chat",
                "user": self.username,
                "text": text,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            await self.websocket.send(json.dumps(message))
    
    async def run_chat(self):
        """Основной цикл чата"""
        self.username = input("Введите ваше имя: ")
        
        if not await self.connect("ws://localhost:8765"):
            return
        
        print(f"\n🎉 Добро пожаловать в чат, {self.username}!")
        print("💡 Команды:")
        print("   - Наберите сообщение и нажмите Enter для отправки")
        print("   - Введите '/exit' для выхода")
        print("-" * 40)
        
        # Запускаем прием сообщений в фоне
        receive_task = asyncio.create_task(self.receive_messages())
        
        try:
            while self.is_connected:
                message_text = await asyncio.get_event_loop().run_in_executor(
                    None, input, "Введите сообщение: "
                )
                
                if message_text.lower() == '/exit':
                    break
                
                if message_text.strip():
                    await self.send_message(message_text)
                
        except KeyboardInterrupt:
            print("\nВыход из чата...")
        finally:
            self.is_connected = False
            receive_task.cancel()
            if self.websocket:
                await self.websocket.close()

async def main():
    client = ChatClient()
    await client.run_chat()

if __name__ == "__main__":
    asyncio.run(main())