from aiogram.types import CallbackQuery, FSInputFile, User
from aiogram_dialog import Dialog, DialogManager, Window, ShowMode, StartMode
from aiogram_dialog.widgets.kbd import Button, Column, Start
from aiogram_dialog.widgets.text import Case, Const, Format
from pandas import DataFrame, ExcelWriter
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from .guests_dialog import guests

from db.requests import (
    count_registered, get_is_registered, get_nickname, guest_list
)
from .filters import is_admin
from fsm.fsm_dialogs import (
    GuestsState, StartState, QuestionnaireState
    )

FILEPATH = Path(__file__).resolve().parent.parent


async def start_getter(
        dialog_manager: DialogManager,
        event_from_user: User,
        session: AsyncSession,
        **kwargs
):
    nickname: str = await get_nickname(
        session, event_from_user.id
    )
    is_registered: str = await get_is_registered(
        session, event_from_user.id
    )
    if nickname:
        username = nickname
    else:
        username = event_from_user.first_name or 'Stranger'
    count = await count_registered(session)
    print(guests.max)
    print(count)
    if is_registered == 0:
        registered = False
        unregistered = True
        text = 1
    else:
        registered = True
        unregistered = False
        text = 2
    if count >= guests.max:
        text = 3
        unregistered = False
    getter_data = {'username': username,
                   'text': text,
                   'registered': registered,
                   'unregistered': unregistered,
                   'user_id': event_from_user.id}
    return getter_data


async def get_registrated(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    session = dialog_manager.middleware_data.get('session')
    count = await count_registered(session)
    await callback.message.answer(
            text=f'Сейчас зарегистрировано участников: {count}'
        )
    await callback.answer()
    await dialog_manager.start(
        StartState.start,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def get_guest_list(
        callback: CallbackQuery,
        button: Button,
        dialog_manager: DialogManager,
):
    session = dialog_manager.middleware_data.get('session')
    list = await guest_list(session)
    filename = ('Список_гостей.xlsx')
    filepath = FILEPATH / f'files/{filename}'
    df = DataFrame(list, columns=[
        'Имя',
        'Количество гостей',
        ])
    df.to_excel(filepath, index=False)
    with ExcelWriter(
            filepath, engine='openpyxl', mode='a'
            ) as writer:
        worksheet = writer.sheets['Sheet1']
        worksheet.title = 'Лист1'

        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[
                column_cells[0].column_letter].width = length + 2
    await callback.message.answer_document(
                FSInputFile(filepath, filename=filename)
            )
    filepath.unlink()
    await dialog_manager.start(
        StartState.start,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


start_dialog = Dialog(
    Window(
        Format('<b>Приветствую, {username}!</b>\n'),
        Const('✨Это бот для регистрации на День рождения '
              'Народного Славянского радио\n\n'
              '✨Вы можете зарегистрировать группу до 5 человек\n'),
        Case(
             texts={
                 1: Const('✨Чтобы сделать это, ответьте всего на 2 вопроса\n'),
                 2: Const('✨Вы можете изменить или отменить регистрацию'),
                 3: Const('✨Извините, в связи с большим количеством желающих,'
                          'регистрация временно приостановлена')
             },
             selector='text',
        ),
        Column(
            Start(Const('Зарегистрироваться'), id='questionnaire',
                  state=QuestionnaireState.nickname, when='unregistered'),
            Start(Const('Внести изменения'), id='change',
                  state=QuestionnaireState.nickname, when='registered'),
            Start(Const('Отменить регистрацию'), id='unreg',
                  state=QuestionnaireState.unregister, when='registered'),
            Button(Const('Сколько зарегистрировалось'), id='admin_stats',
                   on_click=get_registrated, when=is_admin),
            Button(Const('Скачать список гостей'), id='guest_list',
                   on_click=get_guest_list, when=is_admin),
            Start(Const('Максимальное число гостей'), id='guests',
                  state=GuestsState.guests, when=is_admin),
        ),
        getter=start_getter,
        state=StartState.start
    ),
)
