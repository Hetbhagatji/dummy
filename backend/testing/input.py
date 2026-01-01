from job import Job
from pipeline import parse_job_description

# Example job description
job_text = """
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


"""

# Parse the job description
parsed_job = parse_job_description(job_text)

# Validate with Pydantic
job_model = Job(**parsed_job)
print(job_model.model_dump_json(indent=2))
