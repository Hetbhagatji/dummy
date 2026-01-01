from extractor import RawJobExtractor
from structured_extractor import StructuredJobExtractor

# Your existing job_description from stage 1
job_description = """
We’re seeking a skilled backend developer to join our team and contribute to our server-side development processes. You will be responsible for designing and maintaining scalable web services, managing databases, and collaborating with stakeholders to ensure seamless integration between the front and back end. 
 
As part of a cross-functional team, you'll work closely with front-end developers, project managers, and DevOps professionals to enhance functionality, optimize workflows, and deliver high-quality web applications.
Key responsibilities 
Backend developers are responsible for maintaining robust server-side logic and ensuring optimal application functionality. Core duties include:
●	Develop and maintain server-side applications. Build scalable and secure web services using backend programming languages like Python, Ruby, Java, and Node.js.
●	Manage databases and data storage. Optimize database performance using tools such as MySQL, MongoDB, or SQL Server while ensuring secure and reliable data management.
●	Collaborate with team members. Work closely with front-end developers, designers, and project managers to ensure alignment between server-side functionality and user interfaces.
●	Implement APIs and frameworks. Design and implement RESTful APIs to facilitate communication between server-side applications and end-user systems.
●	Conduct troubleshooting and debugging. Identify and resolve performance bottlenecks, security vulnerabilities, and server-side errors to maintain system stability.
●	Optimize scalability and workflows. Develop reusable code and scalable solutions to accommodate future growth.
Qualifications and skills 
To excel as a backend developer, candidates should meet the following qualifications:
●	Education. A bachelor’s degree in computer science, software engineering, or a related field. Certifications in backend frameworks or cloud platforms (e.g., AWS or Azure) are a plus.
●	Work experience. At least 2-3 years of professional experience in backend web development, including familiarity with the full software development lifecycle.
●	Technical skills. Proficiency in backend programming languages (e.g., Java, Python, Ruby, PHP), database management (e.g., MongoDB, MySQL), and version control tools like Git. Experience with frameworks like Django or Node.js is highly valued.
●	Soft skills. Strong problem-solving and communication skills to collaborate effectively with team members and stakeholders.


"""

# STAGE 1: Raw Extraction (existing)
print("=== STAGE 1: RAW EXTRACTION ===")
raw_extractor = RawJobExtractor()
raw_data = raw_extractor.extract(job_description)
print(raw_data.model_dump_json(indent=2))

# STAGE 2: Structured Parsing (NEW)
print("\n=== STAGE 2: STRUCTURED PARSING ===")
structured_extractor = StructuredJobExtractor()
final_job = structured_extractor.parse(raw_data)
print("Pass............................................")
print("\n=== FINAL STRUCTURED JOB ===")
print(final_job.model_dump_json(indent=2))
