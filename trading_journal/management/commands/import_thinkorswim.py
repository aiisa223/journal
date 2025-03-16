import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from trading_journal.models import Trade

class Command(BaseCommand):
    help = 'Import trades from ThinkOrSwim CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        trades_section = False
        trades_data = []

        # Read the CSV file
        with open(csv_file, 'r') as file:
            csv_reader = csv.reader(file)
            
            for row in csv_reader:
                if not row:  # Skip empty rows
                    continue
                    
                # Detect start of Account Trade History section
                if row[0].strip() == 'Account Trade History':
                    trades_section = True
                    continue
                    
                if trades_section:
                    # Skip the header row
                    if row[0].strip() == 'Exec Time':
                        continue
                    
                    # If we hit a blank line or new section, stop processing
                    if not row[0].strip() or row[0].strip() == 'Profits and Losses':
                        break
                        
                    trades_data.append(row)

        # Process trades
        with transaction.atomic():
            for row in trades_data:
                if len(row) < 11:  # Skip invalid rows
                    continue

                exec_time_str = row[0].strip()
                spread = row[1].strip()
                side = row[2].strip()
                qty = row[3].strip()
                pos_effect = row[4].strip()
                symbol = row[5].strip()
                exp = row[6].strip()
                strike = row[7].strip()
                type_ = row[8].strip()
                price = float(row[9].strip())
                net_price = float(row[10].strip())

                # Parse datetime
                exec_time = datetime.strptime(exec_time_str, '%m/%d/%y %H:%M:%S')

                # Determine if it's an opening or closing trade
                is_opening = pos_effect == 'TO OPEN'
                
                # Calculate position size (quantity * price * 100 for options)
                quantity = abs(float(qty))
                position_size = quantity * price
                if type_ == 'PUT' or type_ == 'CALL':
                    position_size *= 100  # Options contracts are for 100 shares

                # Create trade object
                trade = Trade(
                    trade_type='OPTION' if type_ in ['PUT', 'CALL'] else 'STOCK',
                    ticker_symbol=symbol,
                    entry_date=exec_time if is_opening else None,
                    exit_date=exec_time if not is_opening else None,
                    entry_price=price if is_opening else None,
                    exit_price=price if not is_opening else None,
                    position_size=position_size,
                    notes=f"{type_} {strike} {exp}" if type_ in ['PUT', 'CALL'] else "",
                    fees=0,  # You might want to add fees from the Cash Balance section
                )

                # Try to find matching trade to complete the entry/exit
                if not is_opening:
                    # Look for the opening trade
                    try:
                        opening_trade = Trade.objects.filter(
                            ticker_symbol=symbol,
                            exit_date__isnull=True,
                            trade_type=trade.trade_type,
                            notes=trade.notes
                        ).latest('entry_date')
                        
                        # Calculate P&L
                        profit_loss = (price - opening_trade.entry_price) * quantity
                        if trade.trade_type == 'OPTION':
                            profit_loss *= 100
                            
                        # Update the opening trade
                        opening_trade.exit_date = exec_time
                        opening_trade.exit_price = price
                        opening_trade.profit_loss = profit_loss
                        opening_trade.is_win = profit_loss > 0
                        opening_trade.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Updated trade for {symbol}: {"profit" if profit_loss > 0 else "loss"} of ${profit_loss:.2f}'
                            )
                        )
                        continue
                        
                    except Trade.DoesNotExist:
                        pass

                trade.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {"opening" if is_opening else "closing"} trade for {symbol}'
                    )
                )

        self.stdout.write(self.style.SUCCESS('Successfully imported trades')) 