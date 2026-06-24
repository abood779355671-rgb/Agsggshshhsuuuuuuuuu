# ==============================================================================
# sudoers.py - Sudo User Management (Owner Only)
# ==============================================================================
# This plugin allows the bot owner to add/remove sudo users.
# Sudo users have elevated permissions and can use admin commands.
#
# Commands:
# - /addsudo <user> - Grant sudo permissions
# - /delsudo <user> - Revoke sudo permissions
# - /rmsudo <user> - Same as /delsudo
#
# Only the bot owner (defined in config) can manage sudo users.
# ==============================================================================

from pyrogram import types

from UltraMusic import app, db, lang
from UltraMusic.helpers import utils, command, phrase_command


@app.on_message(phrase_command(["اضافة مطور"]) & app.sudo_filter)
@lang.language()
async def _addsudo(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass

    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if user.id in app.sudoers:
        return await m.reply_text(m.lang["sudo_already"].format(user.mention))

    app.sudoers.add(user.id)
    app.sudo_filter.update([user.id])
    await db.add_sudo(user.id)
    await m.reply_text(m.lang["sudo_added"].format(user.mention))


@app.on_message(phrase_command(["حذف مطور"]) & app.sudo_filter)
@lang.language()
async def _delsudo(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass

    user = await utils.extract_user(m)
    if not user:
        return await m.reply_text(m.lang["user_not_found"])

    if user.id not in app.sudoers:
        return await m.reply_text(m.lang["sudo_not"].format(user.mention))

    app.sudoers.discard(user.id)
    app.sudo_filter.update([])  # Reset filter
    app.sudo_filter.update(app.sudoers)  # Rebuild with remaining users
    await db.del_sudo(user.id)
    await m.reply_text(m.lang["sudo_removed"].format(user.mention))


o_mention = None


@app.on_message(command(["المطورين"]) & app.sudo_filter)
@lang.language()
async def _listsudo(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    sent = await m.reply_text(m.lang["sudo_fetching"])

    # Always fetch fresh owner info with ID
    owner_user = await app.get_users(app.owner)
    o_mention = f"{owner_user.mention} ({app.owner})"
    
    txt = m.lang["sudo_owner"].format(o_mention)
    sudoers = await db.get_sudoers()
    
    if sudoers:
        sudo_list = ""
        for user_id in sudoers:
            try:
                user = await app.get_users(user_id)
                sudo_list += f"\n- {user.mention} ({user_id})"
            except:
                # Deleted account or inaccessible user
                sudo_list += f"\n- Deleted Account ({user_id})"
                continue
        
        if sudo_list:
            txt += f"<blockquote><u><b>ꜱᴜᴅᴏ ᴜꜱᴇʀꜱ:</b></u>{sudo_list}\n\n</blockquote>"

    await sent.edit_text(txt)
