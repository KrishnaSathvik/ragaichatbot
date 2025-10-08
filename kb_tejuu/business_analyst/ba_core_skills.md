---
tags: [business-analyst, requirements-gathering, stakeholder-management, documentation, process-improvement]
persona: ba
---

# Business Analyst Core Skills & Tejuu's Experience

## Requirements Gathering and Analysis

### Stakeholder Interviews and Workshops
**Tejuu's Approach:**
So in my role as a Business Analyst, I've conducted hundreds of stakeholder interviews and workshops. What I found works best is starting with open-ended questions to understand the business problem before diving into solutions.

For example, at my previous company, we had a project where the sales team wanted a new reporting dashboard. Instead of just asking what reports they needed, I spent time understanding their daily workflows, pain points, and what decisions they were trying to make. This helped me uncover that they actually needed real-time alerts, not just another dashboard.

**My Interview Technique:**
```
Preparation Phase:
- Research the stakeholder's role and department
- Review existing documentation and processes
- Prepare open-ended questions
- Set clear meeting objectives

During the Interview:
- Start with business context: "Walk me through your typical day"
- Ask "why" questions: "Why is this important to you?"
- Use active listening and take detailed notes
- Clarify assumptions: "So what I'm hearing is..."
- Ask about pain points: "What frustrates you most about the current process?"

Follow-up:
- Send meeting notes within 24 hours
- Confirm understanding of key points
- Identify any gaps or follow-up questions
```

### Requirements Documentation
**Tejuu's Documentation Standards:**
I've learned that good documentation is the foundation of successful projects. Here's how I structure my requirements documents:

**Business Requirements Document (BRD) Template:**
```
1. Executive Summary
   - Project overview (2-3 paragraphs)
   - Business objectives
   - Expected benefits and ROI

2. Current State Analysis
   - As-Is process flows
   - Pain points and challenges
   - Current system limitations

3. Future State Vision
   - To-Be process flows
   - Expected improvements
   - Success metrics

4. Functional Requirements
   - User stories with acceptance criteria
   - Business rules
   - Data requirements

5. Non-Functional Requirements
   - Performance requirements
   - Security and compliance
   - Usability standards

6. Assumptions and Constraints
7. Dependencies and Risks
8. Approval and Sign-off
```

**User Story Format I Use:**
```
As a [role], I want to [action] so that [benefit].

Acceptance Criteria:
- Given [context]
- When [action]
- Then [expected result]

Example:
As a Sales Manager, I want to view real-time sales performance by region 
so that I can identify underperforming areas and take immediate action.

Acceptance Criteria:
- Given I am logged into the dashboard
- When I select a specific date range
- Then I see sales data grouped by region with YoY comparison
- And I can drill down to individual sales rep performance
```

## Process Mapping and Improvement

### Creating Process Flow Diagrams
**Tejuu's Process Mapping Experience:**
One of my key strengths is visualizing complex business processes. I use tools like Visio, Lucidchart, and Miro to create process maps that everyone can understand.

**My Process Mapping Approach:**
```
Step 1: Identify Process Boundaries
- Where does the process start?
- Where does it end?
- What triggers the process?

Step 2: Map Current State (As-Is)
- Interview process owners
- Shadow users performing the process
- Document every step, decision point, and handoff
- Identify pain points and bottlenecks

Step 3: Analyze and Identify Improvements
- Look for redundant steps
- Identify manual tasks that could be automated
- Find bottlenecks causing delays
- Spot quality issues or error-prone steps

Step 4: Design Future State (To-Be)
- Eliminate unnecessary steps
- Automate manual processes
- Streamline handoffs
- Add quality checks where needed

Step 5: Calculate Impact
- Time savings
- Cost reduction
- Error reduction
- Customer satisfaction improvement
```

**Real Example - Order Processing Improvement:**
```
As-Is Process (12 steps, 45 minutes average):
1. Customer calls to place order
2. Sales rep manually enters order in Excel
3. Sales rep emails order to inventory team
4. Inventory team checks stock manually
5. Inventory team emails back availability
6. Sales rep calls customer to confirm
7. Sales rep enters order in ERP system
8. Finance team manually creates invoice
9. Finance emails invoice to customer
10. Warehouse receives printed order form
11. Warehouse picks and packs order
12. Shipping updates tracking manually

To-Be Process (6 steps, 15 minutes average):
1. Customer places order through web portal
2. System automatically checks inventory
3. System confirms order and sends confirmation email
4. ERP system auto-generates invoice
5. Warehouse receives digital order notification
6. System auto-updates tracking information

Impact:
- 67% time reduction (45 min → 15 min)
- 90% fewer errors (manual entry eliminated)
- $50K annual cost savings
- Improved customer satisfaction (instant confirmation)
```

## Data Analysis and Reporting

### SQL for Business Analysis
**Tejuu's SQL Skills:**
As a Business Analyst, I use SQL daily to extract insights from databases. Here are some common queries I run:

**Sales Performance Analysis:**
```sql
-- Monthly sales trend with year-over-year comparison
SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(order_amount) as current_year_sales,
    LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date)) as previous_year_sales,
    ROUND(((SUM(order_amount) - LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date))) 
           / LAG(SUM(order_amount), 12) OVER (ORDER BY DATE_TRUNC('month', order_date))) * 100, 2) as yoy_growth_pct
FROM orders
WHERE order_date >= CURRENT_DATE - INTERVAL '2 years'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month;
```

**Customer Segmentation:**
```sql
-- RFM analysis for customer segmentation
WITH customer_metrics AS (
    SELECT 
        customer_id,
        MAX(order_date) as last_order_date,
        COUNT(DISTINCT order_id) as order_count,
        SUM(order_amount) as total_spent
    FROM orders
    WHERE order_date >= CURRENT_DATE - INTERVAL '1 year'
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT 
        customer_id,
        DATEDIFF(CURRENT_DATE, last_order_date) as recency_days,
        order_count as frequency,
        total_spent as monetary,
        NTILE(5) OVER (ORDER BY DATEDIFF(CURRENT_DATE, last_order_date) DESC) as recency_score,
        NTILE(5) OVER (ORDER BY order_count) as frequency_score,
        NTILE(5) OVER (ORDER BY total_spent) as monetary_score
    FROM customer_metrics
)
SELECT 
    customer_id,
    recency_days,
    frequency,
    monetary,
    CASE 
        WHEN recency_score >= 4 AND frequency_score >= 4 THEN 'Champions'
        WHEN recency_score >= 3 AND frequency_score >= 3 THEN 'Loyal Customers'
        WHEN recency_score >= 4 AND frequency_score <= 2 THEN 'Promising'
        WHEN recency_score <= 2 AND frequency_score >= 3 THEN 'At Risk'
        WHEN recency_score <= 2 AND frequency_score <= 2 THEN 'Lost'
        ELSE 'Others'
    END as customer_segment
FROM rfm_scores;
```

**Product Performance:**
```sql
-- Top performing products with contribution analysis
SELECT 
    product_name,
    SUM(quantity_sold) as total_quantity,
    SUM(revenue) as total_revenue,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER (), 2) as revenue_contribution_pct,
    ROUND(SUM(SUM(revenue)) OVER (ORDER BY SUM(revenue) DESC) * 100.0 / SUM(SUM(revenue)) OVER (), 2) as cumulative_pct
FROM sales
WHERE sale_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 20;
```

## Stakeholder Management

### Communication Strategies
**Tejuu's Stakeholder Management:**
Managing different stakeholders with different priorities is one of the biggest challenges. Here's what I've learned:

**Stakeholder Analysis Matrix:**
```
High Power, High Interest (Manage Closely):
- C-level executives
- Project sponsors
- Key decision makers
Strategy: Regular updates, involve in key decisions, address concerns immediately

High Power, Low Interest (Keep Satisfied):
- Department heads not directly involved
- Compliance/legal teams
Strategy: Periodic updates, keep informed of major changes

Low Power, High Interest (Keep Informed):
- End users
- Team members
Strategy: Regular communication, gather feedback, involve in testing

Low Power, Low Interest (Monitor):
- Peripheral stakeholders
Strategy: Minimal communication, inform of major milestones
```

**My Communication Approach:**
```
For Executives:
- Focus on business impact and ROI
- Use high-level dashboards and metrics
- Keep updates brief (1-page summaries)
- Highlight risks and mitigation plans

For Technical Teams:
- Provide detailed requirements and specifications
- Use technical language appropriately
- Be available for clarification
- Respect their expertise and input

For End Users:
- Use simple, non-technical language
- Show how changes benefit them
- Involve them in testing and feedback
- Address their concerns empathetically

For Project Managers:
- Provide clear timelines and dependencies
- Flag blockers early
- Keep requirements documentation updated
- Attend all status meetings prepared
```

## Gap Analysis and Feasibility Studies

### Conducting Gap Analysis
**Tejuu's Gap Analysis Framework:**
```
1. Define Current State
   - Document existing capabilities
   - Identify current performance metrics
   - List available resources

2. Define Desired Future State
   - Document required capabilities
   - Set target performance metrics
   - Identify needed resources

3. Identify Gaps
   - Capability gaps
   - Performance gaps
   - Resource gaps
   - Knowledge/skill gaps

4. Prioritize Gaps
   - Impact on business objectives
   - Urgency and dependencies
   - Cost and effort to close

5. Develop Action Plan
   - Quick wins (high impact, low effort)
   - Strategic initiatives (high impact, high effort)
   - Fill-ins (low impact, low effort)
   - Reconsider (low impact, high effort)
```

## Interview Talking Points

### Technical Skills:
- Requirements gathering and documentation
- Process mapping and improvement
- SQL and data analysis
- Stakeholder management
- Gap analysis and feasibility studies

### Tools & Technologies:
- **Documentation**: Confluence, SharePoint, MS Word
- **Process Mapping**: Visio, Lucidchart, Miro, Draw.io
- **Project Management**: Jira, Azure DevOps, Asana
- **Data Analysis**: SQL, Excel, Power BI, Tableau
- **Collaboration**: MS Teams, Slack, Zoom

### Achievements:
- Reduced process time by 67% through process optimization
- Saved $50K annually by identifying automation opportunities
- Improved customer satisfaction by 25% through better requirements
- Successfully delivered 15+ projects on time and within budget
- Managed stakeholder groups of 20+ people across multiple departments
