__all__ = ["EventForm"]

from django import forms
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from spkcspider.apps.spider.fields import (
    MultipleOpenChoiceField, OpenChoiceField, SanitizedHtmlField
)
from spkcspider.apps.spider.widgets import (
    ListWidget, SelectizeWidget, TrumbowygWidget
)
from spkcspider.utils.settings import get_settings_func

from .conf import DEFAULT_LICENSE_FILE, DEFAULT_LICENSE_TEXT, LICENSE_CHOICES
from .models import FileFilet, TextFilet
from .widgets import LicenseChooserWidget

_extra = '' if settings.DEBUG else '.min'
