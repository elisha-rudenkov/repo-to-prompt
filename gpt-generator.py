import os
import zipfile
import fnmatch

def should_ignore(file_path, ignore_patterns):
    return any(fnmatch.fnmatch(file_path, pattern) for pattern in ignore_patterns)

def process_directory(directory, output_file, base_path, ignore_patterns):
    for root, dirs, files in os.walk(directory):
        rel_path = os.path.relpath(root, base_path)
        if rel_path != '.':
            output_file.write(f"\n#DIRECTORY: {rel_path}\n\n")
        
        for file in files:
            file_path = os.path.join(root, file)
            rel_file_path = os.path.relpath(file_path, base_path)
            
            if should_ignore(rel_file_path, ignore_patterns):
                continue
            
            output_file.write(f"\n\n+++++ #FILE: {file}\n\n")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    output_file.write(f.read())
                output_file.write("\n\n")
            except Exception as e:
                output_file.write(f"Error reading file: {str(e)}\n\n")

def main():
    zip_file_path = input("Enter the path to your zipped GitHub repo: ")
    output_file_path = "gpt-context.txt"

    #if input is null default to the first zip in current directory
    if zip_file_path == "":
        #find all zip files in current directory
        zip_files = [f for f in os.listdir('.') if f.endswith('.zip')]
        if len(zip_files) == 0:
            print("No zip files found in current directory")
            return
        zip_file_path = zip_files[0]
        print(f"Using {zip_file_path} as the input file")
        
        
    
    # Extract the zip file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        extract_dir = "temp_extracted_repo"
        zip_ref.extractall(extract_dir)
    
    # Read .gitignore patterns
    ignore_patterns = []
    gitignore_path = os.path.join(extract_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as gitignore_file:
            ignore_patterns = [line.strip() for line in gitignore_file if line.strip() and not line.startswith('#')]
    
    # Process the extracted directory
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        process_directory(extract_dir, output_file, extract_dir, ignore_patterns)
    
    # Clean up: remove the temporary extracted directory
    for root, dirs, files in os.walk(extract_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(extract_dir)
    
    print(f"Processing complete. Output written to {output_file_path}")

if __name__ == "__main__":
    main()
