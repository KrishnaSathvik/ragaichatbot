---
tags: [power-bi, dax, data-modeling, performance, rls, best-practices]
persona: business
---

# Advanced Power BI & DAX - Tejuu's Expertise

## Power BI Data Modeling

### Star Schema Design for Healthcare Analytics
**Tejuu's Implementation at Stryker:**
So at Stryker, I designed this comprehensive star schema for our Medicaid and healthcare analytics. The key was understanding the business requirements first - what questions do clinicians, finance, and operations teams need to answer?

**My Star Schema Structure:**
```
Fact Tables:
- fact_claims (claim_id, patient_key, provider_key, date_key, claim_amount, paid_amount, denied_amount)
- fact_patient_visits (visit_id, patient_key, facility_key, date_key, visit_type, duration_minutes, cost)
- fact_inventory (product_key, warehouse_key, date_key, quantity_on_hand, reorder_level, unit_cost)

Dimension Tables:
- dim_patient (patient_key, patient_id, age_group, gender, state, insurance_type, risk_score)
- dim_provider (provider_key, provider_id, provider_name, specialty, network_status, region)
- dim_facility (facility_key, facility_id, facility_name, facility_type, city, state, bed_count)
- dim_product (product_key, product_id, product_name, category, subcategory, manufacturer)
- dim_date (date_key, date, year, quarter, month, week, day_of_week, is_holiday, fiscal_period)
- dim_insurance (insurance_key, payer_name, plan_type, coverage_level)
```

**Relationship Best Practices I Follow:**
```
1. Always use surrogate keys (integers) for relationships
2. One-to-many relationships from dimension to fact
3. Avoid bi-directional relationships (use DAX instead)
4. Hide foreign keys from report view
5. Mark date table properly
6. Use role-playing dimensions sparingly
```

### Row-Level Security (RLS) Implementation
**Tejuu's RLS Strategy:**
So implementing RLS was critical at Central Bank and Stryker because different users needed access to different data. Here's how I approached it:

**Role-Based Access Example:**
```dax
-- Regional Manager Role
[Region] = USERPRINCIPALNAME()

-- State-Level Access
[State] IN {
    LOOKUPVALUE(
        user_access[State],
        user_access[Email],
        USERPRINCIPALNAME()
    )
}

-- Dynamic Security with Bridge Table
VAR UserEmail = USERPRINCIPALNAME()
VAR UserRegions = 
    CALCULATETABLE(
        VALUES(security_bridge[Region]),
        security_bridge[UserEmail] = UserEmail
    )
RETURN
    [Region] IN UserRegions

-- Manager Hierarchy (see your team and below)
VAR CurrentUser = USERPRINCIPALNAME()
VAR UserLevel = 
    LOOKUPVALUE(
        dim_employee[Level],
        dim_employee[Email],
        CurrentUser
    )
RETURN
    dim_employee[Manager_Email] = CurrentUser ||
    dim_employee[Email] = CurrentUser
```

**Testing RLS:**
```
1. Create test users in Azure AD
2. Use "View as" feature in Power BI Desktop
3. Test each role with sample queries
4. Document expected vs actual results
5. Validate with actual users before production
```

## Advanced DAX Patterns

### Time Intelligence Mastery
**Tejuu's Most-Used Time Intelligence Patterns:**

```dax
-- Year-to-Date with Fiscal Calendar
YTD Sales = 
CALCULATE(
    SUM(fact_sales[Amount]),
    DATESYTD(
        dim_date[Date],
        "06/30"  -- Fiscal year ends June 30
    )
)

-- Prior Year Same Period
PY Sales = 
CALCULATE(
    [Total Sales],
    SAMEPERIODLASTYEAR(dim_date[Date])
)

-- Year-over-Year Growth %
YoY Growth % = 
VAR CurrentPeriod = [Total Sales]
VAR PriorPeriod = [PY Sales]
RETURN
    DIVIDE(
        CurrentPeriod - PriorPeriod,
        PriorPeriod,
        0
    )

-- Month-to-Date vs Prior Month-to-Date
MTD vs PMTD = 
VAR MTD = 
    CALCULATE(
        [Total Sales],
        DATESMTD(dim_date[Date])
    )
VAR PMTD = 
    CALCULATE(
        [Total Sales],
        DATESMTD(
            DATEADD(dim_date[Date], -1, MONTH)
        )
    )
RETURN
    MTD - PMTD

-- Rolling 12 Months
Rolling 12M Sales = 
CALCULATE(
    [Total Sales],
    DATESINPERIOD(
        dim_date[Date],
        LASTDATE(dim_date[Date]),
        -12,
        MONTH
    )
)

-- Same Period Last Year with Date Table
SPLY Sales = 
CALCULATE(
    [Total Sales],
    DATEADD(dim_date[Date], -1, YEAR)
)
```

### Complex Calculated Columns vs Measures
**When I Use Each:**

**Calculated Columns (Stored in Model):**
```dax
-- Age Group (Calculated Column)
Age Group = 
SWITCH(
    TRUE(),
    dim_patient[Age] < 18, "Pediatric",
    dim_patient[Age] < 65, "Adult",
    "Senior"
)

-- Days Since Last Visit (Calculated Column)
Days Since Last Visit = 
DATEDIFF(
    dim_patient[Last_Visit_Date],
    TODAY(),
    DAY
)

-- Full Name (Calculated Column)
Full Name = 
dim_patient[First_Name] & " " & dim_patient[Last_Name]
```

**Measures (Calculated at Query Time):**
```dax
-- Total Claims (Measure)
Total Claims = 
SUM(fact_claims[Claim_Amount])

-- Average Claim Amount (Measure)
Avg Claim Amount = 
AVERAGE(fact_claims[Claim_Amount])

-- Distinct Patient Count (Measure)
Patient Count = 
DISTINCTCOUNT(fact_claims[Patient_Key])

-- Claim Approval Rate (Measure)
Approval Rate = 
DIVIDE(
    CALCULATE([Total Claims], fact_claims[Status] = "Approved"),
    [Total Claims],
    0
)
```

### Advanced DAX for Healthcare Analytics
**Tejuu's Medicaid Analytics at Stryker:**

```dax
-- Patient Risk Score
Patient Risk Score = 
VAR PatientVisits = 
    CALCULATE(
        COUNTROWS(fact_patient_visits),
        ALLEXCEPT(fact_patient_visits, fact_patient_visits[Patient_Key])
    )
VAR ChronicConditions = 
    CALCULATE(
        DISTINCTCOUNT(fact_diagnosis[Condition_Code]),
        fact_diagnosis[Is_Chronic] = TRUE()
    )
VAR HighCostFlag = 
    IF(
        CALCULATE(
            SUM(fact_claims[Paid_Amount]),
            ALLEXCEPT(fact_claims, fact_claims[Patient_Key])
        ) > 50000,
        1,
        0
    )
RETURN
    (PatientVisits * 0.3) + 
    (ChronicConditions * 0.5) + 
    (HighCostFlag * 0.2)

-- Readmission Rate (30-day)
30-Day Readmission Rate = 
VAR ReadmissionWindow = 30
VAR Readmissions = 
    CALCULATE(
        COUNTROWS(fact_patient_visits),
        FILTER(
            fact_patient_visits,
            VAR CurrentVisitDate = fact_patient_visits[Visit_Date]
            VAR PatientKey = fact_patient_visits[Patient_Key]
            VAR PriorVisit = 
                CALCULATE(
                    MAX(fact_patient_visits[Visit_Date]),
                    ALLEXCEPT(fact_patient_visits, fact_patient_visits[Patient_Key]),
                    fact_patient_visits[Visit_Date] < CurrentVisitDate
                )
            RETURN
                DATEDIFF(PriorVisit, CurrentVisitDate, DAY) <= ReadmissionWindow
        )
    )
VAR TotalVisits = COUNTROWS(fact_patient_visits)
RETURN
    DIVIDE(Readmissions, TotalVisits, 0)

-- Cost per Member per Month (PMPM)
PMPM = 
VAR TotalCost = SUM(fact_claims[Paid_Amount])
VAR MemberMonths = 
    SUMX(
        VALUES(dim_patient[Patient_Key]),
        CALCULATE(
            DISTINCTCOUNT(dim_date[Month_Year])
        )
    )
RETURN
    DIVIDE(TotalCost, MemberMonths, 0)

-- Length of Stay Analysis
Avg Length of Stay = 
AVERAGEX(
    fact_patient_visits,
    DATEDIFF(
        fact_patient_visits[Admission_Date],
        fact_patient_visits[Discharge_Date],
        DAY
    )
)

-- Case Mix Index
Case Mix Index = 
AVERAGEX(
    VALUES(fact_patient_visits[Visit_ID]),
    RELATED(dim_drg[Relative_Weight])
)
```

### Performance Optimization Techniques
**My DAX Optimization Rules:**

```dax
-- BEFORE: Slow (multiple context transitions)
Slow Measure = 
SUMX(
    fact_sales,
    fact_sales[Quantity] * 
    RELATED(dim_product[Unit_Price])
)

-- AFTER: Fast (calculated column or import both fields)
Fast Measure = 
SUM(fact_sales[Line_Total])

-- BEFORE: Slow (row context in measure)
Slow Customer Count = 
COUNTROWS(
    FILTER(
        dim_customer,
        CALCULATE(SUM(fact_sales[Amount])) > 1000
    )
)

-- AFTER: Fast (use CALCULATETABLE)
Fast Customer Count = 
COUNTROWS(
    CALCULATETABLE(
        VALUES(dim_customer[Customer_Key]),
        fact_sales[Amount] > 1000
    )
)

-- Use Variables to Avoid Recalculation
Optimized Measure = 
VAR TotalSales = SUM(fact_sales[Amount])
VAR TotalCost = SUM(fact_sales[Cost])
VAR Margin = TotalSales - TotalCost
VAR MarginPct = DIVIDE(Margin, TotalSales, 0)
RETURN
    IF(MarginPct > 0.3, "High", "Low")
```

## Power BI Performance Tuning

### Query Performance Optimization
**Tejuu's Optimization Checklist:**

```
1. Data Model Optimization:
   - Remove unused columns and tables
   - Use integer keys instead of text
   - Disable auto date/time hierarchy
   - Use appropriate data types
   - Avoid calculated columns when possible

2. DAX Optimization:
   - Use variables to store intermediate results
   - Avoid row context in measures
   - Use TREATAS instead of FILTER when possible
   - Minimize use of CALCULATE
   - Use SELECTEDVALUE instead of VALUES + HASONEVALUE

3. Visual Optimization:
   - Limit visuals per page (max 10-15)
   - Use bookmarks for different views
   - Avoid high-cardinality fields in visuals
   - Use aggregated data when possible
   - Implement drill-through instead of showing all detail

4. Data Refresh Optimization:
   - Use incremental refresh for large tables
   - Partition large tables by date
   - Schedule refreshes during off-peak hours
   - Use dataflows for common transformations
```

### Incremental Refresh Configuration
**My Implementation at Stryker:**

```
1. Create RangeStart and RangeEnd parameters (Date/Time type)
2. Filter source data:
   = Table.SelectRows(Source, 
       each [Date] >= RangeStart and [Date] < RangeEnd)
3. Configure incremental refresh policy:
   - Archive data: 5 years
   - Incremental refresh: 10 days
   - Detect data changes: Yes
   - Only refresh complete days: Yes
```

## Advanced Visualizations

### Custom Visuals I Use
**Tejuu's Favorite Custom Visuals:**

```
1. Zebra BI Tables - For variance analysis
2. Drill Down Donut PRO - For hierarchical data
3. Chiclet Slicer - For better filter experience
4. Power KPI - For executive dashboards
5. Sankey Diagram - For flow analysis
6. Box and Whisker - For distribution analysis
```

### Conditional Formatting Patterns
**My Advanced Formatting Techniques:**

```dax
-- Color Scale Based on Performance
Color Measure = 
VAR Performance = [Actual] / [Target]
RETURN
    SWITCH(
        TRUE(),
        Performance >= 1.1, "#00B050",  -- Green
        Performance >= 0.9, "#FFC000",  -- Yellow
        "#FF0000"                        -- Red
    )

-- Icon Set Based on Trend
Trend Icon = 
VAR CurrentMonth = [Sales This Month]
VAR PriorMonth = [Sales Last Month]
VAR Change = DIVIDE(CurrentMonth - PriorMonth, PriorMonth, 0)
RETURN
    SWITCH(
        TRUE(),
        Change > 0.05, "▲",
        Change < -0.05, "▼",
        "■"
    )

-- Data Bars with Conditional Logic
Data Bar Value = 
VAR MaxValue = 
    CALCULATE(
        MAX(fact_sales[Amount]),
        ALLSELECTED(dim_product[Product_Name])
    )
VAR CurrentValue = SUM(fact_sales[Amount])
RETURN
    DIVIDE(CurrentValue, MaxValue, 0)
```

## Power BI Deployment & ALM

### Application Lifecycle Management
**Tejuu's ALM Strategy:**

```
Development → Test → Production Pipeline

1. Development Workspace:
   - Individual developer workspaces
   - Connect to Dev database
   - Rapid iteration and testing
   - Git integration for version control

2. Test Workspace:
   - Shared team workspace
   - Connect to Test database
   - UAT with business users
   - Performance testing

3. Production Workspace:
   - Premium capacity
   - Connect to Prod database
   - Scheduled refreshes
   - Monitoring and alerts

Deployment Process:
1. Export .pbix from Dev
2. Update data source to Test
3. Publish to Test workspace
4. UAT sign-off
5. Export from Test
6. Update data source to Prod
7. Publish to Prod workspace
8. Configure refresh schedule
9. Set up monitoring
```

### Version Control with Git
**My Git Workflow:**

```bash
# Save Power BI file as PBIX
# Use external tools to extract PBIT

# Git workflow
git checkout -b feature/new-dashboard
# Make changes in Power BI
git add .
git commit -m "Add sales performance dashboard"
git push origin feature/new-dashboard
# Create pull request
# Code review
# Merge to main
```

### Deployment Pipelines
**Configuration:**

```
Pipeline Stages:
1. Development
   - Auto-deploy on commit to dev branch
   - Run data quality tests
   - Generate documentation

2. Test
   - Deploy on PR approval
   - Run regression tests
   - UAT validation

3. Production
   - Manual approval required
   - Deploy during maintenance window
   - Backup before deployment
   - Rollback plan ready
```

## Power BI Best Practices

### Naming Conventions
**My Standard Naming:**

```
Tables:
- fact_sales, fact_claims, fact_inventory
- dim_customer, dim_product, dim_date

Measures:
- Total Sales, Avg Order Value, YTD Revenue
- Use spaces, title case
- Group related measures in folders

Columns:
- Use snake_case or PascalCase consistently
- Prefix calculated columns with "calc_"
- Hide foreign keys

Relationships:
- Always name relationships descriptively
- Document complex relationships
```

### Documentation Standards
**What I Document:**

```markdown
# Dashboard Documentation

## Purpose
Executive sales performance dashboard for regional managers

## Data Sources
- Azure SQL: sales_db.fact_sales
- Refresh: Daily at 6 AM EST
- Latency: T-1 day

## Key Metrics
- Total Sales: SUM of fact_sales[Amount]
- YoY Growth: (Current - Prior Year) / Prior Year
- Target Attainment: Actual / Target

## Filters
- Date Range: Last 12 months default
- Region: Multi-select
- Product Category: Single select

## Row-Level Security
- Regional managers see their region only
- VPs see all regions
- Executives see all data

## Known Issues
- Data quality issue with Region "Unknown" - investigating
- Slow performance on Product Detail page - optimization in progress

## Change Log
- 2024-01-15: Added YoY comparison
- 2024-01-10: Initial release
```

## Interview Talking Points

### Technical Achievements
- Built 50+ Power BI dashboards serving 200+ users
- Implemented RLS for 10+ different security roles
- Optimized DAX reducing query time from 30s to 3s
- Designed star schemas for healthcare and sales analytics
- Achieved 99% dashboard uptime in production

### Problem-Solving Examples
**Performance Issue:**
"At Stryker, we had this dashboard that was taking 30 seconds to load. I analyzed the DAX and found we were using calculated columns in measures, causing multiple context transitions. I refactored the measures to use variables and proper filter context, and got the load time down to 3 seconds."

**Complex Business Logic:**
"At Central Bank, finance needed a complex calculation for regulatory reporting. It involved multiple date ranges, conditional logic, and aggregations across different grain levels. I broke it down into smaller measures, used variables for readability, and documented each step. The final measure was accurate and performant."

### Tools & Technologies
- **Power BI**: Desktop, Service, Premium, Embedded, Report Server
- **DAX**: Advanced patterns, optimization, debugging
- **Power Query**: M language, custom functions, data transformation
- **Azure**: Synapse, Data Factory, SQL Database
- **Version Control**: Git, Azure DevOps
- **ALM**: Deployment pipelines, testing, documentation
