TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "welcome": (
            "<b>Professional CV Builder</b>\n\n"
            "Create an AI-polished CV with a professional template. If every AI provider "
            "is unavailable, your original answers are used automatically."
        ),
        "choose_language": "Choose your language:",
        "choose_template": "Choose a resume template:",
        "template_saved": "Template updated to <b>{template}</b>.",
        "full_name": "<b>Let’s build your CV.</b>\n\nWhat is your full name?",
        "title": "What professional title should appear below your name?",
        "email": "What is your professional email address?",
        "invalid_email": "Please enter a valid email address.",
        "phone": "What is your phone number? Type <b>skip</b> to omit it.",
        "location": "Where are you located? Example: Berlin, Germany",
        "linkedin": "Send your LinkedIn URL, or type <b>skip</b>.",
        "summary": (
            "Describe your background, specialty, and value in your own words. "
            "AI will turn it into a concise professional summary."
        ),
        "skills": (
            "List 5–10 key skills separated by commas.\n"
            "Example: Python, Project Management, Data Analysis"
        ),
        "skills_required": "Please enter at least one skill.",
        "experience": (
            "<b>Add work experience</b> using this format:\n"
            "<code>Company | Role | Dates | Achievement or responsibility</code>\n\n"
            "Type <b>skip</b> if you have no experience to add."
        ),
        "experience_again": (
            "Send another entry:\n"
            "<code>Company | Role | Dates | Achievement or responsibility</code>"
        ),
        "experience_added": "Experience added. Add another?",
        "education": (
            "<b>Add education</b> using this format:\n"
            "<code>Institution | Degree | Dates</code>\n\n"
            "Type <b>skip</b> if you have no education to add."
        ),
        "education_again": "Send another entry:\n<code>Institution | Degree | Dates</code>",
        "education_added": "Education added. Add another?",
        "add_another": "Add another",
        "done": "Done",
        "finish": "Finish CV",
        "enhancing": "✨ Polishing your content with the available AI providers…",
        "ready_ai": "✅ <b>Your AI-enhanced CV is ready.</b>",
        "ready_static": (
            "✅ <b>Your CV is ready.</b>\n"
            "AI providers were unavailable, so I safely used your original content."
        ),
        "expired": "Your draft expired. Send /create to restart.",
        "text_required": "Please send a text answer.",
        "not_found": "No completed CV found. Send /create to begin.",
        "profile": "Profile",
        "skills_label": "Skills",
        "experience_label": "Experience",
        "education_label": "Education",
        "download": "Download PDF",
        "preparing": "Preparing your PDF…",
        "pdf_caption": "Your professional CV is ready. Good luck with your applications!",
        "deleted": "Your saved CV data has been deleted.",
        "cancelled": "CV creation cancelled. Send /create when ready.",
        "help": (
            "<b>Commands</b>\n"
            "/create — create a new CV\n"
            "/templates — view or change templates\n"
            "/preview — review saved content\n"
            "/pdf — download the PDF\n"
            "/delete — erase saved CV data\n"
            "/cancel — stop the current form"
        ),
    },
    "fa": {
        "welcome": (
            "<b>رزومه‌ساز حرفه‌ای</b>\n\n"
            "رزومه‌ای حرفه‌ای با کمک هوش مصنوعی و قالب دلخواه بسازید. اگر همه سرویس‌های "
            "هوش مصنوعی در دسترس نباشند، پاسخ‌های اصلی شما به‌صورت خودکار استفاده می‌شوند."
        ),
        "choose_language": "زبان خود را انتخاب کنید:",
        "choose_template": "قالب رزومه را انتخاب کنید:",
        "template_saved": "قالب به <b>{template}</b> تغییر کرد.",
        "full_name": "<b>رزومه شما را بسازیم.</b>\n\nنام و نام خانوادگی شما چیست؟",
        "title": "عنوان شغلی شما چیست؟",
        "email": "ایمیل حرفه‌ای شما چیست؟",
        "invalid_email": "لطفاً یک ایمیل معتبر وارد کنید.",
        "phone": "شماره تماس شما چیست؟ برای حذف این بخش <b>رد</b> را بنویسید.",
        "location": "محل سکونت شما کجاست؟ مثال: تهران، ایران",
        "linkedin": "لینک پروفایل لینکدین را بفرستید یا <b>رد</b> را بنویسید.",
        "summary": (
            "سابقه، تخصص و ارزشی که ایجاد می‌کنید را با زبان خودتان توضیح دهید. "
            "هوش مصنوعی آن را به یک خلاصه حرفه‌ای تبدیل می‌کند."
        ),
        "skills": (
            "۵ تا ۱۰ مهارت کلیدی را با ویرگول جدا کنید.\n"
            "مثال: پایتون، مدیریت پروژه، تحلیل داده"
        ),
        "skills_required": "لطفاً حداقل یک مهارت وارد کنید.",
        "experience": (
            "<b>سابقه کاری</b> را با قالب زیر وارد کنید:\n"
            "<code>شرکت | سمت | تاریخ | دستاورد یا مسئولیت</code>\n\n"
            "اگر سابقه‌ای ندارید <b>رد</b> را بنویسید."
        ),
        "experience_again": (
            "سابقه بعدی را وارد کنید:\n"
            "<code>شرکت | سمت | تاریخ | دستاورد یا مسئولیت</code>"
        ),
        "experience_added": "سابقه اضافه شد. مورد دیگری دارید؟",
        "education": (
            "<b>تحصیلات</b> را با قالب زیر وارد کنید:\n"
            "<code>موسسه | مدرک یا رشته | تاریخ</code>\n\n"
            "اگر موردی ندارید <b>رد</b> را بنویسید."
        ),
        "education_again": "مورد بعدی را وارد کنید:\n<code>موسسه | مدرک یا رشته | تاریخ</code>",
        "education_added": "تحصیلات اضافه شد. مورد دیگری دارید؟",
        "add_another": "افزودن مورد",
        "done": "تمام",
        "finish": "ساخت رزومه",
        "enhancing": "✨ در حال بهبود محتوا با سرویس‌های هوش مصنوعی موجود…",
        "ready_ai": "✅ <b>رزومه بهبودیافته با هوش مصنوعی آماده است.</b>",
        "ready_static": (
            "✅ <b>رزومه شما آماده است.</b>\n"
            "سرویس‌های هوش مصنوعی در دسترس نبودند؛ محتوای اصلی شما با اطمینان استفاده شد."
        ),
        "expired": "پیش‌نویس منقضی شده است. برای شروع /create را بفرستید.",
        "text_required": "لطفاً پاسخ متنی ارسال کنید.",
        "not_found": "رزومه تکمیل‌شده‌ای پیدا نشد. برای شروع /create را بفرستید.",
        "profile": "درباره من",
        "skills_label": "مهارت‌ها",
        "experience_label": "سوابق کاری",
        "education_label": "تحصیلات",
        "download": "دریافت PDF",
        "preparing": "در حال آماده‌سازی PDF…",
        "pdf_caption": "رزومه حرفه‌ای شما آماده است. موفق باشید!",
        "deleted": "اطلاعات ذخیره‌شده رزومه شما حذف شد.",
        "cancelled": "ساخت رزومه لغو شد. برای شروع دوباره /create را بفرستید.",
        "help": (
            "<b>دستورها</b>\n"
            "/create — ساخت رزومه جدید\n"
            "/templates — مشاهده یا تغییر قالب\n"
            "/preview — مشاهده محتوای ذخیره‌شده\n"
            "/pdf — دریافت فایل PDF\n"
            "/delete — حذف اطلاعات رزومه\n"
            "/cancel — توقف فرم فعلی"
        ),
    },
}


def text(language: str, key: str, **values: str) -> str:
    selected = language if language in TEXTS else "en"
    return TEXTS[selected][key].format(**values)
