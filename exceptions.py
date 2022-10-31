class SendMessageError(Exception):
    """Ошибка отправки сообщения пользователю."""

    pass


class WrongApiAnswer(Exception):
    """Ошибка ответа от сервера."""

    pass


class InvalidNameHomeWork(Exception):
    """Статус домашнй работы не в списке статусов."""

    pass
