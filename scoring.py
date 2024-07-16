import os
import json
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

class Work_Details(BaseModel):
    Company: str = Field(description="Company (Optional)")
    Job_Role: str = Field(description="Job Role (Optional)")
    Job_Description: str = Field(description="Description of the work experience")

class Proj_Details(BaseModel):
    Name_of_Project: str = Field(description="Name of the Project (Optional)")
    Description: str = Field(description="Description of the Project")

class Achievement_Details(BaseModel):
    Heading: str = Field(description="Heading of the Achievement (Optional)")
    Description: str = Field(description="Description of the Achievement (Optional)")
    
class Education_Details(BaseModel):
    Degree_Name: str = Field(description="Name of the degree or the course required for the job (Optional)")
    Field_of_Study: str = Field(description="Field of study required for the job (Optional)")
    Institute: str = Field(description="Institute required for the job (Optional)")
    Marks_Percentage_GPA: str = Field(description="Marks required for the job (Optional)")
    
class Certification_Details(BaseModel):
    Certification_Title: str = Field(description="Title of the certification required for the job (Optional)")
    Issuing_Organization: str = Field(description="Name of the issuing organization (Optional)")
    
class Job_Description_JSON(BaseModel):
    Keywords: list[str] = Field(description="A comprehensive list of all the keywords present in the job description.")
    Work_Experience: list[Work_Details] = Field(description="Required Work Experience for the job")
    Projects: list[Proj_Details] = Field(description="Required projects for the job")
    Achievements: list[Achievement_Details] = Field(description="Required achievements for the job")
    Certifications: list[Certification_Details] = Field(description="Required certifications for the job")
    Education: list[Education_Details] = Field(description="Required educational background for the job")
    Skills: list[str] = Field(description="Skills required for the job")
    Language_Competencies: list[str] = Field(description="Languages required for the job (Optional)")

def jd_parser(jd_text):
    client = ChatGroq(
        temperature=0,
        model='llama3-70b-8192',
        api_key=os.environ["CHATGROQ_API_KEY"]
        )

    parser = JsonOutputParser(pydantic_object=Job_Description_JSON)

    prompt = PromptTemplate(
            template="""
                    You are a professional job description parsing agent.
                    If the description is <Optional>, do not fill anything if you are not perfectly sure.
                    {format_instructions}
                    {resume}
                """,
            input_variables=["resume"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | client | parser
    text = chain.invoke({"resume": jd_text})
    # print(text)
    response_dict = json.dumps(text, indent=4)
    return json.loads(response_dict)

class Scoring:

    def __init__(self, job_description, resume):

        self.job_description = job_description
        self.resume = resume

        response = jd_parser(self.job_description)
        self.response = self.remove_nulls(response)

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
        model_name = r'S:\resume_parsing\Resume-Manager\Resume_Manager\models\intfloate5-small-v2'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        similarity_arr = dict()
        alpha = 0.8

        for field in self.response.keys():
            if len(self.response[field]) != 0 and any([i.isalnum() for i in self.resume[field]]):
                response_field = str(self.response[field])
                resume_field = str(self.resume[field])

                response_embedding = self.get_embeddings(response_field, tokenizer, model)
                resume_embedding = self.get_embeddings(resume_field, tokenizer, model)
                
                cosine = self.cosine_sim(response_embedding, resume_embedding)
                euclidean = self.frobenius_sim(response_embedding, resume_embedding)
                
                similarity_arr[field] = (alpha * cosine + (1 - alpha) * euclidean).item()

            elif any([i.isalnum() for i in str(self.resume[field])]):
                response_field = str(self.response['Keywords'])
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
        similarity = cosine_similarity(response_embedding.numpy(), resume_embedding.numpy())
        return 1. if similarity[0][0] > 1 else similarity[0][0]
    
    # Function to calculate the Frobenius norm
    def frobenius_sim(self, response_embedding, resume_embedding):
        return 1 / (1 + abs(torch.norm(response_embedding) - torch.norm(resume_embedding)))
    
# Driver code
# if __name__ == "__main__":
#     # Getting the job description
#     jd_text = open(r"S:\resume_parsing\job_descriptions\Prof.-CS-Sitare-University.txt", encoding='utf-8').read()

#     # Getting the resumes
#     resume_info = get_resume_info()

#     # Scoring the resumes
#     scores = dict()
#     for idx, resume in zip(resume_info.keys(), resume_info.values()):
#         resume['Summary'] = resume['Personal Information'][5]['gen_sum']
#         scores[idx] = Scoring(jd_text, resume).final_similarity()

#     print(scores)
