from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

class RegistrationForm(FlaskForm):
    username = StringField(
        'Kullanıcı Adı', 
        validators=[
            DataRequired(message="Kullanıcı adı alanı boş bırakılamaz."),
            Length(min=3, max=64, message="Kullanıcı adı 3 ila 64 karakter uzunluğunda olmalıdır.")
        ]
    )
    password = PasswordField(
        'Şifre', 
        validators=[
            DataRequired(message="Şifre alanı boş bırakılamaz."),
            Length(min=6, max=64, message="Şifre en az 6 karakter uzunluğunda olmalıdır.")
        ]
    )
    submit = SubmitField('Kayıt İşlemini Tamamla')

class LoginForm(FlaskForm):
    username = StringField(
        'Kullanıcı Adı', 
        validators=[
            DataRequired(message="Kullanıcı adı alanı boş bırakılamaz.")
        ]
    )
    password = PasswordField(
        'Şifre', 
        validators=[
            DataRequired(message="Şifre alanı boş bırakılamaz.")
        ]
    )
    submit = SubmitField('Giriş Yap')
