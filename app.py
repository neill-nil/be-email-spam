import configparser
import re
import joblib
from model import Emails, Users, Senders, Receivers, Drafts, db, login
from services.prediction import predict

from flask import Flask, request, jsonify, render_template, redirect, session, url_for
from flask_login import login_required, current_user, login_user,logout_user
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_restful import Resource, Api
from flask_wtf.csrf import CSRFProtect
# from wtforms import StringField, PasswordField, BooleanField, IntegerField, validators
# from wtforms.validators import InputRequired, Email, Length

import numpy
from psycopg2.extensions import register_adapter, AsIs
def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)
def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)
register_adapter(numpy.float64, addapt_numpy_float64)
register_adapter(numpy.int64, addapt_numpy_int64)

app = Flask(__name__)



app.config["SECRET_KEY"] = "mysecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Neillkira99-_-@localhost/data"
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

# csrf = CSRFProtect()
# csrf.init_app(app)

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
        ans1=request.json['ans1']
        ans2=request.json['ans2']

        if Users.query.filter_by(useremail=email).first():
            data = {'note': 'This Email has already been registered..'}
            return jsonify(data), 401
        elif Users.query.filter_by(phno=contact_no).first():
            data = {'note': 'This Mobile number has already been registered..'}
            return jsonify(data), 401
        user=Users(fname=first_name, lname=last_name, useremail=email, phno=contact_no, verifyans1 = ans1, verifyans2 = ans2)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return {'note': 'Registered Successfully!'}
    # return render_template("register.html")

@app.route("/logout", methods=["GET","POST"])
def logout():
            logout_user()
            return {'note': 'Logged out successfully.'}


#for both primary and spam
class Inbox(Resource):
    # @login_required
    def get(self, folder, id):
        
        mails = db.session.query(Emails, Receivers, Users).filter\
        ((Emails.id==Receivers.email_id) & (Receivers.receiver_id==id) & (Receivers.folder==folder) &\
        (Emails.sender_id==Users.id) & (Receivers.is_deleted.is_(False))).all()  

        records = []
        for a, b, c  in mails:
            ic_map = a.to_json()   
            ic_map.update(b.to_json())
            ic_map.update(c.to_json())
            records.append(ic_map)

        return records
    
class Update(Resource):
    #@login_required
    def put(self, id):
        email_id = request.json["email_id"]
        mail = Emails.query.get(email_id)
        if request.json["folder"]!="sent":
            receiver = db.session.query(Receivers).filter((Receivers.receiver_id==id) & (Receivers.email_id==mail.id)).first()
            if request.json["action"]=="delete":
                if receiver.is_deleted == False:
                    receiver.is_deleted = True
                    receiver.star_marked = False
                    db.session.commit()
                    return {'note': 'Moved to Trash!'}
                else:
                    db.session.delete(mail)
                    db.session.commit()
                    return {'note': 'Permanently Deleted!!'}
            elif request.json["action"]=="star" and request.json["folder"]!="trash":
                if receiver.star_marked == False:
                    receiver.star_marked = True
                    db.session.commit()
                    return {'note': 'Starred!'}
                else:
                    receiver.star_marked = False
                    db.session.commit()
                    return {'note': 'Unstarred!'}
            elif request.json["action"]=="read":
                receiver.is_read = True
                db.session.commit()
        else:
            sender = db.session.query(Senders).filter((Senders.sender_id==id) & (Senders.email_id==mail.id)).first()
            if request.json["action"]=="delete":
                if sender.is_deleted == False:
                    sender.is_deleted = True
                    sender.star_marked = False
                    db.session.commit()
                    return {'note': 'Moved to Trash!'}
                else:
                    db.session.delete(mail)
                    db.session.commit()
                    return {'note': 'Permanently Deleted!!'}
            elif request.json["action"]=="star":
                if sender.star_marked == False:
                    sender.star_marked = True
                    db.session.commit()
                    return {'note': 'Starred!'}
                else:
                    sender.star_marked = False
                    db.session.commit()
                    return {'note': 'Unstarred!'}

        

    
class Compose(Resource):
    # @login_required
    def post(self):
        text = request.json['email_body']
        subject = request.json['subject']
        user_id = request.json['userId'] # sender (id)
        r_emids = request.json['to'] # list of receivers emails
        r_ids = []
        for r_emid in r_emids:
            if Users.query.filter_by(useremail=r_emid).first():
                r_id = db.session.query(Users.id).filter_by(useremail=r_emid).scalar()
                r_ids.append(r_id)
            else:
                msg = {'note': 'This email does not exist'}
                return msg, 404
        comb_text = subject + " " + text
        pred = predict(comb_text, loaded_rfc)
        mail = Emails(email_text=text, subject=subject, receivers_emails = r_emids, receivers=r_ids, sender_id=user_id, prediction=pred)
        db.session.add(mail) 
        db.session.commit()
        s_pref = Senders(sender_id = user_id, email_id = mail.id)
        db.session.add(s_pref)
        for r_id in r_ids:
            r_pref = Receivers(receiver_id = r_id, email_id = mail.id, folder='spam' if pred==1 else 'primary')
            db.session.add(r_pref)

        db.session.commit()

        return {'note': 'mail sent!'}

class Starred(Resource):
    @login_required
    def get(self, id):

        mails = db.session.query(Emails, Receivers, Users).filter\
        ((Emails.id==Receivers.email_id) & (Receivers.receiver_id==id) & \
        (Receivers.star_marked.is_(True)) & (Emails.sender_id==Users.id)).all()
        
        records = []
        for a, b, c  in mails:
            ic_map = a.to_json()   
            ic_map.update(b.to_json())
            ic_map.update(c.to_json())
            records.append(ic_map)

        return records


class Sent(Resource):
    #@login_required
    def get(self, id):
        mails = db.session.query(Emails, Senders).filter\
        ((Senders.sender_id==id) & (Emails.id==Senders.email_id)).all()

        records = []
        for a, b  in mails:
            ic_map = a.to_json()   
            ic_map.update(b.to_json())
            records.append(ic_map)

        return records

class Trash(Resource):
    #@login_required
    def get(self, id):
        mails = db.session.query(Emails, Receivers, Users).filter\
        ((Emails.id==Receivers.email_id) & (Receivers.receiver_id==id) & \
        (Receivers.is_deleted.is_(True)) & (Emails.sender_id==Users.id)).all()
        records = []
        records = []
        for a, b, c  in mails:
            ic_map = a.to_json()   
            ic_map.update(b.to_json())
            ic_map.update(c.to_json())
            records.append(ic_map)

        return records

class ChangePass(Resource):
    #@login_required
    def put(self, id):
        user=Users.query.filter_by(id=id).first()
        if user.check_password(request.json["password"]):
            new_pass = request.json["new_pass"]
            confirm_new_pass = request.json["confirm_new_pass"]
            if new_pass == confirm_new_pass:
                user.set_password(new_pass)
                db.session.commit()
                return {'note': 'Password has been updated'}
            else:
                data = {'note': "Passwords do not match"}
                return data, 401
        else:
            data = {'note': "Incorrect password"}
            return data, 401

class ForgotPass(Resource):
    def put(self):
        email = request.json['email']
        ans1 = request.json['ans1']
        ans2 = request.json['ans2']
        user = Users.query.filter_by(useremail=email).first()
        if ans1==user.verifyans1 and ans2==user.verifyans2:
            new_pass = request.json["new_pass"]
            confirm_new_pass = request.json["confirm_new_pass"]
            if new_pass == confirm_new_pass:
                user.set_password(new_pass)
                db.session.commit()
                return {'note': 'Password has been updated'}
            else:
                data = {'note': "Passwords do not match"}
                return data, 401

class UserDetails(Resource):
    def get(self, id):
        user = Users.query.filter_by(id=id).first()
        return {'name': user.fname + " " + user.lname, 'phone': int(user.phno), 'email': user.useremail}

        
api.add_resource(Inbox, '/inbox/<string:folder>/<int:id>')
api.add_resource(Compose, '/compose')
api.add_resource(Starred, '/inbox/starred/<int:id>')
api.add_resource(Update, '/update/<int:id>')
api.add_resource(Trash, '/inbox/trash/<int:id>')
api.add_resource(Sent, '/inbox/sent/<int:id>')
api.add_resource(ChangePass, '/changepass/<int:id>')
api.add_resource(ForgotPass, '/forgotpass')
api.add_resource(UserDetails, '/userdetails/<int:id>')

    

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