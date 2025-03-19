"""
Data download functions for the Papua Natural Capital Assessment.

This module provides functions for downloading and preparing geospatial datasets
needed for the natural capital assessment of Papua.
"""

import os
import urllib.request
import zipfile
import logging
import shutil
import requests
from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

# Set up logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def download_file(url, output_path, description=None):
    """
    Download a file from a URL with progress bar.
    
    Parameters:
    -----------
    url : str
        URL to download
    output_path : str
        Path to save the downloaded file
    description : str, optional
        Description for the progress bar
    
    Returns:
    --------
    str
        Path to the downloaded file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if file already exists
    if os.path.exists(output_path):
        logger.info(f"File already exists: {output_path}")
        return output_path
    
    # Download the file
    logger.info(f"Downloading {url} to {output_path}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Get file size for progress bar
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 KB
        
        desc = description if description else "Downloading"
        
        with open(output_path, 'wb') as f, tqdm(
                desc=desc,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                ) as pbar:
            
            for data in response.iter_content(block_size):
                pbar.update(len(data))
                f.write(data)
                
        logger.info(f"Download completed: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        # Remove partial download if it exists
        if os.path.exists(output_path):
            os.remove(output_path)
        raise

def unzip_file(zip_path, extract_dir=None):
    """
    Extract a zip file.
    
    Parameters:
    -----------
    zip_path : str
        Path to the zip file
    extract_dir : str, optional
        Directory to extract to. If None, extracts to the same directory as the zip file.
    
    Returns:
    --------
    str
        Path to the extracted directory
    """
    if extract_dir is None:
        extract_dir = os.path.dirname(zip_path)
    
    logger.info(f"Extracting {zip_path} to {extract_dir}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        logger.info(f"Extraction completed to {extract_dir}")
        return extract_dir
    
    except Exception as e:
        logger.error(f"Error extracting zip file: {e}")
        raise

def download_admin_boundaries(output_dir, country_code='IDN', admin_level=1):
    """
    Download administrative boundaries for Indonesia from GADM.
    
    Parameters:
    -----------
    output_dir : str
        Directory to save the downloaded files
    country_code : str, optional
        ISO country code, default is 'IDN' for Indonesia
    admin_level : int, optional
        Administrative level (0=country, 1=province, 2=district), default is 1
    
    Returns:
    --------
    str
        Path to the shapefile
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # GADM data URL
    gadm_url = f"https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_{country_code}_shp.zip"
    zip_path = os.path.join(output_dir, f"gadm41_{country_code}_shp.zip")
    
    # Download zip file
    download_file(gadm_url, zip_path, f"Downloading {country_code} admin boundaries")
    
    # Extract zip file
    extract_dir = os.path.join(output_dir, f"gadm41_{country_code}_shp")
    unzip_file(zip_path, extract_dir)
    
    # Path to the shapefile for the requested admin level
    shapefile_path = os.path.join(extract_dir, f"gadm41_{country_code}_{admin_level}.shp")
    
    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Admin boundary shapefile not found: {shapefile_path}")
    
    logger.info(f"Admin boundaries downloaded to {shapefile_path}")
    return shapefile_path

def download_elevation_data(output_dir, bounds, resolution=30):
    """
    Download SRTM elevation data for the specified bounds.
    
    Parameters:
    -----------
    output_dir : str
        Directory to save the downloaded files
    bounds : tuple
        Bounding box (minx, miny, maxx, maxy) in WGS84 coordinates
    resolution : int, optional
        Resolution in meters, default is 30m (SRTM 1 arc-second)
    
    Returns:
    --------
    str
        Path to the downloaded DEM
    """
    # Note: In a real implementation, you would use NASA Earthdata API to download SRTM data
    # This is a simplified version that assumes the data is available at a specific URL
    
    logger.warning("This function is a placeholder. SRTM data requires NASA Earthdata login.")
    logger.warning("In a real implementation, use NASA Earthdata API or download manually.")
    
    # Create a placeholder DEM file
    dem_path = os.path.join(output_dir, "srtm_dem.tif")
    
    # Check if file already exists
    if os.path.exists(dem_path):
        logger.info(f"DEM file already exists: {dem_path}")
        return dem_path
    
    logger.info(f"Creating placeholder DEM file: {dem_path}")
    
    # In a real implementation, you would download the data here
    # For now, create an empty file as a placeholder
    with open(dem_path, 'w') as f:
        f.write("Placeholder for SRTM DEM data")
    
    return dem_path

def download_landcover_data(output_dir, year=2020):
    """
    Download land cover data for Indonesia.
    
    Parameters:
    -----------
    output_dir : str
        Directory to save the downloaded files
    year : int, optional
        Year of land cover data, default is 2020
    
    Returns:
    --------
    str
        Path to the downloaded land cover file
    """
    # Note: This is a placeholder. In reality, you would download from official sources like:
    # - Ministry of Environment and Forestry Indonesia
    # - ESA WorldCover
    # - Copernicus Global Land Service
    
    logger.warning("This function is a placeholder. Land cover data should be downloaded from official sources.")
    
    # Create a placeholder land cover file
    lulc_path = os.path.join(output_dir, f"indonesia_landcover_{year}.tif")
    
    # Check if file already exists
    if os.path.exists(lulc_path):
        logger.info(f"Land cover file already exists: {lulc_path}")
        return lulc_path
    
    logger.info(f"Creating placeholder land cover file: {lulc_path}")
    
    # In a real implementation, you would download the data here
    # For now, create an empty file as a placeholder
    with open(lulc_path, 'w') as f:
        f.write(f"Placeholder for Indonesia land cover data {year}")
    
    return lulc_path

def download_mining_data(output_dir):
    """
    Download mining concession data for Indonesia.
    
    Parameters:
    -----------
    output_dir : str
        Directory to save the downloaded files
    
    Returns:
    --------
    str
        Path to the downloaded mining data
    """
    # Note: This is a placeholder. In reality, you would download from official sources like:
    # - Ministry of Energy and Mineral Resources Indonesia
    # - Global mining databases
    
    logger.warning("This function is a placeholder. Mining data should be downloaded from official sources.")
    
    # Create a placeholder mining data file
    mining_path = os.path.join(output_dir, "indonesia_mining_concessions.shp")
    
    # Check if file already exists
    if os.path.exists(mining_path):
        logger.info(f"Mining data file already exists: {mining_path}")
        return mining_path
    
    logger.info(f"Creating placeholder mining data file: {mining_path}")
    
    # In a real implementation, you would download the data here
    # For now, create an empty file as a placeholder
    with open(mining_path, 'w') as f:
        f.write("Placeholder for Indonesia mining concession data")
    
    return mining_path

def download_biodiversity_data(output_dir, region="papua"):
    """
    Download biodiversity occurrence data for the specified region.
    
    Parameters:
    -----------
    output_dir : str
        Directory to save the downloaded files
    region : str, optional
        Region name, default is "papua"
    
    Returns:
    --------
    str
        Path to the downloaded biodiversity data
    """
    # Note: In a real implementation, you would use the GBIF API to download occurrence data
    
    logger.warning("This function is a placeholder. Biodiversity data should be downloaded from GBIF API.")
    
    # Create a placeholder biodiversity data file
    biodiv_path = os.path.join(output_dir, f"{region}_biodiversity_occurrences.csv")
    
    # Check if file already exists
    if os.path.exists(biodiv_path):
        logger.info(f"Biodiversity data file already exists: {biodiv_path}")
        return biodiv_path
    
    logger.info(f"Creating placeholder biodiversity data file: {biodiv_path}")
    
    # In a real implementation, you would download the data here
    # For now, create an empty file as a placeholder
    with open(biodiv_path, 'w') as f:
        f.write(f"Placeholder for {region} biodiversity occurrence data")
    
    return biodiv_path

def clip_raster_to_region(raster_path, region_boundary, output_path, reproject_to=None):
    """
    Clip a raster to a region boundary.
    
    Parameters:
    -----------
    raster_path : str
        Path to the input raster
    region_boundary : GeoDataFrame
        GeoDataFrame with the region boundary
    output_path : str
        Path to save the clipped raster
    reproject_to : str, optional
        CRS to reproject to (EPSG code or proj4 string)
    
    Returns:
    --------
    str
        Path to the clipped raster
    """
    logger.info(f"Clipping raster {raster_path} to region boundary")
    
    try:
        # Read the raster
        with rasterio.open(raster_path) as src:
            # Reproject the boundary to the raster's CRS if needed
            region_gdf = region_boundary.to_crs(src.crs)
            
            # Create a mask from the boundary
            from rasterio.mask import mask
            from shapely.geometry import mapping
            
            # Get geometry in GeoJSON format
            geoms = [mapping(geom) for geom in region_gdf.geometry]
            
            # Mask the raster (clip it to the boundary)
            out_image, out_transform = mask(src, geoms, crop=True)
            
            # Copy the metadata
            out_meta = src.meta.copy()
            
            # Update the metadata
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })
            
            # Write the clipped raster
            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)
        
        # Reproject if needed
        if reproject_to:
            reproject_raster(output_path, output_path, reproject_to)
        
        logger.info(f"Raster clipped and saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error clipping raster: {e}")
        raise

def reproject_raster(input_path, output_path, dst_crs):
    """
    Reproject a raster to a new coordinate reference system.
    
    Parameters:
    -----------
    input_path : str
        Path to the input raster
    output_path : str
        Path to save the reprojected raster
    dst_crs : str
        Target CRS (EPSG code or proj4 string)
    
    Returns:
    --------
    str
        Path to the reprojected raster
    """
    logger.info(f"Reprojecting raster {input_path} to {dst_crs}")
    
    try:
        # Read the source raster
        with rasterio.open(input_path) as src:
            # Calculate the default transform
            transform, width, height = calculate_default_transform(
                src.crs, dst_crs, src.width, src.height, *src.bounds)
            
            # Update the metadata for the output file
            meta = src.meta.copy()
            meta.update({
                'crs': dst_crs,
                'transform': transform,
                'width': width,
                'height': height
            })
            
            # Create the output file
            with rasterio.open(output_path, 'w', **meta) as dst:
                # Reproject each band
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=dst_crs,
                        resampling=Resampling.nearest)
        
        logger.info(f"Raster reprojected and saved to {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error reprojecting raster: {e}")
        raise

def download_all_data(data_dir, region="central_papua"):
    """Modified to use local data for Central Papua"""
    # Create directory structure
    raw_dir = os.path.join(data_dir, "raw")
    processed_dir = os.path.join(data_dir, "processed")
    
    os.makedirs(processed_dir, exist_ok=True)
    
    # Create subdirectories in processed
    for subdir in ['admin_boundaries', 'elevation', 'landcover', 'mining']:
        os.makedirs(os.path.join(processed_dir, subdir), exist_ok=True)
    
    # Paths to your specific files
    admin_path = os.path.join(raw_dir, "admin_boundaries/central_papua.shp")
    dem_path = os.path.join(raw_dir, "elevation/central_papua_DEM.tif")
    lulc_path = os.path.join(raw_dir, "landcover/landcover_central_papua.tif")
    mining_path = os.path.join(raw_dir, "mining/mining_leases.shp")  # Update with your actual filename
    
    # Copy files to processed directory if needed
    central_papua_path = os.path.join(processed_dir, "admin_boundaries/central_papua_boundary.shp")
    if os.path.exists(admin_path) and not os.path.exists(central_papua_path):
        central_papua_gdf = gpd.read_file(admin_path)
        central_papua_gdf.to_file(central_papua_path)
        logger.info(f"Central Papua boundary saved to {central_papua_path}")
    
    # Return paths
    return {
        "admin_boundaries": admin_path,
        "central_papua_boundary": central_papua_path,
        "elevation": dem_path,
        "landcover": lulc_path,
        "mining": mining_path
    }

# Example usage
if __name__ == "__main__":
    data_dir = "../data"
    datasets = download_all_data(data_dir)
    
    print("\nDownloaded datasets:")
    for name, path in datasets.items():
        print(f"{name}: {path}")
