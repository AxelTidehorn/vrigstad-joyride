import { defineConfig } from 'vite';
import { cpSync, createReadStream, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { viteSingleFile } from 'vite-plugin-singlefile';

// The pages live in src/ (index.html is the game, map.html the map), because the repo root still holds
// the committed builds that GitHub Pages serves until #45. Each page builds to one self-contained file.
export default defineConfig({
  root: 'src',
  publicDir: false,
  // keep @license comments, so the bundled three.js keeps the MIT notice its licence asks for
  build: { outDir: '../dist', rolldownOptions: { output: { comments: { legal: true } } } },
  plugins: [viteSingleFile(), {
    name: 'vehicle-media',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const path = req.url?.split('?')[0];
        if (!path || !/^\/media\/vehicles\/[a-z0-9-]+\.glb$/.test(path)) return next();
        const file = resolve('.' + path);
        if (!existsSync(file)) return next();
        res.setHeader('Content-Type', 'model/gltf-binary');
        createReadStream(file).pipe(res);
      });
    },
    writeBundle(options) {
      if (options.dir) cpSync('media/vehicles', resolve(options.dir, 'media/vehicles'), { recursive: true });
    },
  }],
});
