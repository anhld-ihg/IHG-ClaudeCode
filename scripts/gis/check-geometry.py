#!/usr/bin/env python3
"""
Script kiểm tra lỗi hình học trong shapefile
Trạng thái: TEMPLATE - CHƯA TEST
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from osgeo import ogr, gdal
except ImportError:
    print("Lỗi: Cần cài đặt GDAL/OGR (pip install gdal)")
    sys.exit(1)

def check_geometry(geometry) -> Dict:
    """Kiểm tra một geometry"""
    errors = []
    
    if geometry is None:
        errors.append("NULL_GEOMETRY")
        return errors
    
    # Kiểm tra empty
    if geometry.IsEmpty():
        errors.append("EMPTY_GEOMETRY")
    
    # Kiểm tra validity
    if not geometry.IsValid():
        errors.append("INVALID_GEOMETRY")
    
    # Kiểm tra ring (cho polygon)
    if geometry.GetGeometryType() in [ogr.wkbPolygon, ogr.wkbMultiPolygon]:
        if geometry.GetGeometryRef(0).GetGeometryRef(0).GetX(0) == \
           geometry.GetGeometryRef(0).GetGeometryRef(0).GetX(-1):
            if geometry.GetGeometryRef(0).GetGeometryRef(0).GetY(0) == \
               geometry.GetGeometryRef(0).GetGeometryRef(0).GetY(-1):
                pass  # Closed ring OK
    
    return errors

def process_shapefile(shapefile_path: str) -> Dict:
    """Xử lý một shapefile"""
    driver = ogr.GetDriverByName('ESRI Shapefile')
    datasource = driver.Open(shapefile_path, 0)
    
    if datasource is None:
        return {'error': f'Không mở được file: {shapefile_path}'}
    
    layer = datasource.GetLayer()
    layer_defn = layer.GetLayerDefn()
    
    results = {
        'total': layer.GetFeatureCount(),
        'errors': {
            'NULL_GEOMETRY': [],
            'EMPTY_GEOMETRY': [],
            'INVALID_GEOMETRY': [],
            'OTHER': []
        }
    }
    
    feature = layer.GetNextFeature()
    while feature:
        geom = feature.GetGeometryRef()
        errors = check_geometry(geom)
        
        if errors:
            for error in errors:
                if error in results['errors']:
                    results['errors'][error].append(feature.GetFID())
                else:
                    results['errors']['OTHER'].append(feature.GetFID())
        
        feature = layer.GetNextFeature()
    
    datasource = None
    return results

def print_report(results: Dict, shapefile: str):
    """In báo cáo"""
    print("\n" + "=" * 60)
    print(f"KIỂM TRA HÌNH HỌC: {shapefile}")
    print("=" * 60)
    
    if 'error' in results:
        print(f"\nLỗi: {results['error']}")
        return
    
    print(f"\nTổng đối tượng: {results['total']}")
    
    total_errors = sum(len(v) for v in results['errors'].values())
    print(f"Tổng lỗi: {total_errors}")
    
    if total_errors > 0:
        print(f"\nTỷ lệ lỗi: {total_errors * 100 / results['total']:.2f}%")
    
    for error_type, fids in results['errors'].items():
        if fids:
            print(f"\n{error_type}: {len(fids)} đối tượng")
            print(f"  FID: {', '.join(str(f) for f in fids[:10])}")
            if len(fids) > 10:
                print(f"  ... và {len(fids) - 10} đối tượng khác")
    
    print("\n" + "=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Kiểm tra lỗi hình học')
    parser.add_argument('shapefile', help='Đường dẫn shapefile')
    args = parser.parse_args()
    
    if not Path(args.shapefile).exists():
        print(f"Lỗi: File không tồn tại: {args.shapefile}")
        sys.exit(1)
    
    results = process_shapefile(args.shapefile)
    print_report(results, args.shapefile)

if __name__ == '__main__':
    main()
