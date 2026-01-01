import json
from pydantic import ValidationError

from client import get_groq_client
from raw_schemas import RawJobData
from education_prompt import get_education_parsing_prompt
from eduxation_schema import EDUCATION_SCHEMA
from utills import clean_llm_json


MODEL_NAME = "llama-3.3-70b-versatile"


def run_education_parser(job_description: str):
    # 1️⃣ Create RawJobData (only education is needed)
    raw_data = RawJobData(
        raw_education_requirements_text=job_description
    )

    # 2️⃣ Build prompt
    prompt = get_education_parsing_prompt(raw_data)

    # 3️⃣ Call LLM
    client = get_groq_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a precise education requirement parser."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    # 4️⃣ Clean & print raw output
    content = response.choices[0].message.content
    content = clean_llm_json(content)

    print("\n----- EDUCATION LLM OUTPUT -----")
    print(content)
    print("--------------------------------")

    # 5️⃣ Validate JSON
    try:
        data = json.loads(content)
        print("\n✅ JSON is valid")
    except json.JSONDecodeError as e:
        print("\n❌ Invalid JSON")
        raise e

    return data


if __name__ == "__main__":
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
●	Education. A bachelor’s degree in computer science, software engineering, or a related field and master degree in  information techn. Certifications in backend frameworks or cloud platforms (e.g., AWS or Azure) are a plus.
●	Work experience. At least 2-3 years of professional experience in backend web development, including familiarity with the full software development lifecycle.
●	Technical skills. Proficiency in backend programming languages (e.g., Java, Python, Ruby, PHP), database management (e.g., MongoDB, MySQL), and version control tools like Git. Experience with frameworks like Django or Node.js is highly valued.
●	Soft skills. Strong problem-solving and communication skills to collaborate effectively with team members and stakeholders.



    """

    result = run_education_parser(job_description)

    print("\n===== FINAL PARSED EDUCATION =====")
    print(json.dumps(result, indent=2))
