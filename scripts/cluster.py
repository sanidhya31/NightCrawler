"""
cluster.py  -  assign a job to a work-similarity cluster (angle).

Each cluster is defined by keywords in config.filters.clusters. A job is assigned
to the cluster whose keywords it matches most (ties: earlier cluster wins). Jobs in
the same cluster share one reused resume.

Used by rank.py to tag every job with `cluster`, and by the skill / library to pick
which resume to reuse.
"""


def assign_cluster(job, clusters):
    # Title is the strongest signal -> weight it heavily over the description.
    title = str(job.get("title", "")).lower()
    body = (str(job.get("jobFunction", "")) + " " + str(job.get("descriptionText", ""))).lower()
    best_name, best_score = (clusters[0]["name"] if clusters else "General"), -1
    for c in clusters:
        score = 0
        for k in c["keywords"]:
            kl = k.lower()
            if kl in title:
                score += 5
            elif kl in body:
                score += 1
        if score > best_score:
            best_score, best_name = score, c["name"]
    return best_name, best_score


def cluster_counts(jobs, clusters):
    from collections import Counter
    c = Counter()
    for j in jobs:
        name, _ = assign_cluster(j, clusters)
        c[name] += 1
    return c
