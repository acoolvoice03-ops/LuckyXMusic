from pyrogram import filters
from pyrogram.types import Message

from LuckyXMusic import Lucky
from LuckyXMusic.core.call import Lucky
from LuckyXMusic.utils.database import set_loop
from LuckyXMusic.utils.decorators import AdminRightsCheck
from LuckyXMusic.utils.inline import close_markup
from config import BANNED_USERS


@Lucky.on_message(
    filters.command(["end", "stop", "cend", "cstop"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def stop_music(cli, message: Message, _, chat_id):
    if not len(message.command) == 1:
        return
    await Lucky.stop_stream(chat_id)
    await set_loop(chat_id, 0)
    await message.reply_text(
        _["admin_5"].format(message.from_user.mention), reply_markup=close_markup(_)
    )
