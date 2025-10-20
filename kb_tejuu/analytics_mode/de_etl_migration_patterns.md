---
tags: [data-engineer, etl, migration, patterns, legacy, modernization, tejuu]
persona: analytics
---

# ETL Migration Patterns - Tejuu's Experience

## Introduction
**Tejuu's Migration Philosophy:**
At Central Bank of Missouri, I led the migration of 12M+ legacy records from Excel/Access to Azure SQL/Power BI. I've also worked on data migrations at Stryker and CVS Health. My approach focuses on minimizing business disruption, ensuring data quality, and building scalable modern data platforms. Let me share the patterns and strategies I've learned migrating legacy data systems.

## Migration Strategy Framework

### 1. Assessment Phase
**Tejuu's Assessment Approach:**

```python
# Legacy system assessment tool
class LegacySystemAssessor:
    def __init__(self):
        self.assessment_results = {}
    
    def assess_data_volume(self, source_systems):
        volume_analysis = {}
        
        for system in source_systems:
            if system['type'] == 'excel':
                volume = self.assess_excel_files(system['path'])
            elif system['type'] == 'access':
                volume = self.assess_access_database(system['connection'])
            elif system['type'] == 'sql_server':
                volume = self.assess_sql_server(system['connection'])
            
            volume_analysis[system['name']] = {
                'record_count': volume['records'],
                'data_size_gb': volume['size_gb'],
                'complexity_score': volume['complexity']
            }
        
        return volume_analysis
    
    def assess_data_quality(self, sample_data):
        quality_metrics = {
            'completeness': self.check_completeness(sample_data),
            'consistency': self.check_consistency(sample_data),
            'accuracy': self.check_accuracy(sample_data),
            'duplicates': self.check_duplicates(sample_data)
        }
        
        return quality_metrics
    
    def assess_business_impact(self, data_usage):
        impact_analysis = {
            'critical_systems': self.identify_critical_systems(data_usage),
            'user_dependencies': self.map_user_dependencies(data_usage),
            'reporting_impact': self.assess_reporting_impact(data_usage),
            'compliance_requirements': self.identify_compliance_requirements(data_usage)
        }
        
        return impact_analysis
```

### 2. Migration Planning
**Tejuu's Planning Framework:**

```python
# Migration project planner
class MigrationPlanner:
    def __init__(self):
        self.migration_phases = []
    
    def create_migration_plan(self, assessment_results):
        plan = {
            'phase_1': self.plan_phase_1_preparation(assessment_results),
            'phase_2': self.plan_phase_2_pilot(assessment_results),
            'phase_3': self.plan_phase_3_full_migration(assessment_results),
            'phase_4': self.plan_phase_4_validation(assessment_results),
            'phase_5': self.plan_phase_5_cutover(assessment_results)
        }
        
        return plan
    
    def plan_phase_1_preparation(self, assessment):
        return {
            'duration_weeks': 4,
            'activities': [
                'Set up target Azure environment',
                'Create data mapping documentation',
                'Build data quality validation framework',
                'Develop migration scripts',
                'Train business users on new system'
            ],
            'deliverables': [
                'Target environment ready',
                'Data mapping completed',
                'Validation framework deployed',
                'Migration scripts tested'
            ]
        }
```

## Legacy System Migration Patterns

### 1. Excel to Database Migration
**Tejuu's Excel Migration Pattern:**

```python
# Excel file migration processor
class ExcelMigrationProcessor:
    def __init__(self):
        self.data_quality_rules = DataQualityRules()
        self.mapping_rules = DataMappingRules()
    
    def migrate_excel_files(self, excel_files, target_table):
        migration_results = {
            'total_files': len(excel_files),
            'successful_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'errors': []
        }
        
        for file_path in excel_files:
            try:
                # Read Excel file
                df = self.read_excel_file(file_path)
                
                # Validate data quality
                quality_issues = self.data_quality_rules.validate(df)
                if quality_issues:
                    self.log_quality_issues(file_path, quality_issues)
                
                # Apply data mapping
                df_mapped = self.mapping_rules.apply_mapping(df, target_table)
                
                # Transform data
                df_transformed = self.transform_excel_data(df_mapped)
                
                # Load to target
                self.load_to_target(df_transformed, target_table)
                
                migration_results['successful_files'] += 1
                migration_results['total_records'] += df_transformed.count()
                
            except Exception as e:
                migration_results['failed_files'] += 1
                migration_results['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })
        
        return migration_results
    
    def read_excel_file(self, file_path):
        # Handle different Excel formats
        try:
            df = pd.read_excel(file_path, sheet_name=0)
        except:
            # Try with different engine
            df = pd.read_excel(file_path, engine='openpyxl')
        
        return df
    
    def transform_excel_data(self, df):
        # Standardize data types
        df_clean = (
            df
            .withColumn("customer_id", col("customer_id").cast("string"))
            .withColumn("amount", col("amount").cast("decimal(18,2)"))
            .withColumn("transaction_date", to_date(col("transaction_date"), "MM/dd/yyyy"))
            .withColumn("source_file", lit(self.current_file))
            .withColumn("migrated_at", current_timestamp())
        )
        
        return df_clean
```

### 2. Access Database Migration
**Tejuu's Access Migration Pattern:**

```python
# Access database migration processor
class AccessMigrationProcessor:
    def __init__(self):
        self.connection_string = self.get_access_connection()
    
    def migrate_access_database(self, access_file, target_schema):
        migration_results = {
            'tables_migrated': 0,
            'total_records': 0,
            'errors': []
        }
        
        # Get list of tables
        tables = self.get_access_tables(access_file)
        
        for table_name in tables:
            try:
                # Extract data from Access
                df = self.extract_access_table(table_name)
                
                # Transform data
                df_transformed = self.transform_access_data(df, table_name)
                
                # Load to target
                target_table = f"{target_schema}.{table_name}"
                self.load_to_target(df_transformed, target_table)
                
                migration_results['tables_migrated'] += 1
                migration_results['total_records'] += df_transformed.count()
                
            except Exception as e:
                migration_results['errors'].append({
                    'table': table_name,
                    'error': str(e)
                })
        
        return migration_results
    
    def extract_access_table(self, table_name):
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, self.connection_string)
        return df
    
    def transform_access_data(self, df, table_name):
        # Apply table-specific transformations
        if table_name == 'customers':
            df = self.transform_customer_data(df)
        elif table_name == 'transactions':
            df = self.transform_transaction_data(df)
        elif table_name == 'products':
            df = self.transform_product_data(df)
        
        return df
```

### 3. SQL Server to Azure Migration
**Tejuu's SQL Server Migration Pattern:**

```python
# SQL Server to Azure migration processor
class SQLServerMigrationProcessor:
    def __init__(self):
        self.source_connection = self.get_sql_server_connection()
        self.target_connection = self.get_azure_connection()
    
    def migrate_sql_server_database(self, database_name, target_schema):
        migration_results = {
            'tables_migrated': 0,
            'total_records': 0,
            'migration_time_minutes': 0
        }
        
        start_time = datetime.now()
        
        # Get list of tables
        tables = self.get_sql_server_tables(database_name)
        
        for table_name in tables:
            try:
                # Extract data in batches
                self.migrate_table_in_batches(table_name, target_schema)
                migration_results['tables_migrated'] += 1
                
            except Exception as e:
                self.log_migration_error(table_name, str(e))
        
        end_time = datetime.now()
        migration_results['migration_time_minutes'] = (end_time - start_time).total_seconds() / 60
        
        return migration_results
    
    def migrate_table_in_batches(self, table_name, target_schema, batch_size=10000):
        # Get total record count
        total_records = self.get_table_record_count(table_name)
        
        # Migrate in batches
        for offset in range(0, total_records, batch_size):
            # Extract batch
            df_batch = self.extract_table_batch(table_name, offset, batch_size)
            
            # Transform batch
            df_transformed = self.transform_sql_server_data(df_batch, table_name)
            
            # Load batch
            target_table = f"{target_schema}.{table_name}"
            self.load_batch_to_target(df_transformed, target_table)
    
    def extract_table_batch(self, table_name, offset, batch_size):
        query = f"""
        SELECT * FROM {table_name}
        ORDER BY (SELECT NULL)
        OFFSET {offset} ROWS
        FETCH NEXT {batch_size} ROWS ONLY
        """
        df = pd.read_sql(query, self.source_connection)
        return df
```

## Data Quality During Migration

### 1. Pre-Migration Validation
**Tejuu's Pre-Migration Patterns:**

```python
# Pre-migration data validation
class PreMigrationValidator:
    def __init__(self):
        self.validation_rules = self.load_validation_rules()
    
    def validate_source_data(self, source_data, validation_rules):
        validation_results = {
            'total_records': len(source_data),
            'valid_records': 0,
            'invalid_records': 0,
            'validation_errors': []
        }
        
        for rule in validation_rules:
            rule_results = self.apply_validation_rule(source_data, rule)
            validation_results['validation_errors'].extend(rule_results['errors'])
        
        validation_results['valid_records'] = validation_results['total_records'] - len(validation_results['validation_errors'])
        validation_results['invalid_records'] = len(validation_results['validation_errors'])
        
        return validation_results
    
    def apply_validation_rule(self, data, rule):
        errors = []
        
        if rule['type'] == 'completeness':
            errors.extend(self.check_completeness(data, rule))
        elif rule['type'] == 'format':
            errors.extend(self.check_format(data, rule))
        elif rule['type'] == 'range':
            errors.extend(self.check_range(data, rule))
        elif rule['type'] == 'reference':
            errors.extend(self.check_reference(data, rule))
        
        return {'errors': errors}
```

### 2. Data Cleansing During Migration
**Tejuu's Cleansing Patterns:**

```python
# Data cleansing during migration
class DataCleanser:
    def __init__(self):
        self.cleansing_rules = self.load_cleansing_rules()
    
    def cleanse_data(self, df, table_name):
        df_clean = df
        
        # Apply table-specific cleansing rules
        if table_name == 'customers':
            df_clean = self.cleanse_customer_data(df_clean)
        elif table_name == 'transactions':
            df_clean = self.cleanse_transaction_data(df_clean)
        elif table_name == 'products':
            df_clean = self.cleanse_product_data(df_clean)
        
        # Apply general cleansing rules
        df_clean = self.apply_general_cleansing(df_clean)
        
        return df_clean
    
    def cleanse_customer_data(self, df):
        # Clean customer names
        df = df.withColumn("customer_name", trim(upper(col("customer_name"))))
        
        # Clean phone numbers
        df = df.withColumn("phone", regexp_replace(col("phone"), "[^0-9]", ""))
        
        # Clean email addresses
        df = df.withColumn("email", lower(trim(col("email"))))
        
        # Standardize addresses
        df = df.withColumn("city", initcap(trim(col("city"))))
        df = df.withColumn("state", upper(trim(col("state"))))
        
        return df
    
    def cleanse_transaction_data(self, df):
        # Clean amounts
        df = df.withColumn("amount", regexp_replace(col("amount"), "[^0-9.]", ""))
        df = df.withColumn("amount", col("amount").cast("decimal(18,2)"))
        
        # Clean dates
        df = df.withColumn("transaction_date", to_date(col("transaction_date"), "MM/dd/yyyy"))
        
        # Clean transaction types
        df = df.withColumn("transaction_type", upper(trim(col("transaction_type"))))
        
        return df
```

## Migration Testing Strategies

### 1. Parallel Testing
**Tejuu's Parallel Testing Pattern:**

```python
# Parallel testing during migration
class ParallelTester:
    def __init__(self):
        self.test_results = {}
    
    def run_parallel_tests(self, source_data, target_data):
        tests = [
            self.test_record_count,
            self.test_data_accuracy,
            self.test_data_completeness,
            self.test_business_rules,
            self.test_referential_integrity
        ]
        
        for test in tests:
            test_name = test.__name__
            try:
                result = test(source_data, target_data)
                self.test_results[test_name] = {
                    'status': 'PASSED',
                    'result': result
                }
            except Exception as e:
                self.test_results[test_name] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
        
        return self.test_results
    
    def test_record_count(self, source_data, target_data):
        source_count = source_data.count()
        target_count = target_data.count()
        
        if source_count != target_count:
            raise Exception(f"Record count mismatch: Source={source_count}, Target={target_count}")
        
        return {'source_count': source_count, 'target_count': target_count}
    
    def test_data_accuracy(self, source_data, target_data):
        # Sample data for accuracy testing
        source_sample = source_data.sample(0.1)
        target_sample = target_data.sample(0.1)
        
        # Compare key fields
        accuracy_score = self.calculate_accuracy_score(source_sample, target_sample)
        
        if accuracy_score < 0.95:  # 95% accuracy threshold
            raise Exception(f"Data accuracy below threshold: {accuracy_score}")
        
        return {'accuracy_score': accuracy_score}
```

### 2. Business Validation
**Tejuu's Business Validation Pattern:**

```python
# Business validation during migration
class BusinessValidator:
    def __init__(self):
        self.business_rules = self.load_business_rules()
    
    def validate_business_rules(self, migrated_data):
        validation_results = {
            'total_rules': len(self.business_rules),
            'passed_rules': 0,
            'failed_rules': 0,
            'rule_results': []
        }
        
        for rule in self.business_rules:
            try:
                result = self.execute_business_rule(migrated_data, rule)
                validation_results['rule_results'].append({
                    'rule_name': rule['name'],
                    'status': 'PASSED',
                    'result': result
                })
                validation_results['passed_rules'] += 1
            except Exception as e:
                validation_results['rule_results'].append({
                    'rule_name': rule['name'],
                    'status': 'FAILED',
                    'error': str(e)
                })
                validation_results['failed_rules'] += 1
        
        return validation_results
    
    def execute_business_rule(self, data, rule):
        if rule['type'] == 'aggregation':
            return self.validate_aggregation(data, rule)
        elif rule['type'] == 'calculation':
            return self.validate_calculation(data, rule)
        elif rule['type'] == 'constraint':
            return self.validate_constraint(data, rule)
```

## Cutover Strategies

### 1. Big Bang Cutover
**Tejuu's Big Bang Pattern:**

```python
# Big bang cutover strategy
class BigBangCutover:
    def __init__(self):
        self.cutover_plan = self.create_cutover_plan()
    
    def execute_big_bang_cutover(self):
        cutover_results = {
            'start_time': datetime.now(),
            'phases_completed': [],
            'errors': []
        }
        
        try:
            # Phase 1: Stop source system updates
            self.stop_source_updates()
            cutover_results['phases_completed'].append('stop_source_updates')
            
            # Phase 2: Final data sync
            self.final_data_sync()
            cutover_results['phases_completed'].append('final_data_sync')
            
            # Phase 3: Switch to target system
            self.switch_to_target_system()
            cutover_results['phases_completed'].append('switch_to_target')
            
            # Phase 4: Validate cutover
            self.validate_cutover()
            cutover_results['phases_completed'].append('validate_cutover')
            
            cutover_results['status'] = 'SUCCESS'
            
        except Exception as e:
            cutover_results['status'] = 'FAILED'
            cutover_results['errors'].append(str(e))
            self.rollback_cutover()
        
        cutover_results['end_time'] = datetime.now()
        return cutover_results
```

### 2. Phased Cutover
**Tejuu's Phased Cutover Pattern:**

```python
# Phased cutover strategy
class PhasedCutover:
    def __init__(self):
        self.cutover_phases = self.define_cutover_phases()
    
    def execute_phased_cutover(self):
        cutover_results = {
            'total_phases': len(self.cutover_phases),
            'completed_phases': 0,
            'current_phase': None,
            'errors': []
        }
        
        for phase in self.cutover_phases:
            try:
                cutover_results['current_phase'] = phase['name']
                
                # Execute phase
                phase_result = self.execute_cutover_phase(phase)
                
                if phase_result['status'] == 'SUCCESS':
                    cutover_results['completed_phases'] += 1
                else:
                    cutover_results['errors'].append({
                        'phase': phase['name'],
                        'error': phase_result['error']
                    })
                    break
                
            except Exception as e:
                cutover_results['errors'].append({
                    'phase': phase['name'],
                    'error': str(e)
                })
                break
        
        return cutover_results
    
    def execute_cutover_phase(self, phase):
        if phase['type'] == 'data_migration':
            return self.migrate_data_phase(phase)
        elif phase['type'] == 'system_switch':
            return self.switch_system_phase(phase)
        elif phase['type'] == 'validation':
            return self.validate_phase(phase)
```

## Post-Migration Support

### 1. Data Reconciliation
**Tejuu's Reconciliation Pattern:**

```python
# Post-migration data reconciliation
class DataReconciler:
    def __init__(self):
        self.reconciliation_rules = self.load_reconciliation_rules()
    
    def reconcile_migrated_data(self, source_data, target_data):
        reconciliation_results = {
            'total_checks': len(self.reconciliation_rules),
            'passed_checks': 0,
            'failed_checks': 0,
            'discrepancies': []
        }
        
        for rule in self.reconciliation_rules:
            try:
                result = self.execute_reconciliation_rule(source_data, target_data, rule)
                
                if result['status'] == 'PASSED':
                    reconciliation_results['passed_checks'] += 1
                else:
                    reconciliation_results['failed_checks'] += 1
                    reconciliation_results['discrepancies'].append({
                        'rule': rule['name'],
                        'discrepancy': result['discrepancy']
                    })
                
            except Exception as e:
                reconciliation_results['failed_checks'] += 1
                reconciliation_results['discrepancies'].append({
                    'rule': rule['name'],
                    'error': str(e)
                })
        
        return reconciliation_results
```

### 2. Performance Monitoring
**Tejuu's Performance Monitoring Pattern:**

```python
# Post-migration performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.performance_metrics = {}
    
    def monitor_migration_performance(self, target_system):
        performance_results = {
            'query_performance': self.measure_query_performance(target_system),
            'data_quality': self.measure_data_quality(target_system),
            'user_satisfaction': self.measure_user_satisfaction(target_system),
            'system_availability': self.measure_system_availability(target_system)
        }
        
        return performance_results
    
    def measure_query_performance(self, target_system):
        # Measure query performance against baseline
        test_queries = self.get_performance_test_queries()
        
        performance_metrics = {}
        for query in test_queries:
            execution_time = self.execute_query_and_measure_time(query, target_system)
            performance_metrics[query['name']] = {
                'execution_time_seconds': execution_time,
                'status': 'PASSED' if execution_time < query['threshold'] else 'FAILED'
            }
        
        return performance_metrics
```

My ETL migration experience helps organizations successfully modernize their data platforms while minimizing business disruption and ensuring data quality!
