import os
from dotenv import load_dotenv
import time
import flask
from flask import Flask, render_template, request, redirect, url_for
import fitz
from docx import Document
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from datetime import datetime
import dspy
import json
from scoring import Scoring
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

load_dotenv()
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['GENERATED_JSON'] = 'resume.json'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configuring the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DB_CONNECTION"]
app.app_context().push()
db = SQLAlchemy(app)

# Storing the filepath
resume_filepath = ""

#==================================THAT DASH CODE=======================================
#=======================================================================================

dash_app = dash.Dash(__name__, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/plotly/')

applicant_count_df = pd.read_excel('Applicant_Count.xlsx')
total_applicant_count = applicant_count_df['total_applicant_count'].iloc[0]

work_ex_years_df = pd.read_excel('WorkExYears.xlsx')
work_ex_years = work_ex_years_df.iloc[0].to_dict()

education_level_df = pd.read_excel('EducationLevel.xlsx')
education_levels = education_level_df.iloc[0].to_dict()

total_applicant_fig = go.Figure(go.Bar(
    x=['Total Applicants'],
    y=[total_applicant_count],
    marker_color='blue'
))
total_applicant_fig.update_layout(
    title_text='Total Applicants',
    xaxis_title='',
    yaxis_title='Count',
    font=dict(size=10),
    margin=dict(l=10, r=10, t=30, b=10)
)

work_ex_fig = px.bar(
    x=list(work_ex_years.keys()),
    y=list(work_ex_years.values()),
    labels={'x': 'Years of Experience', 'y': 'Number of Applicants'},
    title='Work Experience Years Distribution'
)
work_ex_fig.update_layout(
    font=dict(size=10),
    margin=dict(l=10, r=10, t=30, b=10)
)

education_level_fig = px.pie(
    names=list(education_levels.keys()),
    values=list(education_levels.values()),
    title='Education Level Distribution'
)
education_level_fig.update_layout(
    font=dict(size=10),
    margin=dict(l=10, r=10, t=30, b=10)
)

wordcloud = WordCloud(background_color='white').generate_from_frequencies(education_levels)
plt.figure(figsize=(4, 2.5))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Top Skills', fontsize=5, loc='left')
plt.savefig('static/wordcloud.png', dpi=1500, bbox_inches='tight')
plt.close()

dash_app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Analytics Dashboard", className='text-center text-primary mb-4', style={'fontSize': '24px'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=total_applicant_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6),
        dbc.Col(dcc.Graph(figure=work_ex_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=education_level_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6),
        dbc.Col(html.Img(src='/static/wordcloud.png', style={'width': '100%', 'height': 'auto'}), xs=12, sm=12, md=6, lg=6, xl=6)
    ])
], fluid=True)

#===========================================END DASH================================================
#===================================================================================================

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
    elif file_path.endswith('.docx') or file_path.endswith('.doc'):
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
def homepage():
    return render_template('home.html')


@app.route('/candidate_button', methods=['POST', 'GET'])
def candidate_button():
    return render_template('upload.html')


@app.route('/hod_button', methods=['POST', 'GET'])
def hod_button():
    return render_template('hod_form.html')


@app.route('/filterr', methods=['POST', 'GET'])
def filterr():
    session = db.session()
    res = session.execute(text("SELECT p.name, p.email, p.phone_number, p.link, s.score FROM personal_information p JOIN score s WHERE p.id = s.personal_information_id ORDER BY s.score DESC;")).cursor
    session.close()

    return render_template('filter.html', data=res)

@app.route('/login',  methods=['POST', 'GET'])
def login():
    return render_template('login.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file:
        global resume_filepath
        resume_filepath = "uploads/" + file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        document_text = read_document(file_path)

        gem = dspy.Google("models/gemini-1.0-pro", api_key=os.environ["GOOGLE_API_KEY"])
        dspy.settings.configure(lm=gem)

        class Parser(dspy.Signature):
            """
            You are a professional resume parsing agent.
            So do as follows:
            1. Extract Personal Information of the applicant with keys being:
            a. Extract name of the applicant.
            b. Extract email of the applicant.
            c. Extract phone number of the applicant.
            d. Exract address of the applicant.
            e. Extract linkedin url of the applicant (Add https:// in front of the link if it is not already present).
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
            You are to generate a valid JSON script as output. Properly deal with trailing commas while formatting the output file.
            Take this empty json format and fill it up:
            {
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
            }"""

            resume = dspy.InputField(desc="This is the resume.")
            json_resume = dspy.OutputField(desc="The JSON script of the resume.")

        output = dspy.Predict(Parser)
        response = output(resume=document_text).json_resume

        text = response.replace('"Personal_Information": [],',
                                '"Personal_Information": [{"Name": null,"Email": null,"Phone_Number": null,"Address": null,"LinkedIn_URL": null}],')
        text = text.replace('"Work_Experience": [],',
                            '"Work_Experience": [{"Company_Name": null,"Mode_of_Work": null,"Job_Role": null,"Start_Date": null,"End_Date": null}],')
        text = text.replace('"Projects": [],',
                            '"Projects": [{"Name_of_Project": null,"Description": null,"Start_Date": null,"End_Date": null}],')
        text = text.replace('"Achievements": [],',
                            '"Achievements": [{"Heading": null,"Description": null,"Start_Date": null,"End_Date": null}],')
        text = text.replace('"Education": [],',
                            '"Education": [{"Degree/Course": null,"Field_of_Study": null,"Institute": null,"Marks/Percentage/GPA": null,"Start_Date": null,"End_Date": null}],')
        text = text.replace('"Certifications": [],',
                            '"Certifications": [{"Certification_Title": null,"Issuing_Organization": null,"Date_Of_Issue": null}],')
        text = text.replace('"Language_Competencies": []',
                            '"Language_Competencies": [{"Language": null,"Proficiency": null}]')
        # print(text)
        response_json = json.loads(text, strict=False)
        output_filename = app.config['GENERATED_JSON']
        with open(output_filename, 'w') as json_file:
            json.dump(response_json, json_file, indent=4)
        return redirect(url_for('resume_form'))


@app.route('/resume_form')
def resume_form():
    with open(app.config['GENERATED_JSON']) as f:
        resume_data = json.load(f)
    return render_template('resume_form.html', data=resume_data)

@app.route('/analytics', methods=['POST', 'GET'])
def view_analytics():
    df = pd.DataFrame()
    session = db.session()
    res = session.execute(text(f'''SELECT COUNT(id) FROM personal_information'''))

    for count in res:
        df['total_applicant_count'] = count
    # df.to_excel('Applicant_Count.xlsx')
    df = pd.DataFrame()
    bac = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'B%' or degree_course LIKE 'b%' '''))
    mas = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'M%' or degree_course LIKE 'm%' '''))
    phd = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'PhD%' or degree_course LIKE 'phd%'
            or degree_course LIKE 'Phd%' or degree_course LIKE 'PHD%' '''))

    for count in bac:
        df['Bachelors'] = count
    for count in mas:
        df['Masters'] = count
    for count in phd:
        df['Doctorate'] = count
    # df.to_excel('EducationLevel.xlsx')

    return flask.redirect('/plotly/')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')


# shila takes over ...
# <======================================================================================================================>

gem = dspy.Google("models/gemini-1.0-pro", api_key=os.environ["GOOGLE_API_KEY"])
dspy.settings.configure(lm=gem)


class Summary(dspy.Signature):
    """
    You are an expert in summarizing text resumes of candidates applying for a
    job position. The resume is given in the format of json and your task is to
    write the summary of this candidate from this resume. Be careful to include all
    relevant skills mentioned in the resume.
    """
    resume_json = dspy.InputField(desc='This is the resume in JSON format.')
    summary = dspy.OutputField(desc='The summary of the resume.')


summ = dspy.Predict(Summary)


class PersonalInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    linkedin_url = db.Column(db.String(255))
    gen_sum = db.Column(db.String(4096))
    link = db.Column(db.String(255))


class Filter(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    cat = db.Column(db.String(16))  # dummy. will be changed later.
    eli = db.Column(db.String(16))  # dummy. will be changed later.


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

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personal_information_id = db.Column(db.Integer, db.ForeignKey('personal_information.id'))
    score = db.Column(db.Double)

# db.drop_all()  # if any changes made to the above database classes.
db.create_all()


@app.route('/submit', methods=['POST'])
def submit():
    # print(request.form)
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    linkedin = request.form['linkedin'].lower()
    gen_sum = summ(resume_json=open('resume.json', 'r').read()).summary

    personal_info = PersonalInformation(name=name, email=email, phone_number=phone, address=address,
                                        linkedin_url=linkedin, gen_sum=gen_sum, link=resume_filepath)
    db.session.add(personal_info)
    db.session.commit()  # commits here to generate the id

    summary = request.form['summary']
    summary_entry = Summary(personal_information_id=personal_info.id, summary=summary)
    db.session.add(summary_entry)

    try:
        cat = request.form['cat']
        eli = request.form['eli']
    except:
        cat = None
        eli = None
    filt = Filter(cat=cat, eli=eli)
    db.session.add(filt)

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

    scoring_we = []
    for i in range(len(compname)):
        # For scoring
        scoring_we.append(compname[i] + ',' + jobrole[i] + ',' + workmode[i] + ',' + jobtype[i])
        work_exp = WorkExperience(personal_information_id=personal_info.id, job_title=jobrole[i],
                                  company_name=compname[i],
                                  start_date=datetime.strptime(startcom[i], '%m-%d-%Y') if startcom[i] else None,
                                  end_date=datetime.strptime(endcom[i], '%m-%d-%Y') if endcom[i] else None,
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

    scoring_prj = []
    for i in range(len(proname)):
        # For scoring
        scoring_prj.append(proname[i] + ',' + prodes[i])
        project_detail = ProjectDetails(personal_information_id=personal_info.id, project_name=proname[i],
                                        description=prodes[i],
                                        start_date=datetime.strptime(prostart[i], '%m-%d-%Y') if prostart[i] else None,
                                        end_date=datetime.strptime(proend[i], '%m-%d-%Y') if proend[i] else None)
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

    scoring_ach = []
    for i in range(len(achead)):
        # For scoring
        scoring_ach.append(achead[i] + ', ' + acdes[i])
        achievement = Achievements(personal_information_id=personal_info.id,
                                   achievement_description=achead[i] + ', ' + acdes[i])
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

    scoring_ed = []
    for i in range(len(degree)):
        # For scoring
        scoring_ed.append(degree[i] + ',' + institute[i] + ',' + marks[i])
        education_detail = EducationDetails(personal_information_id=personal_info.id, degree_course=degree[i],
                                            field_of_study=field[i],
                                            institute=institute[i], marks_percentage_gpa=marks[i],
                                            start_date=datetime.strptime(edustart[i], '%m-%d-%Y') if edustart[
                                                i] else None,
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

    scoring_cert = []
    for i in range(len(certname)):
        # For scoring
        scoring_cert.append(certname[i] + ',' + certorg[i])
        certification_detail = CertificationDetails(personal_information_id=personal_info.id,
                                                    certification_title=certname[i],
                                                    date_of_issue=datetime.strptime(certdate[i], '%m-%d-%Y') if
                                                    certdate[i] else None, issuing_organization=certorg[i])
        db.session.add(certification_detail)

    # skills = request.form['skills']

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
        language_competency = LanguageCompetencies(personal_information_id=personal_info.id, language=language[i],
                                                   proficiency_level=proficiency[i])
        db.session.add(language_competency)

    # Scoring
    resume_info = {'Summary':gen_sum,
                   'Work Experience':scoring_we,
                   'Projects':scoring_prj,
                   'Achievements':scoring_ach,
                   'Education Details':scoring_ed,
                   'Certifications':scoring_cert,
                   'Skills':skills,
                   'Languages':language}

    jd_text = open(r"S:\resume_parsing\job_descriptions\Prof.-CS-Sitare-University.txt", encoding='utf-8').read()

    resume_score = Scoring(jd_text, resume_info).final_similarity()
    db.session.add(Score(personal_information_id=personal_info.id, 
                         score=resume_score))

    db.session.commit()

    # time.sleep(5)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)