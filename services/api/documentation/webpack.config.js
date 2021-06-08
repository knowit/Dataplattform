const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const { DefinePlugin } = require('webpack')

const outputPath = path.resolve(__dirname, 'dist');

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
      API_URL: JSON.stringify('dev-api.new-dev.dataplattform.knowit.no'),
      DEMO_CLIENT_ID: JSON.stringify('46r144f3qdhere7igl8d2gjacr')
      //DEMO_CLIENT_ID: JSON.stringify('27g4krd7m209soqhk050hoa0bn')
    })
  ],
  output: {
    filename: '[name].bundle.js',
    path: outputPath,
  }
};