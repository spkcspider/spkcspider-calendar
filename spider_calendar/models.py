
import logging
from jsonfield import JSONField

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import models
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext
from jsonfield import JSONField
from ranged_response import RangedFileResponse
from spkcspider.apps.spider.conf import (
    FILE_TOKEN_SIZE, image_extensions, media_extensions
)
from spkcspider.apps.spider.contents import BaseContent
from spkcspider.apps.spider import registry
from spkcspider.constants import VariantType
from spkcspider.utils.fields import prepare_description, add_by_field
from spkcspider.utils.security import create_b64_token


logger = logging.getLogger(__name__)


# Create your models here.

class BaseEvent(BaseContent):
    expose_name = "force"
    expose_description = True

    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True, blank=True)
    data: dict = JSONField(default=dict, null=False)


@add_by_field(registry.contents, "_meta.model_name")
class Calendar(BaseContent):
    expose_name = True
    expose_description = True

    appearances = [{"name": "Calendar"}]

    def map_data(self, name, field, data, graph, context):
        if name == "webreferences":
            # per node create a message anonymous Node
            ret = BNode()
            for nname, val in data.items():
                value_node = add_property(
                    graph, nname, ref=ret,
                    literal=literalize(
                        val, field, domain_base=context["hostpart"]
                    )
                )

                graph.add((
                    value_node,
                    spkcgraph["hashable"],
                    Literal(False)
                ))
            return ret
        elif name == "signatures":
            # per node create a signature Entity
            ret = literalize(data["key"], domain_base=context["hostpart"])
            value_node = add_property(
                graph, "signature", ref=ret,
                literal=literalize(
                    data["signature"], field, domain_base=context["hostpart"]
                )
            )

            graph.add((
                value_node,
                spkcgraph["hashable"],
                Literal(False)
            ))
            return ret
        return super().map_data(name, field, data, graph, context)

    def get_template_name(self, scope):
        # view update form
        if scope == "update_guest":
            return 'spider_base/edit_form.html'
        elif scope == "view":
            return 'spider_base/text.html'
        return super().get_template_name(scope)

    def get_content_description(self):
        # use javascript instead
        # currently dead code
        return " ".join(
            prepare_description(
                self.text, 51
            )[:50]
        )

    def get_info(self):
        ret = super().get_info()
        return "%sname=%s\x1e" % (
            ret, self.associated.name
        )

    def get_size(self):
        return len(self.text.encode("utf8")) + super().get_size()

    def get_form(self, scope):
        if scope in ("raw", "export", "list"):
            from .forms import RawTextForm as f
        else:
            from .forms import TextForm as f
        return f

    def get_form_kwargs(self, **kwargs):
        ret = super().get_form_kwargs(**kwargs)
        ret["request"] = kwargs["request"]
        ret["source"] = kwargs.get("source", self.associated.usercomponent)
        ret["scope"] = kwargs["scope"]
        return ret

    def get_abilities(self, context):
        _abilities = set()
        source = context.get("source", self.associated.usercomponent)
        if self.id and self.editable_from.filter(
            pk=source.pk
        ).exists():
            _abilities.add("update_guest")
        return _abilities

    def access_update_guest(self, **kwargs):
        kwargs["legend"] = \
            escape(_("Update \"%s\" (guest)") % self.__str__())
        kwargs["inner_form"] = False
        return self.access_update(**kwargs)

    def access_view(self, **kwargs):
        kwargs["object"] = self
        kwargs["content"] = self.associated
        return render_to_string(
            "spider_filets/text.html", request=kwargs["request"],
            context=kwargs
        )


@add_by_field(registry.contents, "_meta.model_name")
class Event(BaseEvent):
    appearances = [
        {
            "name": "Event"
            # tops workplan
        },
        {
            "name": "Workplan"
        }
    ]

    # references is for calendars


@add_by_field(registry.contents, "_meta.model_name")
class EventInterference(BaseEvent):
    expose_name = False

    appearances = [
        {
            # tops whatever it blocks
            "name": "EventInterference"
        },
    ]
    # references is for events
