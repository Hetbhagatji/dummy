import json

from pass1_raw_extraction import get_pass1_prompt
from pass2_structuring import get_pass2_prompt
from grok_job_llm import GroqJobLLM


import re

def extract_json(text: str) -> str:
    # Remove markdown fences
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    # Extract JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    json_text = text[start:end + 1]

    # 🔥 CRITICAL: remove illegal control characters
    json_text = re.sub(
        r"[\x00-\x1F\x7F]",  # all ASCII control chars
        "",
        json_text
    )

    return json_text


def parse_job(job_text: str) -> dict:
    llm = GroqJobLLM()

    # ---------------- PASS 1 ----------------
    print("\n========== PASS 1 ==========")

    pass1_prompt = get_pass1_prompt(job_text)
    pass1_output = llm.parse(pass1_prompt)

    print("\n--- PASS 1 RAW OUTPUT (LLM) ---")
    print(pass1_output)

    try:
        clean_pass1 = extract_json(pass1_output)
        raw_json = json.loads(clean_pass1)

        print("\n✅ PASS 1 JSON PARSED SUCCESSFULLY")
    except json.JSONDecodeError as e:
        print("\n❌ PASS 1 JSON PARSE FAILED")
        print("Error:", e)
        print("\nFirst 300 chars of output:")
        print(repr(pass1_output[:300]))
        raise

    # ---------------- PASS 2 ----------------
    print("\n========== PASS 2 ==========")

    pass2_prompt = get_pass2_prompt(json.dumps(raw_json))
    pass2_output = llm.parse(pass2_prompt)

    print("\n--- PASS 2 RAW OUTPUT (LLM) ---")
    print(pass2_output)

    try:
        clean_pass2 = extract_json(pass2_output)
        final_json = json.loads(clean_pass2)
        print("\n✅ PASS 2 JSON PARSED SUCCESSFULLY")
        return final_json
    except json.JSONDecodeError as e:
        print("\n❌ PASS 2 JSON PARSE FAILED")
        print("Error:", e)
        print("\nFirst 300 chars of output:")
        print(repr(pass2_output[:300]))
        raise


if __name__ == "__main__":
    job_description = """
About us:

Working at Tech Holding isn't just a job, it's an opportunity to be a part of something bigger. We are a full-service consulting firm that was founded on the premise of delivering predictable outcomes and high-quality solutions to our clients. Our founders and team members have industry experience and have held senior positions in a wide variety of companies – from
 
emerging startups to large Fortune 50 firms – and we have taken our combined experiences and developed a unique approach that is supported by the principles of deep expertise, integrity, transparency, and dependability.
The Role:

At Tech Holding, we don't just build technology- we power digital transformation for some of the world's most recognized brands, from Disney and Hulu to Warner Bros, Amex, and GoodRx. As a Lead DevOps Engineer, you'll play a key role in shaping our DevOps culture, bridging Development and Platform Engineering, and driving innovation across multi-cloud environments. This is a chance to solve complex, high-impact challenges alongside a global team of experts while enjoying a supportive culture that values flexibility, professional growth, and leadership that truly invests in your success.
Key Responsibilities:

●	Define and implement DevOps best practices, including CI/CD pipelines, Infrastructure as Code (IaC), and configuration management.
●	Automate tasks and optimize workflows to continuously improve our DevOps processes.
●	Partner with Development and Product teams to understand their needs and identify opportunities for DevOps adoption.
●	Architect and implement robust infrastructure solutions across multi-cloud environments (example: AWS, GCP or Azure).
●	Design and implement monitoring and alerting systems to ensure infrastructure health and application performance.
●	Stay up to date on the latest DevOps trends and best practices.

Required Skills:

●	Relevant 8+ years of experience as a DevOps Engineer or related role.
●	Experience in either GCP or Azure
●	Self-motivation, outstanding communication skills, and a great team-player attitude who can "switch hats" comfortably and effectively
●	Verbal and written communication skills, problem solving skills, customer service and interpersonal skills
●	Innovative problem-solving ability with excellent critical and analytical skills
●	The ability to self-manage time spent on assigned work
●	Basic programming experience with high level language (Python or Go)
●	Strong understanding of CI/CD principles and automation tools.
●	Expertise in Infrastructure as Code (IaC) methodologies (e.g., Terraform, Ansible).
●	In-depth knowledge of cloud platforms and their associated services (e.g., CDN, CND Edge, ECS, EKS, Batch services).
●	Experience with monitoring and alerting tools (e.g., Datadog, Prometheus, PagerDuty).
●	A passion for developer productivity and tooling.
●	Excellent communication, collaboration, and problem-solving skills.
 
●	A positive and proactive approach to work
●	Programming background with DevOps strength is highly preferred.

Nice to Have:

●	In-depth knowledge of the Azure cloud platform
●	Experience in AWS / GCP Partnership collaboration.
●	Professional level certification in any one of the clouds.

Location:

●	This role is onsite at either our Pune or Ahmedabad location

Work Schedule:

●	Must be available for ~2 hours of evening work to overlap with US teams (until approximately 11:30 PM IST)
What we offer:

●	A culture that values flexibility, work-life balance, and employee well-being - including
Work From Home Fridays
●	Competitive compensation packages and comprehensive health benefits
●	Work with a collaborative, global team of engineers who thrive on solving complex challenges
●	Exposure to multi-cloud environments (AWS, GCP, Azure) and modern DevOps tooling at scale
●	Professional growth through continuous learning, mentorship, and access to new technologies
●	Leadership that recognizes contributions and supports career advancement
●	The chance to shape DevOps best practices and directly influence company-wide engineering culture
●	A people-first environment where your ideas matter and innovation is encouraged 

    """

    result = parse_job(job_description)
    print("\n========== FINAL OUTPUT ==========")
    print(json.dumps(result, indent=2))
