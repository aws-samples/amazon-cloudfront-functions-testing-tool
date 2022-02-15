import datetime, json
from urllib import parse

def json_default(value):
    if isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    raise TypeError('not JSON serializable')

# return cloudfront function ETag
def getETag(session, functionName):
    client = session.client('cloudfront')
    response = client.describe_function(
        Name=functionName
    )

    # aws api returns dict type
    etag = response["ETag"]
    return etag

# test CFF
def testFunction(session, **kwargs):
    client = session.client('cloudfront')

    # set variable
    functionName = kwargs["functionName"]
    etag = kwargs["etag"]
    
    # set initial request header values
    uri = referrer = request_ip = user_agent = query_string = cookies = host_header = "-"
    # declare an array for request headers(input values) of a test result ex. input(172.70.49.4, /, -)
    req_header_values = []
    
    # choose function template json (FunctionTemplate.json for viewer-request, FunctionTemplate_res.json for viewer-response)
    templateFileName = "FunctionTemplate.json" if kwargs["evenType"] == "viewer-request" else "FunctionTemplate_res.json"
    with open(templateFileName,"r") as f:
        #read json template
        data = json.load(f)

        #change values in json template
        for header in kwargs["headers"]:
            #clientIP
            if header == "request_ip":
                request_ip = kwargs["athenaResult"][header]
                req_header_values.append(request_ip)
                data["viewer"] = {}
                data["viewer"]["ip"] = request_ip
            #method
            if header == "method":
                method = kwargs["athenaResult"][header]
                req_header_values.append(method)
                data["request"][header] = method
            #uri
            if header == "uri":
                uri = parse.unquote(kwargs["athenaResult"][header])
                req_header_values.append(uri)
                data["request"][header] = uri
            #querystring
            if header == "query_string":
                query_string = parse.unquote(kwargs["athenaResult"][header])
                #req_header_values.append(query_string) # doesn't need to add it into req_header_values array cause uri includes query_string.
                if query_string != "-":
                    data["request"]["querystring"] = {}
                    arrquery = query_string.split("&")
                    for query in arrquery:
                        tempQuery = query.split("=")
                        key = tempQuery[0].strip()
                        value = tempQuery[1].strip()

                        data["request"]["querystring"][key] = {}
                        data["request"]["querystring"][key]["value"] = value
            #header
            if header in ["referrer", "user_agent", "host_header", "cookie"]:
                data["request"]["headers"] = {}
                #referer
                if header == "referrer":
                    referrer = parse.unquote(kwargs["athenaResult"][header])
                    req_header_values.append(referrer)
                    if referrer != "-":
                        data["request"]["headers"]["referer"] = {}
                        data["request"]["headers"]["referer"]["value"] = referrer
                #user-agent
                if header == "user_agent":
                    user_agent = parse.unquote(kwargs["athenaResult"][header])
                    req_header_values.append(user_agent)
                    if user_agent != "-":
                        data["request"]["headers"][header] = {}
                        data["request"]["headers"][header]["value"] = user_agent
                #host
                if header == "host_header":
                    host_header = parse.unquote(kwargs["athenaResult"][header])
                    req_header_values.append(host_header)
                    if host_header != "-":
                        data["request"]["headers"]["host"] = {}
                        data["request"]["headers"]["host"]["value"] = host_header
                #cookie
                if header == "cookie":
                    cookies = parse.unquote(kwargs["athenaResult"][header])
                    req_header_values.append(cookies)
                    if cookies != "-":
                        data["request"]["cookies"] = {}
                        cookie = cookies
                        arrCookie = cookie.split(";")
                        for query in arrCookie:
                            tempCookie = query.split("=")
                            key = tempCookie[0].strip()
                            value = tempCookie[1].strip()
                            data["request"]["cookies"][key] = {}
                            data["request"]["cookies"][key]["value"] = value

    #print input event_struction
    #print(json.dumps(data, default=json_default, indent=4))

    # test
    response = client.test_function(
        Name=functionName,
        IfMatch=etag,
        Stage='DEVELOPMENT',
        EventObject=json.dumps(data)
    )

    #print test_function result
    #print(json.dumps(response, default=json_default, indent=4))

    cpu = response["TestResult"]["ComputeUtilization"]
    status = "OK" if response["TestResult"]["FunctionErrorMessage"] == "" else "Err"

    #input(1.2.3.4, google.com, /ask) → output (Err, 90%)
    if query_string != "-":
        uri = uri + "?" + query_string
        req_header_values[kwargs["headers"].index("uri")] = uri

    # highlight if cpu utilize more than 80%
    cpu = '\033[31m' + cpu + '\033[0m' if int(cpu) > 80 else cpu

    # print test results
    print('input(' + ', '.join([str(req_header) for req_header in req_header_values]) + ")" + " --> output({}, {}%)".format(status, cpu))

    return cpu, status
