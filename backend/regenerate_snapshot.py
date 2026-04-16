import json
import requests

response = requests.get('http://localhost:8000/openapi.json')
schema = response.json()

# Extract critical paths (per B07: no dashboard/layout)
critical_paths = {
    '/auth/login': schema.get('paths', {}).get('/auth/login', {}),
    '/auth/register': schema.get('paths', {}).get('/auth/register', {}),
    '/auth/refresh': schema.get('paths', {}).get('/auth/refresh', {}),
    '/api/modules': schema.get('paths', {}).get('/api/modules', {}),
    '/health': schema.get('paths', {}).get('/health', {}),
}

# Extract critical schemas (defines the contract per ARCH-5.2)
schemas = schema.get('components', {}).get('schemas', {})
critical_schemas = {
    'TokenPair': schemas.get('TokenPair', {}),
    'TokenRefresh': schemas.get('TokenRefresh', {}),
    'ModuleResponse': schemas.get('ModuleResponse', {}),
    'ModuleListResponse': schemas.get('ModuleListResponse', {}),
    'HealthResponse': schemas.get('HealthResponse', {}),
}

# Complete API contract
critical_api = {
    'paths': critical_paths,
    'components': {'schemas': critical_schemas}
}

with open('tests/snapshots/openapi_critical.json', 'w') as f:
    json.dump(critical_api, f, indent=2, sort_keys=True)

print('OpenAPI baseline regenerated with complete API contract')
print('Paths:', list(critical_paths.keys()))
print('Schemas:', list(critical_schemas.keys()))
