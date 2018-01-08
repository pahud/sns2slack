# -*- coding: utf-8 -*-


import requests, json

def do_webhook(url, body_json, page_all=False, page_present=False):
    print('start webhook')
    postData = {
        # "channel": "#sns2im",
        "username": "sns2slack",
        "text": "*" + body_json['Subject'] + "*",
        "icon_emoji": ":aws:"
    }
    
    subject = body_json['Subject']
    message = body_json['Message']
    print('Subject=%s' % subject)
    print('Message=%s' % message)
    
    severity = 'good'
    
    colors = {
        'good': '#008000',
        'warning': '#ffa500',
        'danger': '#D00000'
    }

    dangerMessages = [
        "ALARM",
        " but with errors",
        " to RED",
        "During an aborted deployment",
        "Failed to deploy application",
        "Failed to deploy configuration",
        "has a dependent object",
        "is not authorized to perform",
        "Pending to Degraded",
        "Stack deletion failed",
        "Unsuccessful command execution",
        "You do not have permission",
        "Your quota allows for 0 more running instance"
        ]

    warningMessages = [
        " aborted operation.",
        " to YELLOW",
        "Adding instance ",
        "Degraded to Info",
        "Deleting SNS topic",
        "is currently running under desired capacity",
        "Ok to Info",
        "Ok to Warning",
        "Pending Initialization",
        "Removed instance ",
        "Rollback of environment"        
        ]
    for i in dangerMessages:
        if subject.find(i)>-1:
            severity = 'danger'
            break

    if severity=='good':
        for i in warningMessages:
            if subject.find(i)>-1:
                severity = 'warning' 
                break
    print('severity: %s' % severity)
    
    fields = []
    for k in message.keys():
        fields.append( {'title': k, 'value': message[k], 'short': 'false' })
        
    alarm_url = 'https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#alarm:alarmFilter=inAlarm;name=%s' % message['AlarmName']

    postData['attachments'] = [
        {
            "fallback": '<{}|click here to see the Alarm>'.format(alarm_url),
            "pretext":  '<{}|click here to see the Alarm>'.format(alarm_url),
            "color": colors[severity], 
            "fields": fields
        }
    ];
    
    # msg = '{}\n'.format(msg)
    # if page_all: msg = '{} @All  '.format(msg)
    # if page_present: msg = '{} @Present  '.format(msg)
        
    # msg = '{} @All   @Present'.format(msg)
    r = requests.post(url=url, json=postData)
    print(r)
    
def is_json(s):
    try:
        json_object = json.loads(s)
    except ValueError:
        return False
    if s[0]=='{' and s[-1]=='}':
        return True
    else:
        return False

def lambda_handler(event, context):
    slack_webhook_domain = 'https://hooks.slack.com'
    page_all = False
    page_present = False
    
    resp = { 
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'ok'
        }
        
    print(json.dumps(event))
    qs = event['queryStringParameters'] or {}
    if qs and 'page_all' in qs:
        page_all = True
    if qs and 'page_present' in qs:
        page_present = True
        
    print(json.dumps(qs))
    if 'body' in event and type(event['body'])==str and is_json(event['body']):
        body_json = json.loads(event['body'])
        if 'Type' in body_json and body_json['Type'] == 'SubscriptionConfirmation' and 'SubscribeURL' in body_json:
            print('[info] got SubscribeURL, sending confirmation signal...')
            r = requests.get(url=body_json['SubscribeURL'])
            print(r)
            resp['body'] = "subscribed"
            return resp
        if 'Message' in body_json and is_json(body_json['Message']):
            body_json['Message'] = json.loads(body_json['Message'])
    elif 'text' in qs and len(qs['text'])>0:
        pass
    else:
        resp['body'] = "invalid http body"
        return resp
            
    qs_flat = '&'.join('{}={}'.format(x,y) for (x,y) in qs.items())   
    webhook_url = '{}/services/{}?{}'.format(slack_webhook_domain, event['pathParameters']['proxy'], qs_flat)
    print('webhook_url=%s' % webhook_url)
    ''' overwrite the message if 'text' in the query string '''
    if 'text' in qs and len(qs['text'])>0:
        if is_json(qs['text']):
            try:
                body_json = json.loads(qs['text'])
                msg2send = json.dumps(body_json, indent=4, separators=(',', ': '))
            except yaml.parser.ParserError:
                #body_json = qs['text']
                msg2send = qs['text']
        else:
            msg2send = qs['text']
    else:
        msg2send = json.dumps(body_json, indent=4, separators=(',', ': '))
    
    do_webhook(webhook_url, body_json, page_all, page_present )
        
    return resp
