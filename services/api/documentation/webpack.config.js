const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { DefinePlugin } = require('webpack')
const fs = require("fs")

const outputPath = path.resolve(__dirname, 'dist');

const serverlessState = JSON.parse(fs.readFileSync(".serverless/serverless-state.json", "utf-8"))

const { cognitoClientId, apiUrl } = serverlessState.service.custom

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
      API_URL: JSON.stringify(apiUrl),
      DEMO_CLIENT_ID: JSON.stringify(cognitoClientId)
      //DEMO_CLIENT_ID: JSON.stringify('5dk4t7d9ad5l3hcmo2fq14is81') // TODO: Ref
    })
  ],
  output: {
    filename: '[name].bundle.js',
    path: outputPath,
  }
};