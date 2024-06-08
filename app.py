# from flask import Flask, render_template, request, jsonify
# import json

# app = Flask(__name__)
# with open('resume.json') as f:
#     resume_data = json.load(f)
# @app.route('/')
# def resume_form():
#     return render_template('resume_form.html', data=resume_data)
# @app.route('/submit', methods=['POST'])
# def submit_form():
#     submitted_data = request.form.to_dict()
#     print(submitted_data)
#     return jsonify({"message": "Form submitted successfully!"})
# if __name__ == '__main__':
#     app.run(debug=True)

import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
import fitz
from docx import Document
import google.generativeai as genai
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_JSON'] = 'resume.json'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def read_document(file_path):
    if file_path.endswith('.pdf'):
        try:
            pdf_document = fitz.open(file_path)
            text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text += page.get_text() + "\n"
            pdf_document.close()
            return text
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    elif file_path.endswith('.docx'):
        try:
            document = Document(file_path)
            text = "\n".join([para.text for para in document.paragraphs])
            return text
        except Exception as e:
            print(f"Error reading Word document: {e}")
            return None
    else:
        print("Unsupported file format")
        return None
    
@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        document_text = read_document(file_path)
        genai.configure(api_key='AIzaSyAy3EjjG0puD1quoYtmxkXPRQuz4RvtsPY')
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"""
        You are a professional resume parsing agent.
        So do as follows:
        1. Extract Personal Information of the applicant with keys being:
        a. Extract name of the applicant.
        b. Extract email of the applicant.
        c. Extract phone number of the applicant.
        d. Exract address of the applicant.
        e. Extract linkedin url of the applicant.
        2. Extract me the Summary of the applicant if mentioned.
        3. Extract me Work Experience details with keys being:
        a. Company name
        b. Mode of work (Offline/Online/Hybrid)
        c. Job Role
        d. Job Type (Full Time or Intern)
        e. Start Date
        f. End Date.
        4. Extract me Project details with keys being:
        a. Name of Project with short introduction of it, if mentioned
        b. Description of project.
        c. Start Date if any.
        d. End Date if any
        5. Extract me Achievement details with keys being:
        a. Heading with short introduction of it, if mentioned
        b. Description of the heading.
        c. Start Date if any.
        d. End Date if any:
        6. Extract me Education details with keys being:
        a. Degree/Course
        b. Field of Study (note: usually written alongside degree, extract from 'degree' key if that is the case)
        c. Institute
        d. Marks/Percentage/GPA
        e. Start Date if any
        f. End Date/ Passing Year
        7. Extract me Certification details with keys being:
        a. Certification Title
        b. Issuing Organization
        c. Date Of Issue
        8. List me all the skills from the following document.
        9. List me all the extracurricular activities/hobbies from the following document.
        10. List me all the language competencies from the following document.
        Resume of applicant: {document_text}
        You are to generate a valid JSON script as output. Properly deal with trailing commas while formatting the output file.
        Take this empty json format and fill it up:
        {{
            "Personal_Information": {{
                "Name": "",
                "Email": "",
                "Phone_Number": "",
                "Address": "",
                "LinkedIn_URL": ""
            }},
            "Summary": "",
            "Work_Experience": [
                {{
                    "Company_Name": "",
                    "Mode_of_Work": "",
                    "Job_Role": "",
                    "Job_Type": "",
                    "Start_Date": "",
                    "End_Date": "",
                }}
            ],
            "Projects": [
                {{
                    "Name_of_Project": "",
                    "Description": "",
                    "Start_Date": "",
                    "End_Date": ""
                }}
            ],
            "Achievements": [
                {{
                    "Heading": "",
                    "Description": "",
                    "Start_Date": "",
                    "End_Date": ""
                }}
            ],
            "Education": [
                {{
                    "Degree/Course": "",
                    "Field_of_Study": "",
                    "Institute": "",
                    "Marks/Percentage/GPA": "",
                    "Start_Date": "",
                    "End_Date": ""
                }}
            ],
            "Certifications": [
                {{
                    "Certification_Title": "",
                    "Issuing_Organization": "",
                    "Date_Of_Issue": ""
                }}
            ],
            "Skills": [],
            "Extracurricular_Activities": [],
            "Language_Competencies": [
                {{
                    "Language": "",
                    "Proficiency": ""
                }}
            ]
        }}""")
        lines = response.text.split('\n')
        truncated_lines = lines[1:-1]
        truncated_text = '\n'.join(truncated_lines)
        response_json = json.loads(truncated_text)
        output_filename = app.config['GENERATED_JSON']
        print(response_json)
        with open(output_filename, 'w') as json_file:
            json.dump(response_json, json_file, indent=4)
        return redirect(url_for('loading_page'))
    
@app.route('/loading')
def loading_page():
    return render_template('loading.html')

@app.route('/resume_form')
def resume_form():
    with open(app.config['GENERATED_JSON']) as f:
        resume_data = json.load(f)
    return render_template('resume_form.html', data=resume_data)



# shila takes over ...
# <======================================================================================================================3

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1/resume'
app.app_context().push()
db = SQLAlchemy(app)

class PersonalInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    linkedin_url = db.Column(db.String(255))

class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    summary = db.Column(db.Text)

class WorkExperience(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    job_title = db.Column(db.String(255))
    company_name = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)

class ProjectDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    project_name = db.Column(db.String(255))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

class Achievements(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    achievement_description = db.Column(db.Text)

class EducationDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    degree_course = db.Column(db.String(255))
    field_of_study = db.Column(db.String(255))
    institute = db.Column(db.String(255))
    marks_percentage_gpa = db.Column(db.String(50))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

class CertificationDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    certification_title = db.Column(db.String(255))
    date_of_issue = db.Column(db.Date)
    issuing_organization = db.Column(db.String(255))

class Skills(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    skill = db.Column(db.String(255))

class ExtracurricularActivities(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    activity = db.Column(db.String(255))

class LanguageCompetencies(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    language = db.Column(db.String(255))
    proficiency_level = db.Column(db.String(255))

db.create_all()

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    linkedin = request.form['linkedin']
    summary = request.form['summary']

    personal_info = PersonalInformation(name=name, email=email, phone_number=phone, address=address, linkedin_url=linkedin)
    db.session.add(personal_info)
    db.session.commit()  # commits here to generate the id

    summary = request.form['summary']
    summary_entry = Summary(personal_information_id=personal_info.id, summary=summary)
    db.session.add(summary_entry)



    compname = []
    workmode = []
    jobrole = []
    jobtype = []
    startcom = []
    endcom = []
    for k in request.form:
        if k.startswith('companyName'):
            compname.append(request.form[k])
        if k.startswith('modeOfWork'):
            workmode.append(request.form[k])
        if k.startswith('jobRole'):
            jobrole.append(request.form[k])
        if k.startswith('jobType'):
            jobtype.append(request.form[k])
        if k.startswith('startDate'):
            startcom.append(request.form[k])
        if k.startswith('endDate'):
            endcom.append(request.form[k])

    for i in range(len(compname)):
        work_exp = WorkExperience(personal_information_id=personal_info.id, job_title=jobrole[i], company_name=compname[i],
                                  start_date=datetime.strptime(startcom[i], '%m-%d-%Y') if startcom[i] else None, end_date=datetime.strptime(endcom[i], '%m-%d-%Y') if endcom[i] else None,
                                  description=workmode[i] + ', ' + jobtype[i])
        db.session.add(work_exp)



    proname = []
    prodes = []
    prostart = []
    proend = []
    for k in request.form:
        if k.startswith('projectName'):
            proname.append(request.form[k])
        if k.startswith('projectDescription'):
            prodes.append(request.form[k])
        if k.startswith('projectStart'):
            prostart.append(request.form[k])
        if k.startswith('projectEnd'):
            proend.append(request.form[k])

    
    for i in range(len(proname)):
        project_detail = ProjectDetails(personal_information_id=personal_info.id, project_name=proname[i], description=prodes[i],
                                        start_date=datetime.strptime(prostart[i], '%m-%d-%Y') if prostart[i] else None, end_date=datetime.strptime(proend[i], '%m-%d-%Y') if proend[i] else None)
        db.session.add(project_detail)


    achead = []
    acdes = []
    acstart = []
    acend = []
    for k in request.form:
        if k.startswith('achievementHeading'):
            achead.append(request.form[k])
        if k.startswith('achievementDescription'):
            acdes.append(request.form[k])
        if k.startswith('achievementStartDate'):
            acstart.append(request.form[k])
        if k.startswith('achievementEndDate'):
            acend.append(request.form[k])

    for i in range(len(achead)):
        achievement = Achievements(personal_information_id=personal_info.id, achievement_description=achead[i] + ', ' + acdes[i])
        db.session.add(achievement)


    degree = []
    field = []
    institute = []
    marks = []
    edustart = []
    eduend = []
    for k in request.form:
        if k.startswith('degree'):
            degree.append(request.form[k])
        if k.startswith('field'):
            field.append(request.form[k])
        if k.startswith('institute'):
            institute.append(request.form[k])
        if k.startswith('marks'):
            marks.append(request.form[k])
        if k.startswith('startDate'):
            edustart.append(request.form[k])
        if k.startswith('endDate'):
            eduend.append(request.form[k])

    for i in range(len(degree)):
        education_detail = EducationDetails(personal_information_id=personal_info.id, degree_course=degree[i], field_of_study=field[i],
                                            institute=institute[i], marks_percentage_gpa=marks[i], start_date=datetime.strptime(edustart[i], '%m-%d-%Y') if edustart[i] else None,
                                            end_date=datetime.strptime(eduend[i], '%m-%d-%Y') if eduend[i] else None)
        db.session.add(education_detail)

    
    certname = []
    certorg = []
    certdate = []
    for k in request.form:
        if k.startswith('certificationTitle'):
            certname.append(request.form[k])
        if k.startswith('issuingOrganization'):
            certorg.append(request.form[k])
        if k.startswith('issueDate'):
            certdate.append(request.form[k])

    for i in range(len(certname)):
        certification_detail = CertificationDetails(personal_information_id=personal_info.id, certification_title=certname[i],
                                                    date_of_issue=datetime.strptime(certdate[i], '%m-%d-%Y') if certdate[i] else None, issuing_organization=certorg[i])
        db.session.add(certification_detail)

    skills = request.form['skills']

    skills = request.form['skills'].split(',')
    for skill in skills:
        skill_entry = Skills(personal_information_id=personal_info.id, skill=skill.strip())
        db.session.add(skill_entry)

    activities = request.form['activities']

    for activity in activities:
        activity_entry = ExtracurricularActivities(personal_information_id=personal_info.id, activity=activity.strip())
        db.session.add(activity_entry)

    language = []
    proficiency = []
    for k in request.form:
        if k.startswith('language'):
            language.append(request.form[k])
        if k.startswith('proficiency'):
            proficiency.append(request.form[k])
    
    for i in range(len(language)):
        language_competency = LanguageCompetencies(personal_information_id=personal_info.id, language = language[i],
                                                   proficiency_level = proficiency[i])
        db.session.add(language_competency)
    
    db.session.commit()


    return 'submitted successfully!'
    

if __name__ == '__main__':
    app.run(debug=True)