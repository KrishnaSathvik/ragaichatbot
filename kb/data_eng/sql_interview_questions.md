---
tags: [sql, interview, queries, window-functions, subqueries]
persona: de
---

# SQL Interview Questions & Solutions

## Finding Second Highest Salary Without TOP/LIMIT

### Method 1: Using Subquery
```sql
SELECT MAX(salary) 
FROM employees 
WHERE salary < (SELECT MAX(salary) FROM employees);
```

### Method 2: Using Window Functions (RANK)
```sql
SELECT salary 
FROM (
    SELECT salary, RANK() OVER (ORDER BY salary DESC) as salary_rank
    FROM employees
) ranked_salaries 
WHERE salary_rank = 2;
```

### Method 3: Using Window Functions (ROW_NUMBER)
```sql
SELECT salary 
FROM (
    SELECT salary, ROW_NUMBER() OVER (ORDER BY salary DESC) as salary_rank
    FROM employees
) ranked_salaries 
WHERE salary_rank = 2;
```

### Method 4: Using Self Join
```sql
SELECT DISTINCT e1.salary
FROM employees e1
WHERE 1 = (SELECT COUNT(DISTINCT e2.salary) 
           FROM employees e2 
           WHERE e2.salary > e1.salary);
```

## Common SQL Interview Patterns

### Nth Highest Salary (Generic)
```sql
SELECT salary 
FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) as salary_rank
    FROM employees
) ranked_salaries 
WHERE salary_rank = N;
```

### Find Duplicates
```sql
SELECT column_name, COUNT(*)
FROM table_name
GROUP BY column_name
HAVING COUNT(*) > 1;
```

### Delete Duplicates (Keep One)
```sql
DELETE e1 FROM employees e1
INNER JOIN employees e2 
WHERE e1.id > e2.id AND e1.email = e2.email;
```

### Find Employees with Same Salary
```sql
SELECT e1.name, e1.salary
FROM employees e1
INNER JOIN employees e2 ON e1.salary = e2.salary AND e1.id != e2.id;
```
