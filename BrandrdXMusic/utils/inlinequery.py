from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

answer = []

answer.extend(
    [
        InlineQueryResultArticle(
            title="إيـقـاف",
            description="إيـقـاف الـتـشـغـيـل الـحـالـي فـي مـكـالـمـة الـفـيـديـو.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/pause"),
        ),
        InlineQueryResultArticle(
            title="اسـتـئـنـاف",
            description="اسـتـئـنـاف الـتـشـغـيـل الـمـتـوقـف مـؤقـتـًا فـي مـكـالـمـة الـفـيـديـو.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/resume"),
        ),
        InlineQueryResultArticle(
            title="تـخـطـي",
            description="تـخـطـي الـتـشـغـيـل الـحـالـي والـانـتـقـال إلـى الـتـشـغـيـل الـتـالـي.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/skip"),
        ),
        InlineQueryResultArticle(
            title="إنـهـاء",
            description="إنـهـاء الـتـشـغـيـل الـحـالـي فـي مـكـالـمـة الـفـيـديـو.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/end"),
        ),
        InlineQueryResultArticle(
            title="خـلـط",
            description="خـلـط الأغـانـي الـمـوجـودة فـي قـائـمـة الـتـشـغـيـل.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/shuffle"),
        ),
        InlineQueryResultArticle(
            title="تـكـرار",
            description="تـكـرار تـشـغـيـل الـمـقـطـع الـحـالـي فـي مـكـالـمـة الـفـيـديـو.",
            thumb_url="https://i.ibb.co/xtwDx01q/pexels-pixabay-269583.jpg",
            input_message_content=InputTextMessageContent("/loop 3"),
        ),
    ]
)
