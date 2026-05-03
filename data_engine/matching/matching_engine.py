from scoring import (
    cosine_sim,
    jaccard,
    exp_match,
    geo_match,
    compute_score
)

# =========================
# MATCHING ENGINE
# =========================
def match_jobs(cv_vector, df, X, user_exp, user_loc, user_skills):
    
    cos_scores = cosine_sim(cv_vector, X)[0]

    results = []

    for i in range(len(df)):
        
        job_skills = str(df.iloc[i]["competences"]).split(",")
        
        jac = jaccard(user_skills, job_skills)
        exp = exp_match(user_exp, df.iloc[i]["experience"])
        geo = geo_match(user_loc, df.iloc[i]["localisation"])

        score = compute_score(
            cos_scores[i],
            jac,
            exp,
            geo
        )

        results.append({
            "job": df.iloc[i]["titre"],
            "score": score,
            "cluster": df.iloc[i]["cluster"]
        })

    # sort best jobs
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results[:10]