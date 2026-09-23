# starmap/data — 星官数据资产 (Chinese asterisms)

`asterisms.json` holds real constellation shapes from the 三垣二十八宿 /
步天歌 tradition, for use by the home starmap (skill-domain → 星官 mapping
and the goal-dipper geometry).

## Schema

```jsonc
{
  "$schema": "asterisms.v1",
  "provenance": "…",
  "asterisms": [
    {
      "id": "beidou",            // ascii slug, stable key for code
      "name_zh": "北斗",          // 星官中文名
      "lore": "天枢·北斗之首…",     // 一句小传
      "stars": [
        { "x": -0.6456, "y": 0.4576, "mag": 1.81, "name": "天枢" }
        // x, y: normalized unit coords (see below)
        // mag: Hipparcos V magnitude (optional)
        // name: individual star name, only where the UI needs to
        //       address stars by name (currently 北斗's 天枢…摇光)
      ],
      "lines": [[0, 1], [1, 2]]   // index pairs into stars[]
    }
  ]
}
```

## Provenance

- **Asterism membership + line topology**: Stellarium `skycultures/chinese`
  (`index.json`), © Stellarium project, CC BY-SA 4.0 —
  <https://github.com/Stellarium/stellarium/tree/master/skycultures/chinese>.
  Each Stellarium "constellation" entry is one 星官: HIP star ids along
  polyline segments.
- **Star positions / magnitudes**: Hipparcos Main Catalogue (ESA, CDS I/239,
  J2000 epoch/equinox) — <https://cdsarc.cds.unistra.fr/ftp/cats/I/239/>.
  Star positions are astronomical facts, not copyrightable.

## Coordinate pipeline

1. Resolve each HIP id to RA/Dec (deg, J2000) from `hip_main.dat`
   (fields 9/10; stars without an astrometric solution, e.g. HIP 55203 in
   三台, fall back to the hms/dms fields 4/5).
2. Gnomonic (tangent-plane) projection about the asterism's centroid —
   x = east, y = north — so wide circumpolar figures (紫微垣 walls) are not
   distorted by a naive RA/Dec-as-plane mapping.
3. Normalize per asterism: subtract the projected centroid (so the centroid
   is the origin — the starmap composes 北斗环卫帝星 by centering each
   figure on its own centroid), then scale so the max radius = 1, preserving
   aspect ratio. Coordinates are rounded to 4 decimals.

## Adding / refreshing asterisms

The generator is a one-off script (not shipped); to add more 星官:

1. Download Stellarium's `skycultures/chinese/index.json` and CDS I/239
   `hip_main.dat`.
2. Pick the 星官 by its `common_name.native` (e.g. `轩辕`), collect unique
   HIP ids along its `lines` segments (first-appearance order), apply the
   pipeline above, and append an entry with an ascii `id`, `name_zh`, and a
   one-line `lore`.
3. Keep `lines` as index pairs into `stars` (split each polyline segment
   into consecutive pairs).
4. Run `npm run test` — `asterisms.test.ts` validates the shape.

Selection here: 紫微垣核心 (北极/勾陈/北斗/左右垣/华盖/文昌/三台/五帝内座),
太微垣 (左右垣/五帝座), 天市垣 (左右垣), and 二十八宿亮官
(角/亢/心/斗/奎/毕/参/柳) — 22 figures total.
