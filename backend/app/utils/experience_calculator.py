from datetime import datetime
from typing import Optional, Tuple

def parse_date_to_year_month(date_str: Optional[str]) -> Optional[Tuple[int, int]]:
    """
    Parse a date string into (year, month) tuple.
    Handles formats: YYYY-MM, YYYY, and current/present/now
    """
    if not date_str:
        return None

    date_str = date_str.strip().lower()

    # Handle current/present/now
    if date_str in {"current", "present", "now"}:
        now = datetime.now()
        return now.year, now.month

    try:
        # YYYY-MM format
        if "-" in date_str:
            year, month = date_str.split("-")
            return int(year), int(month)

        # YYYY format (just a year) - default to January
        year = int(date_str)
        return year, 1

    except (ValueError, AttributeError) as e:
        
        return None


def calculate_experience_months(
    start_date: Optional[str],
    end_date: Optional[str]
) -> Optional[int]:
    """
    Calculate total months of experience between start and end dates.
    Returns None if dates are invalid or if end is before start.
    """
    start = parse_date_to_year_month(start_date)
    end = parse_date_to_year_month(end_date)

    if not start or not end:
        return None

    start_year, start_month = start
    end_year, end_month = end

    # Calculate total months
    total_months = (end_year - start_year) * 12 + (end_month - start_month)

    # Return None for negative durations
    if total_months < 0:
        return None

    return total_months


def enrich_work_history(work_history):
    """
    Enrich work history entries with calculated experience duration.
    Adds total_experience_months and total_experience_years to each entry.
    """
    if not work_history or not work_history.entries:
        return work_history

    for entry in work_history.entries:
        months = calculate_experience_months(
            entry.start_date,
            entry.end_date
        )

        entry.total_experience_months = months
        entry.total_experience_years = (
            round(months / 12, 1) if months is not None else None
        )

    return work_history