#!/usr/bin/env python3
"""
Script kiểm tra metadata sau OCR
Trạng thái: TEMPLATE - CHƯA TEST
"""

import csv
import sys
import argparse
from pathlib import Path
from typing import Dict, List

# === CẤU HÌNH MẶC ĐỊNH ===
REQUIRED_FIELDS = [
    'so_giay_chung_nhan',
    'ngay_cap',
    'ho_ten',
    'dia_chi',
    'lo_dat',
    'dien_tich'
]

def load_csv(file_path: str) -> List[Dict]:
    """Đọc file CSV metadata"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    return data

def check_required_fields(record: Dict, required: List[str]) -> List[str]:
    """Kiểm tra trường bắt buộc"""
    missing = []
    for field in required:
        if field not in record or not record[field].strip():
            missing.append(field)
    return missing

def check_date_format(date_str: str) -> bool:
    """Kiểm tra định dạng ngày (YYYY-MM-DD)"""
    import re
    return bool(re.match(r'\d{4}-\d{2}-\d{2}', date_str))

def validate_metadata(csv_path: str, required_fields: List[str] = None) -> Dict:
    """Kiểm tra toàn bộ metadata"""
    if required_fields is None:
        required_fields = REQUIRED_FIELDS
    
    data = load_csv(csv_path)
    
    results = {
        'total': len(data),
        'valid': 0,
        'missing_fields': [],
        'invalid_dates': [],
        'empty_values': []
    }
    
    for idx, record in enumerate(data, 1):
        missing = check_required_fields(record, required_fields)
        
        if missing:
            results['missing_fields'].append({
                'row': idx,
                'missing': missing
            })
        
        # Kiểm tra ngày
        if 'ngay_cap' in record and record['ngay_cap']:
            if not check_date_format(record['ngay_cap']):
                results['invalid_dates'].append({
                    'row': idx,
                    'value': record['ngay_cap']
                })
        
        # Kiểm tra giá trị rỗng
        for field, value in record.items():
            if not value or not value.strip():
                results['empty_values'].append({
                    'row': idx,
                    'field': field
                })
        
        if not missing:
            results['valid'] += 1
    
    return results

def print_report(results: Dict):
    """In báo cáo"""
    print("\n" + "=" * 60)
    print("BÁO CÁO KIỂM TRA METADATA")
    print("=" * 60)
    
    print(f"\nTổng bản ghi: {results['total']}")
    print(f"Đạt yêu cầu: {results['valid']} ({results['valid']*100//results['total']}%)")
    print(f"Có lỗi: {results['total'] - results['valid']}")
    
    if results['missing_fields']:
        print(f"\n⚠️  TRƯỜNG THIẾU ({len(results['missing_fields'])} bản ghi):")
        for item in results['missing_fields'][:10]:
            print(f"  - Dòng {item['row']}: {', '.join(item['missing'])}")
        if len(results['missing_fields']) > 10:
            print(f"  ... và {len(results['missing_fields']) - 10} bản ghi khác")
    
    if results['invalid_dates']:
        print(f"\n⚠️  NGÀY KHÔNG HỢP LỆ ({len(results['invalid_dates'])} bản ghi):")
        for item in results['invalid_dates'][:5]:
            print(f"  - Dòng {item['row']}: {item['value']}")
    
    print("\n" + "=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Kiểm tra metadata sau OCR')
    parser.add_argument('--input', '-i', required=True, help='Đường dẫn file CSV')
    parser.add_argument('--fields', '-f', nargs='+', help='Trường bắt buộc (mặc định: sử dụng cấu hình)')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Lỗi: File không tồn tại: {args.input}")
        sys.exit(1)
    
    results = validate_metadata(args.input, args.fields)
    print_report(results)

if __name__ == '__main__':
    main()
