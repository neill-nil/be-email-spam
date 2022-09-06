from email.policy import default
import enum
from typing import Text
from xmlrpc.client import Boolean
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, Table, String, JSON, DateTime, BOOLEAN, Enum
from sqlalchemy.orm import declarative_base, relationship
from flask_login import login_required, current_user, login_user,logout_user, LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()
login=LoginManager()



class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    '''
    Id : Field which stores unique id for unique user.
    email_text: contains body of the email
    sender_email: emailID of the sender
    receiver_email: emailID of the sender
    prediction: spam or non spam
    '''
    id = Column(Integer, primary_key=True)
    useremail = Column('User Email', String(60), unique=True)
    fname = Column('First name', String(50))
    lname = Column('Last name', String(50))
    phno = Column('Phone Number', Integer(), unique=True)
    password_hash = Column('Password', String(250))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow(), onupdate=datetime.utcnow())
    # verifya = Column('Verify Answer', String(50))
    
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

       
class MyEnum(enum.Enum):
    starred = 2
    spam = 1
    primary = 0


class Emails(db.Model):
    __tablename__ = 'emails'
    
    '''
    Id : Field which stores unique id for an email.
    sender_id: email
    email_text: contains body of the email
    sender_email: emailID of the sender
    receiver_email: emailID of the sender
    prediction: spam or non spam
    '''
    id = Column('id',Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    receiver_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String(200))
    email_text = Column(String(1000), unique=False, nullable=False)
    prediction = Column(Integer, nullable=False)
    folder = Column(Enum(MyEnum), nullable=False, default=MyEnum(prediction).name)
    attachment = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow(), onupdate=datetime.utcnow())
    star_marked = Column(BOOLEAN, default=False)
    is_deleted = Column(BOOLEAN, default=False)
    is_read = Column(BOOLEAN, default=False)



class Drafts(db.Model):
    __tablename__ = 'drafts'
    
    '''
    Id : Field which stores unique id for an email.
    user_id: user id foriegn key
    email_text: contains body of the email
    created_at: 
    '''
    id = Column('id',Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(Users.id))
    email_text = Column(String(1000), unique=False, nullable=False)
    attachment = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow())
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow(), onupdate=datetime.utcnow())


@login.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))