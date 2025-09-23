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

## Included Sample Book

To make it easy to get started, the repository includes a public-domain
text from Project Gutenberg:

- `books/alice_adventures_in_wonderland.txt`

The default `config.yaml` points at this file, so the benchmark works
out-of-the-box. You are welcome to swap in any other text—just update
`content.book_path` accordingly.

### Need an even larger book?

If you want to stress-test 100k+ token contexts, download a long public
domain novel such as *War and Peace* (Project Gutenberg ebook #2600,
~3.2 MB of text) and drop it in this directory. Point `content.book_path`
at the new file and rerun the benchmark.

## Testing Without a Book

If no book is available, the `book_loader.py` will fall back to synthetic content, but this won't be as realistic for benchmarking purposes.
