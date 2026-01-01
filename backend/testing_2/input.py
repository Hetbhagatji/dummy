from job_schema import Job
from pipeline import parse_job_description

# Example job description
job_text = """
Azure DevOps Engineer

We are looking for a driven and experienced Azure DevOps Engineer to join our dynamic team. The ideal candidate will have a strong background in CI/CD pipelines, infrastructure as code, cloud architecture, and automation within the Microsoft Azure ecosystem. You will collaborate with developers, QA, and operations teams to streamline deployments and ensure reliability, scalability, and performance across all environments.



Experience:



●	2-5+ Years
 
Responsibilities:



●	Develop and implement technical efforts to design, build, and deploy Azure applications at the direction of lead architects, including large-scale data processing, computationally intensive statistical modeling, and advanced analytics.
●	Participate in all aspects of the software development life cycle, including planning, requirements, development, testing, and quality assurance.
●	Troubleshoot incidents, identify root cause, fix and document problems, and implement preventive measures.
●	Educate teams on the implementation of new cloud-based initiatives, providing associated training as required.
●	Employ exceptional problem-solving skills, with the ability to see and solve issues before they affect business productivity.



Desired Candidate Profile::



●	Bachelors degree in computer science, information technology, or mathematics.
●	3+ years of experience architecting, designing, developing, and implementing with Azure platforms.
●	Understanding of and experience with the five pillars of a well-architected frameworks.
●	Experience in several of the following areas: database architecture, ETL, business intelligence, big data, machine learning, advanced analytics.
●	Proven ability to collaborative with multi-disciplinary teams of business analysts, developers, data scientists, and subject matter experts.



Certification and Advance skill:



●	AWS certifications are a plus point.
●	Knowledge of web services, API, REST, and RPC.



Essential Qualification:
 
●	BCA/MCA, BSC IT / MSC IT , B.E- CS/ME-CS, B.Tech IT, PGDC IT, MBA-IT, Any
graduate in IT (Computer), Phd (computer).

"""

# Parse the job description
parsed_job = parse_job_description(job_text)

# Validate with Pydantic
job_model = Job(**parsed_job)
print(job_model.model_dump_json(indent=2))