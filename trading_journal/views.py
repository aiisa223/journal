from django.shortcuts import render
from django.db import models, transaction
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import TradeRule, Tag, Trade, JournalEntry, TagCategory
from .serializers import (
    TradeRuleSerializer, TagSerializer, TradeSerializer, 
    JournalEntrySerializer, TagCategorySerializer
)
import pandas as pd
import numpy as np
from datetime import datetime
from decimal import Decimal
import re
import json

# Create your views here.

class TagCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = TagCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        return TagCategory.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TradeRuleViewSet(viewsets.ModelViewSet):
    serializer_class = TradeRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'category']
    ordering_fields = ['created_at', 'updated_at', 'category']

    def get_queryset(self):
        return TradeRule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        return Tag.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ThinkOrSwimParser:
    def __init__(self, content):
        self.raw_data = content
        self.trades = []
        
    def parse(self):
        """Parse the ThinkOrSwim CSV statement content using pandas."""
        try:
            # Split the content into sections using the headers as delimiters
            sections = self.raw_data.split('\n\n')
            trade_history_section = None
            
            # Find the trade history section
            for section in sections:
                if section.strip().startswith('Account Trade History'):
                    trade_history_section = section
                    break
            
            if not trade_history_section:
                print("No trade history section found")
                return {'trades': []}
            
            # Convert the trade history section to a DataFrame
            trade_lines = trade_history_section.split('\n')
            # Find the header line (the one that starts with "Exec Time")
            header_index = next(i for i, line in enumerate(trade_lines) if 'Exec Time' in line)
            
            # Create DataFrame from the trade lines
            df = pd.read_csv(
                pd.StringIO('\n'.join(trade_lines[header_index:])),
                skipinitialspace=True,
                skip_blank_lines=True
            )
            
            # Clean up column names and drop empty columns
            df.columns = df.columns.str.strip()
            df = df.dropna(axis=1, how='all')
            
            # Process each trade
            trades = []
            open_positions = {}
            
            # Sort trades by execution time
            df['Exec Time'] = pd.to_datetime(df['Exec Time'], format='%m/%d/%y %H:%M:%S')
            df = df.sort_values('Exec Time')
            
            for _, row in df.iterrows():
                try:
                    # Extract trade details
                    symbol = row['Symbol']
                    exec_time = row['Exec Time']
                    side = row['Side']
                    pos_effect = row['Pos Effect']
                    price = float(str(row['Price']).replace('$', '').replace(',', ''))
                    qty = abs(float(str(row['Qty']).replace('+', '').replace('-', '')))
                    
                    # Create position key (include expiration for options)
                    position_key = f"{symbol}_{row['Exp']}" if pd.notna(row['Exp']) else symbol
                    
                    # Determine trade type
                    trade_type = 'STOCK' if row['Type'] == 'STOCK' else 'OPTION'
                    
                    # Calculate position size
                    position_size = qty * price
                    if trade_type == 'OPTION':
                        position_size *= 100
                    
                    if pos_effect == 'TO OPEN':
                        if position_key not in open_positions:
                            open_positions[position_key] = []
                        
                        open_positions[position_key].append({
                            'entry_date': exec_time,
                            'ticker_symbol': symbol,
                            'trade_type': trade_type,
                            'entry_price': price,
                            'quantity': qty,
                            'position_size': position_size,
                            'side': side,
                            'expiration': row['Exp'] if pd.notna(row['Exp']) else None,
                            'strike': row['Strike'] if pd.notna(row['Strike']) else None
                        })
                    
                    elif pos_effect == 'TO CLOSE':
                        if position_key in open_positions and open_positions[position_key]:
                            open_trade = open_positions[position_key].pop(0)
                            
                            # Calculate P&L
                            if open_trade['side'] == 'BUY':
                                profit_loss = (price - open_trade['entry_price']) * qty
                            else:
                                profit_loss = (open_trade['entry_price'] - price) * qty
                            
                            if trade_type == 'OPTION':
                                profit_loss *= 100
                            
                            trade_data = {
                                'entry_date': open_trade['entry_date'],
                                'exit_date': exec_time,
                                'ticker_symbol': symbol,
                                'trade_type': trade_type,
                                'entry_price': open_trade['entry_price'],
                                'exit_price': price,
                                'position_size': open_trade['position_size'],
                                'profit_loss': profit_loss,
                                'is_win': profit_loss > 0,
                                'quantity': qty
                            }
                            
                            if trade_type == 'OPTION':
                                trade_data.update({
                                    'option_expiration': open_trade['expiration'],
                                    'option_strike': open_trade['strike']
                                })
                            
                            trades.append(trade_data)
                
        except Exception as e:
                    print(f"Error processing trade: {str(e)}")
                    continue
            
            return {'trades': trades}
            
        except Exception as e:
            print(f"Error parsing CSV: {str(e)}")
            return {'trades': []}

class TradeViewSet(viewsets.ModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['trade_type', 'ticker_symbol', 'is_win', 'tags']
    search_fields = ['ticker_symbol', 'notes']
    ordering_fields = ['entry_date', 'exit_date', 'profit_loss', 'position_size']

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """Import trades from a ThinkOrSwim CSV statement."""
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        csv_file = request.FILES['file']
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Read the CSV content
            content = csv_file.read().decode('utf-8')
            
            # Parse trades using pandas-based parser
            parser = ThinkOrSwimParser(content)
            result = parser.parse()
            trades = result['trades']
            
            if not trades:
                return Response({
                    'error': 'No trades found in CSV file',
                    'message': 'Failed to import trades'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create trades in database
            trades_created = 0
            for trade_data in trades:
                try:
                    # Check for duplicate trade
                    existing_trade = Trade.objects.filter(
                        user=request.user,
                        ticker_symbol=trade_data['ticker_symbol'],
                        entry_date=trade_data['entry_date'],
                        exit_date=trade_data['exit_date'],
                        trade_type=trade_data['trade_type']
                    ).first()
                    
                    if not existing_trade:
                        trade_data['user'] = request.user
                        Trade.objects.create(**trade_data)
                        trades_created += 1
                
                except Exception as e:
                    print(f"Error creating trade: {str(e)}")
                    continue
            
            return Response({
                'message': f'Successfully imported {trades_created} trades',
                'trades_created': trades_created
            })

        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Failed to import trades'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['delete'])
    def delete_all(self, request):
        """Delete all trades for the authenticated user"""
        try:
            trades = self.get_queryset()
            count = trades.count()
            trades.delete()
            return Response({
                'message': f'Successfully deleted {count} trades',
                'count': count
            })
        except Exception as e:
            return Response(
                {'error': f'Error deleting trades: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get trading statistics for the authenticated user"""
        try:
            trades = self.get_queryset()
            completed_trades = trades.filter(exit_price__isnull=False)
            
            # Basic statistics
            total_trades = completed_trades.count()
            if total_trades == 0:
                return Response({
                    'total_trades': 0,
                    'winning_trades': 0,
                    'win_rate': 0,
                    'profit_factor': 0,
                    'total_profit': 0,
                    'total_loss': 0,
                    'average_profit': 0,
                    'average_loss': 0,
                    'strategy_performance': []
                })
            
            winning_trades = completed_trades.filter(is_win=True).count()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # Profit statistics
            total_profit = completed_trades.filter(profit_loss__gt=0).aggregate(
                Sum('profit_loss'))['profit_loss__sum'] or 0
            total_loss = abs(completed_trades.filter(profit_loss__lt=0).aggregate(
                Sum('profit_loss'))['profit_loss__sum'] or 0)
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # Average trade metrics
            avg_profit = completed_trades.filter(profit_loss__gt=0).aggregate(
                Avg('profit_loss'))['profit_loss__avg'] or 0
            avg_loss = completed_trades.filter(profit_loss__lt=0).aggregate(
                Avg('profit_loss'))['profit_loss__avg'] or 0
            
            # Strategy performance - handle trades with no tags
            strategy_performance = []
            
            # First, get performance for trades with tags
            tagged_performance = completed_trades.exclude(tags=None).values('tags__name').annotate(
                total_trades=Count('id'),
                win_rate=Count('id', filter=Q(is_win=True)) * 100.0 / Count('id'),
                total_pnl=Sum('profit_loss')
            ).order_by('-total_pnl')
            
            strategy_performance.extend([{
                'name': item['tags__name'] or 'Unknown',
                'total_trades': item['total_trades'],
                'win_rate': round(float(item['win_rate']), 2),
                'total_pnl': float(item['total_pnl'])
            } for item in tagged_performance])
            
            # Then, get performance for trades without tags
            untagged_trades = completed_trades.filter(tags=None)
            if untagged_trades.exists():
                untagged_count = untagged_trades.count()
                untagged_wins = untagged_trades.filter(is_win=True).count()
                untagged_pnl = untagged_trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0
                
                strategy_performance.append({
                    'name': 'Untagged',
                    'total_trades': untagged_count,
                    'win_rate': round(float(untagged_wins * 100.0 / untagged_count), 2),
                    'total_pnl': float(untagged_pnl)
                })

            return Response({
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': round(win_rate, 2),
                'profit_factor': round(float(profit_factor), 2),
                'total_profit': float(total_profit),
                'total_loss': float(total_loss),
                'average_profit': float(avg_profit),
                'average_loss': float(avg_loss),
                'strategy_performance': strategy_performance
            })
        except Exception as e:
            import traceback
            return Response(
                {
                    'error': f'Error calculating statistics: {str(e)}',
                    'traceback': traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Get weekly trading summary for the specified date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'detail': 'start_date and end_date are required'},
                status=400
            )
        
        trades = self.get_queryset().filter(
            entry_date__date__gte=start_date,
            entry_date__date__lte=end_date
        )
        
        total_trades = trades.count()
        if total_trades == 0:
            return Response({
                'total_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'average_trade': 0,
                'best_trade': None
            })
        
        winning_trades = trades.filter(is_win=True).count()
        win_rate = (winning_trades / total_trades * 100)
        
        total_pnl = trades.aggregate(Sum('profit_loss'))['profit_loss__sum'] or 0
        average_trade = total_pnl / total_trades
        
        best_trade = trades.order_by('-profit_loss').first()
        
        return Response({
            'total_trades': total_trades,
            'win_rate': round(win_rate, 1),
            'total_pnl': float(total_pnl),
            'average_trade': float(average_trade),
            'best_trade': {
                'symbol': best_trade.ticker_symbol,
                'type': best_trade.trade_type,
                'profit': float(best_trade.profit_loss)
            } if best_trade else None
        })

class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'mood', 'tags']
    search_fields = ['title', 'content']
    ordering_fields = ['date', 'created_at']

    def get_queryset(self):
        return JournalEntry.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
