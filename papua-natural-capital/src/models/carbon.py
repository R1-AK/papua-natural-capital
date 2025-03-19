"""
Carbon Storage and Sequestration Model Functions

This module provides wrapper functions for the InVEST Carbon Storage and Sequestration model
as well as utility functions for preparing inputs and processing outputs.
"""

import os
import logging
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import natcap.invest.carbon

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def prepare_carbon_inputs(lulc_path, carbon_pools_csv, output_dir):
    """
    Prepare and validate inputs for the InVEST Carbon model.
    
    Parameters:
    -----------
    lulc_path : str
        Path to the land use/land cover raster file
    carbon_pools_csv : str
        Path to the carbon pools CSV file
    output_dir : str
        Directory to save the prepared inputs
    
    Returns:
    --------
    dict
        Dictionary of prepared and validated model inputs
    """
    logger.info("Preparing Carbon model inputs...")
    
    # Check if input files exist
    if not os.path.exists(lulc_path):
        raise FileNotFoundError(f"LULC file not found: {lulc_path}")
    if not os.path.exists(carbon_pools_csv):
        raise FileNotFoundError(f"Carbon pools file not found: {carbon_pools_csv}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Validate LULC raster
    try:
        with rasterio.open(lulc_path) as src:
            lulc_meta = src.meta
            lulc_crs = src.crs
            lulc_bounds = src.bounds
            lulc_data = src.read(1)
            unique_values = np.unique(lulc_data)
            logger.info(f"LULC raster loaded: shape={lulc_data.shape}, unique values={len(unique_values)}")
    except Exception as e:
        logger.error(f"Error reading LULC raster: {e}")
        raise
    
    # Validate carbon pools CSV
    try:
        carbon_df = pd.read_csv(carbon_pools_csv)
        required_cols = ['lucode', 'c_above', 'c_below', 'c_soil', 'c_dead']
        missing_cols = [col for col in required_cols if col not in carbon_df.columns]
        if missing_cols:
            raise ValueError(f"Carbon pools CSV missing required columns: {missing_cols}")
        
        # Check if all LULC values have carbon data
        missing_values = [val for val in unique_values if val not in carbon_df['lucode'].values and val != 0]
        if missing_values:
            logger.warning(f"Carbon data missing for LULC classes: {missing_values}")
        
        logger.info(f"Carbon pools data loaded: {len(carbon_df)} land cover classes")
    except Exception as e:
        logger.error(f"Error reading carbon pools CSV: {e}")
        raise
    
    # Prepare model arguments
    args = {
        'lulc_cur_path': lulc_path,
        'carbon_pools_path': carbon_pools_csv,
        'workspace_dir': output_dir,
    }
    
    return args

def run_carbon_model(args):
    """
    Run the InVEST Carbon Storage and Sequestration model.
    
    Parameters:
    -----------
    args : dict
        Dictionary of model arguments
    
    Returns:
    --------
    dict
        Dictionary of model outputs and summary statistics
    """
    logger.info("Running InVEST Carbon Storage and Sequestration model...")
    
    # Run the model
    try:
        carbon_results = natcap.invest.carbon.execute(args)
        logger.info("Carbon model execution completed successfully")
    except Exception as e:
        logger.error(f"Error executing carbon model: {e}")
        raise
    
    # Process and summarize results
    results_summary = summarize_carbon_results(args['workspace_dir'])
    
    return {
        'model_results': carbon_results,
        'summary': results_summary
    }

def summarize_carbon_results(workspace_dir):
    """
    Summarize the carbon model results.
    
    Parameters:
    -----------
    workspace_dir : str
        Path to the workspace directory containing model outputs
    
    Returns:
    --------
    dict
        Dictionary of summary statistics
    """
    logger.info("Summarizing carbon results...")
    
    # Path to the total carbon output raster
    total_carbon_path = os.path.join(workspace_dir, 'total_carbon.tif')
    if not os.path.exists(total_carbon_path):
        raise FileNotFoundError(f"Total carbon output not found: {total_carbon_path}")
    
    # Read the total carbon raster
    with rasterio.open(total_carbon_path) as src:
        carbon_data = src.read(1)
        valid_data = carbon_data[carbon_data > 0]  # Remove NoData values
        
        # Calculate summary statistics
        summary = {
            'mean_carbon': float(np.mean(valid_data)),
            'median_carbon': float(np.median(valid_data)),
            'min_carbon': float(np.min(valid_data)),
            'max_carbon': float(np.max(valid_data)),
            'total_carbon': float(np.sum(valid_data)),
            'pixel_count': int(len(valid_data)),
            'pixel_size': src.res[0] * src.res[1]
        }
        
        # Convert pixel count to area (assuming square pixels)
        # Area in hectares (assuming resolution is in meters)
        if src.res[0] == src.res[1]:  # Square pixels
            pixel_size_m2 = src.res[0] * src.res[1]
            summary['area_ha'] = summary['pixel_count'] * pixel_size_m2 / 10000
        
        logger.info(f"Carbon summary: mean={summary['mean_carbon']:.2f} Mg/ha, "
                   f"total={summary['total_carbon']:.2f} Mg, "
                   f"area={summary.get('area_ha', 'N/A'):.2f} ha")
    
    return summary

def extract_carbon_for_region(carbon_raster_path, region_gdf):
    """
    Extract carbon values for a specific region.
    
    Parameters:
    -----------
    carbon_raster_path : str
        Path to the carbon raster file
    region_gdf : GeoDataFrame
        GeoDataFrame containing the region geometry
    
    Returns:
    --------
    numpy.ndarray
        Array of carbon values for the region
    dict
        Dictionary of summary statistics for the region
    """
    logger.info(f"Extracting carbon values for region: {region_gdf.iloc[0].name if 'name' in region_gdf.columns else 'unnamed'}")
    
    try:
        with rasterio.open(carbon_raster_path) as src:
            # Mask the raster with the region geometry
            shapes = [mapping(geom) for geom in region_gdf.geometry]
            masked_data, masked_transform = mask(src, shapes, crop=True)
            masked_data = masked_data[0]  # Get the first band
            
            # Remove NoData values
            valid_data = masked_data[masked_data > 0]
            
            # Calculate summary statistics
            summary = {
                'mean_carbon': float(np.mean(valid_data)),
                'median_carbon': float(np.median(valid_data)),
                'min_carbon': float(np.min(valid_data)),
                'max_carbon': float(np.max(valid_data)),
                'total_carbon': float(np.sum(valid_data)),
                'pixel_count': int(len(valid_data)),
                'pixel_size': src.res[0] * src.res[1]
            }
            
            # Convert pixel count to area (hectares)
            pixel_size_m2 = src.res[0] * src.res[1]
            summary['area_ha'] = summary['pixel_count'] * pixel_size_m2 / 10000
            
            logger.info(f"Extracted {len(valid_data)} pixels, "
                       f"mean carbon: {summary['mean_carbon']:.2f} Mg/ha, "
                       f"total carbon: {summary['total_carbon']:.2f} Mg")
            
            return valid_data, summary
    except Exception as e:
        logger.error(f"Error extracting carbon values for region: {e}")
        raise

def calculate_carbon_value(carbon_data, area_ha, price_per_ton_co2=40, discount_rate=0.04):
    """
    Calculate the economic value of carbon.
    
    Parameters:
    -----------
    carbon_data : numpy.ndarray or float
        Carbon values in Mg C/ha or total Mg C
    area_ha : float
        Area in hectares
    price_per_ton_co2 : float, optional
        Price per metric ton of CO2, default is 40 USD
    discount_rate : float, optional
        Discount rate for net present value calculation, default is 0.04 (4%)
    
    Returns:
    --------
    dict
        Dictionary of economic values
    """
    logger.info(f"Calculating carbon value with price={price_per_ton_co2} USD/tCO2 and discount_rate={discount_rate}")
    
    # Handle both array and single value inputs
    if isinstance(carbon_data, np.ndarray):
        mean_carbon = np.mean(carbon_data)
        total_carbon = np.sum(carbon_data) * area_ha / len(carbon_data) if len(carbon_data) > 0 else 0
    else:
        mean_carbon = carbon_data
        total_carbon = carbon_data * area_ha
    
    # Convert from C to CO2 (1 ton C = 3.67 tons CO2)
    co2_factor = 3.67
    mean_co2 = mean_carbon * co2_factor
    total_co2 = total_carbon * co2_factor
    
    # Calculate economic value
    value_per_ha = mean_co2 * price_per_ton_co2
    total_value = total_co2 * price_per_ton_co2
    
    # Calculate net present value (assuming permanent storage)
    # NPV = value / discount_rate 
    npv_per_ha = value_per_ha / discount_rate if discount_rate > 0 else float('inf')
    npv_total = total_value / discount_rate if discount_rate > 0 else float('inf')
    
    results = {
        'mean_carbon_mgha': float(mean_carbon),
        'total_carbon_mg': float(total_carbon),
        'mean_co2_mgha': float(mean_co2),
        'total_co2_mg': float(total_co2),
        'value_per_ha_usd': float(value_per_ha),
        'total_value_usd': float(total_value),
        'npv_per_ha_usd': float(npv_per_ha),
        'npv_total_usd': float(npv_total)
    }
    
    logger.info(f"Carbon value: {value_per_ha:.2f} USD/ha, "
               f"total: {total_value:.2f} USD, "
               f"NPV: {npv_total:.2f} USD")
    
    return results

def compare_scenarios(baseline_carbon, scenario_carbon, area_ha, price_per_ton_co2=40):
    """
    Compare carbon storage between baseline and scenario conditions.
    
    Parameters:
    -----------
    baseline_carbon : numpy.ndarray or float
        Baseline carbon values in Mg C/ha
    scenario_carbon : numpy.ndarray or float
        Scenario carbon values in Mg C/ha
    area_ha : float
        Area in hectares
    price_per_ton_co2 : float, optional
        Price per metric ton of CO2, default is 40 USD
    
    Returns:
    --------
    dict
        Dictionary of comparison results
    """
    logger.info("Comparing carbon scenarios...")
    
    # Handle both array and single value inputs
    if isinstance(baseline_carbon, np.ndarray):
        baseline_mean = np.mean(baseline_carbon)
    else:
        baseline_mean = baseline_carbon
        
    if isinstance(scenario_carbon, np.ndarray):
        scenario_mean = np.mean(scenario_carbon)
    else:
        scenario_mean = scenario_carbon
    
    # Calculate differences
    carbon_diff = scenario_mean - baseline_mean
    carbon_diff_total = carbon_diff * area_ha
    
    # Convert to CO2
    co2_factor = 3.67
    co2_diff = carbon_diff * co2_factor
    co2_diff_total = carbon_diff_total * co2_factor
    
    # Calculate value difference
    value_diff_per_ha = co2_diff * price_per_ton_co2
    value_diff_total = co2_diff_total * price_per_ton_co2
    
    # Calculate percent change
    percent_change = (carbon_diff / baseline_mean) * 100 if baseline_mean != 0 else float('inf')
    
    results = {
        'baseline_carbon_mgha': float(baseline_mean),
        'scenario_carbon_mgha': float(scenario_mean),
        'carbon_diff_mgha': float(carbon_diff),
        'carbon_diff_total_mg': float(carbon_diff_total),
        'co2_diff_mgha': float(co2_diff),
        'co2_diff_total_mg': float(co2_diff_total),
        'value_diff_per_ha_usd': float(value_diff_per_ha),
        'value_diff_total_usd': float(value_diff_total),
        'percent_change': float(percent_change)
    }
    
    direction = "increase" if carbon_diff > 0 else "decrease"
    logger.info(f"Scenario comparison: {abs(carbon_diff):.2f} Mg C/ha {direction}, "
               f"{abs(percent_change):.2f}% {direction}, "
               f"value difference: {value_diff_total:.2f} USD")
    
    return results
