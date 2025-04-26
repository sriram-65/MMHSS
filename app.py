## CopyRight @ Muthu Theaver Mukulatore Higher Secondar School (2025)

from flask import Flask, render_template, request, redirect, flash, session  , url_for , jsonify , abort
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
import google.generativeai as genai
from bson.objectid import ObjectId
from datetime import timedelta
import fitz

app = Flask(__name__)
app.secret_key = "1324sriram"


client = MongoClient("mongodb+srv://sriram65raja:1324sriram@cluster0.lhsvjbx.mongodb.net/")
mmhss = client["mmhss"]
Student_Register = mmhss["Student_Register"]
Student_Notes = mmhss["NOTES"]
student_Uploads = mmhss["student_Uploads"]
app.permanent_session_lifetime = timedelta(15)



genai.configure(api_key="AIzaSyAvyLEzkIaibw5BFF4ZCISLljZNbLKd2Cg")
model = genai.GenerativeModel("gemini-2.0-flash")



@app.route("/")
def home():
    if not session.get("id"):
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
        session.permanent = True
        flash("User Logged in Successfully")
        return redirect("/dash")
                
    return render_template("login.html")

@app.route("/dash")
def dash():
    if not session.get("id"):
        return redirect("/sign-in")
    users = session.get("email")
    name = users.split("@")[0] if users else "NOT _ STUDENT"
    return render_template("dash.html", username=name)






@app.route("/get-student-details")
def get_student_info():
    if not session.get("id"):
        return redirect("/")
    Students = Student_Register.find_one({"_id":ObjectId(session.get("id"))})
    get_histry = session.get("chat_history")
    return render_template("student_info.html" , st_info = Students , username = Students["username"] , gh = get_histry)


@app.route("/logout")
def logout():
    session.pop("id" , None)
    return redirect("/")



@app.route("/upload", methods=["POST", "GET"])
def upload():
    if request.method == "POST":
        title = request.form.get("title")
        des = request.form.get("des")
        st_data = Student_Register.find_one({"_id": ObjectId(session.get("id"))})

        data = {
            "STUDENT_NAME": st_data["username"],
            "STUDENT_EMAIL": st_data["email"],
            "TITLE": title,
            "DATA": des
        }

        result = Student_Notes.insert_one(data)
        session["Note_id"] = str(result.inserted_id)  # ✅ FIXED

        return redirect("/take-notes")

    return render_template("upload.html")

         

@app.route("/take-notes")
def Take_Notes():
    if not session.get("id"):
        return redirect("/")
    dta = list(Student_Notes.find({"STUDENT_EMAIL":session.get("email")}))
    return render_template("Take.html" , data=dta)



@app.route("/note-deatils/<note_id>")
def note_deatils(note_id):
    if not session.get("id"):
        return redirect("/")
    
    dta = list(Student_Notes.find({"_id":ObjectId(note_id)}))
    return render_template("note_deatil.html" , data=dta)
    

@app.route("/del/<post_id>" , methods=["POST"])
def delelte(post_id):
    
    note = Student_Notes.find_one({"_id":ObjectId(post_id)})
    if not note:
        abort(404)
    
    if note["STUDENT_EMAIL"] != session.get("email"):
        abort(403)
    
    Student_Notes.delete_one({"_id":ObjectId(post_id)})
    return redirect("/take-notes")
    


@app.route("/edit/<note_id>", methods=["POST", "GET"])
def edit(note_id):
    if not session.get("id"):
        return redirect("/")

    note = Student_Notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        abort(404)

    if note["STUDENT_EMAIL"] != session.get("email"):
        abort(403)

    if request.method == "POST":
        new_title = request.form.get("title")
        new_data = request.form.get("des")

        Student_Notes.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {"TITLE": new_title, "DATA": new_data}}
        )

        return redirect("/take-notes")

    return render_template("edit_note.html", note=note)


@app.route("/get-suggestion")
def Get_sug():
    q = request.args.get("qury")
    res = model.generate_content(f"pls Generate a Suggestion for this text {q}")
    return jsonify({"content":res.text})


def gen_extract_pdf(pdf):
    doc = fitz.open(stream=pdf.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

@app.route("/get-book-sol", methods=["POST", "GET"])
def Get_book_solution():
    if request.method == "POST":
        try:
            
            pdf = request.files.get("PDF")
            if pdf:
                text = gen_extract_pdf(pdf)
                q = request.form.get("q")
                res = get_content(text, q)
                return render_template("get-info.html", answer=res, question=q)
        except:
            return render_template("err.html"  , error_title="Upload Error" , error_message="Some Error Occured While Connecting To The Server" , error_details="Please try Again later or Upload file Less than 10 MB or Upload Only Proper Pdf File")
    return render_template("get-info.html")


def get_content(text, q):
    generated = model.generate_content(f"""
    You are an assistant. Here is a document:
    {text}
    Now answer this question based on the document: {q}
    """)
    return generated.text
    

@app.errorhandler(404)
def page_not_found(e):
    return render_template('err.html',
                         error_title="Page Not Found",
                         error_message="The page you're looking for doesn't exist.",
                         error_details=str(e)), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('err.html',
                         error_title="Server Error",
                         error_message="Something went wrong on our end.",
                         error_details=str(e) if app.debug else None), 500


if __name__== "__main__":
    app.run(debug=True)
