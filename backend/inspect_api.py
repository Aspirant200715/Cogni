from hindsight_client_api.api import default_api
import inspect

source = inspect.getsource(default_api.DefaultApi.recall_memories)
# Find the resource path
lines = source.split('\n')
for i, line in enumerate(lines[:100]):
    print(f"{i:3d}: {line}")
