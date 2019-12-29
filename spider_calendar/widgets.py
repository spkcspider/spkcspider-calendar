__all__ = [

]
import json

from django.conf import settings


_extra = '' if settings.DEBUG else '.min'
