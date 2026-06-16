# -*- coding: utf-8 -*-
"""Auditoría de fidelidad resumida (reutilizable).

Dos chequeos:
  1) Validez XML de cada paquete generado (imsmanifest, module_meta, topics,
     quizzes, assignments). Un XML mal formado (p.ej. un '&' sin escapar en un
     título) hace fallar la importación en Canvas: es BLOQUEANTE.
  2) Fidelidad de las páginas de contenido vs el aula hecha a mano (ratio de
     texto/tablas/links).
"""
import zipfile, sys, io, re
import xml.etree.ElementTree as ET
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from bs4 import BeautifulSoup

PARES = [
    ('fundamentos-de-la-gestion-de-proyectos-05-dot-2026-export (1).imscc',
     'output/working_01_Fundamentos_de_la_Gesti_n_de_Proyecto', 'Conti'),
    ('atraccion-seleccion-y-retencion-del-talento-04-dot-2026-export (1).imscc',
     'output/working_Atracci_n_Selecci_n_y_Retenci_n_de_Talen', 'Astori'),
    ('el-marketing-de-la-experiencia-de-clientes-cx-05-dot-2026-export (1).imscc',
     'output/working_00396', 'Marketing'),
    ('etica-cumplimiento-corporativo-y-perspectiva-ignaciana-2026-export.imscc',
     'output/working_EP00356', 'Mosquera'),
    ('seminario-electivo-problematica-del-habitat-e-inclusion-en-la-agenda-global-06-dot-2026-export.imscc',
     'output/working_Problem_tica_del_h_bitat_e_inclusi_n_en', 'Seminario'),
    ('etica-y-cooperacion-internacional-06-dot-2026-export.imscc',
     'output/working_tica_y_cooperaci_n_Internacional', 'EticaCoop'),
]
GOLD = Path('Elementos de las aulas/Ejemplo de aula ya maquetada')

def perfil(html):
    soup = BeautifulSoup(html, 'html.parser')
    return {
        'texto': len(soup.get_text(' ', strip=True)),
        'tablas': len(soup.find_all('table')),
        'links': len(soup.find_all('a')),
        'figs_diseno': len(re.findall(r'Multimedia%20cargada/(?:M_?\d|Figura|Tabla|Esquema)', html)),
    }

def validar_xml_paquete(working):
    """Devuelve [(archivo, error)] de los XML mal formados del working dir."""
    rotos = []
    raiz = Path(working)
    if not raiz.exists():
        return rotos
    for xml in raiz.rglob('*.xml'):
        try:
            ET.fromstring(xml.read_text(encoding='utf-8'))
        except Exception as e:
            rotos.append((str(xml.relative_to(raiz)), str(e)))
    return rotos

# ---- 1) Validez XML (bloqueante para Canvas) ----
print('=== Validez XML de los paquetes generados ===')
xml_rotos_total = 0
for _gold, working, etiqueta in PARES:
    rotos = validar_xml_paquete(working)
    xml_rotos_total += len(rotos)
    if rotos:
        for arch, err in rotos:
            print(f'  ✗ [{etiqueta}] {arch}: {err}')
    else:
        print(f'  ✓ [{etiqueta}] XML OK')
print()

stats = {'paginas': 0, 'fieles': 0, 'ratios': []}
print(f'{"curso/página":58s} {"texto":>6s} {"tablas":>7s} {"links":>9s}')
for gold_name, working, etiqueta in PARES:
    z = zipfile.ZipFile(GOLD / gold_name)
    wdir = Path(working) / 'wiki_content'
    for name in sorted(z.namelist()):
        if not name.startswith('wiki_content/') or not name.endswith('.html'):
            continue
        base = name.split('/')[-1]
        if 'el-primer-uno' in base or 'el-primer-numero' in base:
            continue  # placeholders del aula base presentes en ambos
        gen_file = wdir / base
        if not gen_file.exists():
            pref = '-'.join(base.split('-')[:3])
            cand = list(wdir.glob(pref + '-*.html'))
            gen_file = cand[0] if cand else None
        pm = perfil(z.read(name).decode('utf-8', errors='replace'))
        if not (gen_file and Path(gen_file).exists()):
            continue
        pg = perfil(Path(gen_file).read_text(encoding='utf-8'))
        ratio = pg['texto'] / pm['texto'] if pm['texto'] else 1
        stats['paginas'] += 1
        stats['ratios'].append(ratio)
        fiel = 0.8 <= ratio <= 1.25 and pg['tablas'] <= pm['tablas'] + 1
        if fiel:
            stats['fieles'] += 1
        else:
            print(f'⚠ [{etiqueta}] {base[:48]:50s} {ratio:5.2f} '
                  f'{pm["tablas"]}→{pg["tablas"]:<4d} {pm["links"]}→{pg["links"]}')
print()
import statistics
print(f'TOTAL: {stats["paginas"]} páginas | dentro de rango fiel (0.8-1.25): '
      f'{stats["fieles"]} ({stats["fieles"]/stats["paginas"]:.0%}) | '
      f'ratio mediano: {statistics.median(stats["ratios"]):.2f}')
if xml_rotos_total:
    print(f'\n⛔ {xml_rotos_total} archivo(s) XML mal formado(s): el/los paquete(s) '
          'NO importarán bien en Canvas. Corregir antes de entregar.')
else:
    print('\n✓ XML de todos los paquetes válido.')
