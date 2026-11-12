# Vrigstad Joyride

A small open-world driving game set in the real village of Vrigstad, Sweden (57.3555° N, 14.4756° E), plus the 3D map it grew out of. Everything runs in the browser from a single HTML file.

- **`index.html`** is the game. Walk around, steal a Volvo 240, a Saab 900, an EPA-traktor or a tractor, and outrun the police.
- **`map.html`** is an interactive 3D terrain model of the same 2.2 × 2.2 km area.

## Play

Open `index.html` in a browser. It needs WebGL and an internet connection the first time (three.js and the fonts load from a CDN).

| Action | Keyboard | Phone |
|---|---|---|
| Move / drive | W A S D or arrows | Left stick |
| Steal / get out | E | Use button |
| Sprint / brake | Shift / Space | Stick sprints on foot / Brake button |
| Look around | Drag the view | Drag the view |
| Back to Torget | R | |

Taking an occupied car always earns a wanted star; a parked one sometimes does. Each star (up to three) sends a police car. Stay about 170 m clear of them for 18 seconds and they give up. Get boxed in at low speed and you are *gripen* and sent back to Torget.

## How it is built

```
src/game.html      game source (HTML, CSS, JS) with a /*DATA*/ placeholder
src/map.html       3D map source, same placeholder
data/raw/          OpenStreetMap extract (osm.json) and one elevation tile (tile.png)
data/vrigstad.json processed data: buildings, roads, water, land use, 25 m elevation grid
tools/fetch.sh     re-downloads data/raw from the Overpass API and Mapzen terrain tiles
tools/process.py   projects and clips the raw data into data/vrigstad.json
tools/build.py     runs process.py and writes index.html and map.html
```

Rebuild after changing anything in `src/`:

```sh
python3 tools/build.py
```

Refresh the map data first with `tools/fetch.sh` if you want the latest OpenStreetMap edits. Only the Python standard library is needed.

## Known simplifications

- Building heights are guessed from footprint size; the source data has none.
- Buildings are flat-roofed boxes.
- Traffic ignores one-way streets and roundabout direction.
- Only six woodland areas are mapped in the source, so the surroundings look more open than they are.

## License

All rights reserved. The game and map code are not open source; see [LICENSE](LICENSE) for what you may do. Third-party data and libraries keep their own licenses, listed there.

## Data credits

- Map data © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors, available under the Open Database License.
- Elevation from Mapzen terrain tiles (terrarium format) hosted on AWS Open Data.
