"""Analiza y extrae los 3 archivos IMSCC base."""
import zipfile
import os

base_dir = r'c:\Users\g0nii\Desktop\Proyecto automatización de Maquetación\Elementos de las aulas'

files = {
    'educacion': os.path.join(base_dir, 'Aulas bases', 'aula-base-educacion-a-distancia-export (2).imscc'),
    'posgrado': os.path.join(base_dir, 'Aulas bases', 'aula-base-educacion-a-distancia-posgrado-export.imscc'),
    'cidilabs': os.path.join(base_dir, 'CIDILABS', 'cidiplus-export.imscc'),
}

for name, path in files.items():
    sep = "=" * 70
    print(f"\n{sep}")
    size_mb = os.path.getsize(path) / 1024 / 1024
    print(f"  ARCHIVO: {name} ({size_mb:.1f} MB)")
    print(sep)
    
    extract_dir = os.path.join(base_dir, f'_extracted_{name}')
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(path, 'r') as zf:
        entries = zf.namelist()
        print(f"  Total archivos: {len(entries)}")
        
        # Agrupar por carpeta raiz
        folders = {}
        for e in entries:
            parts = e.split('/')
            root = parts[0] if len(parts) > 1 else '(raiz)'
            if root not in folders:
                folders[root] = []
            folders[root].append(e)
        
        print(f"  Carpetas raiz: {list(folders.keys())}")
        for folder, items in sorted(folders.items()):
            print(f"    {folder}/ ({len(items)} archivos)")
            for item in items[:5]:
                info = zf.getinfo(item)
                print(f"      {item} ({info.file_size:,} bytes)")
            if len(items) > 5:
                print(f"      ... +{len(items)-5} mas")
        
        # Extraer todo
        zf.extractall(extract_dir)
        print(f"  Extraido en: {extract_dir}")
