import io
import base64
import os
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Set headless backend for matplotlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from backend.models.schemas import MatplotlibPlot

# Professional Modern Palette
PLOT_COLORS = ['#2563eb', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4']

def _fig_to_base64(fig) -> str:
    """Converts a matplotlib figure to base64 data URI and closes it."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"

def generate_matplotlib_plots(records: Any, columns: Optional[List[str]] = None) -> List[MatplotlibPlot]:
    """
    Generates advanced scientific Matplotlib statistical & cluster plots.
    CRITICAL: Only generates plots if meaningful numerical features / distributions exist (>= 2 rows).
    Otherwise returns an empty list (completely hidden).
    """
    if not records or not isinstance(records, list) or len(records) < 2:
        return []

    try:
        df = pd.DataFrame(records)
    except Exception:
        return []

    if df.empty or len(df.columns) == 0:
        return []

    # 1. Detect clean numeric columns (>= 2 non-null values)
    numeric_cols: Dict[str, pd.Series] = {}
    for col in df.columns:
        col_str = str(col)
        # Skip IDs
        if any(k in col_str.lower() for k in ["_id", "id_", "identifier", "ssn", "passport", "phone", "zip", "postal"]):
            continue
        try:
            cleaned_series = pd.to_numeric(
                df[col].astype(str).str.replace(r"[₹\$€£¥,\s%]", "", regex=True),
                errors="coerce"
            ).dropna()
            if len(cleaned_series) >= 2 and cleaned_series.nunique() >= 2:
                numeric_cols[col_str] = cleaned_series
        except Exception:
            continue

    plots: List[MatplotlibPlot] = []

    # Plot 1: K-Means Cluster Analysis (if >= 2 numeric columns and >= 3 rows)
    num_keys = list(numeric_cols.keys())
    if len(num_keys) >= 2 and len(df) >= 3:
        try:
            col_x, col_y = num_keys[0], num_keys[1]
            sub_df = pd.DataFrame({col_x: numeric_cols[col_x], col_y: numeric_cols[col_y]}).dropna()
            
            if len(sub_df) >= 3:
                from sklearn.cluster import KMeans
                k = min(3, len(sub_df) // 2) if len(sub_df) >= 4 else 2
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(sub_df[[col_x, col_y]])
                sub_df['Cluster'] = kmeans.labels_

                fig, ax = plt.subplots(figsize=(6.5, 4.2), dpi=120)
                for c in range(k):
                    pts = sub_df[sub_df['Cluster'] == c]
                    ax.scatter(
                        pts[col_x], pts[col_y],
                        color=PLOT_COLORS[c % len(PLOT_COLORS)],
                        label=f'Cluster {c + 1} (n={len(pts)})',
                        s=55, alpha=0.85, edgecolors='none'
                    )

                # Centroids
                ax.scatter(
                    kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1],
                    color='#dc2626', marker='X', s=130, label='Centroids', zorder=5
                )

                ax.set_title(f"Cluster Analysis: {col_x.title()} vs {col_y.title()}", fontsize=11, fontweight='bold', pad=10)
                ax.set_xlabel(col_x.title(), fontsize=9, fontweight='normal')
                ax.set_ylabel(col_y.title(), fontsize=9, fontweight='normal')
                ax.grid(True, linestyle='--', alpha=0.4)
                ax.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=8)
                plt.tight_layout()

                img_data = _fig_to_base64(fig)
                plots.append(MatplotlibPlot(
                    id=f"plot_cluster_{col_x}_{col_y}".lower(),
                    title=f"K-Means Cluster Plot ({col_x.title()} vs {col_y.title()})",
                    description=f"Automated clustering partitioning {len(sub_df)} records into {k} statistical clusters.",
                    plot_type="cluster",
                    image_base64=img_data,
                    columns_analyzed=[col_x, col_y]
                ))
        except Exception:
            pass

    # Plot 2: Correlation Matrix Heatmap (if >= 2 numeric columns)
    if len(num_keys) >= 2:
        try:
            numeric_matrix = pd.DataFrame({k: numeric_cols[k] for k in num_keys[:5]}).dropna()
            if len(numeric_matrix) >= 2 and len(numeric_matrix.columns) >= 2:
                corr = numeric_matrix.corr()
                
                fig, ax = plt.subplots(figsize=(5.5, 4.2), dpi=120)
                cax = ax.matshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
                fig.colorbar(cax, fraction=0.046, pad=0.04)

                ax.set_xticks(range(len(corr.columns)))
                ax.set_yticks(range(len(corr.columns)))
                ax.set_xticklabels([c.title() for c in corr.columns], rotation=45, ha='left', fontsize=8)
                ax.set_yticklabels([c.title() for c in corr.columns], fontsize=8)

                for i in range(len(corr.columns)):
                    for j in range(len(corr.columns)):
                        val = corr.iloc[i, j]
                        ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="black" if abs(val) < 0.7 else "white", fontsize=8, fontweight='bold')

                ax.set_title("Correlation Matrix Heatmap", fontsize=11, fontweight='bold', pad=25)
                plt.tight_layout()

                img_data = _fig_to_base64(fig)
                plots.append(MatplotlibPlot(
                    id="plot_correlation_heatmap",
                    title="Correlation Matrix Heatmap",
                    description=f"Linear correlation coefficients across {len(corr.columns)} numerical dimensions.",
                    plot_type="correlation",
                    image_base64=img_data,
                    columns_analyzed=list(corr.columns)
                ))
        except Exception:
            pass

    # Plot 3: Numerical Distribution & Boxplot (for up to 2 numeric columns)
    for col_name in num_keys[:2]:
        series = numeric_cols[col_name]
        if len(series) >= 3:
            try:
                fig, (ax_box, ax_hist) = plt.subplots(
                    2, 1, figsize=(6, 4.2), dpi=120,
                    gridspec_kw={'height_ratios': [0.28, 0.72]},
                    sharex=True
                )

                # Top: Horizontal Boxplot
                ax_box.boxplot(series, vert=False, patch_artist=True,
                               boxprops=dict(facecolor='#dbeafe', color='#2563eb'),
                               medianprops=dict(color='#dc2626', linewidth=1.8),
                               whiskerprops=dict(color='#2563eb'),
                               capprops=dict(color='#2563eb'),
                               flierprops=dict(marker='o', color='#ef4444', markersize=4))
                ax_box.set_yticks([])
                ax_box.grid(True, linestyle='--', alpha=0.3)
                ax_box.set_title(f"Distribution & Quartiles: {col_name.title()}", fontsize=11, fontweight='bold', pad=8)

                # Bottom: Histogram
                n_bins = min(10, max(4, len(series) // 2))
                ax_hist.hist(series, bins=n_bins, color='#3b82f6', edgecolor='white', alpha=0.85)
                ax_hist.axvline(series.mean(), color='#10b981', linestyle='--', linewidth=1.5, label=f'Mean: {series.mean():.1f}')
                ax_hist.axvline(series.median(), color='#dc2626', linestyle='-', linewidth=1.5, label=f'Median: {series.median():.1f}')
                ax_hist.set_xlabel(col_name.title(), fontsize=9, fontweight='normal')
                ax_hist.set_ylabel("Frequency", fontsize=9, fontweight='normal')
                ax_hist.grid(True, linestyle='--', alpha=0.4)
                ax_hist.legend(frameon=True, facecolor='white', framealpha=0.9, fontsize=8)

                plt.tight_layout()
                img_data = _fig_to_base64(fig)
                plots.append(MatplotlibPlot(
                    id=f"plot_dist_{col_name}".lower(),
                    title=f"{col_name.title()} Distribution & Outlier Boxplot",
                    description=f"Histogram distribution curve and quartile boxplot for {col_name.title()}.",
                    plot_type="distribution",
                    image_base64=img_data,
                    columns_analyzed=[col_name]
                ))
            except Exception:
                pass

    return plots
