from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from app.config import ALLOWED_CHAT_IDS
from app.services.dadata import dadata_find_by_inn
from app.services.scoring import score_company

router = Router()

def access_ok(message: Message) -> bool:
    return (not ALLOWED_CHAT_IDS) or (message.chat.id in ALLOWED_CHAT_IDS)

@router.message(Command("start"))
async def start(message: Message):
    if not access_ok(message):
        return await message.answer("Доступ запрещён.")
    await message.answer(
        "Команды:\n"
        "/company_check <ИНН>\n"
        "/help\n"
    )

@router.message(Command("help"))
async def help_cmd(message: Message):
    if not access_ok(message):
        return await message.answer("Доступ запрещён.")
    await message.answer("Пример: /company_check 7707083893")

@router.message(Command("company_check"))
async def company_check(message: Message):
    if not access_ok(message):
        return await message.answer("Доступ запрещён.")
    parts = message.text.split()
    if len(parts) < 2:
        return await message.answer("Формат: /company_check <ИНН>")
    inn = parts[1].strip()

    data = await dadata_find_by_inn(inn)
    if not data:
        return await message.answer("Не нашёл компанию по ИНН.")

    result = score_company(data)
    await message.answer(result)
