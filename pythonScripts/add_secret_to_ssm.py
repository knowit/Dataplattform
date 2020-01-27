import boto3


def add_parameter(name, stage, service, description, overwrite, value, type):
	#session = boto3.Session(profile_name="new")
	
	client = boto3.client('ssm')

	finalName = "/" + stage + "/" + service + "/" + name

	response = client.put_parameter(
		Name=finalName,
		Description=description,
		Value=value,
		Type=type,
		Overwrite=overwrite,
		Tier='Standard'
	)

	return finalName




def main():
	name = input("Name:")
	description = input("Description:")
	stage = input("Stage(dev, test, prod):")
	service = input("Service:")
	overwrite = bool(input("Overwrite existing value, true/false?:"))
	type = int(input("Type of parameter(1, 2, or 3)? 1=String, 2=StringList, 3=SecureString:"))
	value = input("Value:")

	types = ["String", "StringList", "SecureString"]

	response = add_parameter(name, stage, service, description, overwrite, value, types[type-1])

	print("Final name: " + response)

if __name__== "__main__" :
	main()
