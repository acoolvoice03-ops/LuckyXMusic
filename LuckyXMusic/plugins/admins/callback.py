import asyncio

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from LuckyXMusic import YouTube, app
from LuckyXMusic.core.call import Lucky as Call
from LuckyXMusic.misc import SUDOERS, db

from LuckyXMusic.utils.database import (
    get_active_chats,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_music_playing,
    is_nonadmin_chat,
    music_off,
    music_on,
    set_loop,
)

from LuckyXMusic.utils.decorators.language import languageCB
from LuckyXMusic.utils.formatters import seconds_to_min
from LuckyXMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from LuckyXMusic.utils.stream.autoclear import auto_clean
from LuckyXMusic.utils.thumbnails import get_thumb

from config import (
    BANNED_USERS,
    SUPPORT_CHAT,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
)

from strings import get_string

checker = {}
upvoters = {}

# ================= CALLBACK HANDLER ================= #

@app.on_callback_query(filters.regex("^ADMIN") & ~BANNED_USERS)
@languageCB
async def admin_callback(client, query, _):
    data = query.data.strip()
    _, payload = data.split(None, 1)
    command, chat = payload.split("|")

    counter = None
    if "_" in chat:
        chat, counter = chat.split("_")

    chat_id = int(chat)

    if not await is_active_chat(chat_id):
        return await query.answer(_["general_5"], show_alert=True)

    mention = query.from_user.mention

    # ================= ADMIN CHECK ================= #
    if command not in ["UpVote"]:
        if not await is_nonadmin_chat(query.message.chat.id):
            if query.from_user.id not in SUDOERS:
                admins = adminlist.get(query.message.chat.id, [])
                if query.from_user.id not in admins:
                    return await query.answer(_["admin_14"], show_alert=True)

    # ================= PLAYER CONTROLS ================= #

    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await query.answer(_["admin_1"], show_alert=True)
        await music_off(chat_id)
        await Call.pause_stream(chat_id)
        await query.message.reply_text(
            _["admin_2"].format(mention),
            reply_markup=close_markup(_),
        )

    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await query.answer(_["admin_3"], show_alert=True)
        await music_on(chat_id)
        await Call.resume_stream(chat_id)
        await query.message.reply_text(
            _["admin_4"].format(mention),
            reply_markup=close_markup(_),
        )

    elif command in ["Stop", "End"]:
        await Call.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await query.message.reply_text(
            _["admin_5"].format(mention),
            reply_markup=close_markup(_),
        )
        await query.message.delete()

    elif command in ["Skip", "Replay"]:
        queue = db.get(chat_id)
        if not queue:
            return await query.answer(_["admin_6"], show_alert=True)

        if command == "Skip":
            popped = queue.pop(0)
            await auto_clean(popped)
            if not queue:
                await Call.stop_stream(chat_id)
                return

        track = queue[0]
        file = track["file"]
        videoid = track["vidid"]
        title = track["title"]
        duration = track["dur"]
        user = track["by"]
        streamtype = track["streamtype"]
        video = True if streamtype == "video" else None

        image = None
        if videoid not in ["telegram", "soundcloud"]:
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                pass

        await Call.skip_stream(chat_id, file, video=video, image=image)

        buttons = stream_markup(_, chat_id)
        await query.message.reply_photo(
            photo=image or STREAM_IMG_URL,
            caption=_["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:25],
                duration,
                user,
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )

        await query.edit_message_text(
            f"➻ Stream updated by {mention}",
            reply_markup=close_markup(_),
        )

    await query.answer()

# ================= MARKUP TIMER ================= #

async def markup_timer():
    while True:
        await asyncio.sleep(7)
        active = await get_active_chats()
        for chat_id in active:
            if not await is_music_playing(chat_id):
                continue

            playing = db.get(chat_id)
            if not playing:
                continue

            mystic = playing[0].get("mystic")
            if not mystic:
                continue

            try:
                lang = await get_lang(chat_id)
                _ = get_string(lang)
            except:
                _ = get_string("en")

            buttons = stream_markup_timer(
                _,
                chat_id,
                seconds_to_min(playing[0]["played"]),
                playing[0]["dur"],
            )
            try:
                await mystic.edit_reply_markup(
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            except:
                pass

asyncio.create_task(markup_timer())
