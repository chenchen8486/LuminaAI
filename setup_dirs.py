import os

dirs = [
    'configs',
    'core/engine',
    'core/models',
    'core/data',
    'core/export',
    'ui/resources',
    'ui/widgets',
    'ui/wizards',
    'ui/pages',
    'user_workspace/models',
    'user_workspace/projects',
    'utils'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")
