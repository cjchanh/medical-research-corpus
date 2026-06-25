"""Authority hierarchy: the evidence-tier ordering that re-ranks retrieval. Offline."""
import authority


def test_tier_ordering_strongest_to_weakest():
    sr = authority.authority_tier({"title": "A systematic review and meta-analysis of X"})
    rct = authority.authority_tier({"title": "A randomized controlled trial of X"})
    cohort = authority.authority_tier({"title": "A prospective cohort study of X"})
    trial = authority.authority_tier({"is_trial": True})
    pre = authority.authority_tier({"is_preprint": True})
    art = authority.authority_tier({"title": "Some article on X"})

    assert sr == (1, "systematic-review")
    assert rct[0] == 2
    assert cohort[0] == 3
    assert trial == (4, "trial-registry")
    assert pre == (5, "preprint")
    assert art == (3, "research-article")
    # strict monotonic: review < RCT < cohort < trial-registry < preprint
    assert sr[0] < rct[0] < cohort[0] < trial[0] < pre[0]


def test_structural_flags_beat_title_keywords():
    # is_trial / is_preprint take precedence over title-derived tiers
    assert authority.authority_tier({"is_trial": True, "title": "systematic review"})[0] == 4
    assert authority.authority_tier({"is_preprint": True, "title": "randomized controlled trial"})[0] == 5


def test_case_report_and_scoping_review():
    assert authority.authority_tier({"title": "A case report of X"})[0] == 4
    assert authority.authority_tier({"title": "A scoping review of X"})[0] == 2
