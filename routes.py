from app import app


@app.route("/", methods=["GET","POST"])
@app.route('/login', methods=["GET","POST"])
def login():
    msg=""
    if current_user.is_authenticated:
        return redirect("/inbox")
    if request.method=="POST":
        email=request.form.get("useremail")
        user=Users.query.filter_by(useremail=email).first()
        if user is not None and user.check_password(request.form.get("password")):
            login_user(user)
            return redirect("/inbox")
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

@app.route('/inbox')
@login_required
def inbox():
    return render_template("inbox.html")


    

@app.route('/inbox/spam',methods=['POST'])
def spam():
    
    '''
    Render spam emails
    '''
@app.route('/inbox/compose',methods=['POST'])
def compose():
    '''
    Compose email
    '''

if __name__ == "__main__":
    app.run(debug=True)