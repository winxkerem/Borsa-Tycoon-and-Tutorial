import random
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Stock, PriceHistory, NewsFeed, Portfolio, TransactionHistory

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    tx_page = request.args.get('tx_page', 1, type=int)
    tx_query = db.select(TransactionHistory).filter_by(user_id=current_user.id).order_by(TransactionHistory.timestamp.desc())
    tx_pagination = db.paginate(tx_query, page=tx_page, per_page=5, error_out=False)
    
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
        news_item=news_item, news_feed=news_feed, leaderboard=leaderboard,
        tx_pagination=tx_pagination
    )

@main.route('/api/market-tick')
@login_required
def market_tick():
    NEWS_POOL = [
        {"ticker": "THYAO", "type": "positive", "headline": "THYAO bu çeyrekte rekor kâr açıkladı! Yatırımcıların ilgisi havacılık sektörüne kayıyor.", "min_change": 4.5, "max_change": 8.5},
        {"ticker": "THYAO", "type": "negative", "headline": "Küresel jet yakıtı fiyatlarındaki artış havacılık maliyetlerini yükseltti, THYAO hisseleri baskı altında.", "min_change": -8.5, "max_change": -4.5},
        {"ticker": "ASELS", "type": "positive", "headline": "ASELSAN yeni bir dev ihracat anlaşmasına imza attı! Sipariş devteri rekor seviyede.", "min_change": 4.5, "max_change": 8.5},
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
                change_pct = random.uniform(-15.0, 15.0)
            else:
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

@main.route('/api/ai-advice')
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

@main.route('/stock/<int:stock_id>')
@login_required
def stock_detail(stock_id):
    stock = db.session.get(Stock, stock_id)
    if not stock:
        flash('Varlık bulunamadı.', 'danger')
        return redirect(url_for('main.dashboard'))
        
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

@main.route('/trade/<int:stock_id>', methods=['POST'])
@login_required
def trade(stock_id):
    action = request.form.get('action', '').upper()
    quantity_str = request.form.get('quantity', '0')
    try:
        quantity = int(quantity_str)
        if quantity <= 0: raise ValueError()
    except ValueError:
        flash('Lütfen geçerli pozitif bir adet girin.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    stock = db.session.get(Stock, stock_id)
    if not stock:
        flash('Varlık bulunamadı.', 'danger')
        return redirect(url_for('main.dashboard'))
        
    total_cost = quantity * stock.current_price
    
    if action == 'BUY':
        if current_user.available_cash < total_cost:
            flash(f'Yetersiz Nakit Bakiye! Bedel: {total_cost:.2f} TL, Nakdiniz: {current_user.available_cash:.2f} TL.', 'danger')
            return redirect(url_for('main.dashboard'))
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
            return redirect(url_for('main.dashboard'))
        current_user.available_cash += total_cost
        portfolio_item.quantity -= quantity
        if portfolio_item.quantity == 0:
            db.session.delete(portfolio_item)
            
        tx = TransactionHistory(user_id=current_user.id, stock_id=stock.id, transaction_type='SAT', quantity=quantity, price=stock.current_price)
        db.session.add(tx)
        db.session.commit()
        flash(f'Başarılı! {quantity} adet {stock.ticker} toplam {total_cost:.2f} TL bedelle satıldı.', 'success')
        
    return redirect(url_for('main.dashboard'))

@main.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@main.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500
