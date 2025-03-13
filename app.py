from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import os
import click

# Flaskアプリケーションの設定
app = Flask(__name__)
# 環境変数から秘密鍵を読み込み、なければデフォルト値（開発環境のみ）を使用
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///marinera.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# データベース初期化
db = SQLAlchemy(app)

# ログインマネージャーの設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# データベースモデル
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"News('{self.title}', '{self.date_posted}')"

# フォーム
class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

class NewsForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('投稿')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 既存のルート
@app.route('/')
def index():
    news = News.query.order_by(News.date_posted.desc()).all()
    return render_template('index.html', news=news)

@app.route('/instructors')
def instructors():
    return render_template('instructors.html')

@app.route('/marinera')
def marinera():
    return render_template('marinera.html')

# 新しいルート - ログイン関連
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
        else:
            flash('ログインに失敗しました。ユーザー名とパスワードを確認してください。', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# 管理画面ルート
@app.route('/admin')
@login_required
def admin_dashboard():
    news = News.query.order_by(News.date_posted.desc()).all()
    return render_template('admin/dashboard.html', news=news)

@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
def new_news():
    form = NewsForm()
    if form.validate_on_submit():
        news = News(title=form.title.data, content=form.content.data)
        db.session.add(news)
        db.session.commit()
        flash('新着情報が追加されました！', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/create_news.html', form=form, legend='新着情報の作成')

@app.route('/admin/news/<int:news_id>')
@login_required
def news_detail(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('admin/news_detail.html', news=news)

@app.route('/admin/news/<int:news_id>/update', methods=['GET', 'POST'])
@login_required
def update_news(news_id):
    news = News.query.get_or_404(news_id)
    form = NewsForm()
    
    if form.validate_on_submit():
        news.title = form.title.data
        news.content = form.content.data
        db.session.commit()
        flash('新着情報が更新されました！', 'success')
        return redirect(url_for('news_detail', news_id=news.id))
    
    elif request.method == 'GET':
        form.title.data = news.title
        form.content.data = news.content
        
    return render_template('admin/create_news.html', form=form, legend='新着情報の更新')

@app.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@login_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('新着情報が削除されました！', 'success')
    return redirect(url_for('admin_dashboard'))

# CLIコマンドを使用して管理者ユーザーを作成
@app.cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.password_option()
def create_admin(username, email, password):
    """管理者アカウントを作成します。例: flask create-admin admin admin@example.com"""
    if User.query.filter_by(username=username).first() is not None:
        click.echo(f'ユーザー名 "{username}" は既に使用されています。')
        return

    if User.query.filter_by(email=email).first() is not None:
        click.echo(f'メールアドレス "{email}" は既に使用されています。')
        return
    
    admin = User(username=username, email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f'管理者アカウント "{username}" が作成されました。')

# Flask 2.0.0以降では app.before_first_request は削除されています
# 代わりにアプリケーションコンテキスト内でデータベースを初期化します
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)