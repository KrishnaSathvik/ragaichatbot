---
tags: [business-intelligence, power-bi, tableau, data-visualization, dashboards, analytics]
persona: business
---

# Business Intelligence Development & Tejuu's Experience

## Power BI Development

### Dashboard Design and Development
**Tejuu's Power BI Expertise:**
I've built over 50 Power BI dashboards across different business functions - sales, finance, operations, and HR. What I've learned is that a good dashboard tells a story and helps users make decisions quickly.

**My Dashboard Design Principles:**
```
1. Know Your Audience
   - Executives need high-level KPIs
   - Managers need drill-down capabilities
   - Analysts need detailed data access

2. Follow the 5-Second Rule
   - Key insights should be visible in 5 seconds
   - Use clear titles and labels
   - Highlight important metrics

3. Use Visual Hierarchy
   - Most important metrics at the top
   - Use size and color to guide attention
   - Group related metrics together

4. Keep It Simple
   - Maximum 5-7 visuals per page
   - Avoid chart junk and unnecessary decorations
   - Use consistent colors and formatting

5. Enable Interactivity
   - Add filters and slicers
   - Enable drill-through pages
   - Use bookmarks for different views
```

**Sales Dashboard Example:**
```
Page 1: Executive Overview
- Total Revenue (Card visual with YoY comparison)
- Revenue Trend (Line chart with forecast)
- Revenue by Region (Map visual)
- Top 10 Products (Bar chart)
- Key Metrics Table (Revenue, Orders, Avg Order Value)

Page 2: Sales Performance
- Sales by Sales Rep (Matrix with conditional formatting)
- Sales vs Target (Gauge charts)
- Win Rate by Product Category (Funnel chart)
- Pipeline Analysis (Waterfall chart)

Page 3: Customer Analysis
- Customer Segmentation (Scatter plot)
- Customer Lifetime Value (Tree map)
- Churn Analysis (Line and column chart)
- Customer Acquisition Cost (KPI visual)
```

### DAX Formulas and Calculations
**Tejuu's DAX Knowledge:**
DAX is essential for creating powerful calculations in Power BI. Here are some of my most-used formulas:

**Time Intelligence:**
```dax
-- Year-to-Date Sales
YTD Sales = 
TOTALYTD(
    SUM(Sales[Amount]),
    'Date'[Date]
)

-- Previous Year Sales
PY Sales = 
CALCULATE(
    SUM(Sales[Amount]),
    SAMEPERIODLASTYEAR('Date'[Date])
)

-- Year-over-Year Growth
YoY Growth % = 
DIVIDE(
    [YTD Sales] - [PY Sales],
    [PY Sales],
    0
)

-- Moving Average (3 months)
3M Moving Avg = 
AVERAGEX(
    DATESINPERIOD(
        'Date'[Date],
        LASTDATE('Date'[Date]),
        -3,
        MONTH
    ),
    [Total Sales]
)
```

**Customer Metrics:**
```dax
-- Customer Count
Total Customers = 
DISTINCTCOUNT(Sales[CustomerID])

-- New Customers
New Customers = 
CALCULATE(
    DISTINCTCOUNT(Sales[CustomerID]),
    FILTER(
        ALL(Sales),
        Sales[OrderDate] = 
        CALCULATE(
            MIN(Sales[OrderDate]),
            ALLEXCEPT(Sales, Sales[CustomerID])
        )
    )
)

-- Customer Retention Rate
Retention Rate = 
VAR CurrentCustomers = [Total Customers]
VAR PreviousCustomers = 
    CALCULATE(
        [Total Customers],
        DATEADD('Date'[Date], -1, MONTH)
    )
VAR RetainedCustomers = 
    CALCULATE(
        DISTINCTCOUNT(Sales[CustomerID]),
        FILTER(
            ALL(Sales),
            [CustomerID] IN VALUES(Sales[CustomerID]) &&
            [OrderDate] >= EOMONTH(TODAY(), -2) &&
            [OrderDate] < EOMONTH(TODAY(), -1)
        )
    )
RETURN
DIVIDE(RetainedCustomers, PreviousCustomers, 0)
```

**Advanced Calculations:**
```dax
-- Running Total
Running Total = 
CALCULATE(
    SUM(Sales[Amount]),
    FILTER(
        ALL('Date'[Date]),
        'Date'[Date] <= MAX('Date'[Date])
    )
)

-- Pareto Analysis (80/20 Rule)
Cumulative % = 
VAR CurrentRevenue = SUM(Sales[Amount])
VAR TotalRevenue = 
    CALCULATE(
        SUM(Sales[Amount]),
        ALL(Products)
    )
VAR RunningTotal = 
    CALCULATE(
        SUM(Sales[Amount]),
        FILTER(
            ALL(Products),
            RANKX(
                ALL(Products),
                SUM(Sales[Amount]),
                ,
                DESC
            ) <= RANKX(
                ALL(Products),
                SUM(Sales[Amount]),
                ,
                DESC
            )
        )
    )
RETURN
DIVIDE(RunningTotal, TotalRevenue, 0)

-- Dynamic Ranking
Product Rank = 
RANKX(
    ALL(Products[ProductName]),
    [Total Sales],
    ,
    DESC,
    DENSE
)
```

### Data Modeling in Power BI
**Tejuu's Data Modeling Approach:**
Good data modeling is the foundation of a fast and reliable Power BI report. Here's my approach:

**Star Schema Design:**
```
Fact Tables:
- Sales (OrderID, CustomerID, ProductID, DateKey, Amount, Quantity)
- Inventory (ProductID, DateKey, StockLevel, WarehouseID)
- Budget (DateKey, DepartmentID, BudgetAmount)

Dimension Tables:
- Customers (CustomerID, Name, Segment, Region, City)
- Products (ProductID, Name, Category, SubCategory, Price)
- Date (DateKey, Date, Year, Quarter, Month, Week, Day)
- Employees (EmployeeID, Name, Department, Manager, HireDate)
```

**Relationship Best Practices:**
```
1. Use Star Schema
   - Fact tables in the center
   - Dimension tables around it
   - One-to-many relationships

2. Create a Date Table
   - Use CALENDAR or CALENDARAUTO
   - Mark as date table
   - Include all needed date attributes

3. Avoid Bi-Directional Relationships
   - Can cause ambiguity
   - Impacts performance
   - Use DAX instead when possible

4. Hide Unnecessary Columns
   - Foreign keys
   - Technical columns
   - Improves user experience

5. Use Calculated Columns vs Measures Appropriately
   - Calculated columns: Static, stored in model
   - Measures: Dynamic, calculated at query time
   - Prefer measures for aggregations
```

## Tableau Development

### Building Interactive Dashboards
**Tejuu's Tableau Experience:**
I've worked with Tableau for 3+ years, building executive dashboards and self-service analytics solutions. Tableau's strength is its intuitive drag-and-drop interface and powerful visualization capabilities.

**My Tableau Dashboard Structure:**
```
1. Overview Dashboard
   - KPI Summary
   - Trend Analysis
   - Geographic Distribution
   - Quick Filters

2. Detailed Analysis
   - Drill-down capabilities
   - Parameter controls
   - Calculated fields
   - Reference lines and bands

3. What-If Analysis
   - Parameters for scenarios
   - Calculated fields for projections
   - Dynamic titles and labels
```

**Calculated Fields in Tableau:**
```
// Year-over-Year Growth
(SUM([Sales]) - LOOKUP(SUM([Sales]), -12)) / LOOKUP(SUM([Sales]), -12)

// Customer Lifetime Value
{FIXED [Customer ID]: SUM([Sales])}

// Cohort Analysis
IF DATEDIFF('month', {FIXED [Customer ID]: MIN([Order Date])}, [Order Date]) = 0
THEN "Month 0"
ELSEIF DATEDIFF('month', {FIXED [Customer ID]: MIN([Order Date])}, [Order Date]) = 1
THEN "Month 1"
ELSE "Month 2+"
END

// Dynamic Ranking
RANK(SUM([Sales]), 'desc')

// Moving Average
WINDOW_AVG(SUM([Sales]), -2, 0)
```

## Excel for Business Intelligence

### Advanced Excel Techniques
**Tejuu's Excel Expertise:**
Even with Power BI and Tableau, Excel remains a critical tool. I use it for ad-hoc analysis, data preparation, and quick reports.

**Power Query (ETL in Excel):**
```
Common Transformations:
1. Remove Duplicates
2. Fill Down/Up
3. Pivot/Unpivot Columns
4. Merge Queries (Joins)
5. Append Queries (Union)
6. Split Columns
7. Change Data Types
8. Add Custom Columns

M Language Examples:
// Add custom column
= Table.AddColumn(#"Previous Step", "Full Name", 
    each [First Name] & " " & [Last Name])

// Filter rows
= Table.SelectRows(#"Previous Step", 
    each [Sales] > 1000)

// Group by
= Table.Group(#"Previous Step", {"Region"}, 
    {{"Total Sales", each List.Sum([Sales]), type number}})
```

**Power Pivot and Data Modeling:**
```
DAX in Excel:
// Total Sales
Total Sales:=SUM(Sales[Amount])

// Sales vs Budget Variance
Variance:=[Total Sales]-[Total Budget]

// Variance %
Variance %:=DIVIDE([Variance],[Total Budget],0)

// Top N Products
Top 10 Products:=
CALCULATE(
    [Total Sales],
    TOPN(10, ALL(Products[Product Name]), [Total Sales], DESC)
)
```

**Advanced Formulas:**
```excel
// Dynamic Named Ranges
=OFFSET(Sheet1!$A$1,0,0,COUNTA(Sheet1!$A:$A),1)

// Array Formulas (Ctrl+Shift+Enter)
=SUM(IF(A2:A100="Yes",B2:B100,0))

// XLOOKUP (Modern Excel)
=XLOOKUP(A2,Table1[ID],Table1[Name],"Not Found",0,1)

// SUMIFS with Multiple Criteria
=SUMIFS(Sales[Amount],Sales[Region],"West",Sales[Date],">="&DATE(2023,1,1))

// Dynamic Dashboard with CHOOSE and MATCH
=CHOOSE(MATCH(B1,{"Sales","Profit","Quantity"},0),
    SUM(Sales[Amount]),
    SUM(Sales[Profit]),
    SUM(Sales[Quantity]))
```

## Data Visualization Best Practices

### Choosing the Right Chart
**Tejuu's Chart Selection Guide:**
```
Comparison:
- Bar Chart: Compare values across categories
- Column Chart: Show changes over time
- Bullet Chart: Compare actual vs target

Composition:
- Pie Chart: Show parts of a whole (max 5 slices)
- Stacked Bar: Show composition across categories
- Treemap: Show hierarchical composition

Distribution:
- Histogram: Show frequency distribution
- Box Plot: Show statistical distribution
- Scatter Plot: Show correlation between variables

Trend:
- Line Chart: Show trends over time
- Area Chart: Show cumulative trends
- Waterfall: Show sequential changes

Relationship:
- Scatter Plot: Show correlation
- Bubble Chart: Show 3 dimensions
- Heat Map: Show patterns in matrix data
```

### Color Theory and Accessibility
**My Color Guidelines:**
```
1. Use Color Purposefully
   - Red: Negative, danger, stop
   - Green: Positive, success, go
   - Blue: Neutral, information
   - Orange/Yellow: Warning, attention

2. Ensure Accessibility
   - Check color blindness compatibility
   - Use patterns in addition to colors
   - Maintain sufficient contrast
   - Test with grayscale

3. Limit Color Palette
   - Maximum 5-6 colors per dashboard
   - Use shades for variations
   - Keep brand colors consistent

4. Highlight What Matters
   - Use bright colors for important data
   - Gray out less important information
   - Use white space effectively
```

## ETL and Data Preparation

### Data Quality Checks
**Tejuu's Data Validation Process:**
```
1. Completeness Checks
   - Missing values
   - Null percentages
   - Required fields populated

2. Accuracy Checks
   - Data type validation
   - Range checks (min/max)
   - Format validation (email, phone)

3. Consistency Checks
   - Cross-field validation
   - Referential integrity
   - Duplicate detection

4. Timeliness Checks
   - Data freshness
   - Update frequency
   - Historical completeness

SQL for Data Quality:
-- Check for nulls
SELECT 
    COUNT(*) as total_records,
    COUNT(customer_id) as non_null_customers,
    COUNT(*) - COUNT(customer_id) as null_count,
    ROUND((COUNT(*) - COUNT(customer_id)) * 100.0 / COUNT(*), 2) as null_percentage
FROM sales;

-- Check for duplicates
SELECT 
    order_id,
    COUNT(*) as duplicate_count
FROM orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- Check data ranges
SELECT 
    MIN(order_date) as earliest_date,
    MAX(order_date) as latest_date,
    MIN(amount) as min_amount,
    MAX(amount) as max_amount,
    AVG(amount) as avg_amount
FROM orders;
```

## Interview Talking Points

### Technical Skills:
- Power BI dashboard development and DAX
- Tableau visualization and calculated fields
- Advanced Excel (Power Query, Power Pivot)
- SQL for data analysis
- Data modeling and ETL
- Data visualization best practices

### Tools & Technologies:
- **BI Tools**: Power BI, Tableau, Qlik Sense
- **Databases**: SQL Server, Oracle, MySQL, PostgreSQL
- **Excel**: Power Query, Power Pivot, VBA
- **ETL**: SSIS, Alteryx, Informatica
- **Cloud**: Azure, AWS, Google Cloud

### Achievements:
- Built 50+ Power BI dashboards used by 200+ users
- Reduced report generation time from 2 days to 2 hours
- Improved data accuracy by 95% through automated quality checks
- Saved $100K annually by identifying cost optimization opportunities
- Trained 30+ business users on self-service BI tools

### Project Examples:
- Sales Performance Dashboard (real-time tracking, 15+ KPIs)
- Customer Analytics Platform (segmentation, churn prediction)
- Financial Reporting Suite (P&L, balance sheet, cash flow)
- Operational Metrics Dashboard (efficiency, productivity, quality)
- Executive KPI Dashboard (company-wide metrics, drill-down)
