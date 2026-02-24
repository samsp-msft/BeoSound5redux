import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
_LOGGER = logging.getLogger(__name__)

def reformat_cache():
    """
    Walks through the motn_cache directory and pretty-prints all JSON files.
    """
    cache_dir = os.path.join(os.path.dirname(__file__), 'motn_cache')
    
    if not os.path.exists(cache_dir):
        _LOGGER.error(f"Cache directory not found: {cache_dir}")
        return

    count = 0
    errors = 0

    _LOGGER.info(f"Starting reformat in {cache_dir}...")

    # Walk through the 256 bucket directories
    for root, dirs, files in os.walk(cache_dir):
        for filename in files:
            if filename.endswith('.json'):
                file_path = os.path.join(root, filename)
                try:
                    # Read current data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Write back formatted
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    
                    count += 1
                    if count % 100 == 0:
                        _LOGGER.info(f"Processed {count} files...")
                
                except Exception as e:
                    _LOGGER.error(f"Error processing {file_path}: {e}")
                    errors += 1

    _LOGGER.info(f"Finished. Reformatted {count} files with {errors} errors.")

if __name__ == "__main__":
    reformat_cache()
