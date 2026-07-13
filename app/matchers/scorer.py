from thefuzz import fuzz, utils as fuzz_utils
import jellyfish


def token_set_ratio(s1: str, s2: str) -> float:
    return float(fuzz.token_set_ratio(s1, s2))


def partial_ratio(s1: str, s2: str) -> float:
    s1 = fuzz_utils.full_process(s1)
    s2 = fuzz_utils.full_process(s2)
    return float(fuzz.partial_ratio(s1, s2))


def soundex_match(name1: str, name2: str) -> float:
    try:
        return 1.0 if jellyfish.soundex(name1) == jellyfish.soundex(name2) else 0.0
    except Exception:
        return 0.0


def metaphone_match(name1: str, name2: str) -> float:
    try:
        return 1.0 if jellyfish.metaphone(name1) == jellyfish.metaphone(name2) else 0.0
    except Exception:
        return 0.0


def combined_score(
    query: str,
    candidate: str,
    weights: tuple = (0.40, 0.30, 0.15, 0.15),
) -> float:
    ts = token_set_ratio(query, candidate)
    pr = partial_ratio(query, candidate)
    sm = soundex_match(query, candidate) * 100
    mm = metaphone_match(query, candidate) * 100
    return round(
        weights[0] * ts + weights[1] * pr + weights[2] * sm + weights[3] * mm,
        1,
    )
