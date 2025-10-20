# 🎯 Interview Bot Answer Quality Checklist

**Rate each answer 1-5 across these dimensions:**

## 📐 **Structure (1-5)**
- [ ] **Problem** clearly stated (1 sentence)
- [ ] **Approach** explained (2-3 sentences) 
- [ ] **Stack/Tools** mentioned inline
- [ ] **Result** with metric included
- [ ] **Business Impact** closing line
- [ ] **Length**: ~130 words (110-150 range)

## 📊 **Metrics (1-5)**
- [ ] Uses **verified numbers** from metrics store
- [ ] Says "approximately" if uncertain
- [ ] **No invented metrics** or hallucinated data
- [ ] **Before→After** comparison when relevant
- [ ] **Specific percentages** (not vague "improved significantly")

## 🎭 **Tone (1-5)**
- [ ] **Conversational** ("The tricky part was...", "So essentially...")
- [ ] **Interview-ready** (not too technical, not too casual)
- [ ] **Confident ownership** ("I designed...", "I implemented...")
- [ ] **Natural transitions** between points
- [ ] **Business context** (why it mattered to users/ops)

## 🔗 **Continuity (1-5)**
- [ ] **Follow-ups** start with bridge ("Building on what I said about...")
- [ ] **References** previous points appropriately
- [ ] **Maintains context** across multi-turn conversations
- [ ] **Avoids repetition** of same details
- [ ] **Progressive depth** (each follow-up goes deeper)

## 🛡️ **Compliance (1-5)**
- [ ] **No PHI/PII** mentioned inappropriately
- [ ] **HIPAA-safe** patterns described
- [ ] **Governance** mentioned for regulated contexts
- [ ] **No internal URLs** or sensitive details
- [ ] **Professional boundaries** maintained

---

## 🎯 **Quick Scoring Guide**

| Score | Description | Example |
|-------|-------------|---------|
| **5** | Excellent | Perfect structure, verified metrics, natural tone, great continuity |
| **4** | Good | Minor issues, mostly follows template, good metrics |
| **3** | Average | Some structure issues, mixed metrics, decent tone |
| **2** | Poor | Major gaps, invented metrics, awkward tone |
| **1** | Failing | No structure, hallucinated data, inappropriate content |

---

## 🔍 **Common Issues to Watch For**

### ❌ **Red Flags**
- Invented metrics ("improved by 87%" with no source)
- PHI in logs ("we logged patient IDs for debugging")
- Internal details ("our internal Jira board at...")
- Vague claims ("significantly improved" without numbers)
- No business impact ("it worked well")

### ✅ **Green Flags**
- Specific, verified metrics
- Clear problem→solution flow
- Business impact closing
- Natural conversation flow
- Compliance awareness

---

## 📝 **Template Intent Mapping**

| Intent | Should Include | Example Keywords |
|--------|----------------|------------------|
| **technical_architecture** | Problem, Stack, Result | "architecture", "pipeline", "system" |
| **metrics_performance** | Baseline, Intervention, Numbers | "accuracy", "latency", "improved" |
| **documentation_process** | What, How, Tools, Outcome | "documentation", "process", "standards" |
| **tool_adaptation** | Acknowledge, Analogy, Mapping | "adapt", "different platform", "switch" |
| **collaboration_leadership** | Cadence, Visibility, Metrics | "team", "offshore", "coordination" |
| **domain_understanding** | Pain, Nuance, Controls | "HIPAA", "compliance", "governance" |
| **followup_drilldown** | Bridge, Detail, Mini-metric | "you mentioned", "earlier", "elaborate" |
| **behavioral_star** | Situation, Task, Action, Result | "tell me about a time", "challenge" |

---

**Total Score: ___/25 (Average: ___)**

**Notes:**
- [ ] Template system working
- [ ] RAG retrieval integrated  
- [ ] Sources panel populated
- [ ] Citations working
- [ ] Auto-detection functioning
