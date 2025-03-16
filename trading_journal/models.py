from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class TagCategory(models.Model):
    """Model for organizing tags into categories"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Tag Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class TradeRule(models.Model):
    """Model for storing trading rules and mindset notes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('GENERAL', 'General Trading Rules'),
        ('DAILY', 'Daily Reminders'),
        ('PSYCH', 'Psychological Insights')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.category}"

class Tag(models.Model):
    """Model for trade strategy tags"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(TagCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='tags')
    color = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.name

class Trade(models.Model):
    """Model for storing trade information"""
    TRADE_TYPES = [
        ('STOCK', 'Stock'),
        ('OPTION', 'Options')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trade_id = models.AutoField(primary_key=True)
    entry_date = models.DateTimeField(default=timezone.now)
    exit_date = models.DateTimeField(null=True, blank=True)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPES)
    ticker_symbol = models.CharField(max_length=20)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    position_size = models.DecimalField(max_digits=15, decimal_places=2)
    fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_loss = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_win = models.BooleanField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='trades')
    notes = models.TextField(blank=True)
    rules_followed = models.ManyToManyField(TradeRule, related_name='trades', blank=True)
    execution_rating = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-entry_date']

    def save(self, *args, **kwargs):
        # If we have both entry and exit prices but no P&L, calculate it
        if self.exit_price and self.entry_price and not self.profit_loss:
            # P&L is (exit - entry) * position_size
            self.profit_loss = (float(self.exit_price) - float(self.entry_price)) * float(self.position_size)
            
            # Subtract fees
            self.profit_loss -= float(self.fees)
            
            # Determine if trade is a win
            self.is_win = self.profit_loss > 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticker_symbol} {self.trade_type} - {self.entry_date.date()}"

class JournalEntry(models.Model):
    """Model for storing trading journal entries and premarket analysis"""
    ENTRY_TYPES = [
        ('journal', 'Daily Journal'),
        ('premarket', 'Premarket Analysis')
    ]
    
    MOOD_CHOICES = [
        ('Confident', 'Confident'),
        ('Cautious', 'Cautious'),
        ('Neutral', 'Neutral'),
        ('Reflective', 'Reflective'),
        ('Positive', 'Positive'),
        ('Negative', 'Negative')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=ENTRY_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    date = models.DateTimeField(default=timezone.now)
    tags = models.ManyToManyField(Tag, related_name='journal_entries', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Journal Entries'
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.date.strftime('%Y-%m-%d')}"
