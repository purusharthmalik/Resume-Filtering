import ast
from langchain_community.utilities import SQLDatabase

def get_resumes_from_db(db_connection_str, query, info, field_name):
    db = SQLDatabase.from_uri(db_connection_str)
    results = ast.literal_eval(db.run(query, fetch='all'))
    
    for result in results:
        deets_list = [{result[1].split('-->')[0]:result[1].split('-->')[1]}]
        for col in result[2:]:
            if col is not None:
                deets_list.append({col.split('-->')[0]:col.split('-->')[1]})
        
        if result[0] not in info.keys():
            info[result[0]] = {field_name:deets_list}
        else:
            info[result[0]][field_name] = deets_list
    
    return info

def get_resume_info():
    info = dict()
    db_connection_str = "mysql://root:@127.0.0.1/resume"
    
    # Personal Info
    personal_query = '''
    SELECT 
        id,
        CONCAT('name-->', GROUP_CONCAT(name ORDER BY id)) AS name,
        CONCAT('email-->', GROUP_CONCAT(email ORDER BY id)) AS email,
        CONCAT('phone_number-->', GROUP_CONCAT(phone_number ORDER BY id)) AS phone_number,
        CONCAT('address-->', GROUP_CONCAT(address ORDER BY id)) AS address,
        CONCAT('linkedin_url-->', GROUP_CONCAT(linkedin_url ORDER BY id)) AS linkedin_url,
        CONCAT('gen_sum-->', GROUP_CONCAT(gen_sum ORDER BY id)) AS gen_sum
    FROM 
        personal_information
    GROUP BY 
        id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, personal_query, info, "Personal Information")
    except:
        pass

    # Education
    education_query = '''
    SELECT 
        personal_information_id,
        CONCAT('degree_courses-->', GROUP_CONCAT(degree_course ORDER BY id)) AS degree_courses,
        CONCAT('fields_of_study-->', GROUP_CONCAT(field_of_study ORDER BY id)) AS fields_of_study,
        CONCAT('institutes-->', GROUP_CONCAT(institute ORDER BY id)) AS institutes,
        CONCAT('marks_percentages_gpas-->', GROUP_CONCAT(marks_percentage_gpa ORDER BY id)) AS marks_percentages_gpas
    FROM 
        education_details
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, education_query, info, "Education Details")
    except:
        pass

    # Certification
    certification_query = '''
    SELECT 
        personal_information_id,
        CONCAT('certification_title-->', GROUP_CONCAT(certification_title ORDER BY id)) AS certification_title,
        CONCAT('date_of_issue-->', GROUP_CONCAT(date_of_issue ORDER BY id)) AS date_of_issue,
        CONCAT('issuing_organization-->', GROUP_CONCAT(issuing_organization ORDER BY id)) AS issuing_organization
    FROM 
        certification_details
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, certification_query, info, "Certifications")
    except:
        pass

    # Achievements
    achi_query = '''
    SELECT 
        personal_information_id,
        CONCAT('achievement_description-->', GROUP_CONCAT(achievement_description ORDER BY id)) AS achievement_description
    FROM 
        achievements
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, achi_query, info, "Achievements")
    except:
        pass

    # Languages
    language_query = '''
    SELECT 
        personal_information_id,
        CONCAT('language-->', GROUP_CONCAT(language ORDER BY id)) AS language,
        CONCAT('proficiency_level-->', GROUP_CONCAT(proficiency_level ORDER BY id)) AS proficiency_level
    FROM 
        language_competencies
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, language_query, info, "Languages")
    except:
        pass

    # Projects
    project_query = '''
    SELECT 
        personal_information_id,
        CONCAT('project_name-->', GROUP_CONCAT(project_name ORDER BY id)) AS project_name,
        CONCAT('description-->', GROUP_CONCAT(description ORDER BY id)) AS description
    FROM 
        project_details
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, project_query, info, "Projects")
    except:
        pass

    # Skills
    skill_query = '''
    SELECT 
        personal_information_id,
        CONCAT('skill-->', GROUP_CONCAT(skill ORDER BY id)) AS skill
    FROM 
        skills
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, skill_query, info, "Skills")
    except:
        pass

    # Work Experience
    we_query = '''
    SELECT 
        personal_information_id,
        CONCAT('job_title-->', GROUP_CONCAT(job_title ORDER BY id)) AS job_title,
        CONCAT('company_name-->', GROUP_CONCAT(company_name ORDER BY id)) AS company_name,
        CONCAT('description-->', GROUP_CONCAT(description ORDER BY id)) AS description
    FROM 
        work_experience
    GROUP BY 
        personal_information_id;
    '''
    try:
        info = get_resumes_from_db(db_connection_str, we_query, info, "Work Experience")
    except:
        pass

    return info