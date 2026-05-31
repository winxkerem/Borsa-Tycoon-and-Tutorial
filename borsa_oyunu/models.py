from datetime import datetime, timezone
from typing import List, Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# Not: db objesini uygulamanızın başka bir yerinde (örneğin app/__init__.py veya app.py) 
# tanımladıysanız oradan import edebilirsiniz: "from app import db"
# Biz bağımsız bir models.py dosyası olarak genel yapıyı kuruyoruz.
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Oyuncu (User) Veri Modeli
    Oyuncunun hesap bilgilerini, şifresini ve cüzdanındaki nakit parasını tutar.
    """
    __tablename__ = 'users'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), unique=True, nullable=False, index=True)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(256), nullable=False)
    # default=100000.0 TL başlangıç parası. Para birimleri için Numeric (Decimal) kullanılması tavsiye edilir.
    available_cash: so.Mapped[float] = so.mapped_column(sa.Numeric(15, 2), default=100000.0, nullable=False)

    # Tablolar Arası İlişkiler (Relationships)
    # Bir kullanıcının portföyünde birden fazla hisse senedi bulunabilir (Portfolio tablosu ile 1-N ilişki)
    portfolio_items: so.Mapped[List['Portfolio']] = so.relationship(back_populates='user', cascade='all, delete-orphan')
    
    # Bir kullanıcının birden fazla işlem geçmişi (AL/SAT) olabilir (TransactionHistory tablosu ile 1-N ilişki)
    transactions: so.Mapped[List['TransactionHistory']] = so.relationship(back_populates='user', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<User {self.username} | Bakiye: {self.available_cash} TL>"


class Stock(db.Model):
    """
    Hisse Senedi (Stock) Veri Modeli
    Borsada işlem gören şirketlerin hisse bilgilerini, güncel fiyatlarını ve oranlarını tutar.
    """
    __tablename__ = 'stocks'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ticker: so.Mapped[str] = so.mapped_column(sa.String(10), unique=True, nullable=False, index=True)  # Örn: THYAO, ASELS
    company_name: so.Mapped[str] = so.mapped_column(sa.String(128), nullable=False)                  # Şirket Adı
    current_price: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), nullable=False)             # Güncel Fiyatı
    sector: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64), nullable=True)                 # Sektör (Opsiyonel)
    pe_ratio: so.Mapped[Optional[float]] = so.mapped_column(sa.Float, nullable=True)                  # F/K Oranı (P/E Ratio - Opsiyonel)

    # Tablolar Arası İlişkiler (Relationships)
    # Bu hisse senedi birçok oyuncunun portföyünde yer alabilir
    portfolio_items: so.Mapped[List['Portfolio']] = so.relationship(back_populates='stock', cascade='all, delete-orphan')
    
    # Bu hisse senedi üzerinden yapılmış geçmiş işlemler
    transactions: so.Mapped[List['TransactionHistory']] = so.relationship(back_populates='stock', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<Stock {self.ticker} | Güncel Fiyat: {self.current_price} TL>"


class Portfolio(db.Model):
    """
    Portföy (Portfolio) Veri Modeli
    Oyuncuların ellerinde tuttukları (satın aldıkları) hisse senetlerini, miktarlarını ve ortalama maliyetlerini tutar.
    """
    __tablename__ = 'portfolios'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    # Yabancı Anahtarlar (Foreign Keys)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False, index=True)
    
    quantity: so.Mapped[int] = so.mapped_column(sa.Integer, default=0, nullable=False)               # Sahip olunan adet
    average_cost: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), default=0.0, nullable=False) # Ortalama Alış Maliyeti

    # İlişki Bağlantıları (Back-references)
    user: so.Mapped['User'] = so.relationship(back_populates='portfolio_items')
    stock: so.Mapped['Stock'] = so.relationship(back_populates='portfolio_items')

    def __repr__(self) -> str:
        return f"<Portfolio User ID: {self.user_id} | Stock: {self.stock.ticker if self.stock else self.stock_id} | Miktar: {self.quantity} | Ort. Maliyet: {self.average_cost}>"


class TransactionHistory(db.Model):
    """
    İşlem Geçmişi / Alışveriş Günlüğü (TransactionHistory) Veri Modeli
    Oyuncuların yaptığı tüm alım (AL) ve satım (SAT) işlemlerinin kayıtlarını tutar.
    """
    __tablename__ = 'transaction_histories'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    
    # Yabancı Anahtarlar (Foreign Keys)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey('stocks.id', ondelete='CASCADE'), nullable=False, index=True)
    
    transaction_type: so.Mapped[str] = so.mapped_column(sa.String(10), nullable=False)            # 'AL' veya 'SAT'
    quantity: so.Mapped[int] = so.mapped_column(sa.Integer, nullable=False)                         # İşlem yapılan miktar
    price: so.Mapped[float] = so.mapped_column(sa.Numeric(10, 2), nullable=False)                   # İşlem anındaki hisse fiyatı
    timestamp: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )                                                                                              # İşlem zamanı

    # İlişki Bağlantıları (Back-references)
    user: so.Mapped['User'] = so.relationship(back_populates='transactions')
    stock: so.Mapped['Stock'] = so.relationship(back_populates='transactions')

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} | User ID: {self.user_id} | Stock: {self.stock.ticker if self.stock else self.stock_id} | Adet: {self.quantity} | Fiyat: {self.price}>"
