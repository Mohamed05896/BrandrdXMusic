import os

from ..logging import LOGGER


def dirr():
    # البحث عن ملفات الصور ومسحها لتنظيف المساحة
    for file in os.listdir():
        if file.endswith(".jpg"):
            os.remove(file)
        elif file.endswith(".jpeg"):
            os.remove(file)
        elif file.endswith(".png"):
            os.remove(file)

    # التأكد من وجود المجلدات الأساسية وإنشائها إذا لم توجد
    if "downloads" not in os.listdir():
        os.mkdir("downloads")
    if "cache" not in os.listdir():
        os.mkdir("cache")

    LOGGER(__name__).info("تم تحديث المجلدات وتنظيف الملفات المؤقتة ✨")
