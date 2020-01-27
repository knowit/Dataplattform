import boto3
from add_secret_to_ssm import add_parameter


def generatePassword(length, name, stage, service, description, overwrite):
	#session = boto3.Session(profile_name="new")
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

	finalName = add_parameter(name, stage, service, description, overwrite, response["RandomPassword"], "SecureString")

	return finalName




def main():

	name = input("Name:")
	description = input("Description:")
	stage = input("Stage(dev, test, prod):")
	service = input("Service:")
	overwrite = bool(input("Overwrite existing value, true/false?:"))

	name = generatePassword(64, name, stage, service, description, overwrite)
	print("Final name: " + name)

if __name__== "__main__" :
	main()
