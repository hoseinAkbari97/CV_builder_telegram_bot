import asyncio
import logging
from functools import partial
from html import escape
from pathlib import Path

from PIL import Image, ImageOps
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from cv_bot.config import load_settings
from cv_bot.i18n import text
from cv_bot.llm import CVEnhancer
from cv_bot.models import CV, parse_education, parse_experience
from cv_bot.pdf import build_cv_pdf
from cv_bot.storage import CVStore
from cv_bot.templates import TEMPLATES, build_template_thumbnail, template_name

(
    LANGUAGE,
    TEMPLATE,
    FULL_NAME,
    TITLE,
    EMAIL,
    PHONE,
    LOCATION,
    LINKEDIN,
    PHOTO,
    SUMMARY,
    SKILLS,
    EXPERIENCE,
    MORE_EXPERIENCE,
    EDUCATION,
    MORE_EDUCATION,
) = range(15)

LOGGER = logging.getLogger(__name__)
STORE_KEY = "cv_store"
PDF_DIRECTORY_KEY = "pdf_directory"
ENHANCER_KEY = "cv_enhancer"


def run() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    settings = load_settings()
    application = (
        ApplicationBuilder().token(settings.telegram_bot_token).post_init(_set_commands).build()
    )
    application.bot_data[STORE_KEY] = CVStore(settings.data_dir)
    application.bot_data[PDF_DIRECTORY_KEY] = settings.data_dir / "pdfs"
    application.bot_data[ENHANCER_KEY] = CVEnhancer.from_settings(settings)
    application.add_handler(_conversation_handler())
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("language", choose_language))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("templates", show_templates))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("pdf", send_pdf))
    application.add_handler(CommandHandler("delete", delete_cv))
    application.add_handler(CallbackQueryHandler(select_language, pattern=r"^language_(en|fa)$"))
    application.add_handler(CallbackQueryHandler(show_templates, pattern="^show_templates$"))
    application.add_handler(CallbackQueryHandler(change_template, pattern=r"^set_template_"))
    application.add_handler(CallbackQueryHandler(send_pdf, pattern="^download_pdf$"))
    application.add_error_handler(_handle_error)
    LOGGER.info("CV bot is running")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def _conversation_handler() -> ConversationHandler:
    def answer_handler(state: int) -> MessageHandler:
        return MessageHandler(filters.TEXT & ~filters.COMMAND, partial(_save_answer, state=state))

    return ConversationHandler(
        entry_points=[
            CommandHandler("create", create_cv),
            CallbackQueryHandler(create_cv, pattern="^create_cv$"),
        ],
        states={
            LANGUAGE: [
                CallbackQueryHandler(_create_language_choice, pattern=r"^create_language_(en|fa)$")
            ],
            TEMPLATE: [CallbackQueryHandler(_template_choice, pattern=r"^create_template_")],
            FULL_NAME: [answer_handler(FULL_NAME)],
            TITLE: [answer_handler(TITLE)],
            EMAIL: [answer_handler(EMAIL)],
            PHONE: [answer_handler(PHONE)],
            LOCATION: [answer_handler(LOCATION)],
            LINKEDIN: [answer_handler(LINKEDIN)],
            PHOTO: [
                MessageHandler(filters.PHOTO, _save_photo),
                answer_handler(PHOTO),
            ],
            SUMMARY: [answer_handler(SUMMARY)],
            SKILLS: [answer_handler(SKILLS)],
            EXPERIENCE: [answer_handler(EXPERIENCE)],
            MORE_EXPERIENCE: [
                CallbackQueryHandler(_experience_choice, pattern="^experience_(add|done)$")
            ],
            EDUCATION: [answer_handler(EDUCATION)],
            MORE_EDUCATION: [
                CallbackQueryHandler(_education_choice, pattern="^education_(add|done)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


async def _set_commands(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("create", "Create a CV | ساخت رزومه"),
            BotCommand("language", "Change language | تغییر زبان"),
            BotCommand("templates", "Choose template | انتخاب قالب"),
            BotCommand("preview", "Preview | پیش‌نمایش"),
            BotCommand("pdf", "Download PDF | دریافت PDF"),
            BotCommand("delete", "Delete data | حذف اطلاعات"),
            BotCommand("help", "Help | راهنما"),
            BotCommand("cancel", "Cancel | لغو"),
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await choose_language(update, context)


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_language_choice(update, prefix="language")


async def _send_language_choice(update: Update, prefix: str) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("English 🇬🇧", callback_data=f"{prefix}_en"),
                InlineKeyboardButton("فارسی 🇮🇷", callback_data=f"{prefix}_fa"),
            ]
        ]
    )
    await update.effective_message.reply_text(
        "Choose your language / زبان خود را انتخاب کنید:",
        reply_markup=keyboard,
    )


async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    language = update.callback_query.data.removeprefix("language_")
    context.user_data["language"] = language
    _store(context).save_language(update.effective_user.id, language)
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(_label(language, "create"), callback_data="create_cv")],
            [InlineKeyboardButton(_label(language, "templates"), callback_data="show_templates")],
        ]
    )
    await update.effective_message.reply_text(
        text(language, "welcome"),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        text(_language(update, context), "help"),
        parse_mode=ParseMode.HTML,
    )


async def create_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    _store(context).discard_draft_photo(update.effective_user.id)
    selected = context.user_data.get("language")
    if update.callback_query and selected in {"en", "fa"}:
        return await _begin_cv(update, context, selected)
    await _send_language_choice(update, prefix="create_language")
    return LANGUAGE


async def _create_language_choice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.callback_query.answer()
    language = update.callback_query.data.removeprefix("create_language_")
    context.user_data["language"] = language
    _store(context).save_language(update.effective_user.id, language)
    return await _begin_cv(update, context, language)


async def _begin_cv(
    update: Update, context: ContextTypes.DEFAULT_TYPE, language: str
) -> int:
    context.user_data["draft"] = CV(language=language)
    await _send_template_gallery(update, language, prefix="create_template")
    return TEMPLATE


async def _template_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    template = update.callback_query.data.removeprefix("create_template_")
    draft = context.user_data.get("draft")
    if not isinstance(draft, CV) or template not in TEMPLATES:
        await update.effective_message.reply_text(text(_language(update, context), "expired"))
        return ConversationHandler.END
    draft.template = template
    await update.effective_message.reply_text(
        text(draft.language, "full_name"),
        parse_mode=ParseMode.HTML,
    )
    return FULL_NAME


async def _save_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, state: int
) -> int:
    draft = context.user_data.get("draft")
    if not isinstance(draft, CV):
        await update.effective_message.reply_text(text(_language(update, context), "expired"))
        return ConversationHandler.END

    value = update.effective_message.text.strip()
    if not value:
        await update.effective_message.reply_text(text(draft.language, "text_required"))
        return state

    if state == FULL_NAME:
        draft.full_name = value
        return await _ask(update, text(draft.language, "title"), TITLE)
    if state == TITLE:
        draft.professional_title = value
        return await _ask(update, text(draft.language, "email"), EMAIL)
    if state == EMAIL:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            await update.effective_message.reply_text(text(draft.language, "invalid_email"))
            return EMAIL
        draft.email = value
        return await _ask(update, text(draft.language, "phone"), PHONE)
    if state == PHONE:
        draft.phone = "" if _is_skip(value) else value
        return await _ask(update, text(draft.language, "location"), LOCATION)
    if state == LOCATION:
        draft.location = "" if _is_skip(value) else value
        return await _ask(update, text(draft.language, "linkedin"), LINKEDIN)
    if state == LINKEDIN:
        draft.linkedin = "" if _is_skip(value) else value
        return await _ask(update, text(draft.language, "photo"), PHOTO)
    if state == PHOTO:
        if not _is_skip(value):
            await update.effective_message.reply_text(text(draft.language, "photo_required"))
            return PHOTO
        draft.photo_path = ""
        return await _ask(update, text(draft.language, "summary"), SUMMARY)
    if state == SUMMARY:
        draft.summary = value
        return await _ask(update, text(draft.language, "skills"), SKILLS)
    if state == SKILLS:
        draft.skills = _parse_skills(value)
        if not draft.skills:
            await update.effective_message.reply_text(text(draft.language, "skills_required"))
            return SKILLS
        return await _ask(update, text(draft.language, "experience"), EXPERIENCE)
    if state == EXPERIENCE:
        if _is_skip(value) and not draft.experiences:
            return await _ask_education(update, draft.language)
        try:
            draft.experiences.append(parse_experience(value))
        except ValueError:
            await update.effective_message.reply_text(text(draft.language, "experience"))
            return EXPERIENCE
        return await _ask_more_experience(update, draft.language)
    if state == EDUCATION:
        if _is_skip(value) and not draft.education:
            return await _finish_cv(update, context, draft)
        try:
            draft.education.append(parse_education(value))
        except ValueError:
            await update.effective_message.reply_text(text(draft.language, "education"))
            return EDUCATION
        return await _ask_more_education(update, draft.language)
    return state


async def _save_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    draft = context.user_data.get("draft")
    if not isinstance(draft, CV):
        await update.effective_message.reply_text(text(_language(update, context), "expired"))
        return ConversationHandler.END
    destination = _store(context).draft_photo_path(update.effective_user.id)
    telegram_file = await update.effective_message.photo[-1].get_file()
    temporary_path = destination.with_suffix(".download")
    await telegram_file.download_to_drive(custom_path=temporary_path)
    with Image.open(temporary_path) as image:
        normalized = ImageOps.exif_transpose(image).convert("RGB")
        normalized.thumbnail((1200, 1200))
        normalized.save(destination, "JPEG", quality=90, optimize=True)
    temporary_path.unlink(missing_ok=True)
    draft.photo_path = str(destination)
    return await _ask(update, text(draft.language, "summary"), SUMMARY)


async def _experience_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    language = _draft_language(context)
    if update.callback_query.data == "experience_add":
        await update.effective_message.reply_text(
            text(language, "experience_again"),
            parse_mode=ParseMode.HTML,
        )
        return EXPERIENCE
    return await _ask_education(update, language)


async def _education_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    language = _draft_language(context)
    if update.callback_query.data == "education_add":
        await update.effective_message.reply_text(
            text(language, "education_again"),
            parse_mode=ParseMode.HTML,
        )
        return EDUCATION
    return await _finish_cv(update, context, context.user_data.get("draft"))


async def _ask_more_experience(update: Update, language: str) -> int:
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(text(language, "add_another"), callback_data="experience_add"),
            InlineKeyboardButton(text(language, "done"), callback_data="experience_done"),
        ]]
    )
    await update.effective_message.reply_text(
        text(language, "experience_added"),
        reply_markup=keyboard,
    )
    return MORE_EXPERIENCE


async def _ask_education(update: Update, language: str) -> int:
    await update.effective_message.reply_text(
        text(language, "education"),
        parse_mode=ParseMode.HTML,
    )
    return EDUCATION


async def _ask_more_education(update: Update, language: str) -> int:
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(text(language, "add_another"), callback_data="education_add"),
            InlineKeyboardButton(text(language, "finish"), callback_data="education_done"),
        ]]
    )
    await update.effective_message.reply_text(
        text(language, "education_added"),
        reply_markup=keyboard,
    )
    return MORE_EDUCATION


async def _finish_cv(update: Update, context: ContextTypes.DEFAULT_TYPE, draft: object) -> int:
    if not isinstance(draft, CV):
        await update.effective_message.reply_text(text(_language(update, context), "expired"))
        return ConversationHandler.END
    await update.effective_message.reply_text(text(draft.language, "enhancing"))
    enhanced = await _enhancer(context).enhance(draft)
    enhanced.photo_path = _store(context).finalize_photo(
        update.effective_user.id,
        has_photo=bool(draft.photo_path),
    )
    _store(context).save(update.effective_user.id, enhanced)
    context.user_data.pop("draft", None)
    ready_key = "ready_static" if enhanced.content_source == "static" else "ready_ai"
    await update.effective_message.reply_text(
        text(enhanced.language, ready_key),
        parse_mode=ParseMode.HTML,
    )
    await _send_preview(update, enhanced)
    return ConversationHandler.END


async def show_templates(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer()
    await _send_template_gallery(update, _language(update, context), prefix="set_template")


async def change_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    template = update.callback_query.data.removeprefix("set_template_")
    cv = _store(context).load(update.effective_user.id)
    language = cv.language if cv.is_ready else _language(update, context)
    if template not in TEMPLATES:
        return
    if cv.is_ready:
        cv.template = template
        _store(context).save(update.effective_user.id, cv)
    await update.effective_message.reply_text(
        text(language, "template_saved", template=template_name(template, language)),
        parse_mode=ParseMode.HTML,
    )


async def _send_template_gallery(update: Update, language: str, prefix: str) -> None:
    await update.effective_message.reply_text(text(language, "choose_template"))
    for template in TEMPLATES:
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    f"✓ {template_name(template, language)}",
                    callback_data=f"{prefix}_{template}",
                )
            ]]
        )
        thumbnail = build_template_thumbnail(template)
        await update.effective_message.reply_photo(
            photo=InputFile(thumbnail, filename=thumbnail.name),
            caption=template_name(template, language),
            reply_markup=keyboard,
        )


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cv = _store(context).load(update.effective_user.id)
    if not cv.is_ready:
        await update.effective_message.reply_text(text(_language(update, context), "not_found"))
        return
    await _send_preview(update, cv)


async def _send_preview(update: Update, cv: CV) -> None:
    photo_path = Path(cv.photo_path)
    if cv.photo_path and photo_path.is_file():
        photo_bytes = await asyncio.to_thread(photo_path.read_bytes)
        await update.effective_message.reply_photo(
            photo=InputFile(photo_bytes, filename="profile.jpg")
        )
    experience = "\n".join(
        f"• <b>{escape(item.role)}</b> — {escape(item.company)} ({escape(item.dates)})"
        for item in cv.experiences
    )
    education = "\n".join(
        f"• <b>{escape(item.degree)}</b> — {escape(item.institution)}"
        for item in cv.education
    )
    sections = [
        f"<b>{escape(cv.full_name)}</b>",
        f"<i>{escape(cv.professional_title)}</i>",
        escape(" · ".join(value for value in [cv.email, cv.phone, cv.location] if value)),
        f"\n<b>{text(cv.language, 'profile')}</b>\n{escape(cv.summary)}",
        f"\n<b>{text(cv.language, 'skills_label')}</b>\n{escape(', '.join(cv.skills))}",
    ]
    if experience:
        sections.append(f"\n<b>{text(cv.language, 'experience_label')}</b>\n{experience}")
    if education:
        sections.append(f"\n<b>{text(cv.language, 'education_label')}</b>\n{education}")
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text(cv.language, "download"), callback_data="download_pdf")]]
    )
    await update.effective_message.reply_text(
        "\n".join(sections),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cv = _store(context).load(update.effective_user.id)
    if update.callback_query:
        await update.callback_query.answer(text(cv.language, "preparing"))
    if not cv.is_ready:
        await update.effective_message.reply_text(text(_language(update, context), "not_found"))
        return
    output_path = Path(context.application.bot_data[PDF_DIRECTORY_KEY]) / (
        f"cv-{update.effective_user.id}.pdf"
    )
    build_cv_pdf(cv, output_path)
    filename = f"{_safe_filename(cv.full_name)}-CV.pdf"
    with output_path.open("rb") as pdf_file:
        await update.effective_message.reply_document(
            document=InputFile(pdf_file, filename=filename),
            caption=text(cv.language, "pdf_caption"),
        )


async def delete_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    language = _language(update, context)
    _store(context).delete(update.effective_user.id)
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text(text(language, "deleted"))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    language = _draft_language(context)
    _store(context).discard_draft_photo(update.effective_user.id)
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text(text(language, "cancelled"))
    return ConversationHandler.END


async def _ask(update: Update, message: str, next_state: int) -> int:
    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)
    return next_state


def _store(context: ContextTypes.DEFAULT_TYPE) -> CVStore:
    return context.application.bot_data[STORE_KEY]


def _enhancer(context: ContextTypes.DEFAULT_TYPE) -> CVEnhancer:
    return context.application.bot_data[ENHANCER_KEY]


def _language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    selected = context.user_data.get("language")
    if selected in {"en", "fa"}:
        return selected
    preferred = _store(context).load_language(update.effective_user.id)
    if preferred:
        context.user_data["language"] = preferred
        return preferred
    saved = _store(context).load(update.effective_user.id)
    if saved.is_ready and saved.language in {"en", "fa"}:
        return saved.language
    telegram_language = (update.effective_user.language_code or "").casefold()
    return "fa" if telegram_language.startswith("fa") else "en"


def _draft_language(context: ContextTypes.DEFAULT_TYPE) -> str:
    draft = context.user_data.get("draft")
    return draft.language if isinstance(draft, CV) else "en"


def _parse_skills(value: str) -> list[str]:
    normalized = value.replace("،", ",")
    return [skill.strip() for skill in normalized.split(",") if skill.strip()]


def _is_skip(value: str) -> bool:
    return value.casefold() in {"skip", "/skip", "none", "n/a", "رد", "هیچ", "ندارم"}


def _safe_filename(value: str) -> str:
    safe = "".join(character for character in value if character.isalnum() or character in " -_")
    return safe.strip().replace(" ", "-") or "Professional"


def _label(language: str, key: str) -> str:
    labels = {
        "en": {"create": "Create my CV", "templates": "View templates"},
        "fa": {"create": "ساخت رزومه", "templates": "مشاهده قالب‌ها"},
    }
    return labels[language][key]


async def _handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled bot error", exc_info=context.error)
