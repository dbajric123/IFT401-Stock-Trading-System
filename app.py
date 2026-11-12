from datetime import datetime, time, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:password@my-rds-instance.cnmq20wmkwnp.us-east-2.rds.amazonaws.com:3306/stock_trading"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# The market runs on Arizona time (UTC-7, no daylight saving). The EC2 server
# clock is UTC, so we always convert before comparing with the market hours.
MARKET_TZ = timezone(timedelta(hours=-7))


# Returns the current Arizona date and time without a timezone attached.
def now_az():
    return datetime.now(MARKET_TZ).replace(tzinfo=None)


# DATABASE TABLES

# Customers and administrators. role is "user" or "admin".
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # bcrypt hash
    role = db.Column(db.String(20), default='user', nullable=False)
    cash_balance = db.Column(db.Numeric(12, 2), default=0, nullable=False)


# A customer can have several named portfolios (names are unique per customer).
class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    __table_args__ = (db.UniqueConstraint('user_id', 'name'),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=now_az, nullable=False)


# Stocks the administrator adds. shares_available goes down on a buy.
class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), unique=True, nullable=False)
    shares_outstanding = db.Column(db.Integer, nullable=False)
    shares_available = db.Column(db.Integer, nullable=False)
    current_price = db.Column(db.Numeric(12, 2), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=now_az, nullable=False)


# How many shares of one stock a portfolio owns.
class Holding(db.Model):
    __tablename__ = 'holdings'
    __table_args__ = (db.UniqueConstraint('portfolio_id', 'stock_id'),)
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


# Every buy or sell. trade_type is BUY or SELL.
# status is PENDING, COMPLETED, CANCELED or FAILED.
class Trade(db.Model):
    __tablename__ = 'trades'
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    trade_type = db.Column(db.String(4), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=now_az, nullable=False)


# Every deposit, withdrawal and trade payment.
# transaction_type is DEPOSIT, WITHDRAWAL, BUY or SELL.
# related_trade_id is empty for deposits and withdrawals.
class CashTransaction(db.Model):
    __tablename__ = 'cash_transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    related_trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_az, nullable=False)


# One row for every price change made by the price generator.
class StockPriceHistory(db.Model):
    __tablename__ = 'stock_price_history'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    old_price = db.Column(db.Numeric(12, 2), nullable=False)
    new_price = db.Column(db.Numeric(12, 2), nullable=False)
    changed_at = db.Column(db.DateTime, default=now_az, nullable=False)


# Weekly trading hours, one row per weekday name (Monday thru Sunday).
# A closed day has is_open False and empty times.
class MarketHour(db.Model):
    __tablename__ = 'market_hours'
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), unique=True, nullable=False)
    is_open = db.Column(db.Boolean, default=True, nullable=False)
    open_time = db.Column(db.Time, nullable=True)
    close_time = db.Column(db.Time, nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=now_az, nullable=False)


# Holidays when the market is closed all day.
class MarketClosure(db.Model):
    __tablename__ = 'market_closures'
    id = db.Column(db.Integer, primary_key=True)
    closure_date = db.Column(db.Date, unique=True, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=now_az, nullable=False)


# Fills market_hours with Monday-Friday 9:00 AM - 5:00 PM the first time the
# app runs (SAD Map 9). It does nothing if the table already has rows.
def seed_market_hours():
    if MarketHour.query.count() > 0:
        return
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for number, day in enumerate(days):
        if number < 5:
            row = MarketHour(day_of_week=day, is_open=True,
                             open_time=time(9, 0), close_time=time(17, 0))
        else:
            row = MarketHour(day_of_week=day, is_open=False)
        db.session.add(row)
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_market_hours()


# ======================================================================
# HELPERS (everyone uses these)

# Flask-Login uses this to find the logged-in user from the session.
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Template filter: {{ 1234.5 | money }} shows $1,234.50
@app.template_filter('money')
def money(value):
    if value is None:
        value = 0
    return "${:,.2f}".format(value)


# Template filter: {{ some_date | datetime }} shows Nov 12, 2026 2:05 PM
@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return ''
    return value.strftime('%b %d, %Y %I:%M %p').replace(' 0', ' ')


# Page protection for administrators only. A customer is sent back to the
# dashboard with the "no access" message.
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('You do not have access to that page.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


# True only when it is a day the market is open, not a holiday, and the
# current Arizona time is between the open time and the close time.
def is_market_open():
    now = now_az()
    if MarketClosure.query.filter_by(closure_date=now.date()).first():
        return False
    today = MarketHour.query.filter_by(day_of_week=now.strftime('%A')).first()
    if today is None or not today.is_open:
        return False
    if today.open_time is None or today.close_time is None:
        return False
    return today.open_time <= now.time() < today.close_time


# Makes market_open available in every template for the nav bar badge.
@app.context_processor
def inject_market_status():
    return {'market_open': is_market_open()}

# Shows the sign-up form. On submit it checks the fields, saves a new
# customer with a hashed password and $0.00 cash, and logs them in.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not full_name or not email or not username or not password:
            flash('Please fill in every field.', 'danger')
        elif User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('That email is already used.', 'danger')
        else:
            try:
                hashed = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = User(full_name=full_name, email=email, username=username,
                                password=hashed, role='user', cash_balance=0)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                return redirect('/')
            except Exception:
                db.session.rollback()
                flash('Something went wrong. Please try again.', 'danger')

        # An error happened, so show the form again with what they typed
        return render_template('register.html', full_name=full_name, email=email, username=username)

    return render_template('register.html')


# Shows the login form. On submit it checks the password and sends
# customers to their dashboard and admins to Manage Stocks.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect('/admin/stocks')
            return redirect('/')

        # One general message so nobody can tell which part was wrong
        flash('Wrong username or password.', 'danger')
        return render_template('login.html', username=username)

    return render_template('login.html')


# Ends the session and returns to the login page.
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')
