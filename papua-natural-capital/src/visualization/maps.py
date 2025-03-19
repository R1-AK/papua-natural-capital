#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Mapping and visualization functions for the Papua Natural Capital Assessment.

This module provides functions for creating maps, charts, and other visualizations
of spatial data related to ecosystem services and natural capital.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.plot import show
from rasterio.mask import mask
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import matplotlib.ticker as mticker
from matplotlib.gridspec import GridSpec
import contextily as ctx

# Set default styling
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']

# Custom color maps
CARBON_CMAP = LinearSegmentedColormap.from_list(
    'carbon_cmap', ['#FFFFE0', '#C5E88F', '#78AB46', '#2A8C3A', '#0F5322']
)

IMPACT_CMAP = LinearSegmentedColormap.from_list(
    'impact_cmap', ['#FF3333', '#FFCC33', '#FFFF99', '#99CC66', '#009966']
)

def create_carbon_map(carbon_raster_path, output_path, admin_boundary=None, 
                      mining_areas=None, title="Carbon Storage (Mg/ha)", 
                      cmap=CARBON_CMAP, add_basemap=False):
    """
    Create a map of carbon storage.
    
    Parameters:
    -----------
    carbon_raster_path : str
        Path to the carbon raster file
    output_path : str
        Path to save the output map
    admin_boundary : GeoDataFrame, optional
        Administrative boundary to display on the map
    mining_areas : GeoDataFrame, optional
        Mining areas to highlight on the map
    title : str, optional
        Title for the map
    cmap : matplotlib.colors.Colormap, optional
        Colormap to use for the raster display
    add_basemap : bool, optional
        Whether to add a basemap from contextily
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Load and display the carbon raster
    with rasterio.open(carbon_raster_path) as src:
        carbon_data = src.read(1)
        
        # Calculate min and max for color scaling, excluding NoData values
        valid_data = carbon_data[carbon_data > 0]
        vmin = np.percentile(valid_data, 1)  # 1st percentile to avoid outliers
        vmax = np.percentile(valid_data, 99)  # 99th percentile to avoid outliers
        
        # Display the raster
        im = show(src, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax, title="")
    
    # Add administrative boundary if provided
    if admin_boundary is not None:
        admin_boundary.boundary.plot(ax=ax, color='black', linewidth=1, alpha=0.7)
    
    # Add mining areas if provided
    if mining_areas is not None:
        mining_areas.boundary.plot(ax=ax, color='red', linewidth=1)
        # Add centroids with labels
        if 'name' in mining_areas.columns:
            for idx, row in mining_areas.iterrows():
                ax.annotate(row['name'], xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                           xytext=(3, 3), textcoords="offset points", 
                           fontsize=8, color='red', weight='bold')
    
    # Add basemap if requested
    if add_basemap:
        try:
            ctx.add_basemap(ax, crs=admin_boundary.crs.to_string() if admin_boundary is not None else None,
                          source=ctx.providers.OpenStreetMap.Mapnik)
        except Exception as e:
            print(f"Warning: Could not add basemap: {e}")
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label('Carbon Storage (Mg/ha)')
    
    # Add title and labels
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    # Add scale bar and north arrow (simplified)
    # In a real project, you'd add a proper scale bar with distance calculations
    ax.annotate('N', xy=(0.98, 0.98), xycoords='axes fraction', 
               fontsize=12, fontweight='bold', ha='center', va='center')
    ax.annotate('↑', xy=(0.98, 0.95), xycoords='axes fraction',
               fontsize=16, ha='center', va='center')
    
    # Add legend for mining areas
    if mining_areas is not None:
        legend_elements = [
            Patch(facecolor='red', edgecolor='black', alpha=0.8, label='Mining Concession')
        ]
        ax.legend(handles=legend_elements, loc='lower right')
    
    # Improve layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_comparison_map(baseline_raster, scenario_raster, output_path, 
                         admin_boundary=None, title="Change in Carbon Storage",
                         cmap=IMPACT_CMAP):
    """
    Create a comparison map between baseline and scenario.
    
    Parameters:
    -----------
    baseline_raster : str
        Path to the baseline raster
    scenario_raster : str
        Path to the scenario raster
    output_path : str
        Path to save the output map
    admin_boundary : GeoDataFrame, optional
        Administrative boundary to display on the map
    title : str, optional
        Title for the map
    cmap : matplotlib.colors.Colormap, optional
        Colormap to use for the difference display
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Load the rasters
    with rasterio.open(baseline_raster) as baseline_src:
        baseline_data = baseline_src.read(1)
        meta = baseline_src.meta
        
    with rasterio.open(scenario_raster) as scenario_src:
        scenario_data = scenario_src.read(1)
    
    # Calculate difference
    diff_data = scenario_data - baseline_data
    
    # Calculate min and max for color scaling, excluding NoData values
    valid_data = diff_data[np.logical_and(baseline_data > 0, scenario_data > 0)]
    vmin = np.percentile(valid_data, 1)  # 1st percentile to avoid outliers
    vmax = np.percentile(valid_data, 99)  # 99th percentile to avoid outliers
    
    # Ensure symmetric color scale for better visualization of changes
    abs_max = max(abs(vmin), abs(vmax))
    vmin = -abs_max
    vmax = abs_max
    
    # Create a temporary file for the difference raster
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
    
    # Write the difference raster to a temporary file
    with rasterio.open(tmp_path, 'w', **meta) as dst:
        dst.write(diff_data, 1)
    
    # Display the difference raster
    with rasterio.open(tmp_path) as src:
        im = show(src, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax, title="")
    
    # Remove temporary file
    os.remove(tmp_path)
    
    # Add administrative boundary if provided
    if admin_boundary is not None:
        admin_boundary.boundary.plot(ax=ax, color='black', linewidth=1, alpha=0.7)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.7)
    cbar.set_label('Change in Carbon Storage (Mg/ha)')
    
    # Add title and labels
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    
    # Improve layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_multi_panel_map(raster_paths, titles, output_path, admin_boundary=None,
                           mining_areas=None, cmap=CARBON_CMAP, main_title=None):
    """
    Create a multi-panel map with multiple rasters.
    
    Parameters:
    -----------
    raster_paths : list of str
        Paths to the raster files
    titles : list of str
        Titles for each panel
    output_path : str
        Path to save the output map
    admin_boundary : GeoDataFrame, optional
        Administrative boundary to display on the map
    mining_areas : GeoDataFrame, optional
        Mining areas to highlight on the map
    cmap : matplotlib.colors.Colormap, optional
        Colormap to use for the raster display
    main_title : str, optional
        Main title for the entire figure
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Determine the grid layout based on number of panels
    n_panels = len(raster_paths)
    if n_panels <= 2:
        rows, cols = 1, n_panels
    elif n_panels <= 4:
        rows, cols = 2, 2
    else:
        rows, cols = (n_panels + 2) // 3, 3  # Ceiling division
    
    # Create figure and axes
    fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 5*rows))
    
    # Flatten axes array for easier indexing
    if n_panels > 1:
        axes = axes.flatten()
    else:
        axes = [axes]
    
    # Process each raster
    for i, (raster_path, title) in enumerate(zip(raster_paths, titles)):
        if i >= len(axes):
            break
            
        ax = axes[i]
        
        # Load and display the raster
        with rasterio.open(raster_path) as src:
            raster_data = src.read(1)
            
            # Calculate min and max for color scaling, excluding NoData values
            valid_data = raster_data[raster_data > 0]
            vmin = np.percentile(valid_data, 1)  # 1st percentile to avoid outliers
            vmax = np.percentile(valid_data, 99)  # 99th percentile to avoid outliers
            
            # Display the raster
            im = show(src, ax=ax, cmap=cmap, vmin=vmin, vmax=vmax, title="")
        
        # Add administrative boundary if provided
        if admin_boundary is not None:
            admin_boundary.boundary.plot(ax=ax, color='black', linewidth=0.5, alpha=0.7)
        
        # Add mining areas if provided
        if mining_areas is not None:
            mining_areas.boundary.plot(ax=ax, color='red', linewidth=0.5)
        
        # Add title
        ax.set_title(title, fontsize=12)
        
        # Remove axis labels for cleaner look
        ax.set_xticks([])
        ax.set_yticks([])
    
    # Hide any unused axes
    for i in range(n_panels, len(axes)):
        axes[i].set_visible(False)
    
    # Add a single colorbar at the bottom
    if n_panels > 0:
        cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.02])  # [left, bottom, width, height]
        cbar = fig.colorbar(im, cax=cbar_ax, orientation='horizontal')
        cbar.set_label('Carbon Storage (Mg/ha)')
    
    # Add main title if provided
    if main_title:
        fig.suptitle(main_title, fontsize=16, fontweight='bold', y=0.98)
    
    # Improve layout and save
    plt.tight_layout(rect=[0, 0.07, 1, 0.95])  # Make room for the colorbar and main title
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    return fig

def create_carbon_distribution_chart(carbon_data_dict, output_path, 
                                    title="Distribution of Carbon Storage"):
    """
    Create a chart comparing carbon storage distributions across different areas.
    
    Parameters:
    -----------
    carbon_data_dict : dict
        Dictionary mapping area names to carbon data arrays
    output_path : str
        Path to save the output chart
    title : str, optional
        Title for the chart
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set color palette
    palette = sns.color_palette("viridis", len(carbon_data_dict))
    
    # Plot distribution for each area
    for (area_name, carbon_data), color in zip(carbon_data_dict.items(), palette):
        sns.kdeplot(carbon_data, label=area_name, color=color, fill=True, alpha=0.3, ax=ax)
    
    # Add labels and title
    ax.set_xlabel('Carbon Storage (Mg/ha)')
    ax.set_ylabel('Density')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add legend
    ax.legend()
    
    # Add statistics in a text box
    stats_text = ""
    for area_name, carbon_data in carbon_data_dict.items():
        stats_text += f"{area_name}:\n"
        stats_text += f"  Mean: {np.mean(carbon_data):.1f} Mg/ha\n"
        stats_text += f"  Median: {np.median(carbon_data):.1f} Mg/ha\n"
        stats_text += f"  Range: {np.min(carbon_data):.1f} - {np.max(carbon_data):.1f} Mg/ha\n\n"
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
    
    # Improve layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    
    return fig

def create_carbon_value_chart(value_data, output_path, 
                             title="Economic Value of Carbon Storage by Land Use Type"):
    """
    Create a bar chart showing carbon values by land use type.
    
    Parameters:
    -----------
    value_data : pandas.DataFrame
        DataFrame with columns for land use type and carbon values
    output_path : str
        Path to save the output chart
    title : str, optional
        Title for the chart
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create the bar chart
    sns.barplot(x='land_use', y='value_per_ha', data=value_data, 
               palette='YlGn', ax=ax)
    
    # Add labels and title
    ax.set_xlabel('Land Use Type')
    ax.set_ylabel('Carbon Value (USD/ha)')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Rotate x-axis labels if needed
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on top of bars
    for i, v in enumerate(value_data['value_per_ha']):
        ax.text(i, v + 5, f"${v:.2f}", ha='center')
    
    # Improve layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    
    return fig

def create_scenario_comparison_chart(scenario_data, output_path, 
                                    value_col='carbon_total', 
                                    title="Carbon Storage Comparison Across Scenarios"):
    """
    Create a chart comparing carbon storage across different scenarios.
    
    Parameters:
    -----------
    scenario_data : pandas.DataFrame
        DataFrame with scenario data
    output_path : str
        Path to save the output chart
    value_col : str, optional
        Column name for the value to compare
    title : str, optional
        Title for the chart
    
    Returns:
    --------
    matplotlib.figure.Figure
        The created figure object
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create the bar chart
    bars = ax.bar(scenario_data['scenario'], scenario_data[value_col], 
                 color=plt.cm.viridis(np.linspace(0, 0.8, len(scenario_data))))
    
    # Add labels and title
    ax.set_xlabel('Scenario')
    ax.set_ylabel(f'Total Carbon Storage ({value_col})')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
               f'{height:.1f}', ha='center', va='bottom')
    
    # Improve layout and save
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    
    return fig

