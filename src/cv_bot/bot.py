import logging
from functools import partial
from html import escape
from pathlib import Path

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
from cv_bot.models import CV, parse_education, parse_experience
from cv_bot.pdf import build_cv_pdf
from cv_bot.storage import CVStore

(
    FULL_NAME,
    TITLE,
    EMAIL,
    PHONE,
    LOCATION,
    LINKEDIN,
    SUMMARY,
    SKILLS,
    EXPERIENCE,
    MORE_EXPERIENCE,
    EDUCATION,
    MORE_EDUCATION,
) = range(12)

LOGGER = logging.getLogger(__name__)
STORE_KEY = "cv_store"
PDF_DIRECTORY_KEY = "pdf_directory"


def run() -> None:
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    settings = load_settings()
    application = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .post_init(_set_commands)
        .build()
    )
    application.bot_data[STORE_KEY] = CVStore(settings.data_dir)
    application.bot_data[PDF_DIRECTORY_KEY] = settings.data_dir / "pdfs"
    application.add_handler(_conversation_handler())
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("preview", preview))
    application.add_handler(CommandHandler("pdf", send_pdf))
    application.add_handler(CommandHandler("delete", delete_cv))
    application.add_handler(CallbackQueryHandler(send_pdf, pattern="^download_pdf$"))
    application.add_error_handler(_handle_error)
    LOGGER.info("CV bot is running")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def _conversation_handler() -> ConversationHandler:
    def answer_handler(state: int) -> MessageHandler:
        return MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            partial(_save_answer, state=state),
        )

    return ConversationHandler(
        entry_points=[
            CommandHandler("create", create_cv),
            CallbackQueryHandler(create_cv, pattern="^create_cv$"),
        ],
        states={
            FULL_NAME: [answer_handler(FULL_NAME)],
            TITLE: [answer_handler(TITLE)],
            EMAIL: [answer_handler(EMAIL)],
            PHONE: [answer_handler(PHONE)],
            LOCATION: [answer_handler(LOCATION)],
            LINKEDIN: [answer_handler(LINKEDIN)],
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
            BotCommand("create", "Create or replace your CV"),
            BotCommand("preview", "Preview your saved CV"),
            BotCommand("pdf", "Download your CV as PDF"),
            BotCommand("delete", "Delete your saved CV"),
            BotCommand("help", "Show help"),
            BotCommand("cancel", "Cancel the current form"),
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Create my CV", callback_data="create_cv")]]
    )
    await update.effective_message.reply_text(
        "<b>Professional CV Builder</b>\n\n"
        "I’ll ask a few focused questions and turn your answers into a clean, "
        "recruiter-friendly PDF.\n\n"
        "Your completed CV is saved privately for future downloads.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "<b>Commands</b>\n"
        "/create — start a new CV\n"
        "/preview — review saved content\n"
        "/pdf — download the PDF\n"
        "/delete — erase saved CV data\n"
        "/cancel — stop the current form\n\n"
        "Tip: write achievements with results, numbers, and strong action verbs.",
        parse_mode=ParseMode.HTML,
    )


async def create_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    context.user_data["draft"] = CV()
    await update.effective_message.reply_text(
        "<b>Let’s build your CV.</b>\n\nWhat is your full name?",
        parse_mode=ParseMode.HTML,
    )
    return FULL_NAME


async def _save_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE, *, state: int
) -> int:
    draft = context.user_data.get("draft")
    if not isinstance(draft, CV):
        await update.effective_message.reply_text("Your draft expired. Send /create to restart.")
        return ConversationHandler.END

    value = update.effective_message.text.strip()
    if not value:
        await update.effective_message.reply_text("Please send a text answer.")
        return state

    if state == FULL_NAME:
        draft.full_name = value
        return await _ask(update, "What professional title should appear below your name?", TITLE)
    if state == TITLE:
        draft.professional_title = value
        return await _ask(update, "What is your professional email address?", EMAIL)
    if state == EMAIL:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            await update.effective_message.reply_text("Please enter a valid email address.")
            return EMAIL
        draft.email = value
        return await _ask(update, "What is your phone number?", PHONE)
    if state == PHONE:
        draft.phone = "" if _is_skip(value) else value
        return await _ask(update, "Where are you located? Example: Berlin, Germany", LOCATION)
    if state == LOCATION:
        draft.location = "" if _is_skip(value) else value
        return await _ask(
            update,
            "Send your LinkedIn URL, or type <b>skip</b>.",
            LINKEDIN,
        )
    if state == LINKEDIN:
        draft.linkedin = "" if _is_skip(value) else value
        return await _ask(
            update,
            "Write a 2–4 sentence professional summary highlighting your experience, "
            "specialty, and value.",
            SUMMARY,
        )
    if state == SUMMARY:
        draft.summary = value
        return await _ask(
            update,
            "List 5–10 key skills separated by commas.\n"
            "Example: Python, Project Management, Data Analysis",
            SKILLS,
        )
    if state == SKILLS:
        draft.skills = [skill.strip() for skill in value.split(",") if skill.strip()]
        if not draft.skills:
            await update.effective_message.reply_text("Please enter at least one skill.")
            return SKILLS
        return await _ask(
            update,
            "<b>Add work experience</b> using this format:\n"
            "<code>Company | Role | Dates | Achievement or responsibility</code>\n\n"
            "Example:\n"
            "<code>Acme | Product Manager | 2022–Present | Increased activation by 24%</code>\n\n"
            "Type <b>skip</b> if you have no experience to add.",
            EXPERIENCE,
        )
    if state == EXPERIENCE:
        if _is_skip(value) and not draft.experiences:
            return await _ask_education(update)
        try:
            draft.experiences.append(parse_experience(value))
        except ValueError as error:
            await update.effective_message.reply_text(str(error))
            return EXPERIENCE
        return await _ask_more_experience(update)
    if state == EDUCATION:
        if _is_skip(value) and not draft.education:
            return await _finish_cv(update, context, draft)
        try:
            draft.education.append(parse_education(value))
        except ValueError as error:
            await update.effective_message.reply_text(str(error))
            return EDUCATION
        return await _ask_more_education(update)

    return state


async def _experience_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    if update.callback_query.data == "experience_add":
        await update.effective_message.reply_text(
            "Send another entry:\n"
            "<code>Company | Role | Dates | Achievement or responsibility</code>",
            parse_mode=ParseMode.HTML,
        )
        return EXPERIENCE
    return await _ask_education(update)


async def _education_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    if update.callback_query.data == "education_add":
        await update.effective_message.reply_text(
            "Send another entry:\n<code>Institution | Degree | Dates</code>",
            parse_mode=ParseMode.HTML,
        )
        return EDUCATION
    draft = context.user_data.get("draft")
    return await _finish_cv(update, context, draft)


async def _ask_more_experience(update: Update) -> int:
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Add another", callback_data="experience_add"),
                InlineKeyboardButton("Done", callback_data="experience_done"),
            ]
        ]
    )
    await update.effective_message.reply_text("Experience added. Add another?", reply_markup=keyboard)
    return MORE_EXPERIENCE


async def _ask_education(update: Update) -> int:
    await update.effective_message.reply_text(
        "<b>Add education</b> using this format:\n"
        "<code>Institution | Degree | Dates</code>\n\n"
        "Example:\n"
        "<code>University of Tehran | BSc Computer Science | 2018–2022</code>\n\n"
        "Type <b>skip</b> if you have no education to add.",
        parse_mode=ParseMode.HTML,
    )
    return EDUCATION


async def _ask_more_education(update: Update) -> int:
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Add another", callback_data="education_add"),
                InlineKeyboardButton("Finish CV", callback_data="education_done"),
            ]
        ]
    )
    await update.effective_message.reply_text("Education added. Add another?", reply_markup=keyboard)
    return MORE_EDUCATION


async def _finish_cv(
    update: Update, context: ContextTypes.DEFAULT_TYPE, draft: object
) -> int:
    if not isinstance(draft, CV):
        await update.effective_message.reply_text("Your draft expired. Send /create to restart.")
        return ConversationHandler.END
    _store(context).save(update.effective_user.id, draft)
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text(
        "✅ <b>Your CV is ready.</b>\n\n"
        "Review the preview below, then download the professional PDF.",
        parse_mode=ParseMode.HTML,
    )
    await _send_preview(update, draft)
    return ConversationHandler.END


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cv = _store(context).load(update.effective_user.id)
    if not cv.is_ready:
        await update.effective_message.reply_text("No completed CV found. Send /create to begin.")
        return
    await _send_preview(update, cv)


async def _send_preview(update: Update, cv: CV) -> None:
    experience = "\n".join(
        f"• <b>{escape(item.role)}</b> at {escape(item.company)} ({escape(item.dates)})"
        for item in cv.experiences
    )
    education = "\n".join(
        f"• <b>{escape(item.degree)}</b>, {escape(item.institution)}"
        for item in cv.education
    )
    sections = [
        f"<b>{escape(cv.full_name)}</b>",
        f"<i>{escape(cv.professional_title)}</i>",
        escape(" · ".join(value for value in [cv.email, cv.phone, cv.location] if value)),
        f"\n<b>Profile</b>\n{escape(cv.summary)}",
        f"\n<b>Skills</b>\n{escape(', '.join(cv.skills))}",
    ]
    if experience:
        sections.append(f"\n<b>Experience</b>\n{experience}")
    if education:
        sections.append(f"\n<b>Education</b>\n{education}")
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Download PDF", callback_data="download_pdf")]]
    )
    await update.effective_message.reply_text(
        "\n".join(sections),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query:
        await update.callback_query.answer("Preparing your PDF…")
    cv = _store(context).load(update.effective_user.id)
    if not cv.is_ready:
        await update.effective_message.reply_text("No completed CV found. Send /create to begin.")
        return

    output_path = Path(context.application.bot_data[PDF_DIRECTORY_KEY]) / (
        f"cv-{update.effective_user.id}.pdf"
    )
    build_cv_pdf(cv, output_path)
    filename = f"{_safe_filename(cv.full_name)}-CV.pdf"
    with output_path.open("rb") as pdf_file:
        await update.effective_message.reply_document(
            document=InputFile(pdf_file, filename=filename),
            caption="Your professional CV is ready. Good luck with your applications!",
        )


async def delete_cv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    _store(context).delete(update.effective_user.id)
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text("Your saved CV data has been deleted.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("draft", None)
    await update.effective_message.reply_text("CV creation cancelled. Send /create when ready.")
    return ConversationHandler.END


async def _ask(update: Update, message: str, next_state: int) -> int:
    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)
    return next_state


def _store(context: ContextTypes.DEFAULT_TYPE) -> CVStore:
    return context.application.bot_data[STORE_KEY]


def _is_skip(value: str) -> bool:
    return value.casefold() in {"skip", "/skip", "none", "n/a"}


def _safe_filename(value: str) -> str:
    safe = "".join(character for character in value if character.isalnum() or character in " -_")
    return safe.strip().replace(" ", "-") or "Professional"


async def _handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOGGER.exception("Unhandled bot error", exc_info=context.error)
