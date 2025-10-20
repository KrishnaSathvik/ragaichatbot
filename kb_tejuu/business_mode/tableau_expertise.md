---
tags: [tableau, data-visualization, calculated-fields, parameters, dashboards, lod]
persona: business
---

# Tableau Expertise - Tejuu's Experience

## Tableau Dashboard Development

### Building Executive Dashboards
**Tejuu's Approach:**
So I've built numerous executive dashboards in Tableau, and what I've learned is that executives want to see the story quickly. They don't have time to dig through data - they need insights at a glance.

**My Executive Dashboard Structure:**
```
Page 1: Overview
- KPI Summary Cards (Revenue, Profit, Growth %)
- Trend Line (12-month rolling)
- Geographic Heat Map
- Top 10 Products/Customers
- Quick Filters (Date, Region, Category)

Page 2: Deep Dive
- Detailed Tables with Drill-Down
- Comparison Charts (Actual vs Target vs Prior Year)
- Distribution Analysis
- Cohort Analysis

Page 3: What-If Analysis
- Parameter Controls for Scenarios
- Calculated Projections
- Sensitivity Analysis
```

### Interactive Features I Implement
**Navigation and Interactivity:**

```
1. Dashboard Actions:
   - Filter Actions: Click on region to filter all visuals
   - Highlight Actions: Hover to highlight related data
   - URL Actions: Link to external systems
   - Parameter Actions: Dynamic parameter updates

2. Navigation:
   - Button navigation between pages
   - Breadcrumb navigation
   - Back button functionality
   - Reset filters button

3. Tooltips:
   - Custom tooltip worksheets
   - Show additional context
   - Mini visualizations in tooltips
   - Formatted text with key metrics
```

## Advanced Calculated Fields

### LOD (Level of Detail) Expressions
**Tejuu's Most-Used LOD Patterns:**

```tableau
// FIXED - Customer Lifetime Value
{FIXED [Customer ID]: SUM([Sales])}

// INCLUDE - Sales with Category Context
{INCLUDE [Category]: AVG([Sales])}

// EXCLUDE - Overall Average Excluding Region
{EXCLUDE [Region]: AVG([Sales])}

// Customer First Purchase Date
{FIXED [Customer ID]: MIN([Order Date])}

// Customer Cohort Analysis
// Cohort Month
{FIXED [Customer ID]: 
    MIN(DATETRUNC('month', [Order Date]))}

// Months Since First Purchase
DATEDIFF('month', 
    {FIXED [Customer ID]: MIN([Order Date])},
    [Order Date]
)

// Percent of Total by Category
SUM([Sales]) / 
{FIXED [Category]: SUM([Sales])}

// Running Total by Customer
RUNNING_SUM(SUM([Sales]))

// Rank within Category
RANK(SUM([Sales]), 'desc')

// Dense Rank for Top N
RANK_DENSE(SUM([Sales]), 'desc')
```

### Table Calculations
**My Frequently Used Table Calcs:**

```tableau
// Year-over-Year Growth
(SUM([Sales]) - LOOKUP(SUM([Sales]), -12)) / 
LOOKUP(SUM([Sales]), -12)

// Moving Average (3 months)
WINDOW_AVG(SUM([Sales]), -2, 0)

// Percent of Total
SUM([Sales]) / TOTAL(SUM([Sales]))

// Running Total
RUNNING_SUM(SUM([Sales]))

// Percent Difference from Average
(SUM([Sales]) - WINDOW_AVG(SUM([Sales]))) / 
WINDOW_AVG(SUM([Sales]))

// Index for Row Numbering
INDEX()

// First/Last Value in Partition
FIRST() = 0  // First row
LAST() = 0   // Last row

// Lookup Previous Value
LOOKUP(SUM([Sales]), -1)

// Window Sum for Cumulative %
RUNNING_SUM(SUM([Sales])) / 
TOTAL(SUM([Sales]))
```

### Complex Business Logic
**Healthcare Analytics at Stryker:**

```tableau
// Patient Risk Stratification
IF [Total Claims] > 50000 AND [Chronic Conditions] >= 3 THEN "High Risk"
ELSEIF [Total Claims] > 25000 OR [Chronic Conditions] >= 2 THEN "Medium Risk"
ELSE "Low Risk"
END

// Readmission Flag
IF DATEDIFF('day', [Previous Discharge Date], [Admission Date]) <= 30
THEN "30-Day Readmission"
ELSE "New Admission"
END

// Length of Stay Category
CASE [Length of Stay]
    WHEN 0 THEN "Same Day"
    WHEN 1 THEN "Overnight"
    WHEN 2 THEN "2 Days"
    WHEN 3 THEN "3 Days"
    ELSE "Extended Stay (4+ days)"
END

// Cost per Day
[Total Cost] / [Length of Stay]

// Case Mix Adjusted Cost
[Total Cost] / [Case Mix Index]

// Utilization Rate
[Actual Bed Days] / [Available Bed Days]
```

## Parameters and What-If Analysis

### Dynamic Parameters
**Tejuu's Parameter Strategies:**

```tableau
// Top N Parameter
Parameter: Top N (Integer, Range 5-20, Default 10)

Calculated Field: Top N Filter
RANK(SUM([Sales]), 'desc') <= [Top N Parameter]

// Date Range Parameter
Parameter: Date Range (String, List)
- Last 7 Days
- Last 30 Days
- Last 90 Days
- Last 12 Months
- Year to Date
- Custom

Calculated Field: Date Filter
CASE [Date Range Parameter]
    WHEN "Last 7 Days" THEN [Order Date] >= TODAY() - 7
    WHEN "Last 30 Days" THEN [Order Date] >= TODAY() - 30
    WHEN "Last 90 Days" THEN [Order Date] >= TODAY() - 90
    WHEN "Last 12 Months" THEN [Order Date] >= DATEADD('month', -12, TODAY())
    WHEN "Year to Date" THEN YEAR([Order Date]) = YEAR(TODAY())
END

// Metric Selector Parameter
Parameter: Select Metric (String, List)
- Sales
- Profit
- Quantity
- Avg Order Value

Calculated Field: Selected Metric
CASE [Select Metric Parameter]
    WHEN "Sales" THEN SUM([Sales])
    WHEN "Profit" THEN SUM([Profit])
    WHEN "Quantity" THEN SUM([Quantity])
    WHEN "Avg Order Value" THEN AVG([Order Value])
END

// Growth Rate Parameter for Projections
Parameter: Growth Rate (Float, Range 0-0.5, Default 0.1)

Calculated Field: Projected Sales
SUM([Sales]) * (1 + [Growth Rate Parameter])
```

### Scenario Analysis
**What-If Modeling:**

```tableau
// Price Elasticity Scenario
Parameter: Price Change % (Float, -50% to +50%)

Calculated Field: New Price
[Current Price] * (1 + [Price Change %])

Calculated Field: Projected Demand
// Assuming elasticity of -1.5
[Current Demand] * POWER(
    (1 + [Price Change %]),
    -1.5
)

Calculated Field: Projected Revenue
[New Price] * [Projected Demand]

// Staffing Scenario
Parameter: Additional Staff (Integer, 0-50)

Calculated Field: Total Staff
[Current Staff] + [Additional Staff]

Calculated Field: Projected Capacity
[Total Staff] * [Productivity per Staff]

Calculated Field: Projected Cost
([Current Staff] * [Current Wage]) + 
([Additional Staff] * [New Hire Wage])

// Budget Allocation Scenario
Parameter: Marketing % (Float, 0-1)

Calculated Field: Marketing Budget
[Total Budget] * [Marketing % Parameter]

Calculated Field: Operations Budget
[Total Budget] * (1 - [Marketing % Parameter])
```

## Data Blending and Relationships

### Cross-Database Joins
**My Approach at CVS Health:**

```
Primary Data Source: SQL Server (Sales Data)
Secondary Data Source: Excel (Target Data)

Blending Strategy:
1. Define relationships on common fields
2. Use primary data source for main viz
3. Bring in secondary data as needed
4. Aggregate appropriately to avoid duplication

Example:
- Primary: fact_sales (Order Date, Product ID, Sales)
- Secondary: targets (Month, Product ID, Target)
- Relationship: Product ID
- Calculation: Actual vs Target %
```

### Data Source Filters
**Performance Optimization:**

```tableau
// Extract Filters
1. Date Range: Last 2 years only
2. Status: Exclude "Cancelled" orders
3. Amount: > $0

// Context Filters
- Region (if analyzing specific region)
- Date Range (before other filters)

// Data Source Filters
- Exclude test data
- Filter out inactive records
- Remove PII if not needed
```

## Dashboard Performance Optimization

### Tejuu's Performance Checklist
**What I Do to Speed Up Dashboards:**

```
1. Data Source Optimization:
   - Use extracts instead of live connections
   - Filter data at source
   - Aggregate data when possible
   - Remove unused fields
   - Use appropriate data types

2. Calculation Optimization:
   - Avoid complex calculations in viz
   - Use table calcs instead of row-level calcs
   - Materialize calculations in extract
   - Use FIXED LODs sparingly
   - Avoid nested LODs

3. Visual Optimization:
   - Limit number of marks (< 10K per sheet)
   - Use aggregated data
   - Avoid high-cardinality dimensions
   - Use filters to reduce data
   - Limit dashboard complexity (< 10 sheets)

4. Dashboard Design:
   - Use containers efficiently
   - Minimize dashboard actions
   - Use sheet-specific filters
   - Hide unused sheets
   - Optimize images and logos

5. Extract Optimization:
   - Schedule refreshes during off-hours
   - Use incremental refresh
   - Partition large extracts
   - Remove historical data if not needed
```

### Extract Refresh Strategies
**My Implementation:**

```
Full Refresh:
- Weekly on Sunday night
- For dimension tables
- For small fact tables

Incremental Refresh:
- Daily for large fact tables
- Filter: [Date] > MAX([Date]) - 7
- Keeps last 7 days refreshable

Hybrid Approach:
- Incremental daily (Mon-Sat)
- Full refresh weekly (Sunday)
- Ensures data consistency
```

## Advanced Visualizations

### Custom Chart Types
**Tejuu's Favorite Advanced Viz:**

```
1. Waterfall Chart
   - Show sequential changes
   - Revenue bridge analysis
   - Budget variance analysis

2. Bullet Chart
   - KPI performance vs target
   - Show good/satisfactory/poor ranges
   - Compact executive view

3. Funnel Chart
   - Conversion analysis
   - Sales pipeline stages
   - Patient journey analysis

4. Sankey Diagram
   - Flow analysis
   - Customer journey
   - Resource allocation

5. Box and Whisker Plot
   - Distribution analysis
   - Outlier detection
   - Statistical analysis

6. Pareto Chart
   - 80/20 analysis
   - Prioritization
   - ABC analysis
```

### Custom Shapes and Icons
**Visual Enhancement:**

```
Custom Shapes for:
- Geographic maps (custom territories)
- Process flow diagrams
- Organization charts
- Network diagrams

Icon Usage:
- KPI indicators (↑ ↓ ■)
- Status indicators (✓ ✗ ⚠)
- Category icons
- Action buttons
```

## Tableau Server Administration

### Publishing and Permissions
**My Governance Model:**

```
Folder Structure:
/Executive Dashboards
  - Finance
  - Operations
  - Sales
/Departmental Reports
  - HR
  - Marketing
  - IT
/Sandbox
  - Development
  - Testing

Permission Levels:
- Viewer: Can view only
- Interactor: Can view and interact
- Editor: Can edit and publish
- Publisher: Full control

Row-Level Security:
- User filters in data source
- Dynamic user-based filtering
- Integration with AD groups
```

### Monitoring and Maintenance
**What I Track:**

```
Performance Metrics:
- Dashboard load times
- Extract refresh duration
- Failed refreshes
- User adoption rates
- Most viewed dashboards

Maintenance Tasks:
- Weekly: Review failed refreshes
- Monthly: Clean up unused content
- Quarterly: Performance audit
- Annually: User access review

Alerts:
- Extract refresh failures
- Dashboard load time > 10s
- Disk space warnings
- License usage threshold
```

## Tableau Prep for ETL

### Data Preparation Workflows
**Tejuu's Prep Flows:**

```
Common Transformations:
1. Clean Data
   - Remove nulls
   - Fix data types
   - Standardize formats
   - Remove duplicates

2. Join Data
   - Left/Right/Inner joins
   - Union multiple sources
   - Pivot/Unpivot

3. Aggregate Data
   - Group by dimensions
   - Calculate summaries
   - Create rollups

4. Calculate Fields
   - Derived columns
   - Conditional logic
   - Date calculations

5. Output
   - Tableau extract (.hyper)
   - Database table
   - CSV file
```

### Prep Best Practices
**My Workflow Design:**

```
1. Modular Design
   - Separate flows for different sources
   - Reusable cleaning steps
   - Clear naming conventions

2. Documentation
   - Add descriptions to steps
   - Document business logic
   - Note data quality issues

3. Error Handling
   - Check for nulls
   - Validate data types
   - Handle edge cases
   - Log errors

4. Performance
   - Filter early
   - Aggregate when possible
   - Limit row sampling in dev
   - Optimize joins
```

## Interview Talking Points

### Technical Achievements
- Built 30+ Tableau dashboards for healthcare and retail
- Implemented complex LOD calculations for patient analytics
- Optimized dashboard performance from 45s to 5s load time
- Created reusable templates reducing development time by 50%
- Trained 20+ users on Tableau best practices

### Problem-Solving Examples
**Performance Issue:**
"At Stryker, we had this patient dashboard that was super slow - taking 45 seconds to load. I analyzed it and found we were using live connection to a large database with no filters. I created an extract with appropriate filters, moved some calculations to the data source, and reduced the number of marks. Got it down to 5 seconds."

**Complex Calculation:**
"At CVS Health, we needed to calculate patient cohort retention over time. This required LOD expressions to identify first purchase date, then table calculations to track behavior over subsequent months. I broke it down into smaller calculated fields, tested each piece, and documented the logic for the team."

### Tools & Technologies
- **Tableau**: Desktop, Server, Prep, Online
- **Calculations**: LOD, Table Calcs, Parameters
- **Data Sources**: SQL Server, Oracle, Excel, CSV
- **Integration**: Tableau APIs, webhooks, embedded analytics
- **Administration**: User management, permissions, monitoring
