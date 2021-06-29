const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { DefinePlugin } = require('webpack')
const { SSMClient, GetParameterCommand} = require("@aws-sdk/client-ssm");

const outputPath = path.resolve(__dirname, 'dist');

// Set the AWS Region.
const REGION = "REGION"; //e.g. "us-east-1"
// Create an Amazon S3 service client object.

const ssmClient = new SSMClient({ region: 'eu-central-1' });

async function getClientId() {
  const input =  {"Name" : '/dev/cognito/UserPoolClientId'}
//const input2 = {name: '/dev/cloudfront-api-dist/distributionAlias'}
  const command = new GetParameterCommand(input)
//const command2 = new GetParameterCommand(input2)

  var result = 0;
  const clientid = await ssmClient.send(command);
  //const apiurl = await ssmClient.send(command2);
  return clientid;
}

const clientid = getClientId()

module.exports = {
  mode: 'development',
  entry: {
    app: './src/index.js',
  },
  module: {
    rules: [
      {
        test: /\.yaml$/,
        use: [
          { loader: 'json-loader' },
          { loader: 'yaml-loader' }
        ]
      },
      {
        test: /\.css$/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
        ]
      }
    ]
  },
  plugins: [
    new CleanWebpackPlugin([
      outputPath
    ]),
    new CopyWebpackPlugin([
      {
        // Copy the Swagger OAuth2 redirect file to the project root;
        // that file handles the OAuth2 redirect after authenticating the end-user.
        from: 'node_modules/swagger-ui/dist/oauth2-redirect.html',
        to: './'
      }
    ]),
    new HtmlWebpackPlugin({
      template: 'index.html'
    }),
    new DefinePlugin({
      API_URL: JSON.stringify('api.new-dev.dataplattform.knowit.no'), //TODO: Ref
      //DEMO_CLIENT_ID: JSON.stringify('5dk4t7d9ad5l3hcmo2fq14is81') // TODO: Ref
      DEMO_CLIENT_ID: JSON.stringify((() => {console.log(clientid.Parameter.Value);
                                                          return clientid.Parameter.Value})()) // TODO: Ref
      //DEMO_CLIENT_ID: JSON.stringify('27g4krd7m209soqhk050hoa0bn')
    })
  ],
  output: {
    filename: '[name].bundle.js',
    path: outputPath,
  }
};