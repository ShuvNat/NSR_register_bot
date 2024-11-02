from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage, Redis

redis = Redis(host='localhost', port=6379, db=3)

storage = RedisStorage(
    redis=redis,
    key_builder=DefaultKeyBuilder(with_destiny=True)
    )


class StartState(StatesGroup):
    start = State()


class QuestionnaireState(StatesGroup):
    register = State()
    nickname = State()
    guests_number = State()
    fail_register = State()
    unregister = State()
    fail_unregister = State()
    save = State()


class GuestsState(StatesGroup):
    guests = State()
    change = State()
