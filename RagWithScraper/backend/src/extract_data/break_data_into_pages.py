import json
import os

def break_data_into_pages():
    # Specify the path to your JSON file.
    input_file = "data/raw/crawl_status_20250408_232747.json"
    
    # Load the JSON data.
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Create a new folder called "pages" if it doesn't already exist.
    output_folder = "data/pages"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Iterate over each page entry in the data.
    # Each entry is stored in data["data"].
    for i, page in enumerate(data.get("data", [])):
        # Try to extract a title from the metadata for naming.
        metadata = page.get("metadata", {})
        title = metadata.get("title", f"page_{i}")
        
        # Create a safe file name by only allowing alphanumeric characters and underscores.
        safe_title = "".join(c if c.isalnum() or c in (" ", "_") else "_" for c in title).strip().replace(" ", "_")
        if not safe_title:
            safe_title = f"page_{i}"
        
        filename = f"{safe_title}.json"
        output_path = os.path.join(output_folder, filename)
        
        # Save the page's data (including metadata) as a separate JSON file.
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(page, out_f, ensure_ascii=False, indent=4)
        
        print(f"Saved: {output_path}")

if __name__ == "__main__":
    break_data_into_pages()
