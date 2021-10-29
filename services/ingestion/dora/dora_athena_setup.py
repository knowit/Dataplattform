import boto3

athena_client = boto3.client('athena')
kms_client = boto3.client('kms')

storage_bucket = "s3://dev-kmsbucket-876363704293/Athena-logs/"
database = 'dev_level_4_database'
workgroup = 'DoraWorkgroups'

def handler(event, context):

    def create_query(name, query):
        response = athena_client.create_named_query(
            Name=name,
            Description='Named query created by athena setup lambda for query ' + name,
            Database=database,
            QueryString=query,
            WorkGroup=workgroup
        )
        return response

    def get_KMS_arn(keyID):
        response = kms_client.describe_key(
            KeyId=keyID,
        )
        return response['KeyMetadata']['Arn']

    def run_query(query):
        athena_client.start_query_execution(
            QueryString = query,
            QueryExecutionContext = {
                'Database': database
            },
            ResultConfiguration = {
                'OutputLocation' : storage_bucket,
                'EncryptionConfiguration' : {
                    'EncryptionOption' : 'SSE_KMS',
                    'KmsKey' : get_KMS_arn('alias/KMSBucketKey')
                }
            },
            WorkGroup = workgroup
        )

    def list_all_queries():
        response = athena_client.list_named_queries(
            WorkGroup=workgroup
        )
        ids = [item for item in response['NamedQueryIds']]
        list_of_named_queries = []
        for id in ids:
            named_query = athena_client.get_named_query(
                NamedQueryId=id
            )
            list_of_named_queries.append(named_query['NamedQuery']['Name'])
        return list_of_named_queries


    def create_queries():
        saved_queries = list_all_queries()
        new_queries = queries
        for key, query in new_queries.items():
            if(key not in saved_queries):
                create_query(key, query)
                run_query(query)
            else:
                run_query(query)

    create_queries()

query1 = '''CREATE OR REPLACE VIEW "github_deployments"
AS 
SELECT
COUNT(distinct id) AS deployments,
Date(from_unixtime(merged_at)) as Date,
partition_1
FROM
github_dora_repos
group by Date(from_unixtime(merged_at)), partition_1;'''

query2 = '''CREATE OR REPLACE VIEW "github_deployments_with_null_values"
AS 
WITH all_dates AS (
   SELECT CAST(date_column AS date) date_column
   FROM
     ((
 VALUES 
        "sequence"("date"("date_add"('month', -3, current_date)), "date"(current_date), INTERVAL  '1' DAY)
   )  t1 (date_array)
   CROSS JOIN UNNEST(date_array) t2 (date_column))
),
all_partitions AS (
    SELECT distinct(partition_1) from github_deployments
),
cross_product AS(
    SELECT * from all_partitions cross join all_dates
)
SELECT
  date_column, 
  partition_1, 
  "sum"(val) deployments
FROM
  (
   SELECT
     date date_column
   , partition_1
   , deployments val
   FROM
     github_deployments
UNION
SELECT
     date_column
   , partition_1
   , 0
   FROM
     cross_product
   WHERE ((date_column >= "date_add"('month', -3, current_date)) AND (date_column <= current_date))
) 
GROUP BY date_column, partition_1
ORDER BY date_column ASC'''

query3 = '''CREATE OR REPLACE VIEW "DeploymentFrequency"
AS with daily_values as(
SELECT
   date_column,
   COUNT(CASE WHEN deployments >0 then 1 end) as deployments,
   partition_1
from github_deployments_with_null_values 
group by date_column, partition_1
),
daily_aggregate_values as(
SELECT 
  WEEK(date_column) as week,
  COUNT(CASE WHEN deployments >0 then 1 end) as daily_deployments,
  partition_1
  from daily_values
  group by WEEK(date_column), partition_1
),
monthly_values as(
select 
   MONTH(date_column) AS MONTH,
   COUNT(CASE WHEN deployments >0 then 1 end) as monthly_deployments,
   partition_1
from github_deployments_with_null_values 
GROUP by MONTH(date_column), partition_1
),
weekly_table as(
Select 
partition_1,
CASE
   when approx_percentile(daily_deployments,0.5) >= 3 then 1
   when approx_percentile(daily_deployments,0.5) >= 1 then 2
   end as DeploymentFrequency
from daily_aggregate_values
group by partition_1
),
monthly_table as(
Select 
partition_1,
CASE
  when approx_percentile(monthly_deployments,0.5) >= 1 then 3
  else 4
  end as DeploymentFrequency
from monthly_values
where partition_1 is not null
Group by partition_1
),
aggregate_table as(
  SELECT * from monthly_table union select * from weekly_table
),
fixed_table as (
    Select 
    partition_1, 
    min(DeploymentFrequency) as DeploymentFrequency
    from aggregate_table group by partition_1
)
Select partition_1, frequency from fixed_table join frequency on fixed_table.DeploymentFrequency = frequency.id'''

query4 = """CREATE EXTERNAL TABLE IF NOT EXISTS frequency(
  id int, frequency string)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 's3://dev-datalake-bucket-*/tablefrequency/'"""

queries = {
    'github_deployments':query1, 
    'github_deployments_with_null_values':query2, 
    'DeploymentFrequency':query3, 
    'frequency':query4
    }