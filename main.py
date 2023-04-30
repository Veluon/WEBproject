from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, EqualTo
import jinja2
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# экземпляры
app = Flask(__name__)
env = jinja2.Environment()

# настройки приложения
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# бд
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# класс формы для логина
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


# класс модели новости
class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255), nullable=False)


# класс формы для добавления новостей
class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Текст новости', validators=[DataRequired()])
    submit = SubmitField('Добавить')


# класс модели пользователя
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))


# класс формы для регистрации
class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')


# главная страница
@app.route('/')
def index():
    print(session.items())  # выводим все ключ-значение, хранящиеся в сессии, в консоль
    news = News.query.order_by(News.id.desc()).all()  # выбираем все новости из базы данных и сортируем их по id
    return render_template('index.html', news=news)  # возвращаем шаблон 'index.html', передавая ему список новостей


# тестовая страничка
@app.route('/first')
def first():
    return render_template('first.html')  # возвращаем шаблон 'first.html'


# логин
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():  # если форма была отправлена и прошла валидацию
        username = form.username.data
        password = form.password.data

        # ищем пользователя в базе данных
        user = User.query.filter_by(username=username).first()

        # если пользователь найден и пароль совпадает, создаем сессию
        if user and user.password == password:
            session['username'] = user.username  # добавляем имя пользователя в сессию
            return redirect(url_for('index'))
        else:
            # иначе возвращаем шаблон 'base.html' с формой и сообщением об ошибке
            return render_template('base.html', form=form, error='Неправильный логин или пароль')

    return render_template('base.html', form=form)


@app.route('/register', methods=['GET', 'POST'])  # регистрация
def register():
    form = RegistrationForm()  # создаем экземпляр формы RegistrationForm
    if form.validate_on_submit():  # если форма была отправлена и прошла валидацию
        username = form.username.data  # получаем значение поля 'username'
        password = form.password.data  # получаем значение поля 'password'

        # проверяем, что пользователь с таким именем не существует
        user = User.query.filter_by(username=username).first()
        if user:
            # если пользователь существует, возвращаем шаблон 'register.html' с формой и сообщением об ошибке
            return render_template('register.html', form=form, error='Пользователь с таким именем уже существует')

        # если пользователь не существует, создаем нового пользователя и добавляем его в базу данных
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        # перенаправляем на страницу входа
        return redirect(url_for('login'))


# профиль пользователя
@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    # проверяем, авторизован ли пользователь
    if 'username' not in session:
        # если нет, перенаправляем на страницу авторизации
        return redirect(url_for('login'))

    # ищем пользователя с заданным именем
    user = User.query.filter_by(username=username).first()
    if not user:
        # если пользователь не найден
        return render_template('404.html'), 404

    if request.method == 'POST':
        # обрабатываем отправленную форму добавления новости
        title = request.form['title']
        content = request.form['content']
        author = user.username
        news = News(title=title, content=content, author=author)
        db.session.add(news)
        db.session.commit()
        # после добавления новости перенаправляем обратно на страницу профиля пользователя
        return redirect(url_for('profile', username=username))

    # страница профиля пользователя с формой добавления новости и списком его новостей
    form = NewsForm()
    news = News.query.filter_by(author=user.username).order_by(News.id.desc()).all()
    return render_template('profile.html', title='Профиль', form=form, user=user, news=news)


# страница добавления новости
@app.route('/profile/add_news', methods=['GET', 'POST'])
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        # обработка формы
        news = News(title=form.title.data, content=form.content.data, author=session['username'])
        db.session.add(news)
        db.session.commit()
        # на главную страницу
        return redirect(url_for('index'))
    return render_template('add_news.html', title='Добавить новость', form=form)


# выход из системы
@app.route('/logout')
def logout():
    # удаляем имя пользователя из сессии
    session.pop('username', None)
    # перенаправляем на главную страницу
    return redirect(url_for('index'))


# переход на страницу другого пользователя
@app.route('/user/<username>')
def user(username):
    # ищем пользователя с заданным именем
    user = User.query.filter_by(username=username).first_or_404()
    # получаем список его новостей и отображаем страницу профиля пользователя
    news = News.query.filter_by(author=username).order_by(News.id.desc()).all()
    return render_template('user_profile.html', user=user, news=news)


if __name__ == '__main__':
    app.run()
    db.create_all()
