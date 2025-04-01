/* eslint-disable @typescript-eslint/no-var-requires */

const { merge } = require('webpack-merge')
const common = require('./webpack.common.js')
const { stylePaths } = require('./stylePaths')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin')
const TerserJSPlugin = require('terser-webpack-plugin')

module.exports = merge(common('production'), {
  mode: 'production',
  devtool: 'source-map',
  optimization: {
    splitChunks: {
      chunks: 'all',
      minSize: 30000,
      maxSize: 244000,
      automaticNameDelimiter: '-',
    },
    minimizer: [
      new TerserJSPlugin({
        terserOptions: {
          compress: {
            drop_console: true,
            drop_debugger: true,
            pure_getters: true,
            passes: 3,
            reduce_vars: true,
            collapse_vars: true,
            negate_iife: false,
          },
          mangle: {
            reserved: ['$', 'exports', 'require'],
          },
          output: {
            comments: false,
          },
        },
        parallel: true,
      }),
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: ['default', { mergeLonghand: false }]
        }
      })
    ]
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name].css',
      chunkFilename: '[name].bundle.css'
    })
  ],
  module: {
    rules: [
      {
        test: /\.css$/,
        include: [...stylePaths],
        use: [MiniCssExtractPlugin.loader, 'css-loader']
      }
    ]
  }
})

