from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
from app.auth.forms import RegistrationForm, LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()
        
        existing_user = db.session.scalar(db.select(User).filter_by(username=username))
        if existing_user:
            flash('Bu kullanıcı adı zaten alınmış. Lütfen başka bir tane seçin.', 'danger')
            return render_template('register.html', form=form)
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password, available_cash=100000.0)
        db.session.add(new_user)
        db.session.commit()
        flash('Kaydınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data.strip()
        
        user = db.session.scalar(db.select(User).filter_by(username=username))
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Hoş geldiniz, {user.username}! Borsada kazançlı günler dileriz.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre.', 'danger')
            
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Güvenli bir şekilde çıkış yaptınız. Tekrar görüşmek üzere!', 'success')
    return redirect(url_for('auth.login'))
