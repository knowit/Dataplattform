const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const {CleanWebpackPlugin} = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { DefinePlugin, ProvidePlugin } = require('webpack')
const fs = require("fs")

const outputPath = path.resolve(__dirname, 'dist');

const serverlessState = JSON.parse(fs.readFileSync(".serverless/serverless-state.json", "utf-8"))

const { cognitoClientId, apiUrl } = serverlessState.service.custom


module.exports = {
  mode: 'development',
  entry: {
    app: './src/index.js',
  },
  resolve: {
    fallback: {
      stream: require.resolve('stream-browserify/')
    }
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
    new CleanWebpackPlugin(),
    new CopyWebpackPlugin(
      {
        patterns:[
      {
        // Copy the Swagger OAuth2 redirect file to the project root;
        // that file handles the OAuth2 redirect after authenticating the end-user.
        from: 'node_modules/swagger-ui/dist/oauth2-redirect.html',
        to: './'
      }
    ]
    }
    ),
    new HtmlWebpackPlugin({
      template: 'index.html'
    }),
    new DefinePlugin({
      API_URL: JSON.stringify(apiUrl),
      DEMO_CLIENT_ID: JSON.stringify(cognitoClientId)
    }),
    new ProvidePlugin({
      Buffer: ['buffer', 'Buffer']
    })
  ],
  output: {
    filename: '[name].bundle.js',
    path: outputPath,
  }
};