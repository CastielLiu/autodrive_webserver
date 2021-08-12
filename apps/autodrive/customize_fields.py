from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat


# 受限的文件阈, 限制文件类型和大小
# https://blog.csdn.net/weixin_42134789/article/details/100012339
class RestrictedFileField(FileField):
    """ max_upload_size:
            2.5MB - 2621440
            5MB - 5242880
            10MB - 10485760
            20MB - 20971520
            50MB - 5242880
            100MB 104857600
            250MB - 214958080
            500MB - 429916160
    """
    def __init__(self, content_types=None, max_upload_size=None, *args, **kwargs):
        self.content_types = content_types
        self.max_upload_size = max_upload_size

        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        file = data.file

        try:
            content_type = file.content_type
            if self.content_types is None or content_type in self.content_types:
                if self.max_upload_size is not None and file.size > self.max_upload_size:
                    raise forms.ValidationError('Please keep filesize under {}. Current filesize {}'
                                                .format(filesizeformat(self.max_upload_size), filesizeformat(file.size)))
            else:
                raise forms.ValidationError('This file type is not allowed.')
        except AttributeError:
            pass
        return data
