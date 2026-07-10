import os

for root, _, files in os.walk('dashboard'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                c = f.read()
            
            c = c.replace('use_container_width=True', 'width="stretch"')
            c = c.replace('use_container_width=False', 'width="content"')
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(c)

print('Replacement complete.')
