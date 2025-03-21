# Trading Journal Application

A full-stack trading journal application built with Django and Next.js that helps traders track, analyze, and improve their trading performance.

## Features

### Trade Management
- Import trades from ThinkOrSwim CSV files
- Manual trade entry with detailed information:
  - Symbol and trade type (Stock/Option)
  - Entry and exit prices
  - Position size
  - Profit/Loss tracking
  - Notes and tags
- Edit and delete trades
- Clear all trades functionality

### Analytics
- Comprehensive trading statistics:
  - Win rate
  - Profit factor
  - Average win/loss
  - Total profit/loss
- Performance charts:
  - Cumulative P&L
  - Daily P&L
  - Win/Loss distribution
- Strategy performance analysis

### Journal Features
- Daily journal entries
- Pre-market analysis templates
- Mood tracking
- Tag-based organization

### Tag Management
- Create and manage custom tags
- Organize tags by categories
- Color-coded tag system
- Filter trades and journal entries by tags

## Technology Stack

### Backend
- Django
- Django REST Framework
- PostgreSQL
- Celery (for background tasks)
- Redis (for caching)

### Frontend
- Next.js 14
- React Query
- Tailwind CSS
- Recharts for data visualization
- Axios for API communication

## Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL
- Redis

### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/aiisa223/journal.git
   cd journal
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with:
   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://user:password@localhost:5432/trading_journal
   REDIS_URL=redis://localhost:6379/0
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

## Running the Application

### Development Mode
1. Start the Django development server:
   ```bash
   python manage.py runserver
   ```

2. In a separate terminal, start the Next.js development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - Admin interface: http://localhost:8000/admin

### Production Mode
1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Configure your production server (e.g., Nginx) to serve the Django application and static files.

## Usage Guide

### Importing Trades
1. Export your trades from ThinkOrSwim as a CSV file
2. In the application, go to the Trades page
3. Click "Import CSV" and select your file
4. The system will automatically parse and import your trades

### Managing Trades
- Add new trades manually using the "New Trade" button
- Edit trades by clicking the "Edit" button on any trade row
- Filter trades by symbol, date range, or win/loss status
- Use tags to categorize trades by strategy or market conditions

### Journal Entries
- Create daily journal entries to track your trading thoughts
- Use the pre-market template for consistent morning analysis
- Tag entries for better organization
- Track your trading psychology with mood indicators

### Analytics
- View your performance metrics on the Dashboard
- Analyze profit/loss trends over time
- Identify your most profitable strategies
- Track your win rate and other key metrics

### Tag System
- Create custom tags for both trades and journal entries
- Organize tags into categories (e.g., Strategies, Market Conditions)
- Use color coding for visual organization
- Filter content using tags for detailed analysis

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ThinkOrSwim for trade data export functionality
- The Django and Next.js communities for excellent documentation and tools
