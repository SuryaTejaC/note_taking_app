import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mykey'

db = SQLAlchemy(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    todos=db.relationship('Todo', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(300), nullable=False)
    done = db.Column(db.Boolean, default=False)
    ownerid = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __rep__(self):
        return '<Task %r>' % self.id

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        user = User(email=request.form.get('email'),
                    password=request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user is not None and user.check_password(request.form.get('password')):
            login_user(user)
            next = request.args.get('next')
            if next == None or not next[0]=='/':
                next = url_for('home')

            return redirect(next)
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/index', methods=['POST','GET'])
def home():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content, owner=current_user)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/index')
        except:
            return 'There was an error while adding the task'

    else:
        userid = current_user.get_id()
        tasks = Todo.query.filter_by(ownerid=userid)
        return render_template("index.html", tasks=tasks)


@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/index')
    except:
        return 'There was an error while deleting that task'


@app.route('/update/<int:id>', methods=['GET','POST'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/index')
        except:
            return 'There was an issue while updating that task'

    else:
        return render_template('update.html', task=task)


@app.route('/done/<int:task_id>')
def resolve_task(task_id):
    task = Todo.query.get(task_id)

    if not task:
        return redirect('/index')
    if task.done:
        task.done = False
    else:
        task.done = True

    db.session.commit()
    return redirect('/index')


if __name__ == '__main__':
    app.run(debug=True)