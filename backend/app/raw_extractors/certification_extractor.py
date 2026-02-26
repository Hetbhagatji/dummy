from typing import List
from app.schemas.job_schema import CertificationRequirements
from app.schemas.resume_schema.certifications_schema import Certifications
from app.services.normalization.object import TextNormalizer
from app.embedding_models.embedder import ResumeJobEmbedder
embedder = ResumeJobEmbedder()

def extract_resume_certifications(resume_certifications: Certifications) -> List[str]:
    """Extract resume certifications for display"""
    if not resume_certifications or not resume_certifications.entries:
        return []
    
    cert_list = []
    for cert in resume_certifications.entries:
        cert_name = cert.certification_name or "Certification"
        issuer = cert.issuing_body or "Unknown Issuer"
        cert_list.append(f"{cert_name} ({issuer})")
    return cert_list

def extract_job_certifications(job_certifications: CertificationRequirements) -> List[str]:
    """Extract job certification requirements for display"""
    if not job_certifications or not job_certifications.groups:
        return []
    
    cert_list = []
    for group in job_certifications.groups:
        for cert_req in group.certifications:
            cert_name = cert_req.certification_name or "Certification"
            issuer = cert_req.issuing_body or "Any Issuer"
            cert_list.append(f"{cert_name} ({issuer})")
    return cert_list


def match_single_certification(job_cert_text: str, resume_cert_texts: List[str], threshold: float) -> float:
    """Returns best similarity score for a job certification against all resume certifications"""
    if not resume_cert_texts:
        return 0.0

    job_vec = embedder.embed_texts([job_cert_text])[0]
    resume_vecs = embedder.embed_texts(resume_cert_texts)

    similarities = [
        embedder.cosine_similarity(job_vec, r_vec)
        for r_vec in resume_vecs
    ]

    best_score = max(similarities)
    return best_score if best_score >= threshold else 0.0

def evaluate_certification_group(group, resume_cert_texts: List[str], threshold: float) -> dict:
    """Evaluate a certification group with AND/OR/N_OF logic"""
    cert_scores = []
    
    for cert_req in group.certifications:
        cert_name = cert_req.certification_name or ""
        text = cert_name.strip()
        
        if text:
            normalized_text = TextNormalizer.normalize(text)
            score = match_single_certification(normalized_text, resume_cert_texts, threshold)
            cert_scores.append(score)
        else:
            cert_scores.append(0.0)

    matched = sum(1 for s in cert_scores if s > 0)
    total = len(cert_scores)

    if group.operator == "AND":
        base_score = sum(cert_scores) / total if total else 0.0
        coverage = matched / total if total else 0.0
        group_score = base_score 
        passed = matched == total

    elif group.operator == "OR":
        if not cert_scores:
            group_score = 0.0
        else:
            best_score = max(cert_scores)
            coverage = matched / total if total else 0.0
            # 70% from best match + 30% bonus for breadth
            group_score = (best_score * 0.7) + (coverage * 0.3)
        passed = matched >= 1

    elif group.operator == "N_OF":
        min_req = group.min_required or 1
        # Base score from average
        base_score = sum(cert_scores) / total if total else 0.0
        # Bonus if exceeding minimum
        if matched >= min_req:
            # Give full credit plus small bonus for extras
            coverage = matched / total if total else 0.0
            group_score = (base_score * 0.8) + (coverage * 0.2)
        else:
            # Partial credit if below minimum
            group_score = base_score * (matched / min_req)
        passed = matched >= min_req

    else:
        group_score = sum(cert_scores) / total if total else 0.0
        passed = matched >= 1

    if group.min_required is not None:
        passed = matched >= group.min_required

    return {
        "group_score": float(round(group_score, 3)),
        "matched_count": matched,
        "required_count": total,
        "passed": passed,
        "mandatory": group.mandatory
    }
