import { defineConfig } from 'tsup'
import type { Plugin } from 'esbuild'

// 修复formidable动态require插件的问题
// formidable在运行时用 require(path.join(__dirname, 'plugins', `${plgName}.js`)) 加载插件
// 打包后__dirname指向snapshot目录，插件文件不存在，导致运行失败
// 此插件将动态require替换为静态require
const fixFormidablePlugin: Plugin = {
  name: 'fix-formidable-dynamic-require',
  setup(build) {
    build.onLoad({ filter: /formidable[\\/]src[\\/]Formidable\.js$/ }, async (args) => {
      const fs = await import('fs')
      let contents = fs.readFileSync(args.path, 'utf8')

      // 将动态插件加载替换为静态require
      const dynamicRequire = `this.options.enabledPlugins.forEach((pluginName) => {
      const plgName = pluginName.toLowerCase();
      // eslint-disable-next-line import/no-dynamic-require, global-require
      this.use(require(path.join(__dirname, 'plugins', \`\${plgName}.js\`)));
    });`

      const staticRequire = `// [exe打包修复] 将动态require替换为静态require
    const _pluginMap = {
      octetstream: require('./plugins/octetstream.js'),
      querystring: require('./plugins/querystring.js'),
      multipart: require('./plugins/multipart.js'),
      json: require('./plugins/json.js'),
    };
    this.options.enabledPlugins.forEach((pluginName) => {
      const plgName = pluginName.toLowerCase();
      if (_pluginMap[plgName]) {
        this.use(_pluginMap[plgName]);
      } else {
        throw new Error('Unknown formidable plugin: ' + plgName);
      }
    });`

      contents = contents.replace(dynamicRequire, staticRequire)

      return { contents, loader: 'js' }
    })
  }
}

export default defineConfig({
  entry: ['src/index.ts'],
  format: ['cjs'],
  outDir: 'dist-exe',
  clean: true,
  // 将所有npm依赖内联打包，避免ESM模块在pkg中无法require的问题
  noExternal: [/.*/],
  platform: 'node',
  target: 'node18',
  // 不生成sourcemap和dts，减小体积
  sourcemap: false,
  dts: false,
  // 打包为单文件
  splitting: false,
  // 跳过node内置模块
  external: [],
  esbuildPlugins: [fixFormidablePlugin],
})
