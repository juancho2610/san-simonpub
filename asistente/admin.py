from django.contrib import admin

from .models import Interaccion


@admin.register(Interaccion)
class InteraccionAdmin(admin.ModelAdmin):
    list_display = ('creada', 'usuario', 'origen', 'tema')
    list_filter = ('origen', 'tema')

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False
