import os
import argparse

def generate_file_listing(directory, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_file:
        # Write the directory structure
        out_file.write("# Directory Structure:\n")
        for root, dirs, files in os.walk(directory):
            relative_path = os.path.relpath(root, directory)
            if relative_path == ".":
                relative_path = directory  # Use the passed root directory instead of "."
            out_file.write(f"{relative_path}:\n")
            for file in files:
                out_file.write(f"  - {file}\n")
        out_file.write("\n# Source Files:\n")
        
        # Write the content of each source file
        for root, dirs, files in os.walk(directory):
            for file in files:
                # Only include source files based on extensions
                if file.endswith(('.py', '.js', '.java', '.cpp', '.c', '.h', '.html', '.css', '.ts', '.go', '.rb', '.sh')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    out_file.write(f"<contents/{relative_path}>\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as src_file:
                            out_file.write(src_file.read())
                    except Exception as e:
                        out_file.write(f"Error reading file: {e}")
                    
                    out_file.write(f"\n</contents/{relative_path}>\n")
            out_file.write("\n")

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate a directory structure and source file listing.")
    parser.add_argument("directory", help="The directory to scan")
    args = parser.parse_args()

    # Validate the directory
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory.")
        exit(1)

    # Generate the file listing
    output_file = "context.txt"
    generate_file_listing(args.directory, output_file)
    print(f"Directory structure and source files written to {output_file}")
