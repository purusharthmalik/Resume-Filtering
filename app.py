import math
import os
import re
from typing import List
from dotenv import load_dotenv
import random
import flask
from flask import Flask, jsonify, render_template, request, redirect, url_for
import fitz
import groq
from docx import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq
from docx import Document
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from pydantic import BaseModel, Field
from sqlalchemy.sql import text
from datetime import datetime
import json
from scoring import Scoring
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px

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
total_applicant_count = applicant_count_df['applicant_count'].iloc[0]

work_df = pd.read_excel('Work.xlsx')
education_df = pd.read_excel('Education.xlsx')
skills_df = pd.read_excel('Skills.xlsx')
time_df = pd.read_excel('Time.xlsx')

colors = {
    'primary': '#2b377c',
    'secondary': '#f2efe9',
    'tertiary': '#cbb27f',
    'background': 'rgba(0, 0, 0, 0)'
}

work_ex_fig = px.bar(
    work_df,
    x='experience_years',
    y='count',
    labels={'experience_years': 'Work Experience (years)', 'count': 'Count'},
    title='Work Experience Count Distribution'
)

work_ex_fig.update_traces(marker_color=colors['primary'], opacity=0.6)

work_ex_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    xaxis=dict(tickmode='linear', dtick=1),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

education_fig = px.pie(
    education_df,
    names=education_df.columns,
    values=education_df.iloc[0],
    title='Education Level Distribution'
)

education_fig.update_traces(marker=dict(colors=[colors['primary'], colors['tertiary'], colors['secondary']]), opacity=0.6)
education_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)
skills_df = skills_df.nlargest(15, 'frequency')
skills_fig = px.bar(
    skills_df,
    x='frequency',
    y='skill',
    orientation='h',
    labels={'frequency': 'Frequency', 'skill': 'Skills'},
    title='Top Skills Frequency Distribution',
    category_orders={'skill': skills_df['skill'].tolist()}
)
skills_fig.update_traces(marker_color=colors['tertiary'], opacity=0.6)
skills_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

time_df['time_stamp'] = pd.to_datetime(time_df['time_stamp']).dt.date
time_aggregated = time_df.groupby('time_stamp').size().reset_index(name='count')
time_aggregated = time_aggregated.sort_values('time_stamp')
time_fig = px.line(
    time_aggregated,
    x='time_stamp',
    y='count',
    labels={'time_stamp': 'Date', 'count': 'Submission Count'},
    title='Submission Time Distribution'
)
time_fig.update_traces(line_color=colors['primary'], opacity=0.6)
time_fig.update_layout(
    font=dict(size=16),
    margin=dict(l=10, r=10, t=80, b=20),
    xaxis=dict(
        tickmode='array',
        tickvals=time_aggregated['time_stamp'],
        tickformat='%Y-%m-%d'
    ),
    yaxis=dict(
        tickmode='linear',
        dtick=1
    ),
    plot_bgcolor=colors['secondary'],
    paper_bgcolor=colors['background']
)

dash_app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Analytics Dashboard", className='text-center mb-4', style={'fontSize': '24px', 'color': colors['primary']}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.H2(f"Total Applicants: {total_applicant_count}", className='text-center', style={'fontSize': '18px', 'color': '#000000'}), width=12)
    ]),
    dbc.Row([
                dbc.Col(dcc.Graph(figure=work_ex_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'}),
        dbc.Col(dcc.Graph(figure=education_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'})
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=skills_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'}),
        dbc.Col(dcc.Graph(figure=time_fig, config={'responsive': True}), xs=12, sm=12, md=6, lg=6, xl=6, style={'padding': '30px'})
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
    elif file_path.endswith(('.docx', '.doc')):
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
    session = db.session()
    name = request.form.get('username')
    password = request.form.get('password')
    
    res = session.execute(text(f"SELECT username FROM faculty WHERE username LIKE '{name}' AND password LIKE '{password}'"))
    try:
        list([dict(row._mapping) for row in res][0].values())[0]
        return render_template('hod_form.html')
    except (Exception):
        error = "Invalid Login Credentials!"
        return render_template('login.html', error=error)

def generate_vectors(jd_vec, dist):
    def random_unit_vector():
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        z = random.uniform(-1, 1)
        length = math.sqrt(x * x + y * y + z * z)
        
        if length == 0:
            return random_unit_vector()  # Prevent division by zero
        
        return [x / length, y / length, z / length]

    unit_vec = random_unit_vector()
    new_vec = [
        jd_vec[0] + unit_vec[0] * dist,
        jd_vec[1] + unit_vec[1] * dist,
        jd_vec[2] + unit_vec[2] * dist,
    ]
    
    return new_vec

@app.route('/filter_candidates')
def filter_candidates():
    # res = request.args.get('res')
    parsed_res = request.args.get('parsed_res')
    resume_vecs = request.args.get('resume_vecs')
    return render_template('filter.html', data=[json.loads(parsed_res), parsed_res, resume_vecs])

@app.route('/no_match', methods=['GET'])
def no_match():
    return render_template('no_match.html')

@app.route('/regular_submit', methods=['POST'])
def regular_submit():
    session = db.session()
    res = session.execute(text("SELECT p.name, p.email, p.phone_number, p.link, s.score FROM personal_information p JOIN score s WHERE p.id = s.personal_information_id ORDER BY s.score DESC;")).cursor
    session.close()

    # Creating vectors for all the resumes
    jd_vec = [10, 10, 10]
    dist = 1
    resume_vecs = []

    for _ in list(res):
        resume_vecs.append(generate_vectors(jd_vec, dist))
        dist += 1

    parsed_res = json.dumps(list(res))
    return jsonify({
        'redirect': url_for('filter_candidates', 
                        parsed_res=parsed_res, 
                        resume_vecs=json.dumps(resume_vecs))
    })

@app.route('/exact_match', methods=['POST'])
def exact_match():
    # Getting data stored in the text area
    info = request.get_json()
    # Getting the generated summary
    session = db.session()
    gen_sum = session.execute(text("SELECT id, gen_sum FROM personal_information; ")).cursor
    
    # Checking for exact match
    matching_id = set()
    for req in list(gen_sum):
        for words in info['txtbox'].split(','):
            for match in req[1].split():
                if re.search(r'\b' + words + r'\b', match):
                    matching_id.add(req[0])
                
    # Calling an empty page if there are no matching ids
    if not matching_id:
        return jsonify({'redirect': url_for('no_match')})

    # Getting the resumes with matching ids
    matching_id_str = ', '.join(map(str, matching_id))
    res = session.execute(text(f"""
            SELECT p.name, p.email, p.phone_number, p.link, s.score
            FROM personal_information p
            JOIN score s ON p.id = s.personal_information_id
            WHERE p.id IN ({matching_id_str})
            ORDER BY s.score DESC;
            """)).cursor
    session.close()

    # Creating vectors for all the resumes
    jd_vec = [10, 10, 10]
    dist = 1
    resume_vecs = []

    for _ in list(res):
        resume_vecs.append(generate_vectors(jd_vec, dist))
        dist += 1

    parsed_res = json.dumps(list(res))
    return jsonify({
        'redirect': url_for('filter_candidates', 
                        parsed_res=parsed_res, 
                        resume_vecs=json.dumps(resume_vecs))
    })


@app.route('/login',  methods=['POST', 'GET'])
def login():
    return render_template('login.html')

# Pydantic Object Format
class PersonalInformation(BaseModel):
    Name: str = Field(description="Name of the person")
    Email: str = Field(description="Email address of the person")
    Phone_Number: str = Field(description="Phone number of the person")
    Address: str = Field(description="Address of the person")
    LinkedIn_URL: str = Field(description="LinkedIn profile URL of the person")

class WorkExperience(BaseModel):
    Company_Name: str = Field(description="Name of the company")
    Mode_of_Work: str = Field(description="Mode of work (e.g., remote, on-site)")
    Job_Role: str = Field(description="Job role/title")
    Job_Type: str = Field(description="Type of job (e.g., full-time, part-time)")
    Start_Date: str = Field(description="Start date of the job")
    End_Date: str = Field(description="End date of the job")

class Project(BaseModel):
    Name_of_Project: str = Field(description="Name of the project")
    Description: str = Field(description="Description of the project")
    Start_Date: str = Field(description="Start date of the project")
    End_Date: str = Field(description="End date of the project")

class Achievement(BaseModel):
    Heading: str = Field(description="Heading of the achievement")
    Description: str = Field(description="Description of the achievement")
    Start_Date: str = Field(description="Start date of the achievement")
    End_Date: str = Field(description="End date of the achievement")
    
class EducationDetails(BaseModel):
    Degree_Name: str = Field(description="Name of the degree persued by the candidate (Like BSc, B.Tech, MSc BCA, Phd, etc.)")
    Field_of_Study: str = Field(description="Field of study")
    University: str = Field(description="Name of the University or Institute")
    Marks_Percentage_GPA: str = Field(description="Marks/Percentage/GPA")
    Start_Date: str = Field(description="Start date of the education")
    End_Date: str = Field(description="End date of the education")
    
class Certification(BaseModel):
    Certification_Title: str = Field(description="Title of the certification")
    Issuing_Organization: str = Field(description="Name of the issuing organization")
    Date_Of_Issue: str = Field(description="Date of issue of the certification")
    
class LanguageCompetency(BaseModel):
    Language: str = Field(description="Language")
    Proficiency: str = Field(description="Proficiency level")

class ResumeJSON(BaseModel):
    Personal_Information: PersonalInformation = Field(description="Personal information of the person")
    Summary: str = Field(description="Summary or objective of the person")
    Work_Experience: List[WorkExperience] = Field(description="Work experience details")
    Projects: List[Project] = Field(description="Project details")
    Achievements: List[Achievement] = Field(description="Achievement details")
    Education: List[EducationDetails] = Field(description="Educational background")
    Certifications: List[Certification] = Field(description="Certification details")
    Skills: List[str] = Field(description="Skills of the person")
    Extracurricular_Activities: List[str] = Field(description="Extracurricular activities of the person")
    Language_Competencies: List[LanguageCompetency] = Field(description="Language competencies")

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

        client = ChatGroq(
            temperature=0,
            model='llama3-70b-8192',
            api_key="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"
        )
        
        parser = JsonOutputParser(pydantic_object=ResumeJSON)

        prompt = PromptTemplate(
                        template="""
                                You are a professional resume parsing agent.
                                You can leave a key empty if you are not sure about the value.
                                {format_instructions}
                                {resume}
                            """,
                        input_variables=["resume"],
                        partial_variables={"format_instructions": parser.get_format_instructions()}
                )

        chain = prompt | client | parser
        text = chain.invoke({"resume": document_text})
        
        if text['Personal_Information'] == []:
            text['Personal_Information'] = [{"Name": '',"Email": '',"Phone_Number": '',"Address": '',"LinkedIn_URL": ''}]
        
        if text['Work_Experience'] == []:
            text['Work_Experience'] = [{"Company_Name": '',"Mode_of_Work": '',"Job_Role": '',"Start_Date": '',"End_Date": ''}]

        if text['Projects'] == []:
            text['Projects'] = [{"Name_of_Project": '',"Description": '',"Start_Date": '',"End_Date": ''}]

        if text['Achievements'] == []:
            text['Achievements'] = [{"Heading": '',"Description": '',"Start_Date": '',"End_Date": ''}]

        if text['Education'] == []:
            text['Education'] = [{"Degree_Name": '',"Field_of_Study": '',"Institute": '',"Marks/Percentage/GPA": '',"Start_Date": '',"End_Date": ''}]
            
        if text['Certifications'] == []:
            text['Certifications'] = [{"Certification_Title": '',"Issuing_Organization": '',"Date_Of_Issue": ''}]

        if text['Language_Competencies'] == []:
            text['Language_Competencies'] = [{"Language": '',"Proficiency": ''}]
        # print(text['Education'])
        output_filename = app.config['GENERATED_JSON']
        with open(output_filename, 'w') as json_file:
            json.dump(text, json_file, indent=4)
        return redirect(url_for('resume_form'))


@app.route('/resume_form')
def resume_form():
    with open(app.config['GENERATED_JSON']) as f:
        resume_data = json.load(f)
    return render_template('resume_form.html', data=resume_data)

@app.route('/analytics', methods=['POST', 'GET'])
def view_analytics():
    session = db.session()
    res = session.execute(text(f'''SELECT COUNT(id) FROM personal_information'''))
    res = list([dict(row._mapping) for row in res][0].values())[0]
    df = pd.DataFrame({'applicant_count':res}, [0])
    df.to_excel('Applicant_Count.xlsx', index=False)

    bac = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'B%' or degree_course LIKE 'b%' '''))
    mas = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'M%' or degree_course LIKE 'm%' '''))
    phd = session.execute(text(
        f'''SELECT COUNT(degree_course) FROM education_details WHERE degree_course LIKE 'PhD%' or degree_course LIKE 'phd%'
            or degree_course LIKE 'Phd%' or degree_course LIKE 'PHD%' '''))

    bac = list([dict(row._mapping) for row in bac][0].values())[0]
    mas = list([dict(row._mapping) for row in mas][0].values())[0]
    phd = list([dict(row._mapping) for row in phd][0].values())[0]

    df = pd.DataFrame({'Bachelors': bac, 'Masters': mas, 'Doctorate': phd}, [0])
    df.to_excel('Education.xlsx', index=False)

    res = session.execute(text('''SELECT time_stamp FROM personal_information'''))
    ress = [dict(row._mapping) for row in res]
    df = pd.DataFrame(ress)
    df.to_excel('Time.xlsx', index=False)

    res = session.execute(text('''SELECT personal_information_id, SUM(DATEDIFF(end_date, start_date)) AS total_workex
        FROM work_experience GROUP BY personal_information_id'''))
    ress = [dict(row._mapping) for row in res]
    df = pd.DataFrame(ress)
    df = df.apply(pd.to_numeric)
    df['experience_years'] = df['total_workex'] // 365
    df = df.groupby('experience_years').size().reset_index(name='count')
    df.to_excel('Work.xlsx', index=False)

    res = session.execute(text('''SELECT skill, COUNT(*) AS frequency FROM skills GROUP BY  skill ORDER BY frequency DESC'''))
    res = [dict(row._mapping) for row in res]
    df = pd.DataFrame(res)
    df.to_excel('Skills.xlsx', index=False)
    session.close()

    return flask.redirect('/plotly/')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')


# shila takes over ...
# <======================================================================================================================>

def summ(rj):
    prompt = f'''You are an expert to fetch all the keywords from a given resume.
                You will be given a resume in json format.
                Read the entire resume and figure out all the keywords.
                Be careful that your list MUST include ALL the keywords mentioned in the resume.
                Start with 1.
                {rj}
             '''
    
    client = groq.Groq(api_key=os.environ["CHATGROQ_API_KEY"])
    response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-70b-8192",
                seed=42
            )
    kws = response.choices[0].message.content
    return ','.join([match.strip() for match in re.findall(r'\d+\.(.*)', kws)])

class PersonalInformation(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    linkedin_url = db.Column(db.String(255))
    gen_sum = db.Column(db.String(4096))
    link = db.Column(db.String(255))
    time_stamp = db.Column(db.Date)

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    password = db.Column(db.String(100))

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
    gen_sum = summ(rj=open('resume.json', 'r').read())

    personal_info = PersonalInformation(name=name, email=email, phone_number=phone, address=address,
                                        linkedin_url=linkedin, gen_sum=gen_sum, link=resume_filepath,
                                        time_stamp=datetime.today())
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

    activities = request.form['activities'].split(',')

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
    resume_info = {'Keywords':gen_sum,
                   'Work_Experience':scoring_we,
                   'Projects':scoring_prj,
                   'Achievements':scoring_ach,
                   'Education':scoring_ed,
                   'Certifications':scoring_cert,
                   'Skills':skills,
                   'Language_Competencies':language}

    jd_text = open(r"S:\resume_parsing\job_descriptions\Prof.-CS-Sitare-University.txt", encoding='utf-8').read()

    resume_score = Scoring(jd_text, resume_info).final_similarity()
    # print(resume_score)
    db.session.add(Score(personal_information_id=personal_info.id, 
                         score=resume_score))

    db.session.commit()

    # time.sleep(5)
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)