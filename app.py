## CopyRight @ Muthu Theaver Mukulatore Higher Secondar School (2025)

from flask import Flask, render_template, request, redirect, flash, session 
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = "1324sriram"


client = MongoClient("mongodb+srv://sriram65raja:1324sriram@cluster0.lhsvjbx.mongodb.net/")
mmhss = client["mmhss"]
Student_Register = mmhss["Student_Register"]


genai.configure(api_key="AIzaSyAvyLEzkIaibw5BFF4ZCISLljZNbLKd2Cg")
model = genai.GenerativeModel("gemini-2.0-flash")

@app.route("/")
def home():
    if not session.get("email") and not session.get("id"):
        return render_template("index.html")
    
    return redirect("/dash")


@app.route("/sign-in", methods=["GET", "POST"])
def sign():
    if session.get("id"):
        return redirect("/dash")
    
    if request.method == "POST":
        username = request.form.get("User")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if Student_Register.find_one({"email": email}):
            flash("Email ID already exists.")
            return render_template("sign-in.html" ,err="Email ID already exists.")
        
        

        hashed_pw = generate_password_hash(password)
        data = {
            "username": username,
            "email": email,
            "password": hashed_pw
        }
        Student_Register.insert_one(data)

        flash("Registration successful. Please log in.")
        return redirect("/login")

    return render_template("sign-in.html") 


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("id"):
        return redirect("/dash")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = Student_Register.find_one({"email": email})
        if not user:
            flash("Email not registered.")
            return render_template("login.html" , err="Email not registered")

        if not check_password_hash(user["password"], password):
            flash("Incorrect password.")
            return render_template("login.html" , err="Incorrect password")

        session["id"] = str(user["_id"])
        session["email"] = user["email"]
        flash("User Logged in Successfully")
        return redirect("/dash")
                
    return render_template("login.html")

@app.route("/dash")
def dash():
    if not session.get("email") and not session.get("id"):
        return redirect("/sign-in")

    
    users = session.get("email")
    name = users.split("@")[0] if users else "NOT _ STUDENT"
    return render_template("dash.html", username=name)

@app.route("/english" , methods=["POST" , "GET"])
def eng():

    if request.method == "POST":
            txt = request.form.get("q")
            res = model.generate_content(f"  {txt}  NOTE : Only respond for English Grammer , Questions Only ! if the user asks any another content then simply say iam only for English AI")
            return render_template("eng.html" , msg = res.text)
    
    return render_template("eng.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
