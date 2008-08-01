from django.contrib import admin
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.models import BaseInlineFormset
from django import forms
from django.contrib.contenttypes.models import ContentType

from ella.tagging.admin import TaggingInlineOptions

from ella.galleries.models import Gallery, GalleryItem
from ella.ellaadmin import widgets, fields
from ella.core.admin import PlacementInlineOptions
from ella.core.cache import get_cached_object
from ella.ellaadmin.options import EllaAdminOptionsMixin

class GalleryItemFormset(BaseInlineFormset):
    " Override default FormSet to allow for custom validation."

    def clean(self):
        """Searches for duplicate references to the same object in one gallery."""
        if not self.is_valid():
            return

        obj = self.instance
        items = set([])

        for i,d in ((i,d) for i,d in enumerate(self.cleaned_data) if d):
            # TODO: why cleaned data does not have target_ct_id prop?
            target = (d['target_ct'].id, d['target_id'],)
            # check for duplicities
            if target in items:
                obj = get_cached_object(get_cached_object(ContentType, pk=d['target_ct'].id), pk=d['target_id'])
                raise forms.ValidationError, ugettext('There are two references to %s in this gallery') % obj
            items.add(target)

        return self.cleaned_data

class GalleryItemTabularOptions(EllaAdminOptionsMixin, admin.TabularInline):
    model = GalleryItem
    extra = 10
    formset = GalleryItemFormset

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'order':
            kwargs['widget'] = widgets.IncrementWidget
        return super(GalleryItemTabularOptions, self).formfield_for_dbfield(db_field, **kwargs)

class GalleryOptions(EllaAdminOptionsMixin, admin.ModelAdmin):
    list_display = ('title', 'created', 'category', 'get_hits', 'full_url',)
    ordering = ('-created',)
    fieldsets = (
        (_("Gallery heading"), {'fields': ('title', 'slug',)}),
        (_("Gallery metadata"), {'fields': ('description', 'content', 'owner', 'category')}),
)
    list_filter = ('created', 'category',)
    search_fields = ('title', 'description', 'slug',)
    inlines = (GalleryItemTabularOptions, PlacementInlineOptions, TaggingInlineOptions,)
    prepopulated_fields = {'slug': ('title',)}
    rich_text_fields = {None: ('description', 'content',)}

admin.site.register(Gallery, GalleryOptions)

