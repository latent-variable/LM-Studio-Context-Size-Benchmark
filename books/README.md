# Book Content Directory

This directory should contain the book or text files used for generating realistic prompts in the benchmark.

## Supported Formats

- **PDF** (recommended) - `.pdf` files
- **Plain Text** - `.txt` files  
- **EPUB** - `.epub` files (if you extend the book_loader.py)
- **Word Documents** - `.docx`, `.doc` files (if you extend the book_loader.py)

## Adding Your Content

1. **Download or obtain a book file** (ensure you have legal rights to use it)
2. **Place it in this directory** - e.g., `books/mybook.pdf`
3. **Update the configuration** - Edit `config.yaml`:
   ```yaml
   content:
     book_path: "books/mybook.pdf"
   ```

## Recommended Books

For realistic benchmarking, use books with:
- **Long content** (500+ pages) to support large context sizes
- **Varied vocabulary** and complex sentence structures
- **Multiple chapters/sections** for content variety

Good options:
- Classic literature (often public domain)
- Technical documentation
- Academic papers or textbooks
- Fiction novels

## Legal Considerations

⚠️ **Important**: Only use books you have legal rights to use:
- Public domain books (Project Gutenberg, etc.)
- Books you own legally
- Open source documentation
- Your own written content

## Current Configuration

The default configuration expects: `books/harrypotter.pdf`

If you don't have this file, either:
1. Add a book with this name, or
2. Update `config.yaml` to point to your book file

## Testing Without a Book

If no book is available, the `book_loader.py` will fall back to synthetic content, but this won't be as realistic for benchmarking purposes.
