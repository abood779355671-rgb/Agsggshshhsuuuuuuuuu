# ==============================================================================
# blacklist.py - Group Blacklist Management (Owner & Sudo Only)
# ==============================================================================
# This plugin lets the bot owner / sudo users blacklist entire groups from
# using the bot. A blacklisted group is blocked from issuing any command to
# the bot and the bot will automatically leave it if it's already a member
# (handled centrally in UltraMusic.core.lang.Language.language(), which
# checks `chat.id in db.blacklisted` on every incoming command).
#
# Commands:
# - /blacklist [chat_id]   - Blacklist a group (defaults to current group)
# - /whitelist [chat_id]   - Remove a group from the blacklist
# - /blacklisted           - List all currently blacklisted groups
#
# Only the bot owner and sudo users (app.sudo_filter) can use these commands.
# ==============================================================================

from pyrogram import types

from UltraMusic import app, db, lang
from UltraMusic.helpers import phrase_command


def _resolve_target_chat_id(m: types.Message) -> int | None:
    """
    Resolve the target chat_id for /blacklist and /whitelist.

    Priority:
    1. An explicit chat_id passed as the command argument.
    2. The current chat, if the command was used inside a group
       (group/supergroup/channel chat IDs are always negative).
    Returns None if no chat_id could be resolved.
    """
    if len(m.command) > 1:
        try:
            return int(m.command[1])
        except ValueError:
            return None

    if m.chat and m.chat.id < 0:
        return m.chat.id

    return None


@app.on_message(phrase_command(["حظر بوت"]) & app.sudo_filter)
@lang.language()
async def _blacklist_chat(_, m: types.Message):
    """Blacklist a group from using the bot."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = _resolve_target_chat_id(m)
    if chat_id is None:
        return await m.reply_text(
            "<blockquote><b>ᴜꜱᴀɢᴇ:</b>\n"
            "<code>/blacklist [chat_id]</code>\n"
            "ᴏʀ ʀᴜɴ ɪɴꜱɪᴅᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʟᴀᴄᴋʟɪꜱᴛ</blockquote>"
        )

    if chat_id > 0:
        return await m.reply_text(m.lang["bl_invalid"])

    blacklisted = await db.get_blacklisted(chat=True)
    if chat_id in blacklisted:
        return await m.reply_text(m.lang["bl_already"])

    try:
        chat = await app.get_chat(chat_id)
        chat_title = chat.title
    except Exception:
        chat_title = f"Chat {chat_id}"

    await db.add_blacklist(chat_id)

    await m.reply_text(
        f"<blockquote><u><b>🚫 ɢʀᴏᴜᴘ ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ</b></u>\n\n"
        f"<b>ɢʀᴏᴜᴘ:</b> {chat_title}\n"
        f"<b>ɪᴅ:</b> <code>{chat_id}</code></blockquote>"
    )

    # If the bot is currently a member of that group, leave it immediately.
    try:
        await app.leave_chat(chat_id)
    except Exception:
        pass


@app.on_message(phrase_command(["الغاء حظر بوت"]) & app.sudo_filter)
@lang.language()
async def _whitelist_chat(_, m: types.Message):
    """Remove a group from the blacklist."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass

    chat_id = _resolve_target_chat_id(m)
    if chat_id is None:
        return await m.reply_text(
            "<blockquote><b>ᴜꜱᴀɢᴇ:</b>\n"
            "<code>/whitelist [chat_id]</code>\n"
            "ᴏʀ ʀᴜɴ ɪɴꜱɪᴅᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴡʜɪᴛᴇʟɪꜱᴛ</blockquote>"
        )

    if chat_id > 0:
        return await m.reply_text(m.lang["bl_invalid"])

    blacklisted = await db.get_blacklisted(chat=True)
    if chat_id not in blacklisted:
        return await m.reply_text(m.lang["bl_not"])

    await db.del_blacklist(chat_id)

    try:
        chat = await app.get_chat(chat_id)
        chat_title = chat.title
    except Exception:
        chat_title = f"Chat {chat_id}"

    await m.reply_text(
        f"<blockquote><u><b>✅ ɢʀᴏᴜᴘ ᴡʜɪᴛᴇʟɪꜱᴛᴇᴅ</b></u>\n\n"
        f"<b>ɢʀᴏᴜᴘ:</b> {chat_title}\n"
        f"<b>ɪᴅ:</b> <code>{chat_id}</code></blockquote>"
    )


@app.on_message(phrase_command(["قائمة حظر البوت"]) & app.sudo_filter)
@lang.language()
async def _blacklisted_groups(_, m: types.Message):
    """Show all groups currently blacklisted from using the bot."""
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass

    sent = await m.reply_text(m.lang["bl_groups_fetching"])

    blacklisted = await db.get_blacklisted(chat=True)
    # Only negative IDs are groups/channels.
    groups = [chat_id for chat_id in blacklisted if chat_id < 0]

    if not groups:
        return await sent.edit_text(m.lang["bl_groups_empty"])

    text = "<u><b>🚫 ʙʟᴀᴄᴋʟɪꜱᴛᴇᴅ ɢʀᴏᴜᴘꜱ:</b></u>\n<blockquote>"

    for chat_id in groups:
        try:
            chat = await app.get_chat(chat_id)
            text += f"\n- {chat.title} (<code>{chat_id}</code>)"
        except Exception:
            text += f"\n- Unknown Group (<code>{chat_id}</code>)"

    text += "\n\n</blockquote>"
    await sent.edit_text(text)
