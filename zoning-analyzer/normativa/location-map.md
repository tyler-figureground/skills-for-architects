# Location Map — nomloccat to TONE Sector/Zone

Maps `nomloccat` values from the Maldonado GIS cadastral portal to TONE sectors and normativa files.

## Mapped Locations

| nomloccat | Región | Título | Capítulo | Sector | Normativa File |
|-----------|--------|--------|----------|--------|----------------|
| LA BARRA | La Barra y José Ignacio | III | II | 1 | titulo-iii-cap-ii-sector-1.md |
| MANANTIALES | La Barra y José Ignacio | III | II | 1 | titulo-iii-cap-ii-sector-1.md |
| JOSE IGNACIO | La Barra y José Ignacio | III | III | 2 | titulo-iii-cap-iii-sector-2.md |
| FARO DE JOSE IGNACIO | La Barra y José Ignacio | III | III | 2 | titulo-iii-cap-iii-sector-2.md |
| LA JUANITA | La Barra y José Ignacio | III | III | 2 | titulo-iii-cap-iii-sector-2.md |
| PUNTA DEL ESTE | Maldonado - Punta del Este | II | II | 1 | (not yet created) |
| MALDONADO | Maldonado - Punta del Este | II | II | 2 | titulo-ii-cap-ii-sector-2.md |
| PIRIAPOLIS | Piriápolis y Solís | IV | II | 1 | (not yet created) |
| SAN CARLOS | Centros Poblados no Balnearios | V | I | 1 | titulo-v-cap-i-sector-1.md |
| GARZON | Otros Centros Poblados no Balnearios | V | II | 2 | titulo-v-cap-ii-sector-2.md |
| AIGUA | Otros Centros Poblados no Balnearios | V | II | 2 | titulo-v-cap-ii-sector-2.md |
| PAN DE AZUCAR | Otros Centros Poblados no Balnearios | V | II | 2 | titulo-v-cap-ii-sector-2.md |

## Digesto Section Index Pages

These are the index pages for each sector's zoning articles:

| Sector | Section URL |
|--------|-------------|
| Sector 1 — La Barra y Manantiales | https://digesto.maldonado.gub.uy/index.php/armado-seccion/966 |
| Sector 1 — San Carlos | https://digesto.maldonado.gub.uy/index.php/armado-seccion/1002 |
| Sector 2 — Maldonado | https://digesto.maldonado.gub.uy/index.php/armado-seccion/961 |
| Sector 2 — Otros Centros Poblados (Garzón, Aiguá, Pan de Azúcar) | https://digesto.maldonado.gub.uy/index.php/armado-seccion/1005 |
| Sector 2 — José Ignacio | https://digesto.maldonado.gub.uy/index.php/armado-seccion/967 |

## Notes

- `nomloccat` values from GIS are UPPERCASE
- Some localities share a sector (e.g., La Barra and Manantiales are both Sector 1)
- Unmapped locations should trigger a search of the digesto website
- After fetching new normativa, update this file with the new mapping
