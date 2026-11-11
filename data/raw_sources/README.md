# Original Data Sources: ISTAC Statistical Operation C00022A

## Source Metadata

* **Operation Name**: Electrical Energy Statistics (*Estadística de Energía Eléctrica* - `C00022A`).
* **Publisher**: Canary Islands Statistics Institute (ISTAC) - Government of the Canary Islands.
* **Official Portal**: [https://www.gobiernodecanarias.org/istac/operaciones/C00022A.html](https://www.gobiernodecanarias.org/istac/operaciones/C00022A.html)
* **REST API**: `https://datos.canarias.es/api/estadisticas/statistical-resources/v1.0/datasets/ISTAC/`
* **License**: Open Data of the Government of the Canary Islands (Public Sector Information Reuse).
* **Geographic Scope**: Canary Islands (Archipelago and individual islands).
* **Load Mode**: Pure ELT extraction via REST API (CSV) into the PostgreSQL `raw` schema.

## Datasets Ingested into `raw`

1. **`raw.c00022a_000001`**: Final electricity consumption and customer count (CUPS) by sector and island (2010–2019).
2. **`raw.c00022a_000002`**: Final electricity consumption and customer count (CUPS) by sector and island (2020–present).
3. **`raw.c00022a_000004`**: Electrical balance (gross production, internal demand, and final consumption) by period and island.
4. **`raw.c00022a_000007`**: Net electricity generation by energy source and electrical system.
5. **`raw.c00022a_000008`**: Net electricity generation by energy source per island and period.

