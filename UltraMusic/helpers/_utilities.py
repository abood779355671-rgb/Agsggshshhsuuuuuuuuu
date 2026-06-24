# ==============================================================================
# _utilities.py - General Utility Functions
# ==============================================================================
# This file contains various helper functions used throughout the bot:
# - Time formatting (ETA, duration)
# - File size formatting (bytes to KB/MB/GB)
# - User extraction from messages (mentions, replies, user IDs)
# - Duration conversion (mm:ss to seconds)
# - Message text extraction
#
# These utilities keep code DRY (Don't Repeat Yourself) across plugins.
# ==============================================================================

import re
from pyrogram import enums, errors, filters, types
from UltraMusic import app, config


# ==============================================================================
# Central command filter
# ==============================================================================
# Every command in the bot is registered through this single helper instead of
# calling `filters.command(...)` directly. It allows every command to be used:
#   - without any prefix   (e.g. "تشغيل اغنية")
#   - with a slash prefix  (e.g. "/تشغيل اغنية")
#   - with a bang prefix   (e.g. "!تشغيل اغنية")
#
# Keeping this in one place means we never have to repeat the prefixes list on
# every handler, and changing the accepted prefixes is a one-line edit here.
# ==============================================================================

# Accepted command prefixes. "" means "no prefix required".
COMMAND_PREFIXES = ["", "/", "!"]


def command(commands):
    """Return a pyrogram command filter that works with or without a prefix."""
    return filters.command(commands, prefixes=COMMAND_PREFIXES)


def phrase_command(phrases: list[str]):
    """Return a pyrogram filter that matches multi-word Arabic (or mixed) phrases.

    Unlike ``filters.command`` — which splits on the first space and only
    matches single-token commands — this filter handles phrases that contain
    internal spaces (e.g. "المغادرة الالية").

    Behaviour
    ---------
    * Accepted prefixes: the same ``COMMAND_PREFIXES`` list used by ``command``
      (currently ``["", "/", "!"]``).
    * Whitespace-insensitive: any run of whitespace between words is collapsed
      before comparison, so "المغادرة  الالية" still matches "المغادرة الالية".
    * Case-insensitive: Arabic letters are unaffected, but any Latin letters or
      digits in the phrase are compared in lowercase, making the filter future-
      proof for mixed-script phrases.
    * After a successful match the filter sets ``m.command`` to a list whose
      first element is the matched phrase (exactly as supplied in *phrases*) and
      whose subsequent elements are the remaining words from the message — i.e.
      the arguments.  This mirrors what ``filters.command`` produces so that all
      existing handlers that read ``m.command[1:]`` work without modification.

    Parameters
    ----------
    phrases:
        A list of phrase strings, each consisting of two or more words
        separated by a single space, e.g. ``["المغادرة الالية", "بدء التشغيل"]``.

    Example
    -------
    A handler registered with ``phrase_command(["المغادرة الالية"])`` will match:

        "المغادرة الالية تفعيل"
        "/المغادرة الالية تفعيل"
        "!المغادرة الالية تفعيل"

    and will set ``m.command = ["المغادرة الالية", "تفعيل"]`` in all three cases.
    """

    # Pre-compile one pattern per phrase for efficiency.
    # Pattern anatomy (for phrase "المغادرة الالية"):
    #
    #   ^[/!]?          – optional prefix (/ or !)
    #   المغادرة\s+الالية  – phrase words joined by \s+ (one-or-more whitespace)
    #   (?:\s+(.+))?    – optional trailing arguments captured in group 1
    #   \s*$            – trailing whitespace allowed
    #
    # Each phrase is normalised (strip + collapse internal spaces) so that the
    # caller doesn't have to worry about accidental double-spaces.

    # Normalise all phrases first, then sort longest-first so that a longer
    # phrase (e.g. "الأكثر تشغيلا عالميا") is always tried before a shorter
    # prefix phrase (e.g. "الأكثر تشغيلا") that would otherwise match first
    # and swallow the extra words as arguments.
    normalised_phrases = [" ".join(p.strip().split()) for p in phrases]
    normalised_phrases.sort(key=lambda p: len(p), reverse=True)

    compiled: list[tuple[str, re.Pattern]] = []
    for normalised in normalised_phrases:
        # Escape each word individually, then join with \s+ to allow any
        # amount of whitespace between words in the incoming message.
        words_escaped = r"\s+".join(re.escape(w) for w in normalised.split())
        pattern = re.compile(
            r"^[/!]?" + words_escaped + r"(?:\s+(.+))?\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        compiled.append((normalised, pattern))

    async def _filter(_, __, m: types.Message) -> bool:  # noqa: ANN001
        # Grab the relevant text from the message.
        text: str | None = m.text or m.caption
        if not text:
            return False

        # Collapse all internal whitespace runs to a single space and strip
        # leading/trailing whitespace before matching.
        normalised_text = " ".join(text.strip().split())

        for phrase, pattern in compiled:
            match = pattern.match(normalised_text)
            if match is None:
                continue

            # Build m.command exactly like filters.command does:
            #   index 0  → the matched phrase
            #   index 1+ → individual argument tokens
            args_raw: str | None = match.group(1)
            if args_raw:
                args = args_raw.split()
            else:
                args = []

            m.command = [phrase, *args]
            return True

        return False

    return filters.create(_filter)


# ==============================================================================
# Manual smoke-test
# ==============================================================================
# To verify phrase_command locally (no Telegram connection needed), run:
#
#   python - <<'EOF'
#   import asyncio, types as _t, re
#
#   # ── Minimal stubs so we can import without a running Pyrogram client ──────
#   class _FakeFilters:
#       @staticmethod
#       def create(fn): return fn
#   class _FakeMod:
#       filters = _FakeFilters()
#       types = _t  # not used in the filter itself
#   import sys, unittest.mock as mock
#   sys.modules.setdefault("pyrogram", mock.MagicMock())
#   sys.modules["pyrogram"].filters = _FakeFilters()
#   # ─────────────────────────────────────────────────────────────────────────
#
#   from UltraMusic.helpers._utilities import phrase_command
#
#   flt = phrase_command(["المغادرة الالية"])
#
#   class FakeMsg:
#       def __init__(self, txt):
#           self.text = txt; self.caption = None; self.command = None
#
#   async def run():
#       cases = [
#           "المغادرة الالية تفعيل",
#           "/المغادرة الالية تفعيل",
#           "!المغادرة الالية تفعيل",
#       ]
#       for txt in cases:
#           m = FakeMsg(txt)
#           matched = await flt(None, None, m)
#           assert matched, f"FAILED to match: {txt!r}"
#           assert m.command == ["المغادرة الالية", "تفعيل"], \
#               f"Wrong command for {txt!r}: {m.command}"
#           print(f"✓  {txt!r}  →  m.command = {m.command}")
#       print("\nAll tests passed.")
#
#   asyncio.run(run())
#   EOF
# ==============================================================================


class Utilities:
    def __init__(self):
        pass

    def format_eta(self, seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d} min"
        else:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            return f"{h}:{m:02d}:{s:02d} h"

    def format_size(self, bytes: int) -> str:
        if bytes >= 1024**3:
            return f"{bytes / 1024 ** 3:.2f} GB"
        elif bytes >= 1024**2:
            return f"{bytes / 1024 ** 2:.2f} MB"
        else:
            return f"{bytes / 1024:.2f} KB"

    def format_duration(self, seconds: int) -> str:
        """Format duration as HH:MM:SS or MM:SS depending on length."""
        if seconds >= 3600:  # 1 hour or more
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:  # Less than 1 hour
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"

    def to_seconds(self, time: str) -> int:
        parts = [int(p) for p in time.strip().split(":")]
        return sum(value * 60**i for i, value in enumerate(reversed(parts)))

    async def extract_user(self, msg: types.Message) -> types.User | None:
        if msg.reply_to_message:
            return msg.reply_to_message.from_user

        if msg.entities:
            for e in msg.entities:
                if e.type == enums.MessageEntityType.TEXT_MENTION:
                    return e.user

        if msg.text:
            try:
                if m := re.search(r"@(\w{5,32})", msg.text):
                    return await app.get_users(m.group(0))
                if m := re.search(r"\b\d{6,15}\b", msg.text):
                    return await app.get_users(int(m.group(0)))
            except:
                pass

        return None

    async def play_log(
        self,
        m: types.Message,
        title: str,
        duration: str,
    ) -> None:
        if m.chat.id == app.logger:
            return
        _text = m.lang["play_log"].format(
            app.name,
            m.chat.id,
            m.chat.title,
            m.from_user.id,
            m.from_user.mention,
            m.link,
            title,
            duration,
        )
        await app.send_message(chat_id=app.logger, text=_text)

    async def send_log(self, m: types.Message) -> None:
        """Log new user to logger group when they start the bot in private chat."""
        await app.send_message(
            chat_id=app.logger,
            text=m.lang["log_user"].format(
                m.from_user.id,
                f"@{m.from_user.username}",
                m.from_user.mention,
            ),
        )

    async def safe_text(
        self,
        message: types.Message,
        text: str,
        *,
        reply_markup=None,
        quote: bool | None = True,
    ) -> types.Message | None:
        """Send text but gracefully fallback to media-only chats."""
        if not message:
            return None
        try:
            return await message.reply_text(
                text=text,
                reply_markup=reply_markup,
                quote=quote,
            )
        except (errors.ChatSendPlainForbidden, errors.ChatWriteForbidden):
            fallback_photo = getattr(config, "START_IMG", None)
            if not fallback_photo:
                return None
            try:
                return await message.reply_photo(
                    photo=fallback_photo,
                    caption=text,
                    reply_markup=reply_markup,
                    quote=quote,
                )
            except errors.RPCError:
                return None
        except errors.RPCError:
            return None

    async def safe_edit(
        self,
        message: types.Message | None,
        text: str,
        *,
        reply_markup=None,
    ) -> bool:
        """Edit text or caption safely depending on message type."""
        if not message:
            return False
        try:
            if message.text is not None:
                await message.edit_text(text=text, reply_markup=reply_markup)
            else:
                await message.edit_caption(caption=text, reply_markup=reply_markup)
            return True
        except errors.RPCError:
            return False
