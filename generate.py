#!/usr/bin/env python3
import os
import shutil
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from PIL import Image
from PIL.ExifTags import TAGS
from collections import defaultdict


# Configurazione percorsi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
BASE_PATH = ""  # Percorso base per il sito (può essere modificato per deployment)

# Carica l'ambiente Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
env.filters['to_json'] = json.dumps
env.globals['base_path'] = BASE_PATH


# Funzione per pulire la cartella output
def clean_output_directory():
    """Rimuove completamente la cartella output e la ricrea vuota"""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        print(f"Cartella '{OUTPUT_DIR}' rimossa")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Cartella '{OUTPUT_DIR}' creata")


# Funzione per ottenere le categorie dalle cartelle delle immagini
def get_categories():
    categories = []
    for item in os.listdir(IMAGES_DIR):
        if os.path.isdir(os.path.join(IMAGES_DIR, item)):
            # Ignora le cartelle nascoste
            if not item.startswith('.'):
                categories.append(item)
    return sorted(categories)


# Estrae i metadati EXIF da un'immagine
def extract_metadata(image_path):
    try:
        with Image.open(image_path) as img:
            metadata = {
                'dimensions': img.size  # (larghezza, altezza)
            }

            exif_data = img._getexif()
            if not exif_data:
                return metadata

            # Estrae data e luogo dai tag EXIF
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)

                # Data di scatto
                if tag_name == 'DateTimeOriginal':
                    try:
                        # Converti in formato YYYY-MM-DD
                        metadata['date'] = value.split()[0].replace(':', '-')
                    except (AttributeError, IndexError):
                        pass

                # Luogo (GPS)
                elif tag_name == 'GPSInfo':
                    try:
                        # Estrai coordinate approssimative (esempio semplificato)
                        latitude = str(value.get(2, [])[:3]) or 'N/D'
                        longitude = str(value.get(4, [])[:3]) or 'N/D'
                        metadata['location'] = f"{latitude}, {longitude}"
                    except:
                        pass

            return metadata

    except Exception as e:
        print(f"Errore lettura metadati per {image_path}: {str(e)}")
        return {'dimensions': (0, 0)}


# Funzione per ottenere le immagini per categoria
def get_images_by_category():
    images = defaultdict(list)
    categories = get_categories()

    for category in categories:
        category_path = os.path.join(IMAGES_DIR, category)

        image_files = sorted([
            f for f in os.listdir(category_path)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        ])

        num_images = len(image_files)

        for idx, filename in enumerate(image_files):
            full_image_path = os.path.join(category_path, filename)
            metadata = extract_metadata(full_image_path)

            prev_filename = image_files[(idx - 1) % num_images]
            next_filename = image_files[(idx + 1) % num_images]

            images[category].append({
                'file_path': f"static/images/{category}/{filename}",
                'page_path': f"{category}/{os.path.splitext(filename)[0]}.html",
                'previous_page_path': f"{category}/{os.path.splitext(prev_filename)[0]}.html",
                'next_page_path': f"{category}/{os.path.splitext(next_filename)[0]}.html",
                'title': os.path.splitext(filename)[0].replace('_', ' ').title(),
                'date': metadata.get('date'),
                'location': metadata.get('location'),
                'dimensions': metadata['dimensions']
            })

    return dict(images)  # Converti in dict normale se non vuoi defaultdict


# Funzione per copiare i file statici
def copy_static_files():
    # Copia i file CSS
    css_src = os.path.join(STATIC_DIR, 'css')
    css_dest = os.path.join(OUTPUT_DIR, 'static', 'css')
    shutil.copytree(css_src, css_dest, dirs_exist_ok=True)

    # Copia i file JS
    js_src = os.path.join(STATIC_DIR, 'js')
    js_dest = os.path.join(OUTPUT_DIR, 'static', 'js')
    shutil.copytree(js_src, js_dest, dirs_exist_ok=True)

    # Copia le immagini (mantenendo la struttura delle cartelle)
    images_src = IMAGES_DIR
    images_dest = os.path.join(OUTPUT_DIR, 'static', 'images')
    shutil.copytree(images_src, images_dest, dirs_exist_ok=True)


def generate_sitemap():
    sitemap_path = os.path.join(OUTPUT_DIR, "sitemap.xml")
    base_url = "https://www.fabiofedrigo.it"  # Cambia con il tuo dominio reale

    urls = []

    # Aggiungi la homepage
    urls.append(f"{base_url}/index.html")

    # Scandisci l'intera cartella output
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(".html") and file != "index.html":
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, OUTPUT_DIR).replace("\\", "/")
                urls.append(f"{base_url}/{relative_path}")

    # Scrivi il file XML
    with open(sitemap_path, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url in urls:
            f.write("  <url>\n")
            f.write(f"    <loc>{url}</loc>\n")
            f.write("  </url>\n")
        f.write("</urlset>\n")

    print(f"Sitemap generata: {sitemap_path}")


# Funzione principale per generare il sito
def generate_site():
    print("Inizio generazione sito...")

    # Pulisce e ricrea la cartella di output
    clean_output_directory()

    # Ricrea le sottocartelle necessarie
    os.makedirs(os.path.join(OUTPUT_DIR, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'static', 'images'), exist_ok=True)

    # Prepara i dati
    categories = get_categories()
    images = get_images_by_category()
    current_year = datetime.now().year

    # Crea il contesto per la home page
    home_context = {
        'categories': categories,
        'images': images,
        'current_year': current_year,
        'base_path': '.',
        'is_homepage': True
    }

    # Renderizza la home page
    home_template = env.get_template('home.html.j2')
    home_output = home_template.render(home_context)

    # Salva la home page
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(home_output)
    print(f"Home page generata: {os.path.join(OUTPUT_DIR, 'index.html')}")

    # Genera le pagine di dettaglio per ogni immagine
    photo_view_template = env.get_template('image_view.html.j2')
    for category in categories:
        for image in images[category]:
            # Crea percorso di output per la pagina di dettaglio
            category_dir = os.path.join(OUTPUT_DIR, category)
            os.makedirs(category_dir, exist_ok=True)

            # Usa il nome del file per creare il percorso HTML
            output_path = os.path.join(OUTPUT_DIR, image['page_path'])

            # Prepara il contesto
            photo_view_context = {
                'category': category,
                'images': images[category],
                'current_image': image,
                'current_year': current_year,
                'base_path': '..',
                'is_homepage': False
            }

            # Renderizza e salva
            photo_view_output = photo_view_template.render(photo_view_context)
            with open(output_path, 'w') as f:
                f.write(photo_view_output)

            print(f"Pagina dettaglio generata: {output_path}")

    # Copia i file statici
    copy_static_files()
    print("File statici copiati.")

    generate_sitemap()

    print("Generazione completata con successo!")


# Esegui la generazione
if __name__ == "__main__":
    generate_site()
