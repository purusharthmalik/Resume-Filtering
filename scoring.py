import os
import json
import groq
import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

def jd_parser(jd_text):
    client = groq.Groq(api_key=os.environ["CHATGROQ_API_KEY"])

    chat_completion = client.chat.completions.create(
    messages=[
                {
                    "role": "user",
                    "content": f"seed=33"
                    f"You are a professional job description parsing agent. "
                    f"So do as follows: "
                    f"1. Generate a Summary of the job description."
                    f"2. Extract the Work Experience requirements with keys being: "
                    f"a. Company name (Optional) "
                    f"b. Job Role "
                    f"c. Job Type (Full Time or Intern) "
                    f"3. Extract the Project details requirements with keys being: "
                    f"a. Name of Project with short introduction of it, if mentioned "
                    f"b. Description of project. "
                    f"4. Extract the Achievement details requirements with keys being: "
                    f"a. Heading with short introduction of it, if mentioned "
                    f"b. Description of the heading. "
                    f"5. Extract the Education details requirements with keys being: "
                    f"a. Degree/Course"
                    f"b. Field of Study (note: usually written alongside degree, extract from 'degree' key if that is the case) "
                    f"c. Institute"
                    f"d. Marks/Percentage/GPA"
                    f"6. Extract the Certification details requirements with keys being: "
                    f"a. Certification Title "
                    f"b. Issuing Organization "
                    f"7. List all the skills from the following document. "
                    f"8. List me all the language competencies from the following document. "
                    f"You are to generate a valid JSON script as output. Properly deal with trailing commas while formatting the output file. Do not write any other note or introductory sentence, stick to generating only the valid json."
                    f"Strictly don't write any additional notes whatsoever."
                    f"When generating output strictly follow this format: "
                    f"1st line: 'Here is the JSON output', No space and next line till last line: Entire JSON content"
                    f"Take this empty json format and fill it up: "
                    f'{{ '
                    f'"Summary": "", '
                    f'"Work_Experience": [ '
                    f'{{ '
                    f'"Company_Name": "", '
                    f'"Job_Role": "", '
                    f'"Job_Type": "", '
                    f'}} '
                    f'], '
                    f'"Projects": [ '
                    f'{{ '
                    f'"Name_of_Project": "", '
                    f'"Description": "", '
                    f'}} '
                    f'], '
                    f'"Achievements": [ '
                    f'{{ '
                    f'"Heading": "", '
                    f'"Description": "", '
                    f'}} '
                    f'], '
                    f'"Education": [ '
                    f'{{ '
                    f'"Degree/Course": "", '
                    f'"Field_of_Study": "", '
                    f'"Institute": "", '
                    f'"Marks/Percentage/GPA": "", '
                    f'}} '
                    f'], '
                    f'"Certifications": [ '
                    f'{{ '
                    f'"Certification_Title": "", '
                    f'"Issuing_Organization": "", '
                    f'}} '
                    f'], '
                    f'"Skills": [], '
                    f'"Language_Competencies": [ '
                    f'{{ '
                    f'"Language": "", '
                    f'"Proficiency": "" '
                    f'}} '
                    f'] '
                    f'}} '
                    f"Job Description: {jd_text}",
                }
            ],
            model="llama3-70b-8192",
        )

    text = chat_completion.choices[0].message.content

    start_index = text.find('{')
    text = text[start_index:]
    last_brace_index = text.rfind('}')
    if last_brace_index != -1:
        text = text[:last_brace_index + 1]

    text = text.replace('"Personal_Information": [],',
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
    response_json = json.loads(text, strict=True)
    return response_json

class Scoring:

    def __init__(self, job_description, resume):

        self.job_description = job_description
        self.resume = resume

        response = jd_parser(self.job_description)
        print(response)
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

            elif field in self.resume.keys():
                response_field = str(self.response['Summary'])
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