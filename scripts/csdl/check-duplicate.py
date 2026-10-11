#!/usr/bin/env python3
"""
Script kiểm tra bản ghi trùng trong CSDL
Trạng thái: TEMPLATE - CHƯA TEST
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

def load_connection_config(config_path: str) -> Dict:
    """Đọc cấu hình kết nối"""
    with open(config_path, 'r') as f:
        return json.load(f)

def connect_db(config: Dict):
    """Kết nối CSDL"""
    db_type = config.get('type', 'postgresql')
    
    if db_type == 'postgresql':
        import psycopg2
        return psycopg2.connect(
            host=config['host'],
            port=config.get('port', 5432),
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
    elif db_type == 'mssql':
        import pymssql
        return pymssql.connect(
            server=config['host'],
            port=config.get('port', 1433),
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
    else:
        raise ValueError(f"Kiểu CSDL không hỗ trợ: {db_type}")

def check_duplicates(connection, table: str, fields: List[str]) -> List[Dict]:
    """Kiểm tra bản ghi trùng"""
    cursor = connection.cursor()
    
    # Xây dựng query
    fields_str = ', '.join(fields)
    query = f"""
        SELECT {fields_str}, COUNT(*) as count
        FROM {table}
        GROUP BY {fields_str}
        HAVING COUNT(*) > 1
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    duplicates = []
    for row in results:
        record = dict(zip(fields, row[:-1]))
        record['duplicate_count'] = row[-1]
        duplicates.append(record)
    
    cursor.close()
    return duplicates

def print_report(duplicates: List[Dict], table: str, fields: List[str]):
    """In báo cáo"""
    print("\n" + "=" * 60)
    print(f"KIỂM TRA BẢN GHI TRÙNG: {table}")
    print("=" * 60)
    
    print(f"\nTrường kiểm tra: {', '.join(fields)}")
    print(f"Tổng nhóm trùng: {len(duplicates)}")
    
    if duplicates:
        total_duplicates = sum(d['duplicate_count'] for d in duplicates)
        print(f"Tổng bản ghi trùng: {total_duplicates}")
        
        print("\nChi tiết:")
        for i, dup in enumerate(duplicates[:20], 1):
            print(f"\n{i}. Số lần trùng: {dup['duplicate_count']}")
            for field in fields:
                print(f"   {field}: {dup[field]}")
        
        if len(duplicates) > 20:
            print(f"\n... và {len(duplicates) - 20} nhóm trùng khác")
    else:
        print("\n✓ Không có bản ghi trùng")
    
    print("\n" + "=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Kiểm tra bản ghi trùng')
    parser.add_argument('--db', required=True, help='File cấu hình kết nối CSDL (JSON)')
    parser.add_argument('--table', required=True, help='Tên bảng')
    parser.add_argument('--fields', required=True, nargs='+', help='Danh sách trường kiểm tra trùng')
    
    args = parser.parse_args()
    
    if not Path(args.db).exists():
        print(f"Lỗi: File cấu hình không tồn tại: {args.db}")
        return
    
    config = load_connection_config(args.db)
    conn = connect_db(config)
    
    duplicates = check_duplicates(conn, args.table, args.fields)
    print_report(duplicates, args.table, args.fields)
    
    conn.close()

if __name__ == '__main__':
    main()
