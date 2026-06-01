import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    # Relative path templates loading for standard folder layouts
    app = Flask(__name__, template_folder='../templates')
    
    # Secure absolute path resolution for SQLite instance file
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(basedir, '../instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    app.config['SECRET_KEY'] = 'borsa-simulasyonu-gizli-anahtar-1923'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_dir, 'borsa.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # LoginManager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bu sayfaya erişebilmek için lütfen giriş yapın.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.auth.routes import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.main.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # User loader callback mapping to DB User model
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Automatic database self-healing and asset seeding on startup
    with app.app_context():
        from app.models import Stock, seed_stocks, seed_bots
        try:
            db.create_all()
            # Schema integrity validation
            count = db.session.query(Stock).count()
            if count < 23:
                raise ValueError("Seeding extended assets.")
            db.session.query(Stock).filter_by(ticker='AKBNK').first()
        except Exception:
            db.session.rollback()
            db.drop_all()
            db.create_all()
        seed_stocks()
        seed_bots()

    return app
