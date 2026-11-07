# ============================================================================
# scoring.py — Weighted Scoring Engine + Critical Checks
# ============================================================================
# YEH FILE KYA KARTI HAI?
# -----------------------
# Ye file AI se mili raw scores ko:
#   1. Weighted average mein convert karti hai (7 categories, total = 100)
#   2. Critical checks lagati hai (kuch issues itne bade hain ki score chahe 
#      kitna bhi ho, post FAIL hogi)
#   3. Final decision deti hai: "pass" ya "fail" ya "needs_review"
#
# WEIGHTED AVERAGE KYA HAI?
# -------------------------
# Normal average: (80 + 90 + 70) / 3 = 80
# Weighted average: har cheez ka alag importance (weight) hota hai
#   Factual Accuracy (20% weight) → zyada important hai
#   Overall Design (10% weight)   → kam important hai
#   Isliye Factual mein kam marks milne ka zyada effect padega final score pe
#
# SCORING MODEL (from the PDF):
# ─────────────────────────────
#   Factual Accuracy       → 20%
#   Regulatory Compliance  → 20%
#   Brand Identity         → 15%
#   Visual Consistency     → 15%
#   Campaign Effectiveness → 10%
#   Accessibility          → 10%
#   Overall Design         → 10%
#   ─────────────────────────────
#   Total                  → 100%
# ============================================================================

# ─── CATEGORY WEIGHTS ───────────────────────────────────────────────────────
# Har category ka weight define karo (decimal mein — 0.20 = 20%)
# Ye weights PDF document ke according hain

CATEGORY_WEIGHTS = {
    "factual_accuracy": 0.20,       # 20% — Facts sahi hain ya nahi
    "regulatory_compliance": 0.20,  # 20% — Indian ad laws follow ho rahe ya nahi
    "brand_identity": 0.15,         # 15% — Tone/words brand se match karte ya nahi
    "visual_consistency": 0.15,     # 15% — Logo/colors sahi hain ya nahi
    "campaign_effectiveness": 0.10, # 10% — Content goal se match karta ya nahi
    "accessibility": 0.10,          # 10% — Readability, contrast sahi hai ya nahi
    "overall_design": 0.10,         # 10% — Layout/visual appeal
}

# Verify: saare weights ka sum 1.0 (100%) hona chahiye
assert abs(sum(CATEGORY_WEIGHTS.values()) - 1.0) < 0.001, \
    "Weights ka total 100% hona chahiye!"
# assert → agar condition False hai toh error throw karo
# Ye ek safety check hai taaki hum galti se weights galat na daal dein


# ─── THRESHOLDS ─────────────────────────────────────────────────────────────
# Thresholds = boundaries jo decide karti hain pass ya fail

PASS_THRESHOLD = 70        # Score >= 85 + no critical issues → human review ke liye ready
WARNING_THRESHOLD = 50     # Score 60-84 → improvement needed but not terrible
CRITICAL_SCORE_CAP = 49    # Critical issue hone pe max score 49 (even if AI gave 95)


# ─── CRITICAL CHECK KEYWORDS ────────────────────────────────────────────────
# Ye lists define karti hain ki kaunse issues "critical" maane jayenge
# Critical = itna bada issue ki post BILKUL nahi ja sakti, chahe score 100 ho

CRITICAL_KEYWORDS = [
    # Unsupported claims — bina proof ke bade bade claims
    "unverified claim",
    "unsupported claim",
    "misleading claim",
    "false claim",
    "unsubstantiated",
    
    # Regulatory violations — kanoon todna
    "regulatory violation",
    "legal violation",
    "missing disclaimer",
    "missing disclosure",
    "mandatory disclosure missing",
    "ASCI violation",           # ASCI = Advertising Standards Council of India
    "advertising standards violation",
    
    # Harmful content
    "offensive content",
    "discriminatory",
    "harmful content",
    
    # IP/Copyright issues
    "copyright violation",
    "unauthorized logo",
    "trademark violation",
]


def calculate_weighted_score(category_scores):
    """
    7 category scores se weighted overall score calculate karo.
    
    INPUT:
        category_scores = {
            "factual_accuracy": 85,
            "regulatory_compliance": 90,
            "brand_identity": 75,
            ... (7 categories, har ek 0-100)
        }
    
    OUTPUT:
        float — overall weighted score (0-100)
    
    FORMULA:
        overall = sum(score_i × weight_i) for each category
        
    EXAMPLE:
        factual_accuracy = 85, weight = 0.20 → contribution = 85 × 0.20 = 17.0
        regulatory = 90, weight = 0.20 → contribution = 90 × 0.20 = 18.0
        ... aur aise total mein add hoga
    """
    weighted_sum = 0.0
    
    for category, weight in CATEGORY_WEIGHTS.items():
        # Category ka score lo (default 0 agar missing hai)
        score = category_scores.get(category, 0)
        
        # Score ko 0-100 range mein clamp karo (safety check)
        score = max(0, min(100, score))
        # max(0, ...) → 0 se neeche nahi jaayega
        # min(100, ...) → 100 se upar nahi jaayega
        
        # Weighted contribution add karo
        weighted_sum += score * weight
    
    return round(weighted_sum, 1)  # 1 decimal place tak round karo


def check_critical_issues(feedback_text, critical_flags_from_ai):
    """
    Critical issues dhundho — ye wo issues hain jo itne serious hain ki
    post publish nahi ho sakti regardless of score.
    
    INPUT:
        feedback_text: str — AI ka poora feedback text
        critical_flags_from_ai: list — AI ne khud jo critical issues identify kiye
    
    OUTPUT:
        list — saare critical issues found
    
    KAISE KAAM KARTA HAI:
    1. AI ne jo critical flags diye, unhe check karo
    2. Feedback text mein critical keywords search karo
    3. Dono combine karke return karo
    """
    found_issues = []
    
    # Step 1: AI ke diye critical flags add karo (agar hain toh)
    if critical_flags_from_ai:
        for flag in critical_flags_from_ai:
            if flag and flag.strip():  # Khali strings skip karo
                found_issues.append(flag.strip())
    
    # Step 2: Feedback text mein critical keywords dhundho
    if feedback_text:
        feedback_lower = feedback_text.lower()  # Case-insensitive search ke liye
        for keyword in CRITICAL_KEYWORDS:
            if keyword.lower() in feedback_lower:
                # Duplicate add mat karo
                issue_msg = f"Critical: '{keyword}' detected in content evaluation"
                if issue_msg not in found_issues:
                    found_issues.append(issue_msg)
    
    return found_issues


def generate_final_result(category_scores, feedback_text="", 
                          critical_flags_from_ai=None):
    """
    FINAL SCORING DECISION — ye main function hai jo sab combine karta hai.
    
    INPUT:
        category_scores: dict — 7 category scores (0-100 each)
        feedback_text: str — AI ka combined feedback
        critical_flags_from_ai: list — AI ne identify kiye critical issues
    
    OUTPUT:
        dict with:
            - overall_score: float (0-100)
            - category_scores: dict (original 7 scores)
            - critical_flags: list (found critical issues)
            - has_critical_issues: bool
            - decision: str ('pass', 'fail', 'needs_improvement')
            - decision_reason: str (kyu ye decision aaya)
            - can_send_for_review: bool (human reviewer ke paas bhej sakte ya nahi)
    
    LOGIC:
        1. Weighted score calculate karo
        2. Critical issues check karo
        3. Decision do:
           - Score >= 85 AND no critical issues → PASS (send for human review)
           - Score >= 85 BUT critical issues → FAIL (fix critical issues first)
           - Score < 85 → NEEDS IMPROVEMENT
           - Score < 60 → FAIL (too many issues)
    """
    if critical_flags_from_ai is None:
        critical_flags_from_ai = []
    
    # Step 1: Weighted score calculate karo
    overall_score = calculate_weighted_score(category_scores)
    
    # Step 2: Critical issues check karo
    critical_issues = check_critical_issues(feedback_text, critical_flags_from_ai)
    has_critical = len(critical_issues) > 0
    
    # Step 3: Critical issues hain toh score cap karo
    # ──────────────────────────────────────────────
    # IMPORTANT: Ye BrandGuard ka core rule hai — 
    # critical issues milne pe score chahe 95 ho, max 49 maana jaayega
    if has_critical:
        capped_score = min(overall_score, CRITICAL_SCORE_CAP)
    else:
        capped_score = overall_score
    
    # Step 4: Decision logic
    # ─────────────────────
    if has_critical:
        decision = "fail"
        reason = (f"❌ Critical issues found ({len(critical_issues)} issue(s)). "
                  f"Score capped at {capped_score}. Fix critical issues before resubmitting.")
        can_send_for_review = False
        
    elif capped_score >= PASS_THRESHOLD:
        decision = "pass"
        reason = (f"✅ Score {capped_score}/100 meets the threshold ({PASS_THRESHOLD}+) "
                  f"with no critical issues. Ready for human review!")
        can_send_for_review = True
        
    elif capped_score >= WARNING_THRESHOLD:
        decision = "needs_improvement"
        reason = (f"⚠️ Score {capped_score}/100 is below the threshold ({PASS_THRESHOLD}). "
                  f"Review suggestions and resubmit with improvements.")
        can_send_for_review = False
        
    else:
        decision = "fail"
        reason = (f"❌ Score {capped_score}/100 is too low. "
                  f"Significant improvements needed across multiple areas.")
        can_send_for_review = False
    
    # Step 5: Result return karo
    return {
        "overall_score": capped_score,
        "original_score": overall_score,  # Cap se pehle ka score (reference ke liye)
        "category_scores": category_scores,
        "critical_flags": critical_issues,
        "has_critical_issues": has_critical,
        "decision": decision,
        "decision_reason": reason,
        "can_send_for_review": can_send_for_review,
    }


def get_score_color(score):
    """
    Score ke according color do (UI mein dikhane ke liye).
    Green = good, Yellow = okay, Red = bad
    """
    if score >= 85:
        return "🟢"   # Green — excellent
    elif score >= 70:
        return "🟡"   # Yellow — needs work  
    elif score >= 50:
        return "🟠"   # Orange — significant issues
    else:
        return "🔴"   # Red — critical problems


def format_score_report(result):
    """
    Score result ko readable text report mein convert karo.
    Ye debugging aur display ke liye useful hai.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("📊 BRANDGUARD EVALUATION REPORT")
    lines.append("=" * 50)
    
    # Overall score
    color = get_score_color(result["overall_score"])
    lines.append(f"\n{color} Overall Score: {result['overall_score']}/100")
    
    if result["original_score"] != result["overall_score"]:
        lines.append(f"   (Original: {result['original_score']}, capped due to critical issues)")
    
    lines.append(f"\n📋 Decision: {result['decision'].upper()}")
    lines.append(f"   {result['decision_reason']}")
    
    # Category-wise scores
    lines.append(f"\n{'─' * 50}")
    lines.append("📈 Category Scores:")
    lines.append(f"{'─' * 50}")
    
    category_labels = {
        "factual_accuracy": "Factual Accuracy",
        "regulatory_compliance": "Regulatory Compliance",
        "brand_identity": "Brand Identity",
        "visual_consistency": "Visual Consistency",
        "campaign_effectiveness": "Campaign Effectiveness",
        "accessibility": "Accessibility",
        "overall_design": "Overall Design",
    }
    
    for cat, weight in CATEGORY_WEIGHTS.items():
        score = result["category_scores"].get(cat, 0)
        color = get_score_color(score)
        label = category_labels.get(cat, cat)
        weight_pct = int(weight * 100)
        lines.append(f"   {color} {label}: {score}/100 (weight: {weight_pct}%)")
    
    # Critical issues
    if result["critical_flags"]:
        lines.append(f"\n{'─' * 50}")
        lines.append("🚨 CRITICAL ISSUES:")
        lines.append(f"{'─' * 50}")
        for i, flag in enumerate(result["critical_flags"], 1):
            lines.append(f"   {i}. {flag}")
    
    lines.append("\n" + "=" * 50)
    return "\n".join(lines)
