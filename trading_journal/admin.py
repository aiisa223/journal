from django.contrib import admin
from .models import TradeRule, Tag, Trade

@admin.register(TradeRule)
class TradeRuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'user', 'created_at')
    list_filter = ('category', 'user', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('trade_id', 'ticker_symbol', 'trade_type', 'entry_date', 'profit_loss', 'is_win')
    list_filter = ('trade_type', 'is_win', 'user', 'entry_date')
    search_fields = ('ticker_symbol', 'notes')
    readonly_fields = ('trade_id', 'created_at', 'updated_at', 'profit_loss', 'is_win')
    filter_horizontal = ('tags', 'rules_followed')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'trade_id', 'ticker_symbol', 'trade_type')
        }),
        ('Trade Details', {
            'fields': ('entry_date', 'exit_date', 'entry_price', 'exit_price', 
                      'position_size', 'fees')
        }),
        ('Performance', {
            'fields': ('profit_loss', 'is_win', 'execution_rating')
        }),
        ('Analysis', {
            'fields': ('tags', 'rules_followed', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
