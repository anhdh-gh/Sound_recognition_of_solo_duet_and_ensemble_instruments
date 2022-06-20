import shutil
from functools import wraps

from django.core.files.storage import FileSystemStorage

# Xóa các file input cũ
from main.models import File
from main.util import export_to_excel


def delete_file_input(view_function):
    @wraps(view_function)
    def wrap(request, *args, **kwargs):
        try:
            fs = FileSystemStorage()
            shutil.rmtree(fs.path('file-input'))
        except FileNotFoundError:
            pass
        return view_function(request, *args, **kwargs)

    return wrap
