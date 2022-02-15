## Amazon CloudFront Functions Testing Tool
Amazon CloudFront Functions Test based on production traffic

## Pre-requisite
* This sample project depends on boto3, the AWS SDK for Python, and requires Python 2.6.5+, 2.7, 3.3, 3.4, or 3.5. You can install boto3 using pip:
```python
pip install boto3
```
* You need to set up your AWS security credentials before the sample code is able to connect to AWS. You can do this by creating a file named "credentials" at ~/.aws/ (C:\Users\USER_NAME\.aws\ for Windows users) and saving the following lines in the file:
```
[default]
aws_access_key_id = <your access key id>
aws_secret_access_key = <your secret key>
```
See the [Security Credentials](https://console.aws.amazon.com/iam/home?#security_credential) page for more information on getting your keys. For more information on configuring boto3, check out the Quickstart section in the [developer guide](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).
* [Configuring Amazon CloudFront logging](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html)
* [setup Amazon Athena to run standard SQL queries on your CloudFront access log data in S3](https://aws.amazon.com/blogs/big-data/analyze-your-amazon-cloudfront-access-logs-at-scale/)

## Architecture
<img src="https://github.com/aws-samples/amazon-cloudfront-functions-testing-tool/blob/main/CFF_test_w__standard_log.png" width="100%" height="100%" title="px(픽셀) 크기 설정" alt="Architecture"></img><br/>
You can find a detailed architecture between lambda <-> Athena <-> Glue in [this blog](https://aws.amazon.com/blogs/big-data/analyze-your-amazon-cloudfront-access-logs-at-scale/).

## How to excute
1. You can use this content by cloning the repository or downloading the files.
2. excute python this command line.
```python
python3 testingCFF.py --function functionName
```
If your function's eventType is for viewer-response, please add a eventType argument.
```python
python3 testingCFF.py --function functionName --eventType viewer-response
```
You can choose request headers used an event object as input to the function.
These headers are extracted based on Amazon CloudFront Standard logs. So please keep it mind all headers are not available.
available headers = ['request_ip', 'method', 'uri', 'referrer', 'user_agent', 'query_string', 'cookie', 'host_header']
```python
python3 testingCFF.py --function functionName --headers request_ip method uri referrer user_agent query_string cookie --eventType viewer-response
```
For help,
```python
python3 testingCFF.py -h                                                                                                                           
usage: testingCFF.py [-h] --function function_name [--eventType eventType] [--headers headers [headers ...]]

testing CloudFront Function ex. python3 testingCFF.py --function functionName --eventType viewer-response --headers request_ip referrer

optional arguments:
  -h, --help            show this help message and exit
  --function function_name
                        CloudFront Fucntion Name
  --eventType eventType
                        default Value: viewer-request
  --headers headers [headers ...]
                        default Value: ['request_ip', 'uri', 'referrer'] , valid headers: request_ip, method, uri, referrer, user_agent, query_string, cookie, host_header
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

