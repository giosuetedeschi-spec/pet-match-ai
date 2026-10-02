# ISTAT municipality reference data

`comuni_istat_2026.csv` contains the 7,894 municipalities listed by ISTAT on 21 February 2026 and representative coordinates calculated from ISTAT's generalized administrative boundaries dated 1 January 2026.

Sources:

- [ISTAT municipality list](https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx)
- [ISTAT generalized boundaries](https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/2026/Limiti01012026_g.zip)
- [ISTAT open data terms](https://www.istat.it/dati/open-data/)

The source boundaries predate two changes reflected in the current list. The build script combines Lirio with Montalto Pavese and Castegnero with Nanto before calculating centroids. Coordinates are centroids in WGS84 derived from the boundary file's WGS84 UTM zone 32N projection. The CSV contains no postal codes; CAP data is a separate source and can be added after its coverage and reuse terms are verified.

To rebuild, download both source files and run:

```powershell
uv pip install --python .venv\Scripts\python.exe pyshp pyproj shapely openpyxl
.venv\Scripts\python.exe scripts\build_comuni_istat.py `
  --boundaries C:\path\to\Limiti01012026_g.zip `
  --municipalities C:\path\to\Elenco-comuni-italiani.xlsx
```

The original source archives are not committed; only the normalized CSV is tracked.
