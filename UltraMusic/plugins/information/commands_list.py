# ==============================================================================
# commands_list.py - Command List ("الأوامر")
# ==============================================================================
# This plugin handles:
# - أوامر / الاوامر / commands - shows every Arabic command the bot accepts,
#   grouped by category, without the "/" prefix.
# ==============================================================================

from pyrogram import enums, types

from UltraMusic import app, lang
from UltraMusic.helpers import command


COMMANDS_TEXT = (
    "⚡️ <b>قائمة أوامر البوت</b>\n\n"

    "<blockquote expandable><b>🎵 التشغيل</b>\n"
    "تشغيل [اسم الأغنية أو رابط]\n"
    "تشغيل_فوري [اسم الأغنية أو رابط]\n"
    "فيديو [اسم الأغنية أو رابط]\n"
    "فيديو_فوري [اسم الأغنية أو رابط]\n"
    "تشغيل_قناة [اسم الأغنية أو رابط]\n"
    "تشغيل_قناة_فوري [اسم الأغنية أو رابط]\n"
    "فيديو_قناة [اسم الأغنية أو رابط]\n"
    "فيديو_قناة_فوري [اسم الأغنية أو رابط]\n"
    "بحث [اسم الأغنية]</blockquote>\n\n"

    "<blockquote expandable><b>🎛️ التحكم بالتشغيل</b>\n"
    "تجميد\n"
    "استمرار\n"
    "تخطي\n"
    "ايقاف\n"
    "كتم\n"
    "الغاء_الكتم\n"
    "عشوائي\n"
    "تكرار\n"
    "تقديم / ترجيع\n"
    "القائمة</blockquote>\n\n"

    "<blockquote expandable><b>⚙️ إعدادات المجموعة</b>\n"
    "تصريح\n"
    "الغاء_التصريح\n"
    "قائمة_التصريح\n"
    "تحديث_المشرفين\n"
    "ربط_القناة\n"
    "جودة_الصوت\n"
    "جودة_الفيديو\n"
    "بدء (مع settings/playmode)</blockquote>\n\n"

    "<blockquote expandable><b>🛠️ أوامر الإدارة</b>\n"
    "تنظيف — مسح الملفات المؤقتة غير المستخدمة\n"
    "اعضاء_الصوت — عرض أعضاء الـ VC وحالتهم</blockquote>\n\n"

    "<blockquote expandable><b>🔐 أوامر المطورين</b> <i>(سودو فقط ما لم يُذكر غير ذلك)</i>\n"
    "\n"
    "<b>• كلمة واحدة:</b>\n"
    "كلمات [اسم الأغنية] — جلب كلمات الأغنية (للجميع)\n"
    ".admin أو @admin — استدعاء جميع المشرفين (للجميع)\n"
    "\n"
    "<b>• حظر عالمي (عبارات):</b>\n"
    "حظر عالمي [معرّف] [السبب] — حظر المستخدم في كل المجموعات\n"
    "الغاء الحظر العالمي [معرّف] — رفع الحظر العالمي\n"
    "قائمة الحظر العالمي — عرض جميع المحظورين عالمياً\n"
    "\n"
    "<b>• حظر البوت (عبارات):</b>\n"
    "حظر بوت [معرّف المجموعة] — منع مجموعة من استخدام البوت\n"
    "الغاء حظر بوت [معرّف المجموعة] — رفع حظر المجموعة\n"
    "قائمة حظر البوت — عرض المجموعات المحظورة من البوت\n"
    "\n"
    "<b>• التحكم التلقائي (عبارات):</b>\n"
    "الانهاء الالي enable/disable — تشغيل/إيقاف الإنهاء التلقائي للبث\n"
    "المغادرة الالية enable/disable — تشغيل/إيقاف المغادرة التلقائية للـ VC</blockquote>"
)


@app.on_message(command(["الاوامر", "الأوامر", "اوامر"]) & ~app.bl_users)
@lang.language()
async def _commands_list(_, m: types.Message):
    """Show the full list of Arabic bot commands (no "/" prefix)."""
    # Auto-delete command message in group chats
    if m.chat.type != enums.ChatType.PRIVATE:
        try:
            await m.delete()
        except Exception:
            pass

    try:
        await m.reply_text(COMMANDS_TEXT, quote=True)
    except Exception:
        pass
