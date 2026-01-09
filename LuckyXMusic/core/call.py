import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup

from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    TelegramServerError,
)
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import (
    HighQualityAudio,
    MediumQualityVideo,
)
from pytgcalls.types.stream import StreamAudioEnded

import config
from LuckyXMusic import LOGGER, YouTube, app
from LuckyXMusic.misc import db
from LuckyXMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    remove_active_chat,
    remove_active_video_chat,
    group_assistant,
    get_lang,
    get_loop,
    set_loop,
    is_autoend,
    music_on,
)
from LuckyXMusic.utils.exceptions import AssistantErr
from LuckyXMusic.utils.formatters import (
    check_duration,
    seconds_to_min,
    speed_converter,
)
from LuckyXMusic.utils.inline.play import stream_markup
from LuckyXMusic.utils.stream.autoclear import auto_clean
from LuckyXMusic.utils.thumbnails import get_thumb
from strings import get_string

autoend = {}
counter = {}


async def _clear_(chat_id: int):
    db[chat_id] = []
    await remove_active_chat(chat_id)
    await remove_active_video_chat(chat_id)


class Call:
    def __init__(self):
        self.userbots = []
        self.calls = []

        for i, string in enumerate(
            [
                config.STRING1,
                config.STRING2,
                config.STRING3,
                config.STRING4,
                config.STRING5,
            ],
            start=1,
        ):
            if not string:
                continue
            client = Client(
                name=f"LuckyXAss{i}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(string),
            )
            call = PyTgCalls(client, cache_duration=100)
            self.userbots.append(client)
            self.calls.append(call)

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls assistants...")
        for client, call in zip(self.userbots, self.calls):
            await client.start()
            await call.start()
        await self.decorators()

    async def decorators(self):
        for call in self.calls:

            @call.on_kicked()
            @call.on_left()
            @call.on_closed_voice_chat()
            async def chat_closed(_, chat_id: int):
                await self.stop_stream(chat_id)

            @call.on_stream_end()
            async def stream_end(client, update: Update):
                if isinstance(update, StreamAudioEnded):
                    await self.change_stream(client, update.chat_id)

    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause_stream(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume_stream(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await _clear_(chat_id)
        try:
            await assistant.leave_group_call(chat_id)
        except:
            pass

    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        stream = (
            AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
            if video
            else AudioPiped(link, audio_parameters=HighQualityAudio())
        )
        await assistant.change_stream(chat_id, stream)

    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)

        stream = (
            AudioVideoPiped(
                link,
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
            if video
            else AudioPiped(link, audio_parameters=HighQualityAudio())
        )

        try:
            await assistant.join_group_call(
                chat_id,
                stream,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except AlreadyJoinedError:
            raise AssistantErr(_["call_9"])
        except TelegramServerError:
            raise AssistantErr(_["call_10"])

        await add_active_chat(chat_id)
        await music_on(chat_id)

        if video:
            await add_active_video_chat(chat_id)

        if await is_autoend():
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

    async def change_stream(self, client, chat_id: int):
        queue = db.get(chat_id)
        if not queue:
            await _clear_(chat_id)
            return await client.leave_group_call(chat_id)

        loop = await get_loop(chat_id)
        if loop == 0:
            finished = queue.pop(0)
        else:
            await set_loop(chat_id, loop - 1)
            finished = queue[0]

        await auto_clean(finished)

        if not queue:
            await _clear_(chat_id)
            return await client.leave_group_call(chat_id)

        current = queue[0]
        video = current["streamtype"] == "video"

        stream = (
            AudioVideoPiped(
                current["file"],
                audio_parameters=HighQualityAudio(),
                video_parameters=MediumQualityVideo(),
            )
            if video
            else AudioPiped(
                current["file"],
                audio_parameters=HighQualityAudio(),
            )
        )

        await client.change_stream(chat_id, stream)

    async def ping(self):
        pings = [await call.ping for call in self.calls]
        return str(round(sum(pings) / len(pings), 3))


Lucky = Call()
