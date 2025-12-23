from job import Job
from pipeline import parse_job_description

# Example job description
job_text = """
Job description: Template
We seek an experienced software tester to join our product team at [Company name].

As a software tester, you will oversee quality assurance activities associated with software analysis. This includes developing test plans, performing exploratory testing and executing functional and regression testing. You will work closely with engineering, product management and support teams to ensure the product is ready for release.

This could be your dream job if you are zealous about UX design, system analysis and debugging software problems. We offer competitive pay and abundant growth opportunities in a fast-paced, inclusive environment within the company.

Objectives of this role
Conduct thorough software testing, analyse data, write test cases and communicate with developers.
Checking software functionality on different operating systems, browsers and devices to ensure that the software is up to the standard and meets the users’ needs.
Testing software for security vulnerabilities and providing input on improving the company’s product solutions.
Communicate the results of software testing efforts to stakeholders and suggest areas of improvement.
Your tasks
Work with project developers, business analysts and customer support teams to ensure software solutions meet our user expectations.
Develop software test cases, based on consumer specifications and requirements.
Perform root cause analysis on defects found to identify and mitigate project risks.
Conduct exploratory and usability testing to locate bugs before the software is introduced into production.
Execute comprehensive testing against the software, ensuring all features function as designed and intended.
Contribute to the continuous improvement of software testing methodologies and develop standard operating procedures (SOPs), if necessary.
Required skills and qualifications
Bachelor’s degree in computer programming, software development or related fields.
3+ years of experience as a software tester or software quality assurance specialist.
Proven aptitude for testing quality software on multiple platforms and knowledge of industry-standard operating procedures and tools.
Understanding of various programming languages like Java, C++ and Python.
Proficiency in writing unit tests and integration tests for programming languages.
Relevant software testing certifications include Certified Software Tester (CSTE), ISTQB Agile Tester Certification or Certified Associate in Software Testing (CAST).
Preferred skills and qualifications
Knowledge of computer architecture and tools for manual & auto testing, unit testing, integration testing, functional testing and bug-tracking systems.
Demonstrated success in software development lifecycle management (SDLC).
Experience in working with test automation tools like Selenium, Appium, or Robot Framework.
Excellent interpersonal skills, analytical soundness, data analysis acumen and troubleshooting & programming capabilities.
Willingness to work collaboratively in a fast-paced environment.

"""

# Parse the job description
parsed_job = parse_job_description(job_text)

# Validate with Pydantic
job_model = Job(**parsed_job)
print(job_model.model_dump_json(indent=2))
