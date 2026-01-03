from typing import Optional, Dict, List, Any
import pandas as pd

def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """Intelligently coerce column types for better chart detection."""
    df = df.copy()
    for c in df.columns:
        if "date" in c.lower() or "time" in c.lower() or "year" in c.lower() or "month" in c.lower():
            df[c] = pd.to_datetime(df[c], errors="coerce")
        else:
            df[c] = pd.to_numeric(df[c], errors="ignore")
    return df

def _is_low_cardinality(series: pd.Series, threshold: int = 10) -> bool:
    """Check if a series has low cardinality (good for pie charts)."""
    return series.nunique() <= threshold

def suggest_chart(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Suggest a Chart.js-compatible visualization based on DataFrame structure.
    
    Returns a dictionary with:
    - chart_type: 'line' | 'bar' | 'pie' | 'area'
    - labels: list of x-axis labels
    - datasets: list of dataset objects compatible with Chart.js
    """
    if df is None or df.empty:
        return None

    df = _coerce_types(df)
    cols = list(df.columns)

    # ---- Detect column types ----
    time_cols = [
        c for c in cols
        if pd.api.types.is_datetime64_any_dtype(df[c])
    ]

    numeric_cols = [
        c for c in cols
        if pd.api.types.is_numeric_dtype(df[c])
        and c not in time_cols
        and not c.lower().endswith("_id")
        and not c.lower().startswith("id")
    ]

    categorical_cols = [
        c for c in cols
        if c not in time_cols and c not in numeric_cols
    ]

    # ---- Chart Selection Logic ----

    # 🎯 PIE CHART: Single categorical + single numeric with low cardinality
    if len(categorical_cols) == 1 and len(numeric_cols) == 1:
        cat_col = categorical_cols[0]
        if _is_low_cardinality(df[cat_col]):
            return {
                "chart_type": "pie",
                "labels": df[cat_col].astype(str).tolist(),
                "datasets": [
                    {
                        "label": numeric_cols[0],
                        "data": df[numeric_cols[0]].tolist(),
                        "backgroundColor": [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)',
                            'rgba(199, 199, 199, 0.7)',
                            'rgba(83, 102, 255, 0.7)',
                            'rgba(255, 99, 255, 0.7)',
                            'rgba(99, 255, 132, 0.7)',
                        ],
                    }
                ],
            }

    # 📈 TIME-SERIES: Time column + metrics → Line or Area Chart
    if time_cols and numeric_cols:
        x_col = time_cols[0]
        labels = df[x_col].dt.strftime('%Y-%m-%d').tolist() if pd.api.types.is_datetime64_any_dtype(df[x_col]) else df[x_col].astype(str).tolist()
        
        # Multi-series support
        datasets = []
        colors = [
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)',
        ]
        
        for idx, metric in enumerate(numeric_cols):
            datasets.append({
                "label": metric,
                "data": df[metric].tolist(),
                "borderColor": colors[idx % len(colors)],
                "backgroundColor": colors[idx % len(colors)].replace('0.8', '0.2'),
                "tension": 0.4,
            })
        
        # Use area chart if multiple series or if data suggests cumulative trends
        chart_type = "area" if len(numeric_cols) > 1 else "line"
        
        return {
            "chart_type": chart_type,
            "labels": labels,
            "datasets": datasets,
        }

    # 📊 CATEGORY vs METRICS: Bar chart with multi-series support
    if categorical_cols and numeric_cols:
        x_col = categorical_cols[0]
        labels = df[x_col].astype(str).tolist()
        
        datasets = []
        colors = [
            'rgba(54, 162, 235, 0.8)',
            'rgba(255, 99, 132, 0.8)',
            'rgba(75, 192, 192, 0.8)',
            'rgba(153, 102, 255, 0.8)',
            'rgba(255, 159, 64, 0.8)',
        ]
        
        for idx, metric in enumerate(numeric_cols):
            datasets.append({
                "label": metric,
                "data": df[metric].tolist(),
                "backgroundColor": colors[idx % len(colors)],
            })
        
        return {
            "chart_type": "bar",
            "labels": labels,
            "datasets": datasets,
        }

    # 🔢 TWO NUMERIC COLUMNS: Line chart (correlation view)
    if len(numeric_cols) >= 2:
        return {
            "chart_type": "line",
            "labels": df[numeric_cols[0]].astype(str).tolist(),
            "datasets": [
                {
                    "label": numeric_cols[1],
                    "data": df[numeric_cols[1]].tolist(),
                    "borderColor": 'rgba(54, 162, 235, 0.8)',
                    "backgroundColor": 'rgba(54, 162, 235, 0.2)',
                    "tension": 0.4,
                }
            ],
        }

    return None