import os
import random
from datetime import datetime, timezone
from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'borsa-simulasyonu-gizli-anahtar-1923'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///borsa.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Bu sayfaya erişebilmek için lütfen giriş yapın.'
login_manager.login_message_category = 'warning'
login_manager.init_app(app)

# ==============================================================================
# DATABASE MODELS
# ==============================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    available_cash = db.Column(db.Float, default=100000.0, nullable=False)
    portfolio_items = db.relationship('Portfolio', backref='user', cascade='all, delete-orphan', lazy=True)
    transactions = db.relationship('TransactionHistory', backref='user', cascade='all, delete-orphan', lazy=True)

class PriceHistory(db.Model):
    __tablename__ = 'price_histories'
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Stock(db.Model):
    __tablename__ = 'stocks'
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(10), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(128), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    sector = db.Column(db.String(64), nullable=True)
    pe_ratio = db.Column(db.Float, nullable=True)
    asset_type = db.Column(db.String(20), default='stock', nullable=False) # 'stock' or 'crypto'
    portfolio_items = db.relationship('Portfolio', backref='stock', cascade='all, delete-orphan', lazy=True)
    transactions = db.relationship('TransactionHistory', backref='stock', cascade='all, delete-orphan', lazy=True)
    price_history = db.relationship('PriceHistory', backref='stock', cascade='all, delete-orphan', lazy=True)

class NewsFeed(db.Model):
    __tablename__ = 'news_feeds'
    id = db.Column(db.Integer, primary_key=True)
    headline = db.Column(db.String(256), nullable=False)
    news_type = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    average_cost = db.Column(db.Float, default=0.0, nullable=False)

class TransactionHistory(db.Model):
    __tablename__ = 'transaction_histories'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==============================================================================
# DATABASE SEEDING
# ==============================================================================
def seed_stocks():
    default_stocks = [
        # Original Stocks
        {"ticker": "THYAO", "company_name": "Türk Hava Yolları A.O.", "current_price": 315.00, "sector": "Ulaşım / Havacılık", "pe_ratio": 4.85, "asset_type": "stock"},
        {"ticker": "ASELS", "company_name": "Aselsan Elektronik Sanayi", "current_price": 55.00, "sector": "Savunma / Teknoloji", "pe_ratio": 12.40, "asset_type": "stock"},
        {"ticker": "EREGL", "company_name": "Ereğli Demir ve Çelik Fabrikaları", "current_price": 42.00, "sector": "Ağır Sanayi / Demir-Çelik", "pe_ratio": 18.10, "asset_type": "stock"},
        {"ticker": "GARAN", "company_name": "Türkiye Garanti Bankası A.Ş.", "current_price": 80.00, "sector": "Finans / Bankacılık", "pe_ratio": 3.15, "asset_type": "stock"},
        {"ticker": "TUPRS", "company_name": "Tüpraş Türkiye Petrol Rafinerileri", "current_price": 135.00, "sector": "Enerji / Petrol", "pe_ratio": 6.50, "asset_type": "stock"},
        
        # 10 More Stocks
        {"ticker": "AKBNK", "company_name": "Akbank T.A.Ş.", "current_price": 60.00, "sector": "Finans / Bankacılık", "pe_ratio": 3.50, "asset_type": "stock"},
        {"ticker": "BAMBI", "company_name": "Bambi Mağazacılık A.Ş.", "current_price": 380.00, "sector": "Perakende / Gıda", "pe_ratio": 14.20, "asset_type": "stock"},
        {"ticker": "FROTO", "company_name": "Ford Otomotiv Sanayi A.Ş.", "current_price": 1050.00, "sector": "Otomotiv / Sanayi", "pe_ratio": 9.80, "asset_type": "stock"},
        {"ticker": "KCHOL", "company_name": "Koç Holding A.Ş.", "current_price": 210.00, "sector": "Holdingler / Yatırım", "pe_ratio": 4.10, "asset_type": "stock"},
        {"ticker": "PETKM", "company_name": "Petkim Petrokimya Holding A.Ş.", "current_price": 22.00, "sector": "Kimya / Petrokimya", "pe_ratio": 11.60, "asset_type": "stock"},
        {"ticker": "PGSUS", "company_name": "Pegasus Hava Taşımacılığı A.Ş.", "current_price": 230.00, "sector": "Ulaşım / Havacılık", "pe_ratio": 5.20, "asset_type": "stock"},
        {"ticker": "SAHOL", "company_name": "Hacı Ömer Sabancı Holding A.Ş.", "current_price": 85.00, "sector": "Holdingler / Yatırım", "pe_ratio": 3.80, "asset_type": "stock"},
        {"ticker": "SISE", "company_name": "Türkiye Şişe ve Cam Fabrikaları", "current_price": 50.00, "sector": "Cam Sanayi / Üretim", "pe_ratio": 8.30, "asset_type": "stock"},
        {"ticker": "TCELL", "company_name": "Turkcell İletişim Hizmetleri A.Ş.", "current_price": 75.00, "sector": "Telekomünikasyon", "pe_ratio": 10.15, "asset_type": "stock"},
        {"ticker": "VESTL", "company_name": "Vestel Elektronik Sanayi A.Ş.", "current_price": 65.00, "sector": "Dayanıklı Tüketim / Teknoloji", "pe_ratio": 7.90, "asset_type": "stock"},

        # Original Crypto
        {"ticker": "BTC", "company_name": "Bitcoin (BTC)", "current_price": 2200000.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "ETH", "company_name": "Ethereum (ETH)", "current_price": 110000.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "SOL", "company_name": "Solana (SOL)", "current_price": 5400.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        
        # 5 More Crypto
        {"ticker": "AVAX", "company_name": "Avalanche (AVAX)", "current_price": 35.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "BNB", "company_name": "Binance Coin (BNB)", "current_price": 580.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "DOGE", "company_name": "Dogecoin (DOGE)", "current_price": 0.15, "sector": "Kripto Para / Memes", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "DOT", "company_name": "Polkadot (DOT)", "current_price": 6.50, "sector": "Kripto Para / Web3", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "XRP", "company_name": "Ripple (XRP)", "current_price": 0.55, "sector": "Kripto Para / Ödemeler", "pe_ratio": None, "asset_type": "crypto"}
    ]
    if db.session.query(Stock).count() == 0:
        for s in default_stocks:
            stock = Stock(ticker=s["ticker"], company_name=s["company_name"], current_price=s["current_price"], sector=s["sector"], pe_ratio=s["pe_ratio"], asset_type=s["asset_type"])
            db.session.add(stock)
            db.session.flush()
            base_p = s["current_price"]
            for i in range(5):
                hist_p = round(base_p * (1 + random.uniform(-2, 2) / 100), 2)
                ph = PriceHistory(stock_id=stock.id, price=hist_p)
                db.session.add(ph)
        db.session.commit()

def seed_bots():
    bot_configs = [
        {"username": "Balina_Ahmet", "cash": 2500000.0},
        {"username": "Shark_Trader", "cash": 500000.0},
        {"username": "Kripto_Kralı", "cash": 1200000.0}
    ]
    for cfg in bot_configs:
        bot = db.session.scalar(db.select(User).filter_by(username=cfg["username"]))
        if not bot:
            hashed = generate_password_hash("bot-sifre-1923")
            new_bot = User(username=cfg["username"], password_hash=hashed, available_cash=cfg["cash"])
            db.session.add(new_bot)
    db.session.commit()

# Self-recreation block for safe zero-conflict upgrades
with app.app_context():
    try:
        db.create_all()
        # Verify schema integrity (forces drop if asset_type or newer assets are missing)
        count = db.session.query(Stock).count()
        if count < 23: # We upgraded from 8 to 23 assets total
            raise ValueError("Upgrading asset database to support extended assets list.")
        db.session.query(Stock).filter_by(ticker='AKBNK').first()
    except Exception:
        db.session.rollback()
        db.drop_all()
        db.create_all()
    seed_stocks()
    seed_bots()

# ==============================================================================
# HTML AUTHENTICATION INLINE TEMPLATES
# ==============================================================================
BASE_CSS = """
:root {
    --bg-primary: #080c14; --bg-surface: rgba(17, 24, 39, 0.7); --bg-input: rgba(10, 15, 26, 0.8);
    --border-color: rgba(255, 255, 255, 0.08); --text-primary: #f3f4f6; --text-secondary: #9ca3af;
    --color-accent: #6366f1; --color-success: #10b981; --color-danger: #ef4444; --color-gold: #f59e0b;
}
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', system-ui, sans-serif; }
body { background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, var(--bg-primary) 75%); color: var(--text-primary); min-height: 100vh; display: flex; flex-direction: column; overflow-x: hidden; }
.glass-card { background: var(--bg-surface); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--border-color); border-radius: 16px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); }
.btn { display: inline-flex; align-items: center; justify-content: center; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; border: none; text-decoration: none; font-size: 0.9rem; }
.btn-primary { background: linear-gradient(135deg, var(--color-accent), #4f46e5); color: white; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); }
.alert-container { width: 100%; margin-bottom: 1.5rem; }
.alert { padding: 0.85rem 1.25rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 4px solid; font-size: 0.88rem; font-weight: 500; animation: slideIn 0.3s ease; }
.alert-success { background: rgba(16, 185, 129, 0.12); border-color: var(--color-success); color: #34d399; }
.alert-danger { background: rgba(239, 68, 68, 0.12); border-color: var(--color-danger); color: #fca5a5; }
.alert-warning { background: rgba(245, 158, 11, 0.12); border-color: var(--color-gold); color: #fcd34d; }
@keyframes slideIn { from { transform: translateY(-10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
"""

AUTH_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Borsa Simülasyonu Oyunu</title>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
    <style>
        {{ base_css|safe }}
        .auth-container { display: flex; align-items: center; justify-content: center; flex-grow: 1; padding: 2rem; }
        .auth-card { width: 100%; max-width: 440px; padding: 2.5rem; }
        .auth-header { text-align: center; margin-bottom: 2rem; }
        .auth-header h1 { font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #a5b4fc, #6366f1); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
        .auth-header p { color: var(--text-secondary); font-size: 0.9rem; }
        .form-group { margin-bottom: 1.25rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }
        .form-control { width: 100%; padding: 0.75rem 1rem; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 8px; color: white; font-size: 0.95rem; transition: all 0.2s ease; }
        .form-control:focus { outline: none; border-color: var(--color-accent); box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25); background: rgba(31, 41, 55, 0.8); }
        .auth-footer { margin-top: 1.5rem; text-align: center; font-size: 0.85rem; color: var(--text-secondary); }
        .auth-footer a { color: var(--color-accent); text-decoration: none; font-weight: 600; }
        .auth-footer a:hover { color: #818cf8; text-decoration: underline; }
    </style>
</head>
<body>
    <div class="auth-container">
        <div class="glass-card auth-card">
            <div class="auth-header">
                <h1>📈 Borsa Simülasyonu</h1>
                <p>{{ 'Hemen kaydol ve 100.000 TL sanal sermaye ile borsaya gir!' if is_register else 'Finansal zekanı test etmeye hemen başla' }}</p>
            </div>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    <div class="alert-container">
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    </div>
                {% endif %}
            {% endwith %}
            <form method="POST" action="{{ url_for('register') if is_register else url_for('login') }}">
                <div class="form-group">
                    <label for="username">Kullanıcı Adı</label>
                    <input type="text" id="username" name="username" class="form-control" placeholder="kullanıcı adınız..." required autocomplete="off">
                </div>
                <div class="form-group">
                    <label for="password">Şifre</label>
                    <input type="password" id="password" name="password" class="form-control" placeholder="şifreniz..." required autocomplete="off">
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">
                    {{ 'Kayıt İşlemini Tamamla' if is_register else 'Giriş Yap' }}
                </button>
            </form>
            <div class="auth-footer">
                {% if is_register %}
                    Zaten hesabınız var mı? <a href="{{ url_for('login') }}">Giriş Yapın</a>
                {% else %}
                    Henüz hesabınız yok mu? <a href="{{ url_for('register') }}">Yeni Hesap Oluşturun</a>
                {% endif %}
            </div>
        </div>
    </div>
</body>
</html>
"""

# ==============================================================================
# ROUTE HANDLERS
# ==============================================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            flash('Kullanıcı adı ve şifre gereklidir.', 'danger')
            return render_template_string(AUTH_TEMPLATE, base_css=BASE_CSS, is_register=True)
        existing_user = db.session.scalar(db.select(User).filter_by(username=username))
        if existing_user:
            flash('Bu kullanıcı adı zaten alınmış. Lütfen başka bir tane seçin.', 'danger')
            return render_template_string(AUTH_TEMPLATE, base_css=BASE_CSS, is_register=True)
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password, available_cash=100000.0)
        db.session.add(new_user)
        db.session.commit()
        flash('Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template_string(AUTH_TEMPLATE, base_css=BASE_CSS, is_register=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Hoş geldiniz, {user.username}! Borsada kazançlı günler dileriz.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
    return render_template_string(AUTH_TEMPLATE, base_css=BASE_CSS, is_register=False)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Güvenli bir şekilde çıkış yaptınız. Tekrar görüşmek üzere!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    news_feed = db.session.scalars(db.select(NewsFeed).order_by(NewsFeed.timestamp.desc())).all()
    stocks = db.session.scalars(db.select(Stock).order_by(Stock.ticker)).all()
    
    news_item = news_feed[0] if news_feed else None
    
    stocks_data = []
    crypto_data = []
    
    for stock in stocks:
        prices_records = db.session.scalars(
            db.select(PriceHistory)
            .filter_by(stock_id=stock.id)
            .order_by(PriceHistory.timestamp.asc())
        ).all()
        history_prices = [ph.price for ph in prices_records][-10:]
        if not history_prices:
            history_prices = [stock.current_price]
            
        asset_obj = {
            'id': stock.id, 'ticker': stock.ticker, 'company_name': stock.company_name,
            'current_price': stock.current_price, 'sector': stock.sector, 'pe_ratio': stock.pe_ratio,
            'history': history_prices, 'asset_type': stock.asset_type
        }
        
        if stock.asset_type == 'crypto':
            crypto_data.append(asset_obj)
        else:
            stocks_data.append(asset_obj)
    
    # Portfolio details
    total_portfolio_value = 0
    portfolio_details = []
    for item in current_user.portfolio_items:
        stock = item.stock
        current_value = item.quantity * stock.current_price
        total_portfolio_value += current_value
        total_cost = item.quantity * item.average_cost
        profit_loss = current_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
        portfolio_details.append({
            'ticker': stock.ticker,
            'quantity': item.quantity,
            'average_cost': item.average_cost,
            'current_price': stock.current_price,
            'current_value': current_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        })
        
    total_wealth = current_user.available_cash + total_portfolio_value
    
    # Global Leaderboard Calculations
    all_users = db.session.scalars(db.select(User)).all()
    leaderboard = []
    for u in all_users:
        u_portfolio_val = 0
        for item in u.portfolio_items:
            u_portfolio_val += item.quantity * item.stock.current_price
        u_wealth = u.available_cash + u_portfolio_val
        
        is_bot = u.username in ["Balina_Ahmet", "Shark_Trader", "Kripto_Kralı"]
        role = "🤖 BALİNA" if is_bot else "🛡️ OYUNCU"
        if u.id == current_user.id:
            role = "⭐ SEN"
            
        leaderboard.append({
            'username': u.username,
            'wealth': u_wealth,
            'role': role,
            'is_current': u.id == current_user.id
        })
    leaderboard = sorted(leaderboard, key=lambda x: x['wealth'], reverse=True)
    
    return render_template(
        'dashboard.html',
        stocks=stocks_data, crypto_stocks=crypto_data, portfolio_details=portfolio_details,
        total_portfolio_value=total_portfolio_value, total_wealth=total_wealth,
        news_item=news_item, news_feed=news_feed, leaderboard=leaderboard
    )

@app.route('/api/market-tick')
@login_required
def market_tick():
    NEWS_POOL = [
        {"ticker": "THYAO", "type": "positive", "headline": "THYAO bu çeyrekte rekor kâr açıkladı! Yatırımcıların ilgisi havacılık sektörüne kayıyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "THYAO", "type": "negative", "headline": "Küresel jet yakıtı fiyatlarındaki artış havacılık maliyetlerini yükseltti, THYAO hisseleri baskı altında.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "ASELS", "type": "positive", "headline": "ASELSAN yeni bir dev ihracat anlaşmasına imza attı! Sipariş defteri rekor seviyede.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "ASELS", "type": "negative", "headline": "ASELSAN küresel tedarik zinciri aksamaları nedeniyle üretimde yavaşlama riskiyle karşı karşıya.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "EREGL", "type": "positive", "headline": "Küresel çelik talebindeki canlanma ve artan ürün fiyatları EREGL kârlılığını uçuruyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "EREGL", "type": "negative", "headline": "İnşaat sektöründeki küresel durgunluk demir-çelik talebini vurdu, EREGL hisseleri gevşiyor.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "GARAN", "type": "positive", "headline": "Bankacılık endeksindeki genel yükseliş ve faiz marjlarındaki iyileşme GARAN hisselerini destekliyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "GARAN", "type": "negative", "headline": "Kredi temerrüt risklerindeki genel artış bankacılık sektörünü endişelendiriyor, GARAN değer kaybetti.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "TUPRS", "type": "positive", "headline": "Tüpraş güçlü rafineri marjları ve yüksek kapasite kullanım oranıyla hedeflerin üzerinde performans gösterdi.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "TUPRS", "type": "negative", "headline": "Tüpraş'ın ana rafinerilerinden birinde yapılan planlı bakım çalışması üretimi geçici olarak yavaşlattı.", "min_change": -8.5, "max_change": -4.5},
        
        # News items for 10 New Stocks
        {"ticker": "AKBNK", "type": "positive", "headline": "Akbank dijital bankacılık alanında rekor yeni müşteri kazandı, kâr beklentileri aşıldı!", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "AKBNK", "type": "negative", "headline": "Akbank'ın dijital altyapısında geçici bir teknik aksaklık yaşandı, işlemler kısa süreli yavaşladı.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "BAMBI", "type": "positive", "headline": "BAMBI Mağazaları yurt genelinde 50 yeni şube açacağını duyurdu! Ciro hedefleri yükseltildi.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "BAMBI", "type": "negative", "headline": "Gıda ve perakende sektörüne gelen tedarik maliyetleri BAMBI mağaza kâr marjlarını daralttı.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "FROTO", "type": "positive", "headline": "Ford Otosan elektrikli araç fabrikasında üretime başladı! Dev ihracat anlaşması kapıda.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "FROTO", "type": "negative", "headline": "Küresel otomotiv chip krizi FROTO üretim bantlarında geçici yavaşlamaya neden oldu.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "KCHOL", "type": "positive", "headline": "Koç Holding yenilenebilir enerji yatırımlarıyla yabancı fonların ilgi odağı oldu.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "KCHOL", "type": "negative", "headline": "KCHOL iştiraklerinden birinde grev kararı alındığı iddiaları hisseyi kısa vadeli baskıladı.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "PETKM", "type": "positive", "headline": "Petkim kapasite kullanım oranını %98'e çıkardı! Etilen fiyat artışı kârı uçuruyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "PETKM", "type": "negative", "headline": "PETKM tesislerinde yapılan planlı bakım duruşu nedeniyle üretim hacminde düşüş bekleniyor.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "PGSUS", "type": "positive", "headline": "Pegasus yeni sezon uçuş planlamalarında doluluk oranını %92 olarak açıkladı! PGSUS uçuşta.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "PGSUS", "type": "negative", "headline": "Avrupa hava sahasındaki grevler Pegasus'un bazı dış hat uçuşlarında iptallere yol açtı.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "SAHOL", "type": "positive", "headline": "Sabancı Holding dış gelirlerini ikiye katladı! Enerji iştirakleri SAHOL'ü destekliyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "SAHOL", "type": "negative", "headline": "Holding bünyesindeki bazı yatırımlarda kâr realizasyonu yapılması SAHOL'ü hafif gevşetti.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "SISE", "type": "positive", "headline": "Şişecam küresel cam pazarında payını %12'ye yükseltti! Rekor ihracat açıklandı.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "SISE", "type": "negative", "headline": "Sanayi doğalgaz fiyatlarındaki artış SISE fırınlarının üretim maliyetlerini yükseltti.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "TCELL", "type": "positive", "headline": "Turkcell 5G altyapı lisanslamasında öncü rol kaparak abone sayısını rekor düzeyde artırdı.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "TCELL", "type": "negative", "headline": "Telekomünikasyon sektöründeki yeni düzenlemeler Turkcell net kârını hafif baskıladı.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "VESTL", "type": "positive", "headline": "Vestel akıllı TV ihracatında Avrupa pazar liderliğini perçinledi! Siparişler rekor seviyede.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "VESTL", "type": "negative", "headline": "Euro/Dolar paritesindeki dalgalanmalar Vestel'in ihracat kârlılığını baskılıyor.", "min_change": -8.5, "max_change": -4.5},

        # Crypto news
        {"ticker": "BTC", "type": "positive", "headline": "ABD Menkul Kıymetler Komisyonu SEC, spot Bitcoin ETF'lerini onayladı! Bitcoin roketlendi.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "BTC", "type": "negative", "headline": "Merkez bankalarından kripto varlıklara ağır vergi taslağı! Bitcoin sert satış yedi.", "min_change": -25.0, "max_change": -15.0},
        {"ticker": "ETH", "type": "positive", "headline": "Ethereum ağındaki 'Sharding' güncellemesi gaz ücretlerini sıfıra indirdi! ETH talebi uçuyor.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "ETH", "type": "negative", "headline": "Vitalik Buterin'in sosyal medya hesabı ele geçirildi, ETH piyasasında panik hakim.", "min_change": -25.0, "max_change": -15.0},
        {"ticker": "SOL", "type": "positive", "headline": "Elon Musk, Solana tabanlı yeni projeleri övdü! SOL çılgınlığı başladı.", "min_change": 18.0, "max_change": 30.0},
        {"ticker": "SOL", "type": "negative", "headline": "Solana ağ doğrulayıcılarında çıkan hata nedeniyle Solana zinciri durdu! SOL değer kaybediyor.", "min_change": -30.0, "max_change": -18.0},
        
        # News items for 5 New Cryptos
        {"ticker": "AVAX", "type": "positive", "headline": "Avalanche ağında saniyede 100 bin işlem sunan devasa alt ağ aktif oldu! AVAX patlama yaptı.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "AVAX", "type": "negative", "headline": "AVAX köprü protokolünde teknik açık iddiaları yatırımcılarda panik satışı tetikledi.", "min_change": -25.0, "max_change": -15.0},
        {"ticker": "BNB", "type": "positive", "headline": "Binance BNB yakım programını tamamlayarak dolaşımdan 2 milyar dolarlık BNB sildi! Deflasyon başladı.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "BNB", "type": "negative", "headline": "Binance borsasına karşı yeni küresel soruşturma açıldığı iddiaları BNB fiyatını sarstı.", "min_change": -25.0, "max_change": -15.0},
        {"ticker": "DOGE", "type": "positive", "headline": "Elon Musk, X platformunda DOGE ile ödeme yapılabilmesi için lisans aldıklarını doğruladı! DOGE uçtu.", "min_change": 18.0, "max_change": 30.0},
        {"ticker": "DOGE", "type": "negative", "headline": "Büyük bir balina elindeki 1 milyar adet Dogecoin'i borsaya transfer etti, panik satışı yayıldı.", "min_change": -30.0, "max_change": -18.0},
        {"ticker": "DOT", "type": "positive", "headline": "Polkadot 2.0 lansmanı ile parachain ücretleri sıfırlandı! DOT ağında talep patlıyor.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "DOT", "type": "negative", "headline": "Polkadot ekosistemindeki dev projelerin rakip zincire göçeceği söylentisi DOT'u zayıflattı.", "min_change": -25.0, "max_change": -15.0},
        {"ticker": "XRP", "type": "positive", "headline": "Ripple SEC davasını kesin zaferle tamamladı! Bankaların XRP entegrasyonu resmen başladı.", "min_change": 15.0, "max_change": 25.0},
        {"ticker": "XRP", "type": "negative", "headline": "Ripple kurucu ortağının büyük miktarda XRP sattığı iddiaları tahtada satış getirdi.", "min_change": -25.0, "max_change": -15.0}
    ]
    
    has_news = random.random() < 0.35
    news_item = None
    if has_news:
        news_item = random.choice(NEWS_POOL)
        news_feed_entry = NewsFeed(headline=news_item["headline"], news_type=news_item["type"])
        db.session.add(news_feed_entry)
        db.session.commit()
        
        news_count = db.session.query(NewsFeed).count()
        if news_count > 5:
            oldest_news = db.session.query(NewsFeed).order_by(NewsFeed.timestamp.asc()).limit(news_count - 5).all()
            for old_n in oldest_news:
                db.session.delete(old_n)
            db.session.commit()
            
    # Fluctuate Prices
    stocks = db.session.scalars(db.select(Stock).order_by(Stock.ticker)).all()
    for stock in stocks:
        if news_item and stock.ticker == news_item["ticker"]:
            change_pct = random.uniform(news_item["min_change"], news_item["max_change"])
        else:
            if stock.asset_type == 'crypto':
                # Crypto Volatility -15% to +15%
                change_pct = random.uniform(-15.0, 15.0)
            else:
                # Stock Volatility -2.5% to +2.5%
                change_pct = random.uniform(-2.5, 2.5)
            
        old_price = float(stock.current_price)
        new_price = max(0.01, round(old_price * (1 + change_pct / 100), 2))
        stock.current_price = new_price
        
        ph = PriceHistory(stock_id=stock.id, price=new_price)
        db.session.add(ph)
        db.session.commit()
        
        history_count = db.session.query(PriceHistory).filter_by(stock_id=stock.id).count()
        if history_count > 30:
            oldest_prices = db.session.query(PriceHistory).filter_by(stock_id=stock.id).order_by(PriceHistory.timestamp.asc()).limit(history_count - 30).all()
            for old_p in oldest_prices:
                db.session.delete(old_p)
            db.session.commit()
            
    # Simulate Bot Trading
    bot_usernames = ["Balina_Ahmet", "Shark_Trader", "Kripto_Kralı"]
    bot_txs = []
    
    for bot_username in bot_usernames:
        if random.random() < 0.35:
            bot_user = db.session.scalar(db.select(User).filter_by(username=bot_username))
            if bot_user:
                target_stock = random.choice(stocks)
                portfolio_item = db.session.scalar(db.select(Portfolio).filter_by(user_id=bot_user.id, stock_id=target_stock.id))
                
                action = 'BUY'
                if portfolio_item and portfolio_item.quantity > 0:
                    action = random.choice(['BUY', 'SELL'])
                    
                if action == 'BUY':
                    trade_cash = bot_user.available_cash * random.uniform(0.01, 0.05)
                    qty = int(trade_cash / target_stock.current_price)
                    if qty > 0:
                        cost = qty * target_stock.current_price
                        bot_user.available_cash -= cost
                        if portfolio_item:
                            portfolio_item.quantity += qty
                            portfolio_item.average_cost = ((portfolio_item.quantity * portfolio_item.average_cost) + cost) / portfolio_item.quantity
                        else:
                            new_item = Portfolio(user_id=bot_user.id, stock_id=target_stock.id, quantity=qty, average_cost=target_stock.current_price)
                            db.session.add(new_item)
                        
                        tx = TransactionHistory(user_id=bot_user.id, stock_id=target_stock.id, transaction_type='AL', quantity=qty, price=target_stock.current_price)
                        db.session.add(tx)
                        
                        qty_fmt = f"{qty:,}".replace(",", ".")
                        bot_txs.append(f"🐳 <strong>{bot_username}</strong>, {qty_fmt} adet <strong>{target_stock.ticker}</strong> satın aldı!")
                else:
                    qty_to_sell = int(portfolio_item.quantity * random.uniform(0.1, 0.5))
                    if qty_to_sell > 0:
                        revenue = qty_to_sell * target_stock.current_price
                        bot_user.available_cash += revenue
                        portfolio_item.quantity -= qty_to_sell
                        if portfolio_item.quantity == 0:
                            db.session.delete(portfolio_item)
                            
                        tx = TransactionHistory(user_id=bot_user.id, stock_id=target_stock.id, transaction_type='SAT', quantity=qty_to_sell, price=target_stock.current_price)
                        db.session.add(tx)
                        
                        qty_fmt = f"{qty_to_sell:,}".replace(",", ".")
                        bot_txs.append(f"🐋 <strong>{bot_username}</strong>, {qty_fmt} adet <strong>{target_stock.ticker}</strong> sattı!")
                        
    db.session.commit()
            
    # Fetch Database Snapshots
    news_feed_records = db.session.scalars(db.select(NewsFeed).order_by(NewsFeed.timestamp.desc())).all()
    news_feed_data = [{
        'headline': n.headline,
        'news_type': n.news_type,
        'time': n.timestamp.strftime('%H:%M:%S')
    } for n in news_feed_records]
    
    stocks_data = []
    for stock in stocks:
        prices_records = db.session.scalars(
            db.select(PriceHistory)
            .filter_by(stock_id=stock.id)
            .order_by(PriceHistory.timestamp.asc())
        ).all()
        history_prices = [ph.price for ph in prices_records]
        stocks_data.append({
            'id': stock.id,
            'ticker': stock.ticker,
            'company_name': stock.company_name,
            'current_price': stock.current_price,
            'history': history_prices[-10:],
            'full_history': history_prices,
            'asset_type': stock.asset_type
        })
        
    # Recalculate Portfolio Values for User
    total_portfolio_value = 0
    portfolio_details = []
    for item in current_user.portfolio_items:
        stock = item.stock
        current_value = item.quantity * stock.current_price
        total_portfolio_value += current_value
        total_cost = item.quantity * item.average_cost
        profit_loss = current_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
        portfolio_details.append({
            'ticker': stock.ticker,
            'quantity': item.quantity,
            'average_cost': item.average_cost,
            'current_price': stock.current_price,
            'current_value': current_value,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct
        })
        
    total_wealth = current_user.available_cash + total_portfolio_value
    
    # Recalculate Leaderboard
    all_users = db.session.scalars(db.select(User)).all()
    leaderboard = []
    for u in all_users:
        u_portfolio_val = 0
        for item in u.portfolio_items:
            u_portfolio_val += item.quantity * item.stock.current_price
        u_wealth = u.available_cash + u_portfolio_val
        
        is_bot = u.username in ["Balina_Ahmet", "Shark_Trader", "Kripto_Kralı"]
        role = "🤖 BALİNA" if is_bot else "🛡️ OYUNCU"
        if u.id == current_user.id:
            role = "⭐ SEN"
            
        leaderboard.append({
            'username': u.username,
            'wealth': u_wealth,
            'role': role,
            'is_current': u.id == current_user.id
        })
    leaderboard = sorted(leaderboard, key=lambda x: x['wealth'], reverse=True)
    
    return jsonify({
        'stocks': stocks_data,
        'news_item': news_item,
        'news_feed': news_feed_data,
        'user_cash': current_user.available_cash,
        'user_portfolio_value': total_portfolio_value,
        'user_wealth': total_wealth,
        'portfolio_details': portfolio_details,
        'leaderboard': leaderboard,
        'bot_activity': bot_txs
    })

@app.route('/api/ai-advice')
@login_required
def ai_advice():
    user_cash = current_user.available_cash
    portfolio_items = current_user.portfolio_items
    
    total_portfolio_value = 0
    owned_stocks = {}
    for item in portfolio_items:
        stock = item.stock
        current_value = item.quantity * stock.current_price
        total_portfolio_value += current_value
        owned_stocks[stock.ticker] = {
            'quantity': item.quantity,
            'average_cost': item.average_cost,
            'current_price': stock.current_price,
            'current_value': current_value
        }
    
    total_wealth = user_cash + total_portfolio_value
    
    recent_news = db.session.scalars(
        db.select(NewsFeed).order_by(NewsFeed.timestamp.desc()).limit(3)
    ).all()
    
    def format_tl_py(val):
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
    all_stocks = db.session.scalars(db.select(Stock).order_by(Stock.ticker)).all()
    
    # 1. State Analysis
    analysis_intro = "💼 **Portföy & Nakit Analizi:**<br>"
    if total_portfolio_value == 0:
        analysis_intro += f"Cüzdanına bakıyorum da... Sıfır hisse, **{format_tl_py(user_cash)} TL** nakit bakiye! Dostum, bu kadar nakitle beklemek enflasyon canavarına kurban gitmektir. Borsada derler ki: 'Kenarda duran para kazandırmaz, sadece paslanır.' Haber rüzgarını arkasına alan hisselerden kademeli olarak alıma başlamalıyız."
    else:
        cash_ratio = user_cash / total_wealth if total_wealth > 0 else 0
        if cash_ratio > 0.7:
            analysis_intro += f"Kasada çok güçlü bir nakit barutu yatıyor: **{format_tl_py(user_cash)} TL** nakit (%{cash_ratio*100:.1f} likidite)! Bu yüksek nakit oranı ani düşüşlerde dip avcılığı yapmak için harika bir cephane. Ancak yükseliş boğa trendini kaçırıyor olabiliriz. Portföy değerin **{format_tl_py(total_portfolio_value)} TL** seviyesinde, kademeli alımlarla bu değeri büyütmeliyiz."
        elif cash_ratio < 0.1:
            analysis_intro += f"Dostum, nakit rezervlerin **{format_tl_py(user_cash)} TL** seviyesine kadar erimiş (%{cash_ratio*100:.1f} nakit)! Tüm kurşunları hisselere sürmüşsün. Portföyün **{format_tl_py(total_portfolio_value)} TL** değerinde. Olası sert dalgalanmalarda veya yeni fırsatlarda manevra alanın kalmamış. Kârda olan bazı tahtalarda ufak realizasyonlar yapıp yedek akçe (nakit) biriktirmek akıllıca olabilir."
        else:
            analysis_intro += f"Nakit dengen harika! **{format_tl_py(user_cash)} TL** nakit ve **{format_tl_py(total_portfolio_value)} TL** portföy değerin var. Hem masada aktif olarak boğa koşusuna katılmış durumdasın, hem de ani fırsatları yakalayacak kurşunun hazır."
            
        # Concentration risk check
        for ticker, data in owned_stocks.items():
            holding_ratio = data['current_value'] / total_portfolio_value if total_portfolio_value > 0 else 0
            if holding_ratio > 0.6:
                analysis_intro += f"<br><br>⚠️ **KONSANTRASYON RİSKİ!** Portföyünün tam **%{holding_ratio*100:.1f}**'i tek başına **{ticker}** hissesinde yoğunlaşmış! Yumurtaları tek sepete koymak cesurca ama riskli. Riski yaymak için bankacılık (GARAN) veya sanayi (EREGL) gibi alternatif hisselere yönelmelisin."
                break
                
    # 2. News Feed Correlation
    news_analysis = "<br><br>📰 **Haber Akışı & Pazar Korelasyonu:**"
    opportunity_ticker = None
    stoploss_ticker = None
    
    if not recent_news:
        news_analysis += "<br>Piyasada şu an yaprak kımıldamıyor, büyük bir haber akışı yok. Bu durum, hisselerin kendi doğal teknik analiz bandında hareket ettiği sakin dönemlerdir."
    else:
        for idx, news in enumerate(recent_news):
            news_ticker = None
            for s in all_stocks:
                if s.ticker in news.headline or s.company_name.split()[0] in news.headline:
                    news_ticker = s.ticker
                    break
            
            if not news_ticker:
                if "THYAO" in news.headline or "Hava Yolları" in news.headline: news_ticker = "THYAO"
                elif "ASELS" in news.headline or "ASELSAN" in news.headline: news_ticker = "ASELS"
                elif "EREGL" in news.headline or "Ereğli" in news.headline: news_ticker = "EREGL"
                elif "GARAN" in news.headline or "Garanti" in news.headline: news_ticker = "GARAN"
                elif "TUPRS" in news.headline or "Tüpraş" in news.headline: news_ticker = "TUPRS"
                elif "AKBNK" in news.headline or "Akbank" in news.headline: news_ticker = "AKBNK"
                elif "BAMBI" in news.headline or "Bambi" in news.headline: news_ticker = "BAMBI"
                elif "FROTO" in news.headline or "Ford" in news.headline: news_ticker = "FROTO"
                elif "KCHOL" in news.headline or "Koç" in news.headline: news_ticker = "KCHOL"
                elif "PETKM" in news.headline or "Petkim" in news.headline: news_ticker = "PETKM"
                elif "PGSUS" in news.headline or "Pegasus" in news.headline: news_ticker = "PGSUS"
                elif "SAHOL" in news.headline or "Sabancı" in news.headline: news_ticker = "SAHOL"
                elif "SISE" in news.headline or "Şişecam" in news.headline: news_ticker = "SISE"
                elif "TCELL" in news.headline or "Turkcell" in news.headline: news_ticker = "TCELL"
                elif "VESTL" in news.headline or "Vestel" in news.headline: news_ticker = "VESTL"
                elif "BTC" in news.headline or "Bitcoin" in news.headline: news_ticker = "BTC"
                elif "ETH" in news.headline or "Ethereum" in news.headline: news_ticker = "ETH"
                elif "SOL" in news.headline or "Solana" in news.headline: news_ticker = "SOL"
                elif "AVAX" in news.headline or "Avalanche" in news.headline: news_ticker = "AVAX"
                elif "BNB" in news.headline or "Binance" in news.headline: news_ticker = "BNB"
                elif "DOGE" in news.headline or "Dogecoin" in news.headline: news_ticker = "DOGE"
                elif "DOT" in news.headline or "Polkadot" in news.headline: news_ticker = "DOT"
                elif "XRP" in news.headline or "Ripple" in news.headline: news_ticker = "XRP"
            
            if news_ticker:
                is_positive = news.news_type == "positive"
                is_owned = news_ticker in owned_stocks
                badge = "🟢 OLUMLU" if is_positive else "🔴 OLUMSUZ"
                
                news_analysis += f"<br>• **{news_ticker}** hakkında {badge} bir haber var: *\"{news.headline}\"*"
                
                if is_owned and is_positive:
                    news_analysis += f" -> **Müthiş Zamanlama!** Portföyündeki hisse uçuşta. Trend kırılmadığı sürece yeşil mumların tadını çıkar."
                elif is_owned and not is_positive:
                    news_analysis += f" -> **Risk Uyarısı!** Elindeki hisse baskı altında. Stop-loss yapmayı ya da dip yapmasını beklemeyi düşünebilirsin."
                    stoploss_ticker = news_ticker
                elif not is_owned and is_positive:
                    news_analysis += f" -> **Fırsat Kaçıyor!** Yükseliş treni kalkıyor ama senin cüzdanında yok. Değerlendirilebilir."
                    opportunity_ticker = news_ticker
                elif not is_owned and not is_positive:
                    news_analysis += f" -> **Ucuz Kurtulmuşuz!** Bu hissenin olmaması büyük şans. Fırtına geçene kadar uzak dur."
            else:
                news_analysis += f"<br>• Son dakika: *\"{news.headline}\"*"

    # 3. Final Strategic Actionable Recommendation
    strategy_recommendation = "<br><br>⚡ **Broker Kerem'in Stratejik Reçetesi:**<br>"
    if opportunity_ticker and user_cash > 20000:
        strategy_recommendation += f"Barutumuz var ve **{opportunity_ticker}** tarafında çok güçlü olumlu bir haber rüzgarı esiyor. Tren kaçmadan nakdinin **%20-30**'luk bir kısmıyla bu tahtaya giriş yapıp yükseliş dalgasını yakalamak şu an en mantıklı aksiyon!"
    elif stoploss_ticker and owned_stocks.get(stoploss_ticker, {}).get('quantity', 0) > 0:
        strategy_recommendation += f"Haber akışı kötü gelen ve portföyünü eriten **{stoploss_ticker}** tahtasında pozisyon azaltmak ve korumacı moda geçmek akıllıca olabilir. Likiditeyi koru ve fırtınanın dinmesini bekle."
    elif total_portfolio_value == 0:
        strategy_recommendation += "Hemen piyasanın amiral gemileri olan **THYAO**, **AKBNK** veya yüksek volatilite seviyorsa ufak bir miktar **DOGE**'ye kademeli giriş yap."
    else:
        strategy_recommendation += "Portföyün mevcut dalgalarla gayet iyi başa çıkıyor. Kripto piyasasındaki yüksek oynaklığa dikkat et. Wall Street'te ne derler bilirsin: *'Borsa, sabırsızların parasını sabırlılara aktaran mekanizmadır.'* Nakit dengeni koru ve bir sonraki büyük dalgayı bekle."

    ai_response = f"👔 **Borsa Kaplanı AI Broker Kerem Sunar:**<br><br>{analysis_intro}{news_analysis}{strategy_recommendation}<br><br>*Yatırım Tavsiyesi Değildir (YTD)! Borsada kurşunlarınız tükenmesin dostlar.*"
    return jsonify({"advice": ai_response})

@app.route('/stock/<int:stock_id>')
@login_required
def stock_detail(stock_id):
    stock = db.session.get(Stock, stock_id)
    if not stock:
        flash('Varlık bulunamadı.', 'danger')
        return redirect(url_for('dashboard'))
        
    prices_records = db.session.scalars(
        db.select(PriceHistory)
        .filter_by(stock_id=stock.id)
        .order_by(PriceHistory.timestamp.asc())
    ).all()
    history_prices = [ph.price for ph in prices_records]
    if not history_prices:
        history_prices = [stock.current_price]
        
    all_news = db.session.scalars(db.select(NewsFeed).order_by(NewsFeed.timestamp.desc())).all()
    
    keywords = {
        "THYAO": ["THYAO", "Hava Yolları"],
        "ASELS": ["ASELS", "ASELSAN"],
        "EREGL": ["EREGL", "Ereğli"],
        "GARAN": ["GARAN", "Garanti"],
        "TUPRS": ["TUPRS", "Tüpraş"],
        "AKBNK": ["AKBNK", "Akbank"],
        "BAMBI": ["BAMBI", "Bambi", "Perakende"],
        "FROTO": ["FROTO", "Ford"],
        "KCHOL": ["KCHOL", "Koç"],
        "PETKM": ["PETKM", "Petkim"],
        "PGSUS": ["PGSUS", "Pegasus"],
        "SAHOL": ["SAHOL", "Sabancı"],
        "SISE": ["SISE", "Şişecam"],
        "TCELL": ["TCELL", "Turkcell"],
        "VESTL": ["VESTL", "Vestel"],
        "BTC": ["BTC", "Bitcoin"],
        "ETH": ["ETH", "Ethereum"],
        "SOL": ["SOL", "Solana"],
        "AVAX": ["AVAX", "Avalanche"],
        "BNB": ["BNB", "Binance"],
        "DOGE": ["DOGE", "Dogecoin"],
        "DOT": ["DOT", "Polkadot"],
        "XRP": ["XRP", "Ripple"]
    }
    
    stock_news = []
    for n in all_news:
        match = False
        for kw in keywords.get(stock.ticker, [stock.ticker]):
            if kw.lower() in n.headline.lower():
                match = True
                break
        if match:
            stock_news.append(n)
            
    portfolio_item = db.session.scalar(db.select(Portfolio).filter_by(user_id=current_user.id, stock_id=stock.id))
    owned_qty = portfolio_item.quantity if portfolio_item else 0
    avg_cost = portfolio_item.average_cost if portfolio_item else 0.0
    current_value = owned_qty * stock.current_price
    total_cost = owned_qty * avg_cost
    profit_loss = current_value - total_cost
    profit_loss_pct = (profit_loss / total_cost * 100) if total_cost > 0 else 0.0
    
    portfolio_detail = {
        'quantity': owned_qty,
        'average_cost': avg_cost,
        'current_value': current_value,
        'profit_loss': profit_loss,
        'profit_loss_pct': profit_loss_pct
    }
    
    return render_template(
        'stock_detail.html',
        stock=stock,
        history_prices=history_prices,
        stock_news=stock_news,
        portfolio_detail=portfolio_detail
    )

@app.route('/trade/<int:stock_id>', methods=['POST'])
@login_required
def trade(stock_id):
    action = request.form.get('action', '').upper()
    quantity_str = request.form.get('quantity', '0')
    try:
        quantity = int(quantity_str)
        if quantity <= 0: raise ValueError()
    except ValueError:
        flash('Lütfen geçerli pozitif bir adet girin.', 'danger')
        return redirect(url_for('dashboard'))
        
    stock = db.session.get(Stock, stock_id)
    if not stock:
        flash('Varlık bulunamadı.', 'danger')
        return redirect(url_for('dashboard'))
        
    total_cost = quantity * stock.current_price
    
    if action == 'BUY':
        if current_user.available_cash < total_cost:
            flash(f'Yetersiz Nakit Bakiye! Bedel: {total_cost:.2f} TL, Nakdiniz: {current_user.available_cash:.2f} TL.', 'danger')
            return redirect(url_for('dashboard'))
        current_user.available_cash -= total_cost
        portfolio_item = db.session.scalar(db.select(Portfolio).filter_by(user_id=current_user.id, stock_id=stock.id))
        if portfolio_item:
            total_qty = portfolio_item.quantity + quantity
            weighted_cost = ((portfolio_item.quantity * portfolio_item.average_cost) + total_cost) / total_qty
            portfolio_item.quantity = total_qty
            portfolio_item.average_cost = weighted_cost
        else:
            new_item = Portfolio(user_id=current_user.id, stock_id=stock.id, quantity=quantity, average_cost=stock.current_price)
            db.session.add(new_item)
            
        tx = TransactionHistory(user_id=current_user.id, stock_id=stock.id, transaction_type='AL', quantity=quantity, price=stock.current_price)
        db.session.add(tx)
        db.session.commit()
        flash(f'Başarılı! {quantity} adet {stock.ticker} toplam {total_cost:.2f} TL bedelle satın alındı.', 'success')
        
    elif action == 'SELL':
        portfolio_item = db.session.scalar(db.select(Portfolio).filter_by(user_id=current_user.id, stock_id=stock.id))
        if not portfolio_item or portfolio_item.quantity < quantity:
            owned = portfolio_item.quantity if portfolio_item else 0
            flash(f'Yetersiz Varlık Miktarı! Portföyünüzde sadece {owned} adet {stock.ticker} bulunuyor.', 'danger')
            return redirect(url_for('dashboard'))
        current_user.available_cash += total_cost
        portfolio_item.quantity -= quantity
        if portfolio_item.quantity == 0:
            db.session.delete(portfolio_item)
            
        tx = TransactionHistory(user_id=current_user.id, stock_id=stock.id, transaction_type='SAT', quantity=quantity, price=stock.current_price)
        db.session.add(tx)
        db.session.commit()
        flash(f'Başarılı! {quantity} adet {stock.ticker} toplam {total_cost:.2f} TL bedelle satıldı.', 'success')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)