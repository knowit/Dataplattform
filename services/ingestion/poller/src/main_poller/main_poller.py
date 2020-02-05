import json

def handler(event, context):

	# Her skal data håndteres ved polling

	return {
		'statusCode': 200,
		'body': json.dumps({
			"message": "success!"
		})
	}
