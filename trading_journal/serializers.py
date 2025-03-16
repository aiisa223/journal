from rest_framework import serializers
from django.contrib.auth.models import User
from .models import TradeRule, Tag, Trade, JournalEntry, TagCategory

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class TagCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TagCategory
        fields = ['id', 'name', 'description', 'color', 'created_at']
        read_only_fields = ('created_by', 'created_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class TagSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'description', 'is_default', 'created_at', 'category', 'color', 'category_name', 'category_color']
        read_only_fields = ('created_by', 'created_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class TradeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeRule
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

class TradeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    rules_followed = TradeRuleSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        required=False,
        source='tags'
    )
    rule_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=TradeRule.objects.all(),
        required=False,
        source='rules_followed'
    )

    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = (
            'user', 'trade_id', 'profit_loss', 'is_win',
            'created_at', 'updated_at'
        )

    def validate(self, data):
        """
        Custom validation to ensure exit price is greater than entry price for long trades
        and vice versa for short trades
        """
        if 'exit_price' in data and data.get('exit_price'):
            entry_price = data.get('entry_price')
            exit_price = data.get('exit_price')
            trade_type = data.get('trade_type')

            if trade_type == 'LONG' and exit_price < entry_price:
                raise serializers.ValidationError(
                    "Exit price must be greater than entry price for long trades"
                )
            elif trade_type == 'SHORT' and exit_price > entry_price:
                raise serializers.ValidationError(
                    "Exit price must be less than entry price for short trades"
                )

        return data

class JournalEntrySerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        required=False,
        source='tags'
    )

    class Meta:
        model = JournalEntry
        fields = ['id', 'type', 'title', 'content', 'mood', 'date', 'tags', 'tag_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data) 