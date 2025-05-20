# Digital_Content_Marketplace/apps/chat/admin.py
from django.contrib import admin
from .models import ChatThread, ChatMessage, ModificationRequest

# Register ChatThread
@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'developer', 'code_content', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at', 'customer', 'developer', 'flagged_for_review')
    search_fields = ('customer__username', 'developer__username', 'code_content__title')
    raw_id_fields = ('customer', 'developer', 'code_content')  # For better performance with large user/content tables
    actions = ['delete_selected_threads']

    def delete_selected_threads(self, request, queryset):
        """Custom action to delete selected threads and their related messages/requests."""
        for thread in queryset:
            thread.messages.all().delete()  # Delete related messages
            ModificationRequest.objects.filter(thread=thread).delete()  # Delete related modification request
            thread.delete()
        self.message_user(request, "Selected chat threads and their related data have been deleted.")
    delete_selected_threads.short_description = "Delete selected threads and related data"

# Register ChatMessage
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'sender', 'message_preview')
    list_filter = ('sent_at','thread')
    search_fields = ('sender__username', 'message', 'thread__code_content__title')
    raw_id_fields = ('thread', 'sender')
    list_per_page = 50

    def message_preview(self, obj):
        """Display a truncated version of the message."""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

# Register ModificationRequest
@admin.register(ModificationRequest)
class ModificationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'proposed_price', 'counter_price', 'final_price', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('thread__code_content__title', 'thread__customer__username', 'thread__developer__username')
    raw_id_fields = ('thread',)
