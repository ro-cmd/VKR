# Archaeological Mapping Toolkit

Набор для археологической топосъёмки на основе табличных данных (CSV с координатами N/E/Z и кодами точек). Поддерживает очистку данных, контроль качества, построение линий и плоскостей, экспорт в GIS-форматы и создание 2D/3D визуализаций.

## Быстрый старт

### 1. Установка окружения (рекомендуется)

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Для веб-версии достаточно зависимостей из `requirements.txt` без PySide6. Десктопное приложение требует полный набор, включая `PySide6`.

### 2. Запуск через конфиг

```bash
python archaeo_mapper.py --config config.ini
```

### 3. Запуск с параметрами

```bash
python archaeo_mapper.py --input sample_survey.csv --crs EPSG:3857 --output-dir output
```

### 4. Десктопное приложение

```bash
python desktop_app.py
```

### 5. Веб-приложение

```bash
cd web_app
python app.py
```

Откройте в браузере:

- **Windows / Linux:** http://127.0.0.1:5000
- **macOS:** http://127.0.0.1:5001 — порт 5000 часто занят системой (AirPlay Receiver)

---

## Формат входных данных

CSV (или XLSX) должен содержать столбцы:

| Столбец     | Описание                                      |
|-------------|-----------------------------------------------|
| PointID     | Идентификатор точки                           |
| N           | Northing (северная координата)                |
| E           | Easting (восточная координата)                |
| Z           | Высота (отметка)                              |
| Code        | Код точки (BASE, STAIN_01, EXC_01, FIND_*, …) |
| Description | Описание (необязательно)                      |

Поддерживаются альтернативные названия: `X`→`E`, `Y`→`N`, `Easting`, `Northing`, `Elevation`, `Height`, `ID`→`PointID`, `CodeType`→`Code`.

Кодировка: система сама определяет кодировку файла. Поддерживаются UTF-8, CP1251, Latin-1.

---

## Выходные файлы (`output/`)

| Файл                     | Описание |
|--------------------------|----------|
| points.geojson           | Точки в GeoJSON |
| lines.geojson            | Линии по кодам |
| planes.geojson           | Плоскости раскопов |
| GEOJSON_README.txt       | Описание формата координат (порядок E/N) |
| summary.csv              | Сводка по кодам (count, min_z, max_z, mean_z) |
| quality.json             | Сводный отчёт качества |
| quality_issues.csv       | Подробный список проблемных точек |
| report.xlsx              | Excel: Summary + Quality + Quality_Issues |
| input_load_report.csv    | Отчёт загрузки (коды и переименования) |
| plan_2d.png              | Статичный 2D план |
| plan_3d.png              | Статичный 3D вид |
| plan_3d_interactive.html | Интерактивная 3D-сцена |
| plan_2d_map.html         | Интерактивная 2D-карта (SVG) |

---

## Показатели `quality.json`

| Поле                 | Описание |
|----------------------|----------|
| total_rows           | Всего строк |
| duplicate_point_id   | Дубликаты PointID |
| duplicate_coordinates| Совпадения E, N, Z |
| z_outliers           | Выбросы по высоте (σ) |
| max_planar_jump      | Макс. скачок между соседями (м) |
| planar_jump_exceed   | Превышения скачка |
| min_point_spacing    | Минимальный шаг (м) |
| spacing_violations   | Нарушения расстояния |

Пороги настраиваются в `config.ini` в секции `[quality]` или аргументами `--max-planar-jump`, `--min-point-spacing`.

## `quality_issues.csv`

Основные поля: `issue_type`, `PointID`, `PointID_neighbor`, `Code`, `value`, `threshold`, `reason`. Типы: `z_outlier`, `planar_jump`, `spacing_violation`, `duplicate_point_id`, `duplicate_coordinates`.

---

## GeoJSON: порядок координат

- `geometry.coordinates`: **[Easting, Northing]** — порядок [E, N]
- `properties.N`, `properties.E` — те же значения
- Для корректного отображения в QGIS и других GIS-системах CRS в файле должен быть указан (EPSG:3857 и др.)

Подробнее см. `output/GEOJSON_README.txt`.

---

## Конфигурация (`config.ini`)

- `[input]` — путь, кодировка, CRS
- `[output]` — папка, форматы (gpkg, geojson, shp)
- `[processing]` — connect_codes, коды раскопов
- `[quality]` — max_z_sigma, max_planar_jump, min_point_spacing
- `[plots]` — заголовок, basemap, interactive_3d

---

## Структура проекта

```
Roma_VKR/
├── archaeo_mapper.py    # CLI
├── desktop_app.py       # PySide6 GUI
├── web_app/app.py       # Flask
├── config.ini
├── app_config.json      # для desktop
├── sample_survey.csv
├── output/              # результаты CLI
├── output_web/          # результаты веб-версии
├── archaeo/
│   ├── io.py            # загрузка CSV/XLSX
│   ├── crs.py           # преобразование CRS
│   ├── processing.py    # линии, плоскости
│   ├── quality.py       # контроль качества
│   ├── plots.py         # 2D/3D визуализация
│   ├── exporting.py     # экспорт (GeoJSON, Excel)
│   └── config.py
└── requirements.txt
```

---

## Советы

- При больших координатах (порядка ~1000–2000 м) CRS нужно задавать явно. Укажите `EPSG:3857` или нужный код в config.
- Если в `input_load_report.csv` появляются **переименования** столбцов — проверьте соответствие output.
- Качество данных на входе напрямую влияет на корректность построений.

