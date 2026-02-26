from app.schemas.job_schema import ExperienceRequirements
from app.schemas.resume_schema.experience_schema import Experience
from app.embedding_models.embedder import ResumeJobEmbedder
from typing import List, Dict
from app.raw_extractors.experience_extractor import _empty_result,_process_group,_find_best_match


class ExperienceMatcher:
    def __init__(self, embedder: ResumeJobEmbedder, similarity_threshold: float = 0.45):
        self.embedder = embedder
        self.SIMILARITY_THRESHOLD = similarity_threshold

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def match_experience(
        self,
        job_requirements: ExperienceRequirements,
        resume_experience: Experience,
    ) -> Dict:
        if not job_requirements or not job_requirements.groups:
            return _empty_result("No job requirements")

        if not resume_experience or not resume_experience.experience_areas:
            return _empty_result("No resume experience")

        group_results = []
        all_match_details = []

        for group_idx, group in enumerate(job_requirements.groups):
            group_result = _process_group(
                group,
                resume_experience.experience_areas,
                group_idx,
            )
            group_results.append(group_result["score"])
            all_match_details.extend(group_result["matches"])

        final_score = sum(group_results) / len(group_results) if group_results else 0.0

        return {
            "score":        round(final_score, 3),
            "details":      all_match_details,
            "group_scores": [round(s, 3) for s in group_results],
            "total_groups": len(group_results),
        }

    # # ------------------------------------------------------------------ #
    # #  Group processing                                                    #
    # # ------------------------------------------------------------------ #

    # def _process_group(self, group, resume_jobs: List, group_idx: int) -> Dict:
    #     requirement_scores = []
    #     match_details = []

    #     for requirement in group.experiences:
    #         best_match = self._find_best_match(
    #             requirement.experience_area,
    #             requirement.min_years,
    #             requirement.max_years,
    #             resume_jobs,
    #         )
    #         requirement_scores.append(best_match["score"])
    #         match_details.append({
    #             "group":       group_idx + 1,
    #             "requirement": requirement.experience_area,
    #             "min_years":   requirement.min_years,
    #             "max_years":   requirement.max_years,
    #             **best_match,
    #         })

    #     total = len(requirement_scores)

    #     if group.operator == "AND":
    #         group_score = sum(requirement_scores) / total if total else 0.0

    #     elif group.operator == "OR":
    #         # ✅ FIX D: Pure OR = best single score is sufficient.
    #         # OLD: (best*0.7) + (coverage*0.3) — punished when only 1 of N matched,
    #         #      even though OR means any ONE is enough.
    #         group_score = max(requirement_scores) if requirement_scores else 0.0

    #     else:
    #         group_score = sum(requirement_scores) / total if total else 0.0

    #     return {"score": group_score, "matches": match_details}

    # # ------------------------------------------------------------------ #
    # #  Best-match finder  ← core of Fix A + Fix C                         #
    # # ------------------------------------------------------------------ #

    # def _find_best_match(
    #     self,
    #     experience_area: str,
    #     min_years: float,
    #     max_years: float,
    #     resume_jobs: List,
    # ) -> Dict:
    #     """
    #     Find ALL resume jobs that semantically match the requirement area,
    #     ACCUMULATE their years, then compute a single score.

    #     ✅ FIX C: Old code picked ONLY the single highest-scoring job and used
    #     its years alone.  A candidate with three 1-year AI roles was treated as
    #     having 1 year, not 3.  Now we sum years across all matching jobs first.

    #     ✅ FIX A (partial): Keywords are built via _build_keywords(), which now
    #     includes responsibilities — see that method for details.
    #     """
    #     matching_jobs  = []
    #     best_similarity = 0.0

    #     for job in resume_jobs:
    #         combined_keywords = self._build_keywords(job)
    #         if not combined_keywords:
    #             continue

    #         similarity = self._calculate_keyword_similarity(experience_area, combined_keywords)

    #         if similarity >= self.SIMILARITY_THRESHOLD:
    #             years = job.total_experience_years or 0.0
    #             matching_jobs.append({
    #                 "job_title":  job.job_title,
    #                 "company":    job.company_name,
    #                 "keywords":   combined_keywords,
    #                 "similarity": similarity,
    #                 "years":      years,
    #             })
    #             best_similarity = max(best_similarity, similarity)

    #     if not matching_jobs:
    #         return {
    #             "matched_job":      None,
    #             "company":          None,
    #             "matched_keywords": [],
    #             "similarity":       0.0,
    #             "years":            0.0,
    #             "year_score":       0.0,
    #             "score":            0.0,
    #         }

    #     # ✅ FIX C: Accumulate years across ALL matched jobs
    #     total_years = sum(j["years"] for j in matching_jobs)
    #     year_score  = self._calculate_year_score(total_years, min_years, max_years)

    #     # Final score = best semantic match × year fulfilment
    #     combined_score =  year_score

    #     matched_titles    = ", ".join({j["job_title"] for j in matching_jobs if j["job_title"]})
    #     matched_companies = ", ".join(j["company"]    for j in matching_jobs if j["company"])
    #     all_keywords      = list({kw for j in matching_jobs for kw in j["keywords"]})

    #     return {
    #         "matched_job":      matched_titles,
    #         "company":          matched_companies,
    #         "matched_keywords": all_keywords,
    #         "similarity":       round(best_similarity, 3),
    #         "years":            round(total_years, 2),
    #         "year_score":       round(year_score, 3),
    #         "score":            round(combined_score, 3),
    #     }

    # # ------------------------------------------------------------------ #
    # #  Keyword builder  (new helper — Fix A)                              #
    # # ------------------------------------------------------------------ #

    # def _build_keywords(self, job) -> List[str]:
    #     """
    #     ✅ FIX A: Build a rich keyword list from ALL available job fields.

    #     OLD code: keywords = extracted_keywords (null) + job_title only.
    #     The entire semantic match rested on ONE short string.

    #     NEW code: also pulls responsibilities[], which is populated for every job.
    #     Example: BlocBelt responsibilities include "Strategic AI Leadership",
    #     "Data-Driven Strategy", "AI Integration" — these match "AI/ML engineering"
    #     much better than the job title alone.

    #     SPECIAL CASE — null years + good keywords (e.g. "Artificial Intelligence
    #     Engineer" with extracted_keywords=["Ai/ML Engineering","Data Science"]):
    #     The keywords are still used for similarity, but years=0 means year_score=0
    #     and that job contributes 0 to the accumulated year total.  That is correct
    #     behaviour — we cannot count undated experience toward a year requirement.
    #     """
    #     keywords = []

    #     if hasattr(job, "job_title") and job.job_title:
    #         keywords.append(job.job_title)

    #     if hasattr(job, "extracted_keywords") and job.extracted_keywords:
    #         if isinstance(job.extracted_keywords, list):
    #             keywords.extend(job.extracted_keywords)
    #         elif isinstance(job.extracted_keywords, str):
    #             keywords.append(job.extracted_keywords)

    #     if hasattr(job, "responsibilities") and job.responsibilities:
    #         if isinstance(job.responsibilities, list):
    #             keywords.extend(job.responsibilities)
    #         elif isinstance(job.responsibilities, str):
    #             keywords.append(job.responsibilities)

    #     # Deduplicate, preserve order
    #     seen, unique = set(), []
    #     for kw in keywords:
    #         if kw and kw not in seen:
    #             seen.add(kw)
    #             unique.append(kw)
    #     return unique

    # # ------------------------------------------------------------------ #
    # #  Similarity calculation                                              #
    # # ------------------------------------------------------------------ #

    # def _calculate_keyword_similarity(
    #     self, experience_area: str, keywords: List[str]
    # ) -> float:
    #     if not keywords:
    #         return 0.0
    #     req_vec      = self.embedder.embed_texts([experience_area])[0]
    #     keyword_vecs = self.embedder.embed_texts(keywords)
    #     return float(max(
    #         self.embedder.cosine_similarity(req_vec, kw_vec)
    #         for kw_vec in keyword_vecs
    #     ))

    # # ------------------------------------------------------------------ #
    # #  Year scoring  (Fix B)                                              #
    # # ------------------------------------------------------------------ #

    # def _calculate_year_score(
    #     self,
    #     actual_years: float,
    #     min_years: float,
    #     max_years: float = None,
    # ) -> float:
    #     """
    #     ✅ FIX B: No overqualified penalty.

    #     A candidate with 4 years for a 2–3 yr role is an asset, not a problem.
    #     Penalising over-qualification caused strong candidates to score lower
    #     than weaker ones — a clear ranking inversion.

    #       actual >= min  →  1.0          (perfect)
    #       actual <  min  →  actual / min  (partial credit)
    #     """
    #     min_y = min_years or 0.0
    #     if actual_years >= min_y:
    #         return 1.0   # overqualified = 1.0, never penalize
    #     return (actual_years / min_y) if min_y > 0 else 0.0
