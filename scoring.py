import json
import torch
import dspy
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAI
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from extract_from_db import get_resume_info
from dotenv import load_dotenv

load_dotenv()

class JobDescription(dspy.Signature):
    """
        You are a professional job description parsing agent.
        All the points are mandatory. You can not skip any point. Create key names in JSON as per the given key names.
        Perform the following steps for the given job description:
        1. Extract me the Summary of the job (mandatory) (Key Name - Summary).
        2. Extract me Work Experience details with keys being (Key Name - Work Experience):
        a. Job Role
        b. Job Type (Full Time or Intern)
        3. Extract me Project details with keys being (Key Name - Projects):
        a. Name of Project with short introduction of it, if mentioned
        b. Description of project.
        4. Extract me Achievement details with keys being (Key Name - Achievements):
        a. Heading with short introduction of it, if mentioned
        b. Description of the heading.
        5. Extract me Education Details with keys being (mandatory) (Key Name - Education Details):
        a. Degree/Course
        b. Field of Study (note: usually written alongside degree, extract from 'degree' key if that is the case)
        c. Institute
        d. Marks/Percentage/GPA
        6. Extract me Certification details with keys being (Key Name - Certifications):
        a. Certification Title
        b. Issuing Organization
        7. List me all the skills needed from the following document (mandatory) (Key Name - Skills).
        8. List me all the language competencies from the following document (Key Name - Languages).
        You are to generate a valid JSON script as output. Properly deal with trailing commas while formatting the output file.
    """
    jd = dspy.InputField(desc='This is the job description.')
    summary = dspy.OutputField(desc='JSON script for the job description.')
            
class Scoring:

    def __init__(self, job_description, resume):

        self.job_description = job_description
        self.resume = resume

        llm = dspy.Google("models/gemini-1.0-pro", api_key=os.environ["GOOGLE_API_KEY"])
        dspy.settings.configure(lm=llm)

        output = dspy.Predict(JobDescription)
        response = json.loads(output(jd = self.job_description).summary[8:-4])
        self.response = self.remove_nulls(response)

        return None


    # Function to remove null values from the output
    def remove_nulls(self, value):
        if isinstance(value, dict):
            return {k: self.remove_nulls(v) for k, v in value.items() if v is not None}
        elif isinstance(value, list):
            return [self.remove_nulls(item) for item in value if item is not None]
        else:
            return value
        
    # Function to calculate the final similarity score
    def final_similarity(self):
        model_name = 'intfloat/e5-small-v2'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        similarity_arr = dict()
        alpha = 0.8

        for field in self.response.keys():
            if field in self.resume.keys() and len(self.response[field]) != 0:
                response_field = str(self.response[field])
                resume_field = str(self.resume[field])

                response_embedding = self.get_embeddings(response_field, tokenizer, model)
                resume_embedding = self.get_embeddings(resume_field, tokenizer, model)
                
                cosine = self.cosine_sim(response_embedding, resume_embedding)
                euclidean = self.frobenius_sim(response_embedding, resume_embedding)
                
                similarity_arr[field] = (alpha * cosine + (1 - alpha) * euclidean).item()
            else:
                similarity_arr[field] = 0
                
        final_score = 0
        for i in similarity_arr.values():
            final_score += (100/8) * i
            
        return final_score


    # Function to get the text embeddings
    def get_embeddings(self, text, tokenizer, model):
        inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings
    
    # Function to calculate the cosine similarity
    def cosine_sim(self, response_embedding, resume_embedding):
        similarity = cosine_similarity(resume_embedding.numpy(), resume_embedding.numpy())
        return 1. if similarity[0][0] > 1 else similarity[0][0]
    
    # Function to calculate the Frobenius norm
    def frobenius_sim(self, response_embedding, resume_embedding):
        return 1 / (1 + abs(torch.norm(response_embedding) - torch.norm(resume_embedding)))
    
# Driver code
if __name__ == "__main__":
    # Getting the job description
    jd_text = open(r"S:\resume_parsing\job_descriptions\Prof.-CS-Sitare-University.txt", encoding='utf-8').read()

    # Getting the resumes
    resume_info = get_resume_info()

    # Scoring the resumes
    scores = dict()
    for idx, resume in zip(resume_info.keys(), resume_info.values()):
        resume['Summary'] = resume['Personal Information'][5]['gen_sum']
        scores[idx] = Scoring(jd_text, resume).final_similarity()

    print(scores)