import joblib
from model import Emails, Users, Drafts, db, login

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user, login_user,logout_user
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
# from flask_wtf import FlaskForm 
# from wtforms import StringField, PasswordField, BooleanField, IntegerField, validators
# from wtforms.validators import InputRequired, Email, Length

app = Flask(__name__)


app.config["SECRET_KEY"] = "mysecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False
# app.config['SQLALCHEMY_BINDS'] = {'emails': 'sqlite:///emails.db', 'drafts': 'sqlite:///drafts.db'}

bootstrap = Bootstrap(app)


loaded_rfc = joblib.load("./random_forest.joblib")


db.init_app(app)
login.init_app(app)

login.login_view= 'login'
@app.before_first_request
def create_all():
    db.create_all()

migrate = Migrate(app, db)

@login.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))



@app.route("/", methods=["GET","POST"])
@app.route('/login', methods=["GET","POST"])
def login():
    msg=""
    if current_user.is_authenticated:
        return redirect(url_for('inbox', id=current_user.id))
    if request.method=="POST":
        email=request.form.get("useremail")
        user=Users.query.filter_by(useremail=email).first()
        if user is not None and user.check_password(request.form.get("password")):
            login_user(user)
            return redirect(url_for('inbox', id=current_user.id))
        else:
            msg="Email or Password is incorrect!!"
            return render_template("login.html",msg=msg)
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    msg=""
    if current_user.is_authenticated:
        return redirect("/login")
    if request.method=="POST":
        first_name=request.form.get("fname")
        last_name=request.form.get("lname")
        contact_no=request.form.get("phno")
        email=request.form.get("useremail")
        password=request.form.get("password")

        if Users.query.filter_by(useremail=email).first():
            msg="Email is already registerd"
            return render_template("register.html",msg=msg)
        elif Users.query.filter_by(phno=contact_no).first():
            msg="Mobile Number is already registerd"
            return render_template("register.html",msg=msg)
        user=Users(fname=first_name, lname=last_name, useremail=email, phno=contact_no)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/logout", methods=["GET","POST"])
def logout():
            logout_user()
            return redirect("/login")

@app.route('/inbox/<int:id>', methods=["GET", "POST"])
@login_required
def inbox(id):
    mails = Emails.query.filter((Emails.receiver_id==id) & (Emails.folder=='primary')).first_or_404()
    msg=f"hello {id}"
    return render_template("inbox2.html") #, msg=msg, mails=mails)


    

@app.route('/inbox/spam',methods=['POST'])
@login_required
def spam(user):
    
    mails = Emails.query.filter((Emails.receiver_id==user.id) & (Emails.folder=='spam')).first_or_404()
    return render_template("inbox.html", mails=mails)


@app.route('/inbox/starred',methods=['POST'])
@login_required
def starred(user):
    
    mails = Emails.query.filter((Emails.receiver_id==user.id) & (Emails.folder=='starred')).first_or_404()
    return render_template("inbox.html", mails=mails)


@app.route('/inbox/compose',methods=['POST'])
def compose(sender):
    # if:
    #     email_text=request.form.get("text")
    #     receiver=request.form.get("receiver")
    #     contact_no=request.form.get("phno")
    #     mail=Emails(email_text=email_text, sender_id=sender, phno=contact_no)
    #     db.session.add(mail)
    #     db.session.commit()
    # elif :
        
        
    return redirect("/compose")

if __name__ == "__main__":
    app.run(debug=True)