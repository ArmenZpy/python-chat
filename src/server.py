# Модуль: src/server.py
# Назначение: Веб-сервер для чата через интернет.

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List

# Импортируем наш класс Message
from message import Message

app = FastAPI()


# ---- Класс для управления подключениями (ООП: Инкапсуляция) ----
class ConnectionManager:
    """Управляет активными WebSocket подключениями."""

    def __init__(self):
        # Список для хранения активных подключений
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Принимает новое подключение и добавляет его в список. Сложность: O(1)."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Удаляет подключение из списка. Сложность: O(n)."""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Рассылает сообщение всем активным подключениям. Сообщение — это словарь (JSON). Сложность: O(n)."""
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()

# --- HTML-страница для клиента (со звуком) ---
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Простой Чат</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 2em auto; }
            #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
            #messageForm { display: flex; }
            #messageInput { flex: 1; padding: 8px; }
            button { padding: 9px 15px; }
        </style>
    </head>
    <body>
        <h1>Чат</h1>
        <div id="messages"></div>
        <form id="messageForm">
            <input type="text" id="usernameInput" placeholder="Твоё имя" required>
            <input type="text" id="messageInput" placeholder="Сообщение..." required autocomplete="off"/>
            <button type="submit">Отправить</button>
        </form>
        <script>
            // Подключаем WebSocket
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            const messagesDiv = document.getElementById('messages');
            const form = document.getElementById('messageForm');
            const usernameInput = document.getElementById('usernameInput');
            
            let currentUsername = '';
            let audioCtx = null; // Глобальный аудио-контекст

            // Логи для отладки
            ws.onopen = function() { console.log("✅ WebSocket ПОДКЛЮЧЕН!"); };
            ws.onclose = function() { console.log("❌ WebSocket ОТКЛЮЧЕН!"); };
            ws.onerror = function(error) { console.log("⚠️ Ошибка WebSocket:", error); };

            // Функция инициализации звука (вызывается при первом клике/отправке)
            function initAudio() {
                if (!audioCtx) {
                    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                }
                if (audioCtx.state === 'suspended') {
                    audioCtx.resume();
                }
            }

            // Функция для приятного двухтонального сигнала
            function playBeep() {
                if (!audioCtx) return; // Если звук не разблокирован, молчим

                const masterGain = audioCtx.createGain();
                masterGain.gain.value = 0.3; // Громкость
                masterGain.connect(audioCtx.destination);

                // Тон 1 (ДИНЬ)
                const osc1 = audioCtx.createOscillator();
                const gain1 = audioCtx.createGain();
                osc1.type = 'triangle';
                osc1.frequency.value = 880;
                gain1.gain.setValueAtTime(0.5, audioCtx.currentTime);
                gain1.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.15);
                osc1.connect(gain1);
                gain1.connect(masterGain);
                osc1.start();
                osc1.stop(audioCtx.currentTime + 0.15);

                // Тон 2 (ДОН)
                const osc2 = audioCtx.createOscillator();
                const gain2 = audioCtx.createGain();
                osc2.type = 'triangle';
                osc2.frequency.value = 660;
                gain2.gain.setValueAtTime(0.5, audioCtx.currentTime + 0.15);
                gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
                osc2.connect(gain2);
                gain2.connect(masterGain);
                osc2.start(audioCtx.currentTime + 0.15);
                osc2.stop(audioCtx.currentTime + 0.35);
            }

            // Получение сообщения
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                const messageDiv = document.createElement('div');
                messageDiv.textContent = `[${data.time}] ${data.sender}: ${data.text}`;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;

                // Звук только для входящих
                if (data.sender !== currentUsername) {
                    playBeep();
                }
            };

            // Отправка сообщения
            form.onsubmit = function(event) {
                event.preventDefault();
                initAudio(); // Разблокируем звук при отправке!

                const username = usernameInput.value.trim();
                const text = document.getElementById('messageInput').value.trim();
                
                if (!username) {
                    alert('Введите имя');
                    return;
                }
                
                currentUsername = username;
                if (text) {
                    ws.send(JSON.stringify({ sender: username, text: text }));
                    document.getElementById('messageInput').value = '';
                }
            };
        </script>
    </body>
</html>
"""

# --- Эндпоинты сервера ---

@app.get("/")
async def get():
    """Отдаем HTML - страницу чата. Сложность O(1)."""
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Основной WebSocket - эндпоинт. Принимает сообщения"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = Message(sender=data["sender"], text=data["text"])
            
            await manager.broadcast({
                "sender": msg.sender,
                "text": msg.text,
                "time": msg.time
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)