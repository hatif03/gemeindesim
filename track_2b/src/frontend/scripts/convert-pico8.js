/**
 * Convert pico8-sample.tmx (Tiled TMX XML) → pico8-city.json (Tiled JSON).
 * No npm dependencies — uses built-in Node.js modules only.
 */
const fs = require("fs");
const path = require("path");

const TMX_PATH = path.join(
  __dirname,
  "..",
  "public",
  "assets",
  "maps",
  "pico8-sample.tmx",
);
const OUT_PATH = path.join(
  __dirname,
  "..",
  "public",
  "assets",
  "maps",
  "pico8-city.json",
);

const xml = fs.readFileSync(TMX_PATH, "utf-8");

// Parse <map> attributes
function attr(tag, name) {
  const m = tag.match(new RegExp(`${name}="([^"]*)"`));
  return m ? m[1] : null;
}

const mapTag = xml.match(/<map[^>]*>/)[0];
const width = parseInt(attr(mapTag, "width"), 10);
const height = parseInt(attr(mapTag, "height"), 10);
const tilewidth = parseInt(attr(mapTag, "tilewidth"), 10);
const tileheight = parseInt(attr(mapTag, "tileheight"), 10);

// Parse <tileset> — we know there's one external TSX reference
const tilesetTag = xml.match(/<tileset[^>]*\/>/)[0];
const firstgid = parseInt(attr(tilesetTag, "firstgid"), 10);

// Read the TSX file to get tileset properties
// The TMX references "sample-sheet.tsx" relative to itself, but the actual
// file lives in the citymap_pico8 directory alongside the tileset image.
const tsxPath = path.join(
  __dirname,
  "..",
  "public",
  "assets",
  "citymap_pico8",
  "sample-sheet.tsx",
);
const tsxXml = fs.readFileSync(tsxPath, "utf-8");
const tsxTag = tsxXml.match(/<tileset[^>]*>/)[0];
const tilecount = parseInt(attr(tsxTag, "tilecount"), 10);
const columns = parseInt(attr(tsxTag, "columns"), 10);
const spacing = parseInt(attr(tsxTag, "spacing") || "0", 10);
const imageTag = tsxXml.match(/<image[^>]*\/>/)[0];
const imageWidth = parseInt(attr(imageTag, "width"), 10);
const imageHeight = parseInt(attr(imageTag, "height"), 10);

// Parse <layer> elements
const layerRegex =
  /<layer[^>]*>[\s\S]*?<data[^>]*>([\s\S]*?)<\/data>[\s\S]*?<\/layer>/g;
const layers = [];
let match;
const layerTags = xml.match(/<layer[^>]*>/g);
let layerIdx = 0;

while ((match = layerRegex.exec(xml)) !== null) {
  const layerTag = layerTags[layerIdx++];
  const name = attr(layerTag, "name");
  const id = parseInt(attr(layerTag, "id"), 10);
  const csvData = match[1].trim();

  const data = csvData
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
    .map((s) => parseInt(s, 10));

  layers.push({
    data,
    height,
    id,
    name,
    opacity: 1,
    type: "tilelayer",
    visible: true,
    width,
    x: 0,
    y: 0,
  });
}

// Build Tiled JSON output
const tiledJson = {
  compressionlevel: -1,
  height,
  infinite: false,
  layers,
  nextlayerid: layers.length + 1,
  nextobjectid: 1,
  orientation: "orthogonal",
  renderorder: "right-down",
  tiledversion: "1.8.2",
  tileheight,
  tilesets: [
    {
      columns,
      firstgid,
      image: "/assets/citymap_pico8/tilemap_packed.png",
      imageheight: imageHeight,
      imagewidth: imageWidth,
      margin: 0,
      name: "city-tileset",
      spacing,
      tilecount,
      tileheight,
      tilewidth,
    },
  ],
  tilewidth,
  type: "map",
  version: "1.8",
  width,
};

fs.writeFileSync(OUT_PATH, JSON.stringify(tiledJson, null, 2));
console.log(`Wrote ${OUT_PATH}`);
console.log(
  `  Map: ${width}x${height}, tile: ${tilewidth}x${tileheight}, spacing: ${spacing}`,
);
console.log(`  Layers: ${layers.map((l) => l.name).join(", ")}`);
console.log(`  Tileset: ${tilecount} tiles, ${columns} columns`);
