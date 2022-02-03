import boto3
import CFF_call_test
from datetime import datetime, timedelta
import argparse
import time
import re

# Dispatch the query to Athena
def athena_query(client, params):
    response = client.start_query_execution(
        QueryString=params["query"],
        QueryExecutionContext={
            'Database': params['database']
        },
        ResultConfiguration={
            'OutputLocation': 's3://' + params['bucket'] + '/' + params['path']
        }
    )
    return response

def get_result(d):
    return [obj['VarCharValue'] for obj in d['Data']]

# send the query to athena and get results, 
def athena_to_s3(session, params, max_execution = 10):
    client = session.client('athena', region_name=params["region"])
    execution = athena_query(client, params)
    execution_id = execution['QueryExecutionId']
    state = 'RUNNING'

    # more rows from athena, need more max_excution value.
    while (max_execution > 0 and state in ['RUNNING', 'QUEUED']):
        max_execution = max_execution - 1
        response = client.get_query_execution(QueryExecutionId = execution_id)

        if 'QueryExecution' in response and \
                'Status' in response['QueryExecution'] and \
                'State' in response['QueryExecution']['Status']:
            state = response['QueryExecution']['Status']['State']
            if state == 'FAILED':
                return False
            elif state == 'SUCCEEDED':
                # Poll the results and once the query is finished
                s3_path = response['QueryExecution']['ResultConfiguration']['OutputLocation']
                filename = re.findall('.*\/(.*)', s3_path)[0]
                
                response_query_result = client.get_query_results(
                    QueryExecutionId = execution_id
                )
                result_data = response_query_result['ResultSet']
                
                if len(response_query_result['ResultSet']['Rows']) > 1:
                    header = response_query_result['ResultSet']['Rows'][0]
                    rows = response_query_result['ResultSet']['Rows'][1:]
                    header = [obj['VarCharValue'] for obj in header['Data']]
                    result = [dict(zip(header, get_result(row))) for row in rows]
    
                    return s3_path, result
                else:
                    return s3_path, None

        time.sleep(3)
    
    return False

# Deletes all files in your path so use carefully!
def clean_up(session, params):
    s3 = session.resource('s3')
    bucket = s3.Bucket(params['bucket'])
    for item in bucket.objects.filter(Prefix=params['path']):
        item.delete()

def main(argv):
    queries = """\
    SELECT count(*) cnt, request_ip, method, uri, referrer, user_agent, query_string, cookie, host_header
    -- please change the table name to yours
    FROM combined
    -- filtering 24 hours(1d) data
    WHERE concat(year, month, day, hour) >= DATE_FORMAT
    GROUP BY request_ip, method, uri, referrer, user_agent, query_string, cookie, host_header
    ORDER BY cnt desc
    -- top 10 requests
    limit 10"""

    now = datetime.utcnow()
    # filtering -24hours(1d) data
    filtered_date = (now - timedelta(days=1)).strftime('%Y%m%d%H')
    # filtering -5hours data 
    #filtered_date = (now - timedelta(hours=5)).strftime('%Y%m%d%H')
    athena_query = queries.replace("DATE_FORMAT","'" + filtered_date + "'")
    #print(athena_query)

    # please change the values in params to your region, database, bucket, path.
    region = "ap-northeast-2"
    database = "yourdatabasename"
    bucket = "yourbucketname"
    path = "temp/athena/output"

    params = {
        'region': region,
        'database': database,
        'bucket': bucket,
        'path': path,
        'query': athena_query
    }

    session = boto3.Session()

    # Query Athena and get the s3 filename and query results
    location, data = athena_to_s3(session, params)

    #get CloudFront Function ETag - pre-requisite parameter of CFF test
    functionName = argv.function
    eventType = argv.eventType
    CFF_etag = CFF_call_test.getETag(session, functionName)

    #print input/output sample
    print("input(request_ip, host_header, url, referer, user-agent, cookies) --> output(status(Err or OK), ComputeUtilization%)")

    #call test_function of Cloudfront Function
    for queryResult in data:
        cpu, testResult = CFF_call_test.testFunction(session, etag=CFF_etag, athenaResult=queryResult, functionName=functionName, evenType=eventType)
    
    # Deletes all files in your path so use carefully!
    clean_up(session, params)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="testing CloudFront Function \
        ex. testingCFF.py --function functionName --eventType viewer-response")
    parser.add_argument('--function', metavar='function_name', required=True, help='CloudFront Fucntion Name')
    parser.add_argument('--eventType', metavar='eventType', required=False, default="viewer-request", help='default Value: viewer-request')

    args = parser.parse_args()
    main(args)
