def split_long_message(text: str, max_len: int = 4000) -> list:
    """Эта функция разрезает очень длинное письмо на маленькие кусочки,
    чтобы Telegram не ругался и всё пришло тебе нормально"""
    
    if len(text) <= max_len:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_len:
            parts.append(text)
            break
        
        # Ищем, где можно красиво разрезать (по новой строке)
        split_point = text.rfind('\n', 0, max_len)
        if split_point == -1:
            split_point = max_len
            
        parts.append(text[:split_point])
        text = text[split_point:].lstrip()
    
    return parts


def log_message(message: str):
    """Просто печатает сообщение, чтобы мы видели, что происходит"""
    print(f"[LOG] {message}")
