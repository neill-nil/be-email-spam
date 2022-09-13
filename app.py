import re
import joblib
from model import Emails, Users, Drafts, db, login
from services.prediction import predict

from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from flask_login import login_required, current_user, login_user,logout_user
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_restful import Resource, Api
# from wtforms import StringField, PasswordField, BooleanField, IntegerField, validators
# from wtforms.validators import InputRequired, Email, Length

app = Flask(__name__)



app.config["SECRET_KEY"] = "mysecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False


api=Api(app)
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



@app.route("/", methods=["POST"])
@app.route('/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        return {'user_id': current_user.id, 'email': current_user.useremail}
    if request.method=="POST":
        email=request.json["email"]
        user=Users.query.filter_by(useremail=email).first()
        if user is not None and user.check_password(request.json["password"]):
            login_user(user)
            # session['user_id'] = current_user.id
            return {'user_id': current_user.id, 'email': current_user.useremail}
        else:
            data = {'note': 'Incorrect Email or Password! Please try again.'}
            return jsonify(data), 401
    # return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
    # if current_user.is_authenticated:
    #     return redirect("/login")
    if request.method=="POST":
        first_name=request.json['firstname']
        last_name=request.json['lastname']
        contact_no=request.json['contact_no']
        email=request.json['email']
        password=request.json['password']

        if Users.query.filter_by(useremail=email).first():
            data = {'note': 'This Email has already been registered..'}
            return jsonify(data), 401
        elif Users.query.filter_by(phno=contact_no).first():
            data = {'note': 'This Mobile number has already been registered..'}
            return jsonify(data), 401
        user=Users(fname=first_name, lname=last_name, useremail=email, phno=contact_no)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return {'note': 'Registered Successfully!'}
    # return render_template("register.html")

@app.route("/logout", methods=["GET","POST"])
def logout():
            logout_user()
            return {'note': 'Logged out successfully.'}

# @app.route('/inbox/<int:id>', methods=["GET", "POST"])
# @login_required
# def inbox(id):
#     # mails = Emails.query.filter((Emails.receiver_id==id) & (Emails.folder=='primary')).first_or_404()
#     msg=f"hello {id}"
#     return render_template("inbox.html") #, msg=msg, mails=mails)


#for both primary and spam
class Inbox(Resource):
    def get(self, folder, id):
            # mails = Emails.query.filter((Emails.receiver_id==current_user.id)).first()
        mails = db.session.query(Emails, Users).filter((Emails.receiver_id==id) & (Emails.folder==folder) & (Emails.is_deleted.is_(False))).join(Users,Emails.sender_id==Users.id).all()
        records = []
        for a, b  in mails:
            ic_map = a.json()
            ic_map.update(b.json())
            records.append(ic_map)

        return records
    
class Update:
    def put(self):
        email_id = request.json["email_id"]
        mail = Emails.query.get(email_id)
        if request.json["action"]=="delete":
            if mail.is_deleted==False:
                mail.is_deleted = True
                db.session.commit()
                return {'note': 'Moved to Trash!'}
        elif request.json["action"]=="star":
            mail.star_marked = True if mail.star_marked == False else False
            db.session.commit()
            return {'note': 'Starred!'}
        elif request.json["action"]=="read":
            mail.is_read = True
            db.session.commit()

        

    
class Compose(Resource):
    def post(self):
        text = request.json['text']
        subject = request.json['subject']
        user_id = request.json['user_id']
        r_emid = request.json['receiver_id']
        r_id = db.session.query(Users.id).filter_by(useremail=r_emid)
        comb_text = subject + " " + text
        pred = predict(comb_text, loaded_rfc)
        mail = Emails(email_text=text, subject=subject, receiver_id=r_id, sender_id=user_id, prediction=pred, folder='spam' if pred==1 else 'primary')
        db.session.add(mail)
        db.session.commit()

        return {'note': 'mail sent!'}

class Starred(Resource):
    def get(self, id):
        mails = db.session.query(Emails, Users).filter((Emails.receiver_id==id) & (Emails.star_marked.is_(True))).join(Users,Emails.sender_id==Users.id).all()
        records = []
        for a, b  in mails:
            ic_map = a.json()   
            ic_map.update(b.json())
            records.append(ic_map)

        return records

    def put(self, id):
        email_id = request.json["email_id"]
        mail = Emails.query.get(email_id)
        if request.json["action"]=="delete":
            if mail.is_deleted==False:
                mail.is_deleted = True
                db.session.commit()
                return {'note': 'Moved to Trash!'}
        elif request.json["action"]=="star":
            mail.star_marked = True if mail.star_marked == False else False
            db.session.commit()
            return {'note': 'Starred!'}
        elif request.json["action"]=="read":
            mail.is_read = True
            db.session.commit()

    # def delete(self,id):
    #     mail=Emails.query.filter_by(id=id).first()
    #     db.session.delete(mail)
    #     db.session.commit()

    #     return {'note':'Deleted successfully'}

class Sent(Resource):
    def get(self, id):
        mails = db.session.query(Emails, Users).filter(Emails.sender_id==id).join(Users,Emails.receiver_id==Users.id).all()
        records = []
        for a, b  in mails:
            ic_map = a.json()
            ic_map.update(b.json())
            records.append(ic_map)

        return records

class Trash(Resource):
    def get(self, id):
        mails = db.session.query(Emails, Users).filter((Emails.receiver_id==id) & (Emails.is_deleted.is_(True))).join(Users,Emails.sender_id==Users.id).all()
        records = []
        for a, b  in mails:
            ic_map = a.json()   
            ic_map.update(b.json())
            records.append(ic_map)

        return records

    def put(self, id):
        email_id = request.json["email_id"]
        mail = Emails.query.get(email_id)
        if request.json["action"]=="delete":
            db.session.delete(mail)
            db.session.commit()
            return {'note': 'Permanently Deleted!!'}
        
api.add_resource(Inbox, '/inbox/<string:folder>/<int:id>')
api.add_resource(Compose, '/compose')
api.add_resource(Starred, '/inbox/starred/<int:id>')
api.add_resource(Update, '/update')
api.add_resource(Trash, '/inbox/trash/<int:id>')
api.add_resource(Sent, '/inbox/sent/<int:id>')

    

# @app.route('/inbox/spam',methods=['POST'])
# @login_required
# def spam(user):
    
#     mails = Emails.query.filter((Emails.receiver_id==user.id) & (Emails.folder=='spam')).first_or_404()
#     return render_template("inbox.html", mails=mails)


# @app.route('/inbox/starred',methods=['POST'])
# @login_required
# def starred(user):
    
#     mails = Emails.query.filter((Emails.receiver_id==user.id) & (Emails.folder=='starred')).first_or_404()
#     return render_template("inbox.html", mails=mails)


# @app.route('/inbox/compose',methods=['POST'])
# def compose(sender):
#     # if:
#     #     email_text=request.form.get("text")
#     #     receiver=request.form.get("receiver")
#     #     mail=Emails(email_text=email_text, sender_id=sender, phno=contact_no)
#     #     db.session.add(mail)
#     #     db.session.commit()
#     # elif :
        
        
#     return redirect("/compose")

if __name__ == "__main__":
    app.run(debug=True)