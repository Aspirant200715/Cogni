#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('HINDSIGHT_API_KEY')
print(f'Key found: {bool(key)}')
print(f'Key repr: {repr(key)}')
print(f'Key length: {len(key) if key else 0}')

print('\n--- Testing Updated HindsightService ---')
try:
    from app.services.hindsight_service import hindsight_service
    print('[OK] Service imported')
    print(f'   api_available: {hindsight_service.api_available}')
    print(f'   client type: {type(hindsight_service.client).__name__}')
    
    if hindsight_service.api_available:
        print('\nCalling hindsight_service.recall_temporal_archaeology()...')
        import asyncio
        result = asyncio.run(hindsight_service.recall_temporal_archaeology('test', 3))
        if result.get('demo_mode'):
            print(f'[DEMO] Still in demo mode')
        else:
            print(f'[SUCCESS] Got real API response!')
            print(f'Result: {result}')
    else:
        print('[ERROR] API not available')
except Exception as e:
    import traceback
    print(f'[ERROR] {type(e).__name__}: {str(e)[:200]}')
    traceback.print_exc()
