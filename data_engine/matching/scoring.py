from sklearn.metrics.pairwise import cosine_similarity

def cosine_sim(user_vector, job_vectors):
    return cosine_similarity(user_vector, job_vectors)

def jaccard(set1, set2):
    set1, set2 = set(set1), set(set2)
    if len(set1 | set2) == 0:
        return 0
    return len(set1 & set2) / len(set1 | set2)

def exp_match(user_exp, job_exp):
    return 1 if str(user_exp).lower() in str(job_exp).lower() else 0

def geo_match(user_loc, job_loc):
    return 1 if str(user_loc).lower() in str(job_loc).lower() else 0

def compute_score(cos, jac, exp, geo):
    return 0.5 * cos + 0.25 * jac + 0.15 * exp + 0.10 * geo