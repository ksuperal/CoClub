# AI Boost Recommendation Flow

## Overview

After 72 hours of metrics collection, the AI automatically analyzes post performance and suggests which posts should be boosted with recommended budgets.

---

## 📊 Complete Timeline

```
Day 0 (Hour 0):
├─ User creates campaign
├─ AI detects campaign type (educational, promotional, etc.)
├─ AI assigns primary metric (saves, reach, link_clicks)
├─ AI calculates expected thresholds based on brand size
└─ Posts are published to Facebook/Instagram

Hour 1-72:
├─ Metrics polled every hour
├─ post_metrics table accumulates snapshots
└─ User can view metrics graph in real-time

Hour 72 (After 3 days):
├─ Feedback job runs (step5_feedback.py)
├─ Final metrics collected
├─ Campaign report generated
├─ ✨ AI BOOST RECOMMENDATIONS GENERATED ← NEW!
│   ├─ Compares actual vs expected performance
│   ├─ Identifies posts that exceeded expectations
│   ├─ Calculates optimal budget based on performance
│   └─ Stores recommendations in database
└─ Campaign marked as "completed"
```

---

## 🧠 Boost Recommendation Logic

### **When AI Suggests a Boost:**

```python
# Post qualifies if:
1. Actual metric >= 1.5x "good" threshold
2. Post status = "posted" (successfully published)
3. Has real metrics data (not failed/pending)

# Example:
Expected saves (good threshold): 500
Actual saves: 900
Performance: 1.8x (180% of expected)
→ ✅ RECOMMEND BOOST
```

### **Confidence Levels:**

| Performance | Confidence | Action |
|---|---|---|
| 2.0x+ over expected | **High** | Strong recommendation, 7-day boost |
| 1.5-2.0x over expected | **Medium** | Moderate recommendation, 5-day boost |
| < 1.5x over expected | **Low** | No recommendation |

---

## 💰 Budget Calculation

AI dynamically calculates budget based on performance:

```python
Base Budget: $10/day
+ Bonus: $2 per 50% over threshold (capped at +$20)

Examples:
- 1.5x performance → $10 + $2 = $12/day
- 2.0x performance → $10 + $8 = $18/day
- 3.0x performance → $10 + $20 = $30/day (maxed)
```

**Duration:**
- High confidence: 7 days
- Medium confidence: 5 days

---

## 📋 Recommendation Data Structure

Stored in `content_performance_insights.ai_analysis`:

```json
{
  "boost_suggestion": {
    "should_boost": true,
    "reason": "Educational post exceeded expected saves by 180% (900 vs 500 expected)",
    "confidence": "high",
    "suggested_budget": 18.00,
    "suggested_duration": 7,
    "expected_reach": 25000,
    "objective": "OUTCOME_ENGAGEMENT"
  }
}
```

---

## 🔄 Integration Points

### **1. Feedback Job (step5_feedback.py)**

```python
# After 72 hours, automatically:
run_feedback_job(campaign_id)
    ↓
generate_boost_recommendations_for_campaign(campaign_id)
    ↓
store_boost_recommendations(campaign_id, recommendations)
```

### **2. Frontend Display (TO BUILD)**

```javascript
// Fetch post with performance insights
const post = await fetch(`/v1/campaigns/posts/${postId}/insights`);

if (post.ai_analysis?.boost_suggestion?.should_boost) {
  // Show boost recommendation UI
  showBoostBanner({
    reason: post.ai_analysis.boost_suggestion.reason,
    suggestedBudget: post.ai_analysis.boost_suggestion.suggested_budget,
    confidence: post.ai_analysis.boost_suggestion.confidence
  });
}
```

---

## 🎨 Frontend UI Examples

### **1. Post Card with Boost Badge**

```
┌─────────────────────────────────────────┐
│ Post #2: "How to choose stocking color" │
├─────────────────────────────────────────┤
│ Performance: EXCELLENT ⭐⭐⭐            │
│ Saves: 900 (180% above expected!)       │
│                                         │
│ 💡 AI RECOMMENDATION                    │
│ ┌─────────────────────────────────────┐ │
│ │ 🚀 This post is crushing it!        │ │
│ │                                     │ │
│ │ Boost it to reach 25,000+ more     │ │
│ │ people who will save & share.      │ │
│ │                                     │ │
│ │ Suggested: $18/day for 7 days      │ │
│ │                                     │ │
│ │ [Boost Now] [Maybe Later]          │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### **2. Campaign Dashboard Widget**

```
┌─────────────────────────────────────────┐
│ 📊 Campaign Report                      │
├─────────────────────────────────────────┤
│ Status: Completed (72 hours)            │
│ Top Performer: Post #2 (900 saves)      │
│                                         │
│ 🎯 AI RECOMMENDATIONS                   │
│ ┌─────────────────────────────────────┐ │
│ │ 2 posts ready to boost              │ │
│ │                                     │ │
│ │ 1. Post #2 (High confidence)        │ │
│ │    $18/day × 7 days = $126 total    │ │
│ │    Expected: +25,000 reach          │ │
│ │                                     │ │
│ │ 2. Post #4 (Medium confidence)      │ │
│ │    $12/day × 5 days = $60 total     │ │
│ │    Expected: +15,000 reach          │ │
│ │                                     │ │
│ │ [Review All] [Boost Both - $186]    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### **3. Boost Modal (Pre-filled)**

```
┌─────────────────────────────────────────┐
│ 🚀 Boost This Post                      │
├─────────────────────────────────────────┤
│ 💡 AI Recommendation                    │
│ "Educational post exceeded expected     │
│  saves by 180%"                         │
│                                         │
│ Budget: $[18] /day ▼                    │
│         ↑ AI suggested                  │
│                                         │
│ Duration: [7] days ▼                    │
│           ↑ AI suggested                │
│                                         │
│ Expected Results:                       │
│ • +25,000 people reached                │
│ • ~1,250 additional saves               │
│ • $2.85 CPM (cost per 1000 views)       │
│                                         │
│ Total Cost: $126.00                     │
│                                         │
│ ✅ Use AI Settings                      │
│ ⚙️ Customize Budget                     │
│                                         │
│ [Cancel] [Start Boost]                  │
└─────────────────────────────────────────┘
```

---

## 🎯 Decision Matrix

### **Campaign Type → Objective Mapping**

| Campaign Type | Primary Metric | Boost Objective |
|---|---|---|
| Educational | saves | OUTCOME_ENGAGEMENT |
| Promotional | link_clicks | OUTCOME_TRAFFIC |
| Brand Awareness | reach | OUTCOME_AWARENESS |
| Product Launch | reach | OUTCOME_AWARENESS |
| Event | reach | OUTCOME_AWARENESS |

---

## 📊 Example Scenarios

### **Scenario 1: High-Performing Educational Post**

```
Campaign: "Stocking Color Guide"
Type: Educational
Expected saves: 500 (good), 800 (excellent)
Actual saves: 1200 (150% of excellent)

AI Decision:
✅ Should Boost: YES
Confidence: HIGH
Reason: "Educational post exceeded expected saves by 150%"
Budget: $18/day × 7 days = $126
Objective: OUTCOME_ENGAGEMENT
Expected Reach: +25,000 people
```

### **Scenario 2: Moderate Promotional Post**

```
Campaign: "Flash Sale 40% Off"
Type: Promotional
Expected link_clicks: 100 (good), 200 (excellent)
Actual link_clicks: 175 (87.5% of excellent, 175% of good)

AI Decision:
✅ Should Boost: YES
Confidence: MEDIUM
Reason: "Promotional post exceeded expected link_clicks by 75%"
Budget: $12/day × 5 days = $60
Objective: OUTCOME_TRAFFIC
Expected Reach: +15,000 people
```

### **Scenario 3: Under-Performing Post**

```
Campaign: "New Product Launch"
Type: Product Launch
Expected reach: 5000 (good), 8000 (excellent)
Actual reach: 4200 (84% of good)

AI Decision:
❌ Should Boost: NO
Reason: Post did not meet "good" threshold
Action: None (no recommendation generated)
```

---

## 🔍 Where Recommendations Are Stored

### **Database Table:**
`content_performance_insights`

### **Column:**
`ai_analysis` (JSONB)

### **Structure:**
```json
{
  "hook_type": "question",
  "visual_style": "product-comparison",
  "caption_strategy": "educational-tips",
  "boost_suggestion": {  ← NEW!
    "should_boost": true,
    "reason": "...",
    "confidence": "high",
    "suggested_budget": 18.00,
    "suggested_duration": 7,
    "expected_reach": 25000,
    "objective": "OUTCOME_ENGAGEMENT"
  }
}
```

---

## 🚀 API Endpoints (Existing)

### **Get Post Insights (includes boost recommendation):**
```http
GET /v1/campaigns/posts/{post_id}/insights
Authorization: Bearer {token}

Response:
{
  "post_id": "...",
  "performance_tier": "excellent",
  "ai_analysis": {
    "boost_suggestion": {
      "should_boost": true,
      ...
    }
  }
}
```

### **Get Campaign Insights (all posts):**
```http
GET /v1/campaigns/{campaign_id}/performance-insights
Authorization: Bearer {token}

Response: [
  {
    "post_id": "...",
    "ai_analysis": { "boost_suggestion": {...} }
  }
]
```

---

## ⚙️ Configuration Options

### **Minimum Multiplier (can be tuned):**
```python
# In boost_recommendations.py line ~60
if performance_multiplier < 1.5:  # Default: 1.5x
    return None

# To be more aggressive: use 1.3x
# To be more conservative: use 2.0x
```

### **Budget Calculation (can be tuned):**
```python
# In boost_recommendations.py line ~100
base_budget = 10.0  # Minimum budget
bonus_budget = min((performance_multiplier - 1) * 4, 20.0)  # Bonus per performance

# To suggest higher budgets: increase multiplier (e.g., * 6)
# To cap lower: reduce max (e.g., 15.0)
```

---

## 🎓 Key Benefits

### **For Users:**
✅ **No guesswork** - AI tells them exactly which posts to boost
✅ **Optimal budget** - Don't waste money on underperformers
✅ **Right timing** - Boost after organic performance plateaus
✅ **Smart targeting** - Objective matches campaign type

### **For CoClub:**
✅ **Higher boost adoption** - Users see clear ROI potential
✅ **Better results** - Only boosting proven winners
✅ **User retention** - Success leads to more campaigns
✅ **Data-driven** - Decisions based on actual performance

---

## 📈 Success Metrics to Track

Once implemented in frontend:

1. **Recommendation Acceptance Rate**
   - How many users boost when AI recommends?
   - Target: >40% acceptance rate

2. **Boosted Post Performance**
   - Do boosted posts perform better than non-boosted?
   - Target: 2-3x better ROAS

3. **Budget Accuracy**
   - Is suggested budget appropriate?
   - Track if users adjust up/down

4. **Confidence Correlation**
   - Do "high confidence" recommendations perform better?
   - Validate the confidence model

---

## 🔮 Future Enhancements

### **Phase 2: Learn from Boost Results**
```python
# After boost completes, compare predicted vs actual
# Update budget calculation model based on real outcomes
```

### **Phase 3: Multi-Post Strategy**
```python
# Suggest boosting top 2-3 posts in sequence
# Optimize total campaign budget allocation
```

### **Phase 4: A/B Testing**
```python
# Boost same post with different budgets/targeting
# Find optimal settings per campaign type
```

---

## ✅ Current Implementation Status

- ✅ Boost recommendation logic (`boost_recommendations.py`)
- ✅ Integration with feedback job (`step5_feedback.py`)
- ✅ Database storage (`content_performance_insights.ai_analysis`)
- ✅ API endpoints (existing insights endpoints)
- ❌ Frontend UI (not built yet)
- ❌ User notifications (not built yet)

---

## 🏁 Summary

**When:** After 72 hours of metrics collection
**What:** AI analyzes performance vs expectations
**Decision:** Recommend boost if 1.5x+ over "good" threshold
**Budget:** $10-30/day based on performance multiplier
**Storage:** `content_performance_insights.ai_analysis`
**Next:** Build frontend UI to display recommendations

---

**The system is ready!** Just need to build the UI to show boost recommendations to users. 🚀
