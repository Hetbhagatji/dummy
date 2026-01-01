from extractor import RawJobExtractor

job_description = """
Job description
Responsibilities:

*	Conduct quality checks on equipment performance

*	Ensure compliance with industry standards

*	Collaborate with cross-functional teams

*	Prepare quotes accurately

*	Execute detail engineering tasks


Role: Production & Manufacturing - Other

Industry Type: Aviation
 
Department: Production, Manufacturing & Engineering

Employment Type: Full Time, Permanent

Role Category: Production & Manufacturing - Other

Education


UG: B.Tech/B.E. in Aviation, Mechanical, Diploma in Mechatronics

Key Skills


Detail Engineering are preferred key skill. Communication Skills, English,Telugu, Documentation,
Quality Check, Quote Preparation, Hindi, Quality Assurance

"""

extractor = RawJobExtractor()
raw_data = extractor.extract(job_description)

print(raw_data.model_dump_json(indent=2))

