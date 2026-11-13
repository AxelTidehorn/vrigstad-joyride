// Builds the game (index.html) and the map (map.html) into dist/, one page at a time:
// vite-plugin-singlefile cannot inline a build with several pages.
// Then copies both to the repo root, which GitHub Pages serves until #45 deploys dist/ from CI.
import { copyFileSync } from 'node:fs';
import { build } from 'vite';

for (const [i, page] of ['index.html', 'map.html'].entries()) {
  await build({ build: { rollupOptions: { input: `src/${page}` }, emptyOutDir: i === 0 } });
  copyFileSync(`dist/${page}`, page);
}
