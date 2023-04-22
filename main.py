from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo
import jinja2
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
env = jinja2.Environment()
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<News {self.id} {self.title}>'


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


@app.route('/')
def index():
    news = News.query.all()
    return render_template('index.html', news=news)


@app.route('/first')
def first():
    return render_template('first.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = user.username
            return redirect(url_for('profile'))
        else:
            print(session.items())
            print(username)
            print(password)
            print(user)
            return render_template('base.html', form=form, error='Неправильный логин или пароль')

    return render_template('base.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user:
            return render_template('register.html', form=form, error='Пользователь с таким именем уже существует')

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = session['username']
        news = News(title=title, content=content, author=author)
        db.session.add(news)
        db.session.commit()
        return redirect(url_for('profile'))

    form = NewsForm()
    return render_template('profile.html', title='Профиль', form=form)


@app.route('/profile/add_news', methods=['GET', 'POST'])
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        news = News(title=form.title.data, content=form.content.data, author=session['username'])
        db.session.add(news)
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('add_news.html', title='Добавить новость', form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
    db.create_all()
