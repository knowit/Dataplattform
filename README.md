# Dataplattform
This project is an internal initiative for Knowit Objectnet. The purpose of the project is manyfold. It should give hand-on experience on cloud solutions and serverless architecture and it aims to make data available for users of the data platform. 

The main architecture consists of [AWS Lambda](https://aws.amazon.com/lambda/)-functions serving for data ingestion and processing and [AWS S3](https://aws.amazon.com/s3/) as datalake storage. API's for data exploration is under development and schemas are auto-generated using [AWS Glue](https://aws.amazon.com/glue/) while querys can be done using [AWS Athena](https://aws.amazon.com/athena/).  

Currently the platform gathers data from several different datasources, both as scheduled event polls and web hook events. Amongst the supported datasources are [yr](yr.no), github-repos and the internal CV database for Knowit, CV Partner.  
### Dependecies
1. [python 3.7](https://www.python.org/downloads/)
2. [nodejs and npm](https://www.npmjs.com/get-npm)
3. [serverless](https://serverless.com/framework/docs/getting-started#install-via-npm): `npm install -g serverless`
4. [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
It is also highly recommended that you use a virtual environment or similar to manage pip packages and dependencies. 
To configure `aws-cli`, please contact an existing member of the team for credentials.

## Running the services
The indvidual services are deployed to AWS using
`sls deploy --stage {STAGE}` where `dev` is the only currently supported stage.  
## Contributing
Contributing by adding a new datasource or other small improvements can be done by creating a pull request as local testing can be utilized and AWS connections mocked. For cloud testing one must be member of the Dataplattform team at Knowit Objectnet.
