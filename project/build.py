import os
import re
import markdown
import shutil
import json
from jinja2 import Environment, FileSystemLoader

# Configuration
INPUT_DIR_TALKS = r"E:\Ajahn Thate\project\content\talks"
INPUT_DIR_BOOKS = r"E:\Ajahn Thate\project\content\books"
INPUT_DIR_BIO = r"E:\Ajahn Thate\project\content\bio"

OUTPUT_DIR = r"E:\Ajahn Thate\website_output"
TEMPLATES_DIR = "templates"
IFRAMES_JSON = "dhamma_talks_iframes.json"

def setup_directories():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if os.path.exists("static"):
        shutil.copytree("static", os.path.join(OUTPUT_DIR, "static"), dirs_exist_ok=True)

def get_markdown_files(directory):
    files = [f for f in os.listdir(directory) if f.endswith('.md')]
    
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower()
                for text in re.split(r'(\d+)', s)]
    
    return sorted(files, key=natural_sort_key)

def process_category(env, input_dir, output_subdir, list_filename, page_title, page_desc, iframes_data=None, is_bio=False):
    if not os.path.exists(input_dir):
        print(f"Warning: Directory not found: {input_dir}. Skipping {list_filename}.")
        return

    # Create the nested output directory if it doesn't exist
    full_output_subdir = os.path.join(OUTPUT_DIR, output_subdir)
    if not os.path.exists(full_output_subdir):
        os.makedirs(full_output_subdir)

    # Using the single content layout template
    content_template = env.get_template('talk.html')
    md_files = get_markdown_files(input_dir)
    items_data = []

    # First pass: Gather metadata
    for filename in md_files:
        name_without_ext = os.path.splitext(filename)[0]
        output_filename = f"{name_without_ext.replace(' ', '_')}.html"

        # Regex conditional for bio (numbers at end) vs books/talks (numbers at start)
        if is_bio:
            match = re.search(r'(\d+)\s*$', name_without_ext)
        else:
            match = re.match(r'^\s*(\d+)', name_without_ext)

        item_number = match.group(1) if match else ""

        items_data.append({
            'original_file': filename,
            'title': name_without_ext,
            'output_file': output_filename,
            'file_path_from_root': f"{output_subdir}/{output_filename}",
            'number': item_number
        })

    # Second pass: Generate individual pages
    for index, item in enumerate(items_data):
        input_path = os.path.join(input_dir, item['original_file'])
        with open(input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        html_content = markdown.markdown(md_content)

        prev_item = items_data[index - 1] if index > 0 else None
        next_item = items_data[index + 1] if index < len(items_data) - 1 else None
        
        audio_iframe = iframes_data.get(item['original_file'], None) if iframes_data else None

        rendered_item = content_template.render(
            title=item['title'],
            content=html_content,
            prev_talk=prev_item,
            next_talk=next_item,
            audio_iframe=audio_iframe,
            parent_url=list_filename,
            parent_title=page_title,
            root_path="../../" # Since files are in content/[category]/
        )

        output_path = os.path.join(full_output_subdir, item['output_file'])
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_item)

    # Generate the List Index for the category (This stays in the root)
    list_template = env.get_template('list_page.html')
    rendered_list = list_template.render(
        title=page_title,
        description=page_desc,
        items=items_data,
        root_path="" # List pages are in the root directory
    )
    with open(os.path.join(OUTPUT_DIR, list_filename), 'w', encoding='utf-8') as f:
        f.write(rendered_list)

def build_site():
    setup_directories()
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    
    iframes_data = {}
    if os.path.exists(IFRAMES_JSON):
        with open(IFRAMES_JSON, 'r', encoding='utf-8') as f:
            iframes_data = json.load(f)
    else:
        print(f"Warning: {IFRAMES_JSON} not found. Audio embeds will be skipped.")

    # Process all three dynamic sections with their new subdirectories
    process_category(env, INPUT_DIR_TALKS, 'content/talks', 'dhamma_talks.html', 'Dhamma Talks', 'An archive of recorded teachings of Ajahn Thate Desaraṅsī', iframes_data, is_bio=False)
    
    process_category(env, INPUT_DIR_BOOKS, 'content/books', 'dhamma_books.html', 'Dhamma Books', 'An archive of published writings by Ajahn Thate Desaraṅsī', None, is_bio=False)
    
    process_category(env, INPUT_DIR_BIO, 'content/bio', 'autobiography.html', 'Autobiography', 'The Life of a Forest Monk', None, is_bio=True)

    # Configured mapping for root-level static pages to specific layout templates
    static_pages = [
        {
            'output_file': 'index.html',
            'template_name': 'index.html',
            'title': 'Ajahn Thate Archive - Home'
        },
        {
            'output_file': 'about.html',
            'template_name': 'about.html',
            'title': 'About Ajahn Thate'
        },
        {
            'output_file': 'dhamma_quotes.html',
            'template_name': 'generic_page.html',
            'title': 'Dhamma Quotes'
        },
        
        {
            'output_file': 'download.html',
            'template_name': 'download.html',
            'title': 'Downloads'
        }
    ]
    
    for page in static_pages:
        try:
            template = env.get_template(page['template_name'])
        except Exception:
            print(f"Template '{page['template_name']}' not found. Falling back to generic_page.html for {page['output_file']}")
            template = env.get_template('generic_page.html')
            
        rendered_page = template.render(title=page['title'], root_path="")
        with open(os.path.join(OUTPUT_DIR, page['output_file']), 'w', encoding='utf-8') as f:
            f.write(rendered_page)
            
    print(f"\nWebsite successfully built in: {OUTPUT_DIR}")

if __name__ == "__main__":
    build_site()