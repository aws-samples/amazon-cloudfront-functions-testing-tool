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
    uri = parse.unquote(kwargs["athenaResult"]["uri"])
    referer = parse.unquote(kwargs["athenaResult"]["referrer"])
    user_agent = parse.unquote(kwargs["athenaResult"]["user_agent"])
    queryString = parse.unquote(kwargs["athenaResult"]["query_string"])
    cookies = parse.unquote(kwargs["athenaResult"]["cookie"])
    host_header = parse.unquote(kwargs["athenaResult"]["host_header"])
    clientIP = kwargs["athenaResult"]["request_ip"]

    # choose function template json (FunctionTemplate.json for viewer-request, FunctionTemplate_res.json for viewer-response)
    templateFileName = "FunctionTemplate.json" if kwargs["evenType"] == "viewer-request" else "FunctionTemplate_res.json"

    with open(templateFileName,"r") as f:
        #read json template
        data = json.load(f)

        #change values in json template
        #clientIP
        data["viewer"] = {}
        data["viewer"]["ip"] = clientIP

        #method
        data["request"]["method"] = kwargs["athenaResult"]["method"]

        #uri
        data["request"]["uri"] = uri

        #querystring
        if queryString != "-":
            data["request"]["querystring"] = {}
            arrquery = queryString.split("&")
            for query in arrquery:
                tempQuery = query.split("=")
                key = tempQuery[0].strip()
                value = tempQuery[1].strip()

                data["request"]["querystring"][key] = {}
                data["request"]["querystring"][key]["value"] = value

        #header
        data["request"]["headers"] = {}
        #referer
        if referer != "-":
            data["request"]["headers"]["referer"] = {}
            data["request"]["headers"]["referer"]["value"] = referer
        #user-agent
        if user_agent != "-":
            data["request"]["headers"]["user-agent"] = {}
            data["request"]["headers"]["user-agent"]["value"] = user_agent
        #host
        if host_header != "-":
            data["request"]["headers"]["host"] = {}
            data["request"]["headers"]["host"]["value"] = host_header
        
        #cookie
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
    url = uri if queryString == "-" else uri + "?" + queryString

    # highlight if cpu utilize more than 80%
    cpu = '\033[31m' + cpu + '\033[0m' if int(cpu) > 80 else cpu

    print("input({}, {}, {}, {}, {}, {})".format(clientIP, host_header, url, referer, user_agent, cookies) + " --> output({}, {}%)".format(status, cpu))

    return cpu, status