import re

with open('price_compare_bot/service/search/taobao_shop/service.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')
    
    matches = []
    for i, line in enumerate(lines):
        if 'TARGET_SHOPS' in line:
            matches.append((i+1, line))
    
    print(f'Found {len(matches)} matches:')
    for line_num, line in matches:
        print(f'{line_num}: {line}')
        
    # 也搜索TARGET_SHOPS的定义
    print('\nSearching for TARGET_SHOPS definition...')
    for i, line in enumerate(lines):
        if 'TARGET_SHOPS' in line and '=' in line:
            print(f'Possible definition at line {i+1}: {line}')