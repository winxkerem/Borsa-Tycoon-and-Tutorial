import random
from datetime import datetime, timezone
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from app import db

# ==============================================================================
# DATABASE SCHEMAS (SQLAlchemy 2.x Declarative Mapped Style)
# ==============================================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    available_cash: so.Mapped[float] = so.mapped_column(sa.Float, default=100000.0, nullable=False)
    
    # Relationships
    portfolio_items: so.Mapped[List['Portfolio']] = so.relationship(back_populates='user', cascade='all, delete-orphan')
    transactions: so.Mapped[List['TransactionHistory']] = so.relationship(back_populates='user', cascade='all, delete-orphan')

class PriceHistory(db.Model):
    __tablename__ = 'price_histories'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    stock_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False)
    price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    
    # Relationships
    stock: so.Mapped['Stock'] = so.relationship(back_populates='price_history')

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ticker: so.Mapped[str] = so.mapped_column(sa.String(10), unique=True, nullable=False, index=True)
    company_name: so.Mapped[str] = so.mapped_column(sa.String(128), nullable=False)
    current_price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    sector: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64), nullable=True)
    pe_ratio: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, nullable=True)
    asset_type: so.Mapped[str] = so.mapped_column(sa.String(20), default='stock', nullable=False)
    
    # Relationships
    portfolio_items: so.Mapped[List['Portfolio']] = so.relationship(back_populates='stock', cascade='all, delete-orphan')
    transactions: so.Mapped[List['TransactionHistory']] = so.relationship(back_populates='stock', cascade='all, delete-orphan')
    price_history: so.Mapped[List['PriceHistory']] = so.relationship(back_populates='stock', cascade='all, delete-orphan')

class NewsFeed(db.Model):
    __tablename__ = 'news_feeds'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    headline: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    news_type: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False, index=True)
    quantity: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, nullable=False)
    average_cost: so.Mapped[float] = so.mapped_column(sa.Float, default=0.0, nullable=False)
    
    # Relationships
    user: so.Mapped['User'] = so.relationship(back_populates='portfolio_items')
    stock: so.Mapped['Stock'] = so.relationship(back_populates='portfolio_items')

class TransactionHistory(db.Model):
    __tablename__ = 'transaction_histories'
    
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False, index=True)
    transaction_type: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False)
    quantity: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)
    price: so.Mapped[float] = so.mapped_column(sa.Float, nullable=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    
    # Relationships
    user: so.Mapped['User'] = so.relationship(back_populates='transactions')
    stock: so.Mapped['Stock'] = so.relationship(back_populates='transactions')

# ==============================================================================
# DATABASE SEEDERS
# ==============================================================================
def seed_stocks():
    default_stocks = [
        # Stocks
        {"ticker": "THYAO", "company_name": "Türk Hava Yolları A.O.", "current_price": 315.00, "sector": "Ulaşım / Havacılık", "pe_ratio": 4.85, "asset_type": "stock"},
        {"ticker": "ASELS", "company_name": "Aselsan Elektronik Sanayi", "current_price": 55.00, "sector": "Savunma / Teknoloji", "pe_ratio": 12.40, "asset_type": "stock"},
        {"ticker": "EREGL", "company_name": "Ereğli Demir ve Çelik Fabrikaları", "current_price": 42.00, "sector": "Ağır Sanayi / Demir-Çelik", "pe_ratio": 18.10, "asset_type": "stock"},
        {"ticker": "GARAN", "company_name": "Türkiye Garanti Bankası A.Ş.", "current_price": 80.00, "sector": "Finans / Bankacılık", "pe_ratio": 3.15, "asset_type": "stock"},
        {"ticker": "TUPRS", "company_name": "Tüpraş Türkiye Petrol Rafinerileri", "current_price": 135.00, "sector": "Enerji / Petrol", "pe_ratio": 6.50, "asset_type": "stock"},
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
        # Crypto
        {"ticker": "BTC", "company_name": "Bitcoin (BTC)", "current_price": 2200000.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "ETH", "company_name": "Ethereum (ETH)", "current_price": 110000.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
        {"ticker": "SOL", "company_name": "Solana (SOL)", "current_price": 5400.00, "sector": "Kripto Para / DeFi", "pe_ratio": None, "asset_type": "crypto"},
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
