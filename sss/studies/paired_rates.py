"""Descriptive failure rates and paired changes for a frozen question sample.

Intervals describe the sampled generator distribution under independent-trial
assumptions, not universal competence. They never change an acceptance policy.
"""
import math


def failure_rate(failures, total):
    if type(total) is not int or type(failures) is not int or not 0 <= failures <= total or total == 0:
        raise ValueError('Explicit positive sample size and integer failure count required')
    z = 1.959963984540054
    rate = failures / total
    denominator = 1 + z*z/total
    center = (rate + z*z/(2*total))/denominator
    radius = z * math.sqrt(rate*(1-rate)/total + z*z/(4*total*total))/denominator
    return dict(failures=failures, total=total, failure_rate=rate,
                wilson_95=[max(0., center-radius), min(1., center+radius)])


def paired_rates(before, after):
    if (type(before) is not dict or type(after) is not dict or not before or before.keys() != after.keys()
            or any(type(v) is not bool for v in [*before.values(), *after.values()])):
        raise ValueError('Exactly the same frozen cases and Boolean outcomes are required')
    gained = sum(not before[k] and after[k] for k in before)
    lost = sum(before[k] and not after[k] for k in before)
    discordant = gained + lost
    # Conditional exact two-sided McNemar test. A zero-discordance sample is
    # not proof of equivalence; it simply supplies no direction-of-change evidence.
    probability = (min(1., 2*sum(math.comb(discordant, i) for i in range(min(gained, lost)+1))/2**discordant)
                   if discordant else 1.)
    return dict(baseline=failure_rate(sum(not v for v in before.values()), len(before)),
                candidate=failure_rate(sum(not v for v in after.values()), len(after)),
                newly_correct=gained, newly_wrong=lost,
                failure_rate_change=(lost-gained)/len(before),
                discordant_pairs=discordant, mcnemar_exact_two_sided_p=probability,
                automatic_acceptance=False)
