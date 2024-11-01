from aiogram.enums import ContentType
from aiogram.types import CallbackQuery, Message, User
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Button, Back, Cancel, Row, Start, SwitchTo
)
from aiogram_dialog.widgets.text import Const, Format

from db.requests import registrate_user, unregistrate_user
from fsm.fsm_dialogs import StartState, QuestionnaireState


async def username_getter(
        dialog_manager: DialogManager,
        event_from_user: User,
        **kwargs
):
    getter_data = {
        'username': event_from_user.first_name or 'Stranger',
        }
    return getter_data


async def first_name_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager):
    if message.text.isalpha():
        dialog_manager.dialog_data["first_name"] = message.text
        print(dialog_manager.middleware_data)
        await dialog_manager.next()
    else:
        dialog_manager.show_mode = ShowMode.NO_UPDATE
        await message.answer(
            text='Пожалуйста, напишите только одно слово.\n'
                 'Если нужно несколько, используйте нижнее подчеркивание'
            )


async def guests_handler(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager,
) -> None:
    if message.text.isdigit() and 1 <= int(message.text) <= 5:
        dialog_manager.dialog_data["guests_number"] = message.text
        session = dialog_manager.middleware_data.get('session')
        user = dialog_manager.event.from_user.id
        await registrate_user(
            session, user, *dialog_manager.dialog_data.values()
            )
        await message.answer(
                text='💫 Народное Славянское радио с радостью приглашает вас '
                     'на празднования своего дня рождения!\n\n'
                     '📨 В телеграмм чате "День Рождения НСР" вы найдете время '
                     'и место нашей встречи и сможете задать интересующие вас вопросы.\n\n'
                     'https://t.me/+6WHU_-Cx5Lw3MjMy \n\n'
                     '✨ Мы будем рады встрече с вами.\n'
                     '✨ Быть добру!\n'
            )
        await dialog_manager.switch_to(QuestionnaireState.save,
                                       show_mode=ShowMode.SEND)
    else:
        dialog_manager.show_mode = ShowMode.NO_UPDATE
        await message.answer(
            text='Пожалуйста, напишите только количество гостей от 1 до 5'
                 )


async def unregister(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager
) -> None:
    session = dialog_manager.middleware_data.get('session')
    user = dialog_manager.event.from_user.id
    await unregistrate_user(
        session, user,
        )
    await dialog_manager.switch_to(QuestionnaireState.fail_register)


questionnaire_dialog = Dialog(
    Window(
        Const('1. Напишите ваше имя или ник'),
        Cancel(Const('Отмена'), id='cancel'),
        MessageInput(
            func=first_name_handler,
            content_types=ContentType.TEXT,
        ),
        state=QuestionnaireState.nickname,
    ),
    Window(
        Const('2. Сколько гостей собирается прийти, включая вас?'),
        Const('Поставьте цифру от 1 до 5'),
        Row(
            Cancel(Const('Отмена'), id='cancel'),
            Back(Const('Назад'), id='back'),
        ),
        MessageInput(
            func=guests_handler,
            content_types=ContentType.TEXT,
        ),
        state=QuestionnaireState.guests_number,
    ),
    Window(
        Const('Вы действительно хотите отменить регистрацию?'),
        Row(
            Button(Const('Да'), id='yes', on_click=unregister),
            SwitchTo(Const('Нет'), id='no',
                     state=QuestionnaireState.fail_unregister),
            ),
        state=QuestionnaireState.unregister,
    ),
    Window(
        Const('Нам жаль, что вы передумали\n'
              'Если все-таки захотите приехать, вы всегда сможете '
              'зарегистрироваться в этом боте.'),
        Start(Const('На старт'), id='start', state=StartState.start,
              mode=StartMode.RESET_STACK),
        state=QuestionnaireState.fail_register,
    ),
    Window(
        Const('Рады, что вы остаетесь с нами\n'
              'Если все-таки решите отменить регистрацию, '
              'вернитесь на старт.'),
        Start(Const('На старт'), id='start', state=StartState.start,
              mode=StartMode.RESET_STACK),
        state=QuestionnaireState.fail_unregister,
    ),
    Window(
        Format('Благодарим за регистацию, {dialog_data[first_name]}!\n\n'
               '✨Если вы передумаете или не сможете прийти, '
               'пожалуйста, отмените или измените регистацию.\n'
               'Это можно сделать в стартовом меню бота.\n'),
        Start(Const('На старт'), id='start', state=StartState.start,
              mode=StartMode.RESET_STACK),
        state=QuestionnaireState.save,
        getter=username_getter
    ),
)
