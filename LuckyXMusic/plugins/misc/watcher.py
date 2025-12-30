from pyrogram import filters
from pyrogram.types import Message

from LuckyXMusic import Lucky
from LuckyXMusic.core.call import Lucky

welcome = 20
close = 30


@Lucky.on_message(filters.video_chat_started, group=welcome)
@Lucky.on_message(filters.video_chat_ended, group=close)
async def welcome(_, message: Message):
    await Lucky.stop_stream_force(message.chat.id)
