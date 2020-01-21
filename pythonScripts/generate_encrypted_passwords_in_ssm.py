import boto3


def generatePassword(length, name, stage, service, description, overwrite):
	#ession = boto3.Session(profile_name="new")
	client = boto3.client('secretsmanager')
	
	response = client.get_random_password(
		PasswordLength=length,
		ExcludeNumbers=False,
		ExcludePunctuation=True,
		ExcludeUppercase=False,
		ExcludeLowercase=False,
		IncludeSpace=False,
		RequireEachIncludedType=False
	)
	
	client = session.client('ssm')

	finalName = "/" + stage + "/" + service + "/" + name
	print(finalName)

	response = client.put_parameter(
		Name=finalName,
		Description=description,
		Value=response["RandomPassword"],
		Type='SecureString',
		Overwrite=overwrite,
		Tags=[
			{
				'Key': 'Project',
				'Value': "Dataplattform"
			},
		],
		Tier='Standard'
	)




def main():
	#/dev/auroradb/root/password
	generatePassword(64, "root/password", "dev", "auroradb", "Admin password for auroraDB", False)

if __name__== "__main__" :
	main()
