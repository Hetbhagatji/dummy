from typing import List, Dict, Tuple
from app.schemas.matching_result_schema import (
    MatchingResult,
    AdditionalScores,
    CategoryScores,
)

from app.services.excess_calculator import DEGREE_WEIGHTS


class ComparativeScorer:
    """
    Calculates comparative scores across multiple candidates.

    Key Concepts:
    ─────────────
    • Base scores       → ABSOLUTE  [0.0, 1.0]
    • Additional scores → RELATIVE  [-1.0, +1.0]  (best gets +1, worst gets -1)
    • Final score       → COMBINED  [0.0, 1.0]

    Tiebreaker philosophy:
    ──────────────────────
    When two candidates both score 1.0 on skills (both have all required skills),
    the one with MORE extra skills stays at 1.0 while the others get REDUCED.

    Example (base_weight=0.90, additional_weight=0.10, skills weight=0.50):
        Candidate A: 6 extra skills → additional_norm = +1.0
            final = 0.90 × base_weighted_sum + 0.10 × (+1.0 × 0.50 + ...) → higher

        Candidate B: 2 extra skills → additional_norm =  0.0  (middle)
            final = 0.90 × base_weighted_sum + 0.10 × (0.0  × 0.50 + ...) → base

        Candidate C: 0 extra skills → additional_norm = -1.0
            final = 0.90 × base_weighted_sum + 0.10 × (-1.0 × 0.50 + ...) → lower

    Score range guarantee:
    ──────────────────────
    final = base_stage × base_weight + tiebreaker × additional_weight

    Worst case for final:
        base_stage  = 0.0 (no requirements met)
        tiebreaker  = -additional_weight × sum(category_weights) = -additional_weight
        → final_min ≈ 0.0 - additional_weight  → clamped to 0.0

    Best case:
        base_stage  = base_weight
        tiebreaker  = +additional_weight
        → final_max = 1.0  ✓

    Category scores:
    ────────────────
    category_scores are for DISPLAY only (shows per-category combined value).
    They are clamped to [0.0, 1.0] so the API never shows values like 1.1.
    The final_comparative_score is computed from raw base_scores + raw
    additional_scores so no information is lost by the display clamping.
    """

    DEGREE_WEIGHTS: Dict[str, float] = DEGREE_WEIGHTS

    # ==================== EXCESS VALUE CALCULATORS ====================

    @staticmethod
    def calculate_education_excess_value(excess_metrics) -> float:
        """
        Education excess weighted by degree level using deduplicated degree_levels.

        Deduplication is done upstream in ExcessCalculator so 5× Bachelor's
        is stored as 1× Bachelor's — no bogus bonus for duplicate degrees.

        excess_value = max(0, candidate_weight − required_weight)
        Always >= 0 before normalisation.
        """
        if not excess_metrics.degree_levels:
            return 0.0

        candidate_weight = sum(
            DEGREE_WEIGHTS.get(level.lower().strip(), 1.0)
            for level in excess_metrics.degree_levels
        )
        required_weight = float(excess_metrics.required_degrees) * 1.0
        return max(0.0, candidate_weight - required_weight)

    @staticmethod
    def calculate_skills_excess_value(excess_metrics) -> float:
        """
        Skills beyond the minimum required. Floored at 0.
        Always >= 0 before normalisation.
        """
        return float(max(0, excess_metrics.excess_count))

    @staticmethod
    def calculate_experience_excess_value(excess_metrics) -> float:
        """
        Composite excess: years (70%) + area breadth (30%).
        May be slightly negative when required areas are unmatched.
        Normalisation handles the full range correctly.
        """
        years_component = max(0.0, excess_metrics.excess_years)

        if excess_metrics.required_areas > 0:
            if excess_metrics.excess_areas >= 0:
                areas_component = excess_metrics.excess_areas / excess_metrics.required_areas
            else:
                coverage = excess_metrics.matched_areas / excess_metrics.required_areas
                areas_component = -1.0 * (1.0 - coverage)
        else:
            areas_component = 0.0

        return (years_component * 0.7) + (areas_component * 0.3)

    @staticmethod
    def calculate_certification_excess_value(excess_metrics) -> float:
        """
        Certifications beyond the minimum required. Floored at 0.
        Always >= 0 before normalisation.
        """
        return float(max(0, excess_metrics.excess_count))

    # ==================== NORMALISE ACROSS CANDIDATES ====================

    @staticmethod
    def normalize_scores(scores: List[float]) -> Tuple[List[float], Dict]:
        """
        Normalise raw excess values to [-1.0, +1.0].

        Mapping:
            best  candidate → +1.0  (most excess → full positive bonus)
            worst candidate → -1.0  (least excess → penalty applied)
            all tied        →  0.0  (no differentiation → no change)

        Formula:
            normalised_i = 2 × (score_i − min) / (max − min) − 1

        Why [-1, +1] and not [0, +1]:
            You want the candidate with MORE excess to keep 1.0 while the
            one with LESS gets REDUCED.  A [-1, +1] scale achieves this:
            the best is rewarded (+bonus) and the worst is penalised (-penalty).

        Why it's safe:
            The penalty magnitude is bounded by additional_weight (e.g. 0.10).
            A candidate cannot lose more than additional_weight from their score.
            final_comparative_score is hard-clamped to [0.0, 1.0] at the end.

        Returns (normalised_list, stats_dict)
        """
        if not scores:
            return [], {}

        min_score  = min(scores)
        max_score  = max(scores)
        mean_score = sum(scores) / len(scores)

        if max_score == min_score:
            # Everyone identical → no one benefits or suffers
            normalised = [0.0] * len(scores)
        else:
            normalised = [
                2.0 * (s - min_score) / (max_score - min_score) - 1.0
                for s in scores
            ]

        stats = {
            "min":  round(min_score, 3),
            "max":  round(max_score, 3),
            "mean": round(mean_score, 3),
        }
        return normalised, stats

    # ==================== CALCULATE ADDITIONAL SCORES (BATCH) ====================

    @staticmethod
    def calculate_additional_scores_batch(
        candidates: List[MatchingResult],
    ) -> Tuple[List[MatchingResult], Dict]:
        """
        Compute and assign normalised additional scores [-1.0, +1.0] to all candidates.

        Steps:
          1. Compute raw excess value per dimension for every candidate.
          2. Normalise each dimension across the batch → [-1, +1].
          3. Assign the resulting AdditionalScores to each candidate.

        Returns (updated_candidates, normalization_stats)
        """
        if not candidates:
            return [], {}

        education_values:     List[float] = []
        skills_values:        List[float] = []
        experience_values:    List[float] = []
        certification_values: List[float] = []

        for candidate in candidates:
            education_values.append(
                ComparativeScorer.calculate_education_excess_value(
                    candidate.excess_metrics.education
                )
            )
            skills_values.append(
                ComparativeScorer.calculate_skills_excess_value(
                    candidate.excess_metrics.skills
                )
            )
            experience_values.append(
                ComparativeScorer.calculate_experience_excess_value(
                    candidate.excess_metrics.experience
                )
            )
            certification_values.append(
                ComparativeScorer.calculate_certification_excess_value(
                    candidate.excess_metrics.certifications
                )
            )

        edu_norm,  edu_stats  = ComparativeScorer.normalize_scores(education_values)
        sk_norm,   sk_stats   = ComparativeScorer.normalize_scores(skills_values)
        exp_norm,  exp_stats  = ComparativeScorer.normalize_scores(experience_values)
        cert_norm, cert_stats = ComparativeScorer.normalize_scores(certification_values)

        for i, candidate in enumerate(candidates):
            candidate.additional_scores = AdditionalScores(
                education_additional=      round(edu_norm[i],  3),
                skills_additional=         round(sk_norm[i],   3),
                experience_additional=     round(exp_norm[i],  3),
                certifications_additional= round(cert_norm[i], 3),
            )

        normalization_stats = {
            "education":      edu_stats,
            "skills":         sk_stats,
            "experience":     exp_stats,
            "certifications": cert_stats,
        }
        return candidates, normalization_stats

    # ==================== CATEGORY SCORES (DISPLAY ONLY) ====================

    @staticmethod
    def calculate_category_scores(
        candidate: MatchingResult,
        additional_weight: float = 0.10,
    ) -> CategoryScores:
        """
        Per-category combined score for DISPLAY purposes only.

        Formula:
            category_score = clamp(base_score + additional_norm × additional_weight, 0.0, 1.0)

        FIX — clamp to [0.0, 1.0]:
            Previously category_scores were NOT clamped, which produced values
            like 1.1 in the API response.  These are display scores only;
            the actual final_comparative_score is computed from raw values
            in calculate_final_comparative_score(), so clamping here loses
            nothing mathematically.

        Rules:
            • Education bonus only when base_education > 0 (irrelevant degrees earn nothing).
            • Responsibilities has no excess dimension — equals base only.
        """
        if not candidate.additional_scores:
            return CategoryScores(
                skills=          candidate.base_scores.skills,
                experience=      candidate.base_scores.experience,
                education=       candidate.base_scores.education,
                certifications=  candidate.base_scores.certifications,
                responsibilities=candidate.base_scores.responsibilities,
            )

        additional = candidate.additional_scores
        edu_base   = candidate.base_scores.education

        def _combine(base: float, additional_val: float) -> float:
            """Combine base + bonus and clamp to [0.0, 1.0]."""
            return round(max(0.0, min(1.0, base + additional_val * additional_weight)), 3)

        return CategoryScores(
            skills=         _combine(candidate.base_scores.skills,         additional.skills_additional),
            experience=     _combine(candidate.base_scores.experience,     additional.experience_additional),
            education=      _combine(
                                candidate.base_scores.education,
                                additional.education_additional if edu_base > 0 else 0.0
                            ),
            certifications= _combine(candidate.base_scores.certifications, additional.certifications_additional),
            responsibilities=candidate.base_scores.responsibilities,
        )

    # ==================== FINAL COMPARATIVE SCORE ====================

    @staticmethod
    def calculate_final_comparative_score(
        candidate: MatchingResult,
        category_weights: Dict[str, float],
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
    ) -> float:
        """
        Compute the final comparative score. Clamped to [0.0, 1.0].

        Two stages:

        Stage 1 — weighted base sum × base_weight:
            Uses raw base_scores (NOT category_scores) so display clamping
            in calculate_category_scores() has zero effect here.
            Max = 1.0 × base_weight = 0.90

        Stage 2 — tiebreaker × additional_weight:
            additional_scores are in [-1, +1].
            Range = [-additional_weight, +additional_weight] = [-0.10, +0.10]

        Combined range before clamping:
            min ≈ 0.0 - 0.10 = -0.10  → clamped to 0.0
            max = 0.90 + 0.10 = 1.00  ✓

        Example with all base scores = 1.0:
            A (most skills) → additional_skills = +1.0
                stage1 = 0.90, stage2 = +0.10×0.50 = +0.05 → final ≈ 0.95

            B (mid skills) → additional_skills =  0.0
                stage1 = 0.90, stage2 =  0.00 → final = 0.90

            C (least skills) → additional_skills = -1.0
                stage1 = 0.90, stage2 = -0.10×0.50 = -0.05 → final ≈ 0.85

            → A > B > C, all in [0, 1] ✓

        Rules:
            • Education bonus = 0 when base_education == 0.
            • Responsibilities excluded from Stage 2.
            • Hard clamp to [0.0, 1.0] as final safety net.
        """
        if not candidate.additional_scores:
            return round(candidate.final_base_score, 3)

        # ── Stage 1: pure base weighted sum × base_weight ────────────────────
        stage1 = (
            candidate.base_scores.skills
                * category_weights.get("skills", 0.50)
            + candidate.base_scores.experience
                * category_weights.get("experience", 0.25)
            + candidate.base_scores.education
                * category_weights.get("education", 0.15)
            + candidate.base_scores.certifications
                * category_weights.get("certifications", 0.05)
            + candidate.base_scores.responsibilities
                * category_weights.get("responsibilities", 0.05)
        ) * base_weight

        # ── Stage 2: tiebreaker (can be negative for weakest candidates) ─────
        edu_base = candidate.base_scores.education

        stage2 = (
            candidate.additional_scores.skills_additional
                * category_weights.get("skills", 0.50)
                * additional_weight

            + candidate.additional_scores.experience_additional
                * category_weights.get("experience", 0.25)
                * additional_weight

            + (
                candidate.additional_scores.education_additional
                    * category_weights.get("education", 0.15)
                    * additional_weight
                if edu_base > 0 else 0.0
              )

            + candidate.additional_scores.certifications_additional
                * category_weights.get("certifications", 0.05)
                * additional_weight

            # responsibilities intentionally excluded — no excess dimension
        )

        # Hard clamp — handles edge case where base was near 0 and penalty fires
        return round(min(1.0, max(0.0, stage1 + stage2)), 3)

    # ==================== COMPLETE RANKING PIPELINE ====================

    @staticmethod
    def rank_candidates(
        candidates: List[MatchingResult],
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
        category_weights: Dict[str, float] = None,
    ) -> Tuple[List[MatchingResult], Dict]:
        """
        Complete comparative ranking pipeline. Final scores in [0.0, 1.0].

        Steps:
          1. Compute normalised additional scores [-1, +1] across all candidates.
          2. Compute category scores clamped to [0, 1] for display.
          3. Compute final comparative scores from raw values (not clamped display scores).
          4. Sort descending by final_comparative_score.
          5. Assign integer ranks (1 = best).

        Args:
            candidates:        Candidates to rank.
            base_weight:       Weight of absolute base component (default 0.90).
            additional_weight: Weight of relative tiebreaker component (default 0.10).
            category_weights:  Per-category weights. Must sum to 1.0.

        Returns:
            (ranked_candidates, normalization_stats)
        """
        if not candidates:
            return [], {}

        if category_weights is None:
            category_weights = {
                "skills":           0.50,
                "experience":       0.25,
                "education":        0.15,
                "certifications":   0.05,
                "responsibilities": 0.05,
            }

        # Step 1 — normalised additional scores [-1, +1]
        candidates, norm_stats = ComparativeScorer.calculate_additional_scores_batch(
            candidates
        )

        # Step 2 — display category scores clamped to [0, 1]
        for candidate in candidates:
            candidate.category_scores = ComparativeScorer.calculate_category_scores(
                candidate, additional_weight=additional_weight
            )

        # Step 3 — final comparative scores from raw values, clamped to [0, 1]
        for candidate in candidates:
            candidate.final_comparative_score = (
                ComparativeScorer.calculate_final_comparative_score(
                    candidate,
                    category_weights,
                    base_weight=base_weight,
                    additional_weight=additional_weight,
                )
            )

        # Step 4 — sort descending
        candidates.sort(
            key=lambda c: c.final_comparative_score or 0.0,
            reverse=True,
        )

        # Step 5 — assign ranks
        for rank, candidate in enumerate(candidates, start=1):
            candidate.rank = rank

        return candidates, norm_stats