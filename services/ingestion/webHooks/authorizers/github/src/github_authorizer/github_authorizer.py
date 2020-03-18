

def handler(event, context):
    print("EVENT:", event)


#    headers = event.get("headers", {})
#    signature = headers.get("X-Hub-Signature", None)
#    if not signature:
#        return {
#            'statusCode': 403,
#            'body': json.dumps({"reason": "No signature"})
#        }
#
#
#
#    return
#        'statusCode': 200,
#        'body': ""
#    }
