from django import template
from django.conf import settings
from django.db import IntegrityError

from ella.media.models import Media, FormattedMedia, Format
from ella.core.cache.utils import get_cached_object

register = template.Library()

class MediaTag(template.Node):
    def __init__(self, media, format, var_name):
        self.media, self.format, self.var_name = media, format, var_name

    def render(self, context):

        if isinstance(self.media, basestring):
            try:
                media = template.resolve_variable(self.media, context)
            except template.VariableDoesNotExist:
                return ''
            try:
                formatted_media = get_cached_object(FormattedMedia, source=media, format=self.format)
            except FormattedMedia.DoesNotExist:
                try:
                    formatted_media = FormattedMedia.objects.create(source=media, format=self.format)
                except (IOError, SystemError, IntegrityError):
#                    context[self.var_name] = self.format.get_blank_img()
                    return ''
        else:
            formatted_media = self.media

        context[self.var_name] = formatted_media
        return ''

@register.tag
def media(parser, token):
    """
    Examples:

        {% media FORMAT for VAR as VAR_NAME %}
        {% media FORMAT with FIELD VALUE as VAR_NAME %}
    """
    bits = token.split_contents()

    if len(bits) < 2 or bits[-2] != 'as':
        raise template.TemplateSyntaxError, "{% media FORMAT for VAR as VAR_NAME %} or {% media FORMAT with FIELD VALUE as VAR_NAME %}"

    try:
        format = get_cached_object(Format, name=bits[1])
    except Format.DoesNotExist:
        raise template.TemplateSyntaxError, "Format with name %r does not exist" % bits[1]

    if len(bits) == 6:
        # media FORMAT for VAR
        if bits[2] != 'for':
            raise template.TemplateSyntaxError, "{% media FORMAT for VAR as VAR_NAME %}"
        formatted_media = bits[3]
    elif len(bits) == 7:
        # media FORMAT with FIELD VALUE
        if bits[2] != 'with':
            raise template.TemplateSyntaxError, "{% media FORMAT with FIELD VALUE as VAR_NAME %}"
        try:
            media = get_cached_object(Media, **{str(bits[3]) : bits[4]})
        except media.DoesNotExist:
            raise template.TemplateSyntaxError, "Media with %r of %r does not exist" % (bits[3],  bits[4])

        try:
            formatted_media = get_cached_object(FormattedMedia, source=media, format=format)
        except FormattedMedia.DoesNotExist:
            formatted_media = FormattedMedia.objects.create(source=media, format=format)
    else:
        raise template.TemplateSyntaxError, "{% media FORMAT for VAR as VAR_NAME %} or {% media FORMAT with FIELD VALUE as VAR_NAME %}"

    return MediaTag(formatted_media, format, bits[-1])


