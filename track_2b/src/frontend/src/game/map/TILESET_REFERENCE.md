# CCity Tileset Reference

## Tileset Info
- **Image:** `/assets/citymap_tilesets/CCity_mockup.png`
- **Size:** 640×256px
- **Grid:** 40 columns × 16 rows = 640 tiles
- **Tile size:** 16×16px
- **Margin:** 0, **Spacing:** 0
- **Tiled firstgid:** 1 (tile index 0 = GID 1 in Tiled JSON)

## Tile IDs (0-indexed, as used in tileset)

### Ground
| Element | Tile ID(s) | Notes |
|---------|-----------|-------|
| Grass | 0 | Single tile, fill for parks |
| Rock | 404, 405, 444, 445 | 2×2 group (2 cols × 2 rows) |
| Water (full) | 566 | Single tile, deep water fill |
| River edge (horizontal) | 490 | Land-to-water transition, x-axis |

### Roads
| Element | Tile ID(s) | Notes |
|---------|-----------|-------|
| Road X-axis (top lane) | 350 | Horizontal road, top half |
| Road X-axis (bottom lane) | 390 | Horizontal road, bottom half |
| Road Y-axis | 194, 195 | Vertical road, 2 tiles side by side |

### Buildings — ALL must be placed as groups (multi-tile)

#### Factory (4 wide × 3 tall)
```
Row 0: 226, 227, 228, 229
Row 1: 266, 267, 268, 269
Row 2: 306, 307, 308, 309
```

#### Shop #1 (2 wide × 4 tall)
```
Row 0: 176, 177
Row 1: 216, 217
Row 2: 256, 257
Row 3: 296, 297
```

#### Shop #2 (2 wide × 2 tall)
```
Row 0: 248, 249
Row 1: 288, 289
```

#### Long Shop (4 wide × 2 tall)
```
Row 0: 252, 253, 254, 255
Row 1: 292, 293, 294, 295
```

#### House (2 wide × 2 tall)
```
Row 0: 270, 271
Row 1: 310, 311
```

#### Hospital (4 wide × 4 tall, top rows mix with grass)
```
Row 0: 178, 179, 180, 181
Row 1: 218, 219, 220, 221
Row 2: 258, 259, 260, 261
Row 3: 298, 299, 300, 301
```

#### Concrete Building (4 wide × 4 tall, top rows mix with grass)
```
Row 0: 164, 165, 166, 167
Row 1: 204, 205, 206, 207
Row 2: 244, 245, 246, 247
Row 3: 284, 285, 286, 287
```

### Ground / Paving
| Element | Tile ID(s) | Notes |
|---------|-----------|-------|
| Gray concrete floor | 290, 291 | 1×2 pair, use for parking lots and plazas |
| Parking (car facing north) | 250, 251 | 1×2 pair, car in parking space |

### Road Details
| Element | Tile ID(s) | Notes |
|---------|-----------|-------|
| Road top edge | 350 | Horizontal road, top lane |
| Road bottom edge | 390 | Horizontal road, bottom lane |
| Road (no edge) | 354 | Plain road fill (interior) |
| Road bottom-right corner | 395 | Corner piece |
| Crossing X-axis | 282, 283 | Pedestrian crossing, horizontal |
| Crossing Y-axis (right) | 321, 361 | Pedestrian crossing, vertical right |
| Crossing Y-axis (left) | 324, 364 | Pedestrian crossing, vertical left |

### Nature
| Element | Tile ID(s) | Notes |
|---------|-----------|-------|
| Tree | 356, 357, 396, 397 | 2×2 group (2 cols × 2 rows) |

## Tiled JSON GID Conversion
In Tiled JSON format, add 1 to all tile IDs above (firstgid = 1).
- Grass 0 → GID 1
- Road top 350 → GID 351
- Factory 226 → GID 227
- etc.

Use GID 0 for empty/transparent tiles.

## Map Layout Plan (40×30 grid)
- Rows 0-2: Park (grass + trees + rocks)
- Rows 3-4: Horizontal road
- Rows 5-8: Government (city hall = large building) + residential houses
- Rows 9-10: Horizontal road
- Rows 11-16: Commercial district (shops along road, houses in blocks)
- Rows 17-18: Horizontal road
- Rows 19-24: Industrial zone (factories) + worker housing
- Rows 25-26: Horizontal road
- Rows 27-28: Riverbank (grass + river edge)
- Row 29: Water
- Vertical roads at cols 5-6, 19-20, 33-34
