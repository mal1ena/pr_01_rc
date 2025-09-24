# pr_01_rc

Цель работы:
 освоить принципы удаленного вызова процедур (RPC) и их применение
в распределенных системах;
 изучить основы фреймворка gRPC и языка определения интерфейсов
Protocol Buffers (Protobuf);
 научиться определять сервисы и сообщения с помощью Protobuf;
 реализовать клиент-серверное приложение на языке Python с
использованием gRPC;
 получить практические навыки в генерации кода, реализации серверной
логики и клиентских вызовов для различных типов RPC.

## Шаг 1. Подготовка окружения(Ubuntu 20.04+)
•Обновляю пакеты и установливаю Python

•Создаю и активирую виртуальное
окружение

•Установливаю библиотеки Websocet

<img width="834" height="565" alt="image" src="https://github.com/user-attachments/assets/8fbb6596-7484-4930-851c-ae72b7286942" />


## Шаг 2. Реализация сервера

server.py
```
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
```
client.py
```
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
```

## Шаг 3. Запуск и проверка
Запускаем сервер с помощью кода 
```
source venv/bin/activate
python server.py
```
А также запускаем с двух терминалов двух клиентов с помощью кода
```

```
и вводим их имена. Теперь клиенты могут общаться между собой.
<img width="1252" height="599" alt="image" src="https://github.com/user-attachments/assets/f79c6481-6446-4ae2-87be-947e9306ab4f" />

## Шаг 4. Дополнительный сервер
Кроме этого, был создан html файл, который реализует онлайн-чат через браузер с помощью кода python3 -m http.server 8000

<img width="769" height="700" alt="image" src="https://github.com/user-attachments/assets/b4664bc6-f0a8-467c-82f5-2b5e283d2ce6" />

