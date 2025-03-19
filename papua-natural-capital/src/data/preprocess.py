#!/usr/bin/env python
# coding: utf-8

# In[ ]:


"""
Data preprocessing functions for the Papua Natural Capital Assessment.

This module provides functions for preprocessing and preparing geospatial datasets
for use in InVEST models and other analyses.
"""

import os
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import mapping, box
import json

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def prepare_lulc_for_invest(lulc_path, output_path, reclassify_table=None):
    """
    Prepare land use/land cover data for InVEST models.
    
    Parameters:
    -----------
    lulc_path : str
        Path to the input LULC raster
    output_path : str
        Path to save the processed LULC raster
    reclassify_table : str or DataFrame, optional
        Path to CSV file or DataFrame with reclassification values
    
    Returns:
    --------
    str
        Path to the processed LULC raster
    """
    logger.info(f"Preparing LULC data for InVEST: {lulc_path}")
    
    try:
        # Read the LULC raster
        with rasterio.open(lulc_path) as src:
            lulc_data = src.read(1)
            meta = src.meta.copy()
            
            # Reclassify if table is provided
            if reclassify_table is not None:
                # Load reclassification table if it's a string (path)
                if isinstance(reclassify_table, str):
                    reclass_df = pd.read_csv(reclassify_table)
                else:
                    reclass_df = reclassify_table
                
                # Create a reclassification dictionary
                reclass_dict = dict(zip(reclass_df['original_value'], reclass_df['new_value']))
                
                # Apply reclassification
                logger.info("Reclassifying LULC values...")
                reclass_data = np.copy(lulc_data)
                
                for orig_val, new_val in reclass_dict.items():
                    reclass_data[lulc_data == orig_val] = new_val
                
                lulc_data = reclass_data
            
            # Update the metadata if needed
            meta.update({
                "driver": "GTiff",
                "compress": "lzw",
                "nodata": 0
            })
            
            # Write the processed LULC raster
            with rasterio.open(output_path, "w", **meta) as dest:
                dest.write(lulc_data, 1)
        
        logger.info(f"Processed LULC raster saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error preparing LULC data: {e}")
        raise

def create_lulc_attribute_table(lulc_path, output_csv, class_names=None):
    """
    Create an attribute table for LULC classes with carbon pool values.
    
    Parameters:
    -----------
    lulc_path : str
        Path to the LULC raster
    output_csv : str
        Path to save the attribute table CSV
    class_names : dict, optional
        Dictionary mapping LULC values to class names
    
    Returns:
    --------
    str
        Path to the output CSV file
    """
    logger.info(f"Creating LULC attribute table from {lulc_path}")
    
    try:
        # Read the LULC raster to get unique values
        with rasterio.open(lulc_path) as src:
            lulc_data = src.read(1)
            unique_values = np.unique(lulc_data)
            # Remove 0 or NoData values
            unique_values = unique_values[unique_values > 0]
        
        logger.info(f"Found {len(unique_values)} unique LULC classes")
        
        # Create a DataFrame for the attribute table
        attr_df = pd.DataFrame({
            'value': unique_values
        })
        
        # Add class names if provided
        if class_names:
            attr_df['class_name'] = attr_df['value'].map(class_names).fillna('Unknown')
        else:
            attr_df['class_name'] = [f"Class {val}" for val in attr_df['value']]
        
        # Save the attribute table
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        attr_df.to_csv(output_csv, index=False)
        
        logger.info(f"LULC attribute table saved to {output_csv}")
        return output_csv
    
    except Exception as e:
        logger.error(f"Error creating LULC attribute table: {e}")
        raise

def create_carbon_pool_table(lulc_classes_csv, output_csv, carbon_values=None):
    """
    Create a carbon pool table for InVEST Carbon Storage and Sequestration model.
    
    Parameters:
    -----------
    lulc_classes_csv : str
        Path to CSV with LULC classes
    output_csv : str
        Path to save the carbon pool table
    carbon_values : dict, optional
        Dictionary with carbon values for each LULC class
    
    Returns:
    --------
    str
        Path to the output carbon pool table
    """
    logger.info(f"Creating carbon pool table from {lulc_classes_csv}")
    
    try:
        # Read the LULC classes
        lulc_df = pd.read_csv(lulc_classes_csv)
        
        # Create a carbon pool DataFrame
        carbon_df = pd.DataFrame({
            'lucode': lulc_df['value'],
            'lulc_name': lulc_df['class_name']
        })
        
        # Add carbon pool values
        if carbon_values:
            # Use provided carbon values
            for lucode in carbon_df['lucode']:
                if lucode in carbon_values:
                    for pool, value in carbon_values[lucode].items():
                        carbon_df.loc[carbon_df['lucode'] == lucode, pool] = value
        else:
            # Use default values based on land cover type
            # These are placeholder values and should be replaced with actual values
            # based on literature for the study region
            carbon_df['c_above'] = 0  # Above-ground carbon (Mg/ha)
            carbon_df['c_below'] = 0  # Below-ground carbon (Mg/ha)
            carbon_df['c_soil'] = 0   # Soil carbon (Mg/ha)
            carbon_df['c_dead'] = 0   # Dead matter carbon (Mg/ha)
            
            # Set values based on class name (very simplified)
            for idx, row in carbon_df.iterrows():
                class_name = row['lulc_name'].lower()
                
                if 'forest' in class_name:
                    if 'primary' in class_name:
                        carbon_df.loc[idx, 'c_above'] = 200
                        carbon_df.loc[idx, 'c_below'] = 40
                        carbon_df.loc[idx, 'c_soil'] = 100
                        carbon_df.loc[idx, 'c_dead'] = 20
                    elif 'secondary' in class_name:
                        carbon_df.loc[idx, 'c_above'] = 150
                        carbon_df.loc[idx, 'c_below'] = 35
                        carbon_df.loc[idx, 'c_soil'] = 90
                        carbon_df.loc[idx, 'c_dead'] = 15
                elif 'shrub' in class_name:
                    carbon_df.loc[idx, 'c_above'] = 70
                    carbon_df.loc[idx, 'c_below'] = 20
                    carbon_df.loc[idx, 'c_soil'] = 60
                    carbon_df.loc[idx, 'c_dead'] = 5
                elif 'grass' in class_name or 'savanna' in class_name:
                    carbon_df.loc[idx, 'c_above'] = 15
                    carbon_df.loc[idx, 'c_below'] = 5
                    carbon_df.loc[idx, 'c_soil'] = 40
                    carbon_df.loc[idx, 'c_dead'] = 1
                elif 'crop' in class_name:
                    carbon_df.loc[idx, 'c_above'] = 5
                    carbon_df.loc[idx, 'c_below'] = 2
                    carbon_df.loc[idx, 'c_soil'] = 30
                    carbon_df.loc[idx, 'c_dead'] = 0
                elif 'urban' in class_name or 'built' in class_name:
                    carbon_df.loc[idx, 'c_above'] = 2
                    carbon_df.loc[idx, 'c_below'] = 1
                    carbon_df.loc[idx, 'c_soil'] = 20
                    carbon_df.loc[idx, 'c_dead'] = 0
                elif 'mine' in class_name:
                    carbon_df.loc[idx, 'c_above'] = 0
                    carbon_df.loc[idx, 'c_below'] = 0
                    carbon_df.loc[idx, 'c_soil'] = 5
                    carbon_df.loc[idx, 'c_dead'] = 0
        
        # Save the carbon pool table
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        carbon_df.to_csv(output_csv, index=False)
        
        logger.info(f"Carbon pool table saved to {output_csv}")
        return output_csv
    
    except Exception as e:
        logger.error(f"Error creating carbon pool table: {e}")
        raise

def create_scenario_lulc(base_lulc_path, scenario_lulc_path, change_areas, new_values):
    """
    Create a scenario LULC raster by modifying specific areas.
    
    Parameters:
    -----------
    base_lulc_path : str
        Path to the base LULC raster
    scenario_lulc_path : str
        Path to save the scenario LULC raster
    change_areas : list of GeoDataFrame or geometries
        Areas to modify
    new_values : list of int
        New LULC values for each change area
    
    Returns:
    --------
    str
        Path to the scenario LULC raster
    """
    logger.info(f"Creating scenario LULC from {base_lulc_path}")
    
    try:
        # Read the base LULC raster
        with rasterio.open(base_lulc_path) as src:
            lulc_data = src.read(1)
            meta = src.meta.copy()
            
            # Create a copy for the scenario
            scenario_data = np.copy(lulc_data)
            
            # Update the scenario based on change areas
            for i, (area, new_value) in enumerate(zip(change_areas, new_values)):
                # Convert area to GeoDataFrame if it's not already
                if not isinstance(area, gpd.GeoDataFrame):
                    area_gdf = gpd.GeoDataFrame(geometry=[area], crs=src.crs)
                else:
                    # Ensure the GeoDataFrame has the correct CRS
                    area_gdf = area.to_crs(src.crs)
                
                # Create a mask for the area
                geoms = [mapping(geom) for geom in area_gdf.geometry]
                area_mask, transform = mask(src, geoms, crop=False, invert=False)
                area_mask = area_mask[0].astype(bool)
                
                # Update the scenario data
                scenario_data[area_mask] = new_value
                
                logger.info(f"Updated change area {i+1} to value {new_value}")
            
            # Write the scenario LULC raster
            with rasterio.open(scenario_lulc_path, "w", **meta) as dest:
                dest.write(scenario_data, 1)
        
        logger.info(f"Scenario LULC raster saved to {scenario_lulc_path}")
        return scenario_lulc_path
    
    except Exception as e:
        logger.error(f"Error creating scenario LULC: {e}")
        raise

def extract_invest_results(invest_workspace, output_dir, model_name):
    """
    Extract and organize results from InVEST model runs.
    
    Parameters:
    -----------
    invest_workspace : str
        Path to the InVEST workspace directory
    output_dir : str
        Directory to save the extracted results
    model_name : str
        Name of the InVEST model (e.g., 'carbon', 'habitat_quality')
    
    Returns:
    --------
    dict
        Dictionary of extracted results
    """
    logger.info(f"Extracting results for {model_name} model from {invest_workspace}")
    
    try:
        results = {}
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        if model_name == 'carbon':
            # Extract carbon model results
            total_carbon_path = os.path.join(invest_workspace, 'total_carbon.tif')
            
            # Copy the total carbon raster to the output directory
            output_carbon_path = os.path.join(output_dir, 'total_carbon.tif')
            
            if os.path.exists(total_carbon_path):
                import shutil
                shutil.copy2(total_carbon_path, output_carbon_path)
                results['total_carbon'] = output_carbon_path
            
            # Check for valuation results
            npv_path = os.path.join(invest_workspace, 'net_present_value.tif')
            if os.path.exists(npv_path):
                output_npv_path = os.path.join(output_dir, 'net_present_value.tif')
                shutil.copy2(npv_path, output_npv_path)
                results['npv'] = output_npv_path
            
            # Calculate summary statistics
            if 'total_carbon' in results:
                with rasterio.open(results['total_carbon']) as src:
                    carbon_data = src.read(1)
                    valid_data = carbon_data[carbon_data > 0]
                    
                    summary = {
                        'mean_carbon': float(np.mean(valid_data)),
                        'total_carbon': float(np.sum(valid_data)),
                        'min_carbon': float(np.min(valid_data)),
                        'max_carbon': float(np.max(valid_data)),
                        'std_carbon': float(np.std(valid_data))
                    }
                    
                    # Save summary as JSON
                    summary_path = os.path.join(output_dir, 'carbon_summary.json')
                    with open(summary_path, 'w') as f:
                        json.dump(summary, f, indent=4)
                    
                    results['summary'] = summary_path
        
        elif model_name == 'habitat_quality':
            # Extract habitat quality model results
            quality_path = os.path.join(invest_workspace, 'quality.tif')
            
            # Copy the habitat quality raster to the output directory
            output_quality_path = os.path.join(output_dir, 'habitat_quality.tif')
            
            if os.path.exists(quality_path):
                import shutil
                shutil.copy2(quality_path, output_quality_path)
                results['habitat_quality'] = output_quality_path
            
            # Check for degradation results
            deg_path = os.path.join(invest_workspace, 'degradation.tif')
            if os.path.exists(deg_path):
                output_deg_path = os.path.join(output_dir, 'habitat_degradation.tif')
                shutil.copy2(deg_path, output_deg_path)
                results['degradation'] = output_deg_path
        
        elif model_name == 'sdr':
            # Extract sediment delivery ratio model results
            sed_export_path = os.path.join(invest_workspace, 'sed_export.tif')
            
            # Copy the sediment export raster to the output directory
            output_sed_path = os.path.join(output_dir, 'sediment_export.tif')
            
            if os.path.exists(sed_export_path):
                import shutil
                shutil.copy2(sed_export_path, output_sed_path)
                results['sediment_export'] = output_sed_path
            
            # Check for retention results
            ret_path = os.path.join(invest_workspace, 'sed_retention.tif')
            if os.path.exists(ret_path):
                output_ret_path = os.path.join(output_dir, 'sediment_retention.tif')
                shutil.copy2(ret_path, output_ret_path)
                results['sediment_retention'] = output_ret_path
        
        logger.info(f"Extracted {len(results)} results for {model_name} model")
        return results
    
    except Exception as e:
        logger.error(f"Error extracting InVEST results: {e}")
        raise

def prepare_all_data(raw_data_dir, processed_data_dir, invest_input_dir):
    """
    Prepare all data for the natural capital assessment.
    
    Parameters:
    -----------
    raw_data_dir : str
        Directory containing raw data
    processed_data_dir : str
        Directory to save processed data
    invest_input_dir : str
        Directory to save InVEST model inputs
    
    Returns:
    --------
    dict
        Dictionary of paths to prepared datasets
    """
    logger.info("Preparing all data for natural capital assessment...")
    
    # Create output directories
    os.makedirs(processed_data_dir, exist_ok=True)
    os.makedirs(invest_input_dir, exist_ok=True)
    
    # 1. Process administrative boundaries
    admin_dir = os.path.join(raw_data_dir, "admin_boundaries")
    papua_path = os.path.join(processed_data_dir, "admin_boundaries/papua_boundary.shp")
    
    # 2. Process land cover data
    lulc_dir = os.path.join(raw_data_dir, "landcover")
    lulc_files = [f for f in os.listdir(lulc_dir) if f.endswith('.tif')]
    
    if lulc_files:
        lulc_path = os.path.join(lulc_dir, lulc_files[0])
        
        # Clip LULC to Papua
        if os.path.exists(papua_path):
            papua_gdf = gpd.read_file(papua_path)
            papua_lulc_path = os.path.join(processed_data_dir, "lulc/papua_lulc.tif")
            os.makedirs(os.path.dirname(papua_lulc_path), exist_ok=True)
            
            from download import clip_raster_to_region
            clip_raster_to_region(lulc_path, papua_gdf, papua_lulc_path)
            
            lulc_path = papua_lulc_path
        
        # Create LULC attribute table
        lulc_classes_path = os.path.join(processed_data_dir, "lulc/lulc_classes.csv")
        create_lulc_attribute_table(lulc_path, lulc_classes_path)
        
        # Create carbon pool table for InVEST
        carbon_pools_path = os.path.join(invest_input_dir, "carbon_pools.csv")
        create_carbon_pool_table(lulc_classes_path, carbon_pools_path)
    else:
        logger.warning("No LULC files found in the landcover directory")
        lulc_path = None
        lulc_classes_path = None
        carbon_pools_path = None
    
    # 3. Process mining data
    mining_dir = os.path.join(raw_data_dir, "mining")
    mining_files = [f for f in os.listdir(mining_dir) if f.endswith('.shp')]
    
    if mining_files:
        mining_path = os.path.join(mining_dir, mining_files[0])
        
        # Clip mining data to Papua
        if os.path.exists(papua_path):
            papua_gdf = gpd.read_file(papua_path)
            papua_mining_path = os.path.join(processed_data_dir, "mining/papua_mining.shp")
            os.makedirs(os.path.dirname(papua_mining_path), exist_ok=True)
            
            mining_gdf = gpd.read_file(mining_path)
            mining_in_wp = gpd.overlay(mining_gdf, papua_gdf, how='intersection')
            mining_in_wp.to_file(papua_mining_path)
            
            mining_path = papua_mining_path
    else:
        logger.warning("No mining files found in the mining directory")
        mining_path = None
    
    # 4. Create scenario LULC (restoration scenario)
    if lulc_path and mining_path:
        scenario_dir = os.path.join(processed_data_dir, "scenarios")
        os.makedirs(scenario_dir, exist_ok=True)
        
        restoration_lulc_path = os.path.join(scenario_dir, "restoration_scenario.tif")
        
        # Use mining areas as change areas
        mining_gdf = gpd.read_file(mining_path)
        
        # Buffer mining areas by 1km for restoration zone
        mining_buffer = mining_gdf.copy()
        mining_buffer.geometry = mining_gdf.buffer(1000)
        
        # Get forest class value (simplified approach)
        if os.path.exists(lulc_classes_path):
            lulc_classes = pd.read_csv(lulc_classes_path)
            forest_classes = lulc_classes[lulc_classes['class_name'].str.contains('forest', case=False)]
            
            if len(forest_classes) > 0:
                forest_value = forest_classes.iloc[0]['value']
            else:
                forest_value = 1  # Placeholder value
        else:
            forest_value = 1  # Placeholder value
        
        # Create restoration scenario
        create_scenario_lulc(lulc_path, restoration_lulc_path, [mining_buffer], [forest_value])
        
        # Create carbon pool table for the scenario
        scenario_carbon_pools_path = os.path.join(invest_input_dir, "scenario_carbon_pools.csv")
        create_carbon_pool_table(lulc_classes_path, scenario_carbon_pools_path)
    else:
        logger.warning("Cannot create restoration scenario without LULC and mining data")
        restoration_lulc_path = None
        scenario_carbon_pools_path = None
    
    # Return paths to all prepared datasets
    return {
        "papua_boundary": papua_path,
        "papua_lulc": lulc_path,
        "lulc_classes": lulc_classes_path,
        "carbon_pools": carbon_pools_path,
        "papua_mining": mining_path,
        "restoration_scenario": restoration_lulc_path,
        "scenario_carbon_pools": scenario_carbon_pools_path
    }

# Example usage
if __name__ == "__main__":
    raw_data_dir = "../data/raw"
    processed_data_dir = "../data/processed"
    invest_input_dir = "../data/invest_inputs"
    
    prepared_data = prepare_all_data(raw_data_dir, processed_data_dir, invest_input_dir)
    
    print("\nPrepared datasets:")
    for name, path in prepared_data.items():
        print(f"{name}: {path}")

