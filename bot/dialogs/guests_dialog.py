from aiogram.enums import ContentType
from aiogram.types import Message, User
from aiogram_dialog import Dialog, DialogManager, Window, ShowMode, StartMode
from aiogram_dialog.widgets.kbd import Cancel, Next, Start
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Const, Format

from fsm.fsm_dialogs import GuestsState, StartState


class Guests:
    max = 80


guests = Guests()


async def guests_getter(
        dialog_manager: DialogManager,
        event_from_user: User,
        **kwargs
):
    return {'max_guests': guests.max}


async def guests_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager,
) -> None:
    if message.text.isdigit() and 1 <= int(message.text) <= 1000:
        guests.max = int(message.text)
        await dialog_manager.back()
    else:
        dialog_manager.show_mode = ShowMode.NO_UPDATE
        await message.answer(
            text='Пожалуйста, напишите только число больше 0'
                 )


guests_dialog = Dialog(
    Window(
        Format('Сейчас максимальноей число гостей: {max_guests}'),
        Next(Const('Изменить'), id='next'),
        Start(Const('На старт'), id='start', state=StartState.start,
              mode=StartMode.RESET_STACK),
        getter=guests_getter,
        state=GuestsState.guests,
    ),
    Window(
        Const('Введите новое максимальное число гостей'),
        Cancel(Const('Отмена'), id='cancel'),
        MessageInput(
            func=guests_handler,
            content_types=ContentType.TEXT,
        ),
        state=GuestsState.change,
    ),
)