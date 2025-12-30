from datetime import datetime

from pyrogram import filters
from pyrogram.types import Message

from LuckyXMusic import Lucky
from LuckyXMusic.core.call import Lucky
from LuckyXMusic.utils import bot_sys_stats
from LuckyXMusic.utils.decorators.language import language
from LuckyXMusic.utils.inline import supp_markup
from config import BANNED_USERS, PING_IMG_URL


@Lucky.on_message(filters.command(["ping", "alive"]) & ~BANNED_USERS)
@language
async def ping_com(client, message: Message, _):
    start = datetime.now()
    response = await message.reply_photo(
        photo=PING_IMG_URL,
        caption=_["ping_1"].format(Lucky.mention),
    )
    pytgping = await Lucky.ping()
    UP, CPU, RAM, DISK = await bot_sys_stats()
    resp = (datetime.now() - start).microseconds / 1000
    await response.edit_text(
        _["ping_2"].format(resp, Lucky.mention, UP, RAM, CPU, DISK, pytgping),
        reply_markup=supp_markup(_),
    )
