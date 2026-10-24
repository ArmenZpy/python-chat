# МОДУЛЬ: src/message.py
# Назначение: форматирование сообщений

from datetime import datetime


class Message:
    """Одно текстовое сообщение.

    Принцип ООП: ИНКАПСУЛЯЦИЯ.
    Данные (sender, text, time) и метод (to_string) вместе.
    """

    def __init__(self, sender: str, text: str) -> None:
        """Конструктор сообщения.

        Аргументы:
            sender (str): Имя отправителя.
            text (str): Текст сообщения.

        Сложность: O(1).
        """
        self.sender = sender
        self.text = text
        self.time = datetime.now().strftime("%H:%M:%S")

    def to_string(self) -> str:
        """Возвращает красиво отформатированную строку.
        Пример: [15:30:00] Armen: Hello!
        Сложность: O(1).
        """
        return f"[{self.time}] {self.sender}: {self.text}"

    def __repr__(self) -> str:
        """Вызов при print(message)."""
        return self.to_string()