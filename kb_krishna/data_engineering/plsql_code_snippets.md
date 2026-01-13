---
tags: [krishna, oracle, plsql, code, snippets]
persona: plsql_code
---

# Oracle PL/SQL Code Snippets

Use this document ONLY when user explicitly asks for code ("write", "show", "example", "snippet", "demo").

---

## Procedure with SQL%ROWCOUNT check

```sql
CREATE OR REPLACE PROCEDURE upd_salary(p_emp_id IN NUMBER, p_salary IN NUMBER) AS
BEGIN
  UPDATE employees SET salary = p_salary WHERE employee_id = p_emp_id;

  IF SQL%ROWCOUNT = 0 THEN
    RAISE_APPLICATION_ERROR(-20001, 'Employee not found');
  END IF;

EXCEPTION
  WHEN OTHERS THEN
    log_error('upd_salary', SQLCODE, SQLERRM);
    RAISE;
END;
/
```

---

## Function (safe for SQL)

```sql
CREATE OR REPLACE FUNCTION get_dept_name(p_dept_id IN NUMBER)
RETURN VARCHAR2 AS
  v_name VARCHAR2(100);
BEGIN
  SELECT dept_name INTO v_name FROM dept WHERE dept_id = p_dept_id;
  RETURN v_name;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    RETURN NULL;
END;
/
```

---

## BULK COLLECT + FORALL with LIMIT and COMMIT per batch

```sql
DECLARE
  TYPE t_ids IS TABLE OF employees.employee_id%TYPE;
  l_ids t_ids;
  CURSOR c IS SELECT employee_id FROM employees WHERE status = 'active';
BEGIN
  OPEN c;
  LOOP
    FETCH c BULK COLLECT INTO l_ids LIMIT 1000;
    EXIT WHEN l_ids.COUNT = 0;

    FORALL i IN 1..l_ids.COUNT
      UPDATE employees SET status = 'inactive' WHERE employee_id = l_ids(i);

    COMMIT;
  END LOOP;
  CLOSE c;
END;
/
```

---

## FORALL with SAVE EXCEPTIONS

```sql
DECLARE
  TYPE t_ids IS TABLE OF emp.emp_id%TYPE;
  l_ids t_ids;
  e_bulk EXCEPTION;
  PRAGMA EXCEPTION_INIT(e_bulk, -24381);
BEGIN
  SELECT emp_id BULK COLLECT INTO l_ids FROM emp WHERE dept_id = 10;

  FORALL i IN 1..l_ids.COUNT SAVE EXCEPTIONS
    UPDATE emp SET salary = salary * 1.05 WHERE emp_id = l_ids(i);

EXCEPTION
  WHEN e_bulk THEN
    FOR j IN 1..SQL%BULK_EXCEPTIONS.COUNT LOOP
      DBMS_OUTPUT.PUT_LINE(
        'Idx=' || SQL%BULK_EXCEPTIONS(j).ERROR_INDEX ||
        ' Code=' || SQL%BULK_EXCEPTIONS(j).ERROR_CODE
      );
    END LOOP;
END;
/
```

---

## FORALL with INDICES OF (sparse collection)

```sql
FORALL i IN INDICES OF l_ids
  UPDATE emp SET processed = 'Y' WHERE emp_id = l_ids(i);
```

---

## Package (Spec + Body)

```sql
-- Spec
CREATE OR REPLACE PACKAGE emp_pkg AS
  PROCEDURE give_raise(p_dept_id IN NUMBER, p_pct IN NUMBER);
  FUNCTION get_emp_count(p_dept_id IN NUMBER) RETURN NUMBER;
END emp_pkg;
/

-- Body
CREATE OR REPLACE PACKAGE BODY emp_pkg AS
  FUNCTION validate_dept(p_dept_id IN NUMBER) RETURN BOOLEAN IS
    v_cnt NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_cnt FROM dept WHERE dept_id = p_dept_id;
    RETURN v_cnt > 0;
  END;

  FUNCTION get_emp_count(p_dept_id IN NUMBER) RETURN NUMBER IS
    v_cnt NUMBER;
  BEGIN
    SELECT COUNT(*) INTO v_cnt FROM emp WHERE dept_id = p_dept_id;
    RETURN v_cnt;
  END;

  PROCEDURE give_raise(p_dept_id IN NUMBER, p_pct IN NUMBER) IS
  BEGIN
    IF NOT validate_dept(p_dept_id) THEN
      RAISE_APPLICATION_ERROR(-20001, 'Invalid department');
    END IF;
    UPDATE emp SET salary = salary * (1 + p_pct/100) WHERE dept_id = p_dept_id;
  END;
END emp_pkg;
/
```

---

## Autonomous Logging Procedure

```sql
CREATE OR REPLACE PROCEDURE log_error(
  p_proc   IN VARCHAR2,
  p_code   IN NUMBER,
  p_msg    IN VARCHAR2
) AS
  PRAGMA AUTONOMOUS_TRANSACTION;
BEGIN
  INSERT INTO error_log(proc_name, error_code, error_msg, log_time)
  VALUES (p_proc, p_code, p_msg, SYSDATE);
  COMMIT;
END;
/
```

---

## REF CURSOR

```sql
CREATE OR REPLACE PROCEDURE get_emp_by_dept(
  p_dept_id IN NUMBER,
  p_rc OUT SYS_REFCURSOR
) AS
BEGIN
  OPEN p_rc FOR
    SELECT emp_id, emp_name, salary
    FROM emp
    WHERE dept_id = p_dept_id;
END;
/
```

---

## Compound Trigger (12c+)

```sql
CREATE OR REPLACE TRIGGER trg_emp_compound
FOR UPDATE ON emp
COMPOUND TRIGGER
  TYPE t_audit_rec IS RECORD (
    emp_id     emp.emp_id%TYPE,
    old_salary emp.salary%TYPE,
    new_salary emp.salary%TYPE,
    change_dt  DATE
  );
  TYPE t_audit_tab IS TABLE OF t_audit_rec INDEX BY PLS_INTEGER;
  g_audits t_audit_tab;
  g_idx PLS_INTEGER := 0;

  AFTER EACH ROW IS
  BEGIN
    g_idx := g_idx + 1;
    g_audits(g_idx).emp_id     := :OLD.emp_id;
    g_audits(g_idx).old_salary := :OLD.salary;
    g_audits(g_idx).new_salary := :NEW.salary;
    g_audits(g_idx).change_dt  := SYSDATE;
  END AFTER EACH ROW;

  AFTER STATEMENT IS
  BEGIN
    FORALL i IN 1..g_idx
      INSERT INTO emp_audit(emp_id, old_salary, new_salary, change_date)
      VALUES (g_audits(i).emp_id, g_audits(i).old_salary, 
              g_audits(i).new_salary, g_audits(i).change_dt);
  END AFTER STATEMENT;
END;
/
```

---

## DBMS_XPLAN.DISPLAY_CURSOR

```sql
-- Last statement in same session:
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST'));

-- Specific SQL_ID:
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR('abc123xyz', NULL, 'ALLSTATS LAST'));
```

---

## Dynamic SQL with bind variables

```sql
DECLARE
  v_sql  VARCHAR2(4000);
  v_cnt  NUMBER;
BEGIN
  v_sql := 'SELECT COUNT(*) FROM emp WHERE dept_id = :1';
  EXECUTE IMMEDIATE v_sql INTO v_cnt USING 10;
  DBMS_OUTPUT.PUT_LINE('Count=' || v_cnt);
END;
/
```

---

## Delete duplicates (ROW_NUMBER method)

```sql
DELETE FROM emp
WHERE ROWID IN (
  SELECT rid FROM (
    SELECT ROWID rid,
           ROW_NUMBER() OVER (PARTITION BY emp_name, dept_id ORDER BY ROWID) rn
    FROM emp
  )
  WHERE rn > 1
);
```

---

## MERGE (upsert)

```sql
MERGE INTO emp_target t
USING emp_source s ON (t.emp_id = s.emp_id)
WHEN MATCHED THEN
  UPDATE SET t.salary = s.salary, t.dept_id = s.dept_id
WHEN NOT MATCHED THEN
  INSERT (emp_id, emp_name, salary, dept_id)
  VALUES (s.emp_id, s.emp_name, s.salary, s.dept_id);
```

---

## Compound Trigger to Avoid Mutating Table Error

```sql
CREATE OR REPLACE TRIGGER trg_validate_salary
FOR UPDATE OF salary ON employees
COMPOUND TRIGGER

  TYPE t_emp_ids IS TABLE OF employees.employee_id%TYPE INDEX BY PLS_INTEGER;
  g_emp_ids t_emp_ids;
  g_idx PLS_INTEGER := 0;

  -- Collect affected rows
  AFTER EACH ROW IS
  BEGIN
    g_idx := g_idx + 1;
    g_emp_ids(g_idx) := :NEW.employee_id;
  END AFTER EACH ROW;

  -- Validate after all rows processed (table is stable)
  AFTER STATEMENT IS
    v_avg_salary NUMBER;
  BEGIN
    SELECT AVG(salary) INTO v_avg_salary FROM employees;
    
    FOR i IN 1..g_idx LOOP
      -- Business validation using table data (no mutating error)
      NULL; -- Add validation logic here
    END LOOP;
  END AFTER STATEMENT;

END trg_validate_salary;
/
```

---

## Pipelined Table Function

```sql
-- Define the return type
CREATE OR REPLACE TYPE t_emp_row AS OBJECT (
  emp_id   NUMBER,
  emp_name VARCHAR2(100),
  dept_id  NUMBER
);
/

CREATE OR REPLACE TYPE t_emp_tab AS TABLE OF t_emp_row;
/

-- Pipelined function
CREATE OR REPLACE FUNCTION get_employees_pipelined(p_dept_id IN NUMBER)
RETURN t_emp_tab PIPELINED AS
  CURSOR c IS 
    SELECT employee_id, first_name || ' ' || last_name, department_id
    FROM employees WHERE department_id = p_dept_id;
BEGIN
  FOR r IN c LOOP
    PIPE ROW(t_emp_row(r.employee_id, r.first_name, r.department_id));
  END LOOP;
  RETURN;
END;
/

-- Usage: SELECT * FROM TABLE(get_employees_pipelined(10));
```

---

## Collections Comparison

```sql
DECLARE
  -- Associative Array (index-by table) - in-memory only, sparse
  TYPE t_assoc IS TABLE OF VARCHAR2(100) INDEX BY PLS_INTEGER;
  l_assoc t_assoc;
  
  -- Nested Table - can store in DB, can become sparse
  TYPE t_nested IS TABLE OF VARCHAR2(100);
  l_nested t_nested := t_nested();
  
  -- VARRAY - fixed max size, always dense
  TYPE t_varray IS VARRAY(10) OF VARCHAR2(100);
  l_varray t_varray := t_varray();
BEGIN
  -- Associative array - direct assignment
  l_assoc(1) := 'First';
  l_assoc(100) := 'Sparse - gap allowed';
  
  -- Nested table - must extend first
  l_nested.EXTEND(2);
  l_nested(1) := 'First';
  l_nested(2) := 'Second';
  
  -- VARRAY - must extend, respects max size
  l_varray.EXTEND(2);
  l_varray(1) := 'First';
  l_varray(2) := 'Second';
END;
/
```

---

## Strong vs Weak REF CURSOR

```sql
DECLARE
  -- Strong REF CURSOR - compile-time type checking
  TYPE t_strong_cursor IS REF CURSOR RETURN employees%ROWTYPE;
  l_strong t_strong_cursor;
  l_emp employees%ROWTYPE;
  
  -- Weak REF CURSOR - runtime flexibility
  TYPE t_weak_cursor IS REF CURSOR;
  l_weak t_weak_cursor;
  
  -- SYS_REFCURSOR - predefined weak type
  l_sys SYS_REFCURSOR;
BEGIN
  -- Strong cursor must match return type
  OPEN l_strong FOR SELECT * FROM employees WHERE department_id = 10;
  FETCH l_strong INTO l_emp;
  CLOSE l_strong;
  
  -- Weak/SYS_REFCURSOR can open for any query
  OPEN l_sys FOR SELECT department_name FROM departments;
  CLOSE l_sys;
END;
/
```

---

## Window Functions (Analytic)

```sql
-- ROW_NUMBER, RANK, DENSE_RANK comparison
SELECT 
  employee_id,
  department_id,
  salary,
  ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) as row_num,
  RANK()       OVER (PARTITION BY department_id ORDER BY salary DESC) as rnk,
  DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) as dense_rnk
FROM employees;

-- Running total with SUM OVER
SELECT 
  order_date,
  amount,
  SUM(amount) OVER (ORDER BY order_date) as running_total
FROM orders;

-- LAG/LEAD - access previous/next row
SELECT 
  employee_id,
  salary,
  LAG(salary, 1, 0) OVER (ORDER BY employee_id)  as prev_salary,
  LEAD(salary, 1, 0) OVER (ORDER BY employee_id) as next_salary
FROM employees;

-- De-duplicate: keep latest record per employee
DELETE FROM emp_staging
WHERE ROWID IN (
  SELECT rid FROM (
    SELECT ROWID rid,
           ROW_NUMBER() OVER (PARTITION BY emp_id ORDER BY updated_date DESC) rn
    FROM emp_staging
  )
  WHERE rn > 1
);
```

---

## DBMS_PROFILER Usage

```sql
-- Setup: Run as SYS or with profiler privileges
-- @?/rdbms/admin/proftab.sql (creates profiler tables)

DECLARE
  v_run_number NUMBER;
BEGIN
  -- Start profiling
  DBMS_PROFILER.START_PROFILER(
    run_comment => 'Testing my_procedure',
    run_number  => v_run_number
  );
  
  -- Execute the code to profile
  my_package.my_procedure(100);
  
  -- Stop profiling
  DBMS_PROFILER.STOP_PROFILER;
  
  DBMS_OUTPUT.PUT_LINE('Run number: ' || v_run_number);
END;
/

-- Query results: find slowest lines
SELECT 
  u.unit_name,
  d.line#,
  d.total_time / 1000000000 as seconds,
  d.total_occur as executions
FROM plsql_profiler_data d
JOIN plsql_profiler_units u ON d.runid = u.runid AND d.unit_number = u.unit_number
WHERE d.runid = (SELECT MAX(runid) FROM plsql_profiler_runs)
ORDER BY d.total_time DESC
FETCH FIRST 20 ROWS ONLY;
```

---

## INSTEAD OF Trigger on View

```sql
-- Complex view joining two tables
CREATE OR REPLACE VIEW emp_dept_view AS
SELECT e.employee_id, e.first_name, e.last_name, e.salary,
       d.department_id, d.department_name
FROM employees e
JOIN departments d ON e.department_id = d.department_id;

-- Can't INSERT directly into this view, so use INSTEAD OF
CREATE OR REPLACE TRIGGER trg_emp_dept_insert
INSTEAD OF INSERT ON emp_dept_view
FOR EACH ROW
BEGIN
  -- Insert into base table
  INSERT INTO employees (employee_id, first_name, last_name, salary, department_id)
  VALUES (:NEW.employee_id, :NEW.first_name, :NEW.last_name, 
          :NEW.salary, :NEW.department_id);
END;
/
```

---

## PLS_INTEGER for Performance

```sql
DECLARE
  -- PLS_INTEGER - machine arithmetic, faster for loops
  l_counter PLS_INTEGER := 0;
  
  -- SIMPLE_INTEGER (11g+) - even faster, no null/overflow check
  l_fast SIMPLE_INTEGER := 0;
  
  -- NUMBER - slower, use for precision/large values
  l_amount NUMBER := 0;
BEGIN
  -- Fast loop with PLS_INTEGER
  FOR i IN 1..1000000 LOOP
    l_counter := l_counter + 1;
  END LOOP;
END;
/
```

---

## Check Object Dependencies

```sql
-- Find all objects that depend on a table
SELECT 
  owner,
  name,
  type,
  referenced_owner,
  referenced_name,
  referenced_type
FROM all_dependencies
WHERE referenced_name = 'EMPLOYEES'
  AND referenced_owner = 'HR'
ORDER BY type, name;

-- Find invalid objects after DDL change
SELECT owner, object_name, object_type, status
FROM all_objects
WHERE status = 'INVALID'
  AND owner = 'HR';

-- Recompile invalid objects
ALTER PROCEDURE hr.my_proc COMPILE;
ALTER PACKAGE hr.my_pkg COMPILE BODY;
```
