#!/usr/bin/env python3
"""
Book content loader for realistic benchmark prompts
"""

import PyPDF2
import tiktoken
import re
from typing import List, Optional

class BookChunkLoader:
    def __init__(self, pdf_path: str = "books/harrypotter.pdf"):
        self.pdf_path = pdf_path
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
        self.book_text = None
        self.load_book()
    
    def load_book(self):
        """Load and extract text from the PDF"""
        print(f"📖 Loading book from {self.pdf_path}...")
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                text_parts = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    # Clean up the text
                    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                    text = text.strip()
                    
                    if text:  # Only add non-empty pages
                        text_parts.append(text)
                
                self.book_text = ' '.join(text_parts)
                
                # Calculate token count
                token_count = len(self.encoding.encode(self.book_text))
                
                print(f"✅ Loaded {len(pdf_reader.pages)} pages")
                print(f"📝 Total text length: {len(self.book_text):,} characters")
                print(f"🔢 Total tokens: {token_count:,}")
                
        except Exception as e:
            print(f"❌ Error loading book: {e}")
            # Fallback to synthetic content
            self.book_text = self._generate_fallback_content()
    
    def _generate_fallback_content(self) -> str:
        """Generate fallback content if PDF loading fails"""
        return """
        In a world of magic and wonder, where ancient spells echo through castle halls and mysterious creatures roam forbidden forests, young wizards learn the arts of enchantment and divination. The great library contains thousands of volumes on potion-making, transfiguration, and the delicate art of charms. Students practice their wand movements in spacious classrooms while professors observe their progress with keen eyes.
        
        The castle itself is a marvel of magical architecture, with moving staircases that change direction at will, portraits that speak and move within their frames, and suits of armor that patrol the corridors. In the depths of the dungeons, bubbling cauldrons produce mysterious brews while in the highest towers, telescopes point toward the stars where the future might be read in celestial movements.
        
        Ancient magic flows through every stone of the castle, accumulated over centuries of learning and practice. The very walls seem to hum with power, and students often report feeling the presence of magic in the air itself. This is a place where the impossible becomes possible, where young minds are shaped not just by knowledge but by wonder and the endless possibilities that magic represents.
        """ * 100  # Repeat to make it longer
    
    def get_chunk_by_tokens(self, target_tokens: int) -> str:
        """Get a chunk of book content with approximately target_tokens"""
        if not self.book_text:
            return self._generate_fallback_content()[:target_tokens * 4]
        
        # Encode the full text to get token positions
        tokens = self.encoding.encode(self.book_text)
        
        if len(tokens) <= target_tokens:
            # If book is shorter than target, repeat it
            repeats_needed = (target_tokens // len(tokens)) + 1
            repeated_tokens = tokens * repeats_needed
            chunk_tokens = repeated_tokens[:target_tokens]
        else:
            # Take a chunk from the book
            # Start from different positions to get variety
            import random
            max_start = len(tokens) - target_tokens
            start_pos = random.randint(0, max(0, max_start))
            chunk_tokens = tokens[start_pos:start_pos + target_tokens]
        
        # Decode back to text
        chunk_text = self.encoding.decode(chunk_tokens)
        
        # Clean up any truncated sentences at the end
        chunk_text = self._clean_chunk_end(chunk_text)
        
        return chunk_text
    
    def _clean_chunk_end(self, text: str) -> str:
        """Clean up truncated sentences at the end of a chunk"""
        # Find the last complete sentence
        sentences = text.split('.')
        if len(sentences) > 1:
            # Keep all complete sentences
            complete_text = '.'.join(sentences[:-1]) + '.'
            return complete_text
        else:
            # If no complete sentences, just return as is
            return text
    
    def create_analysis_prompt(self, book_chunk: str) -> str:
        """Create a realistic analysis prompt using the book chunk"""
        
        system_prompts = [
            """You are a literary analysis expert. Analyze the following text for themes, character development, narrative techniques, and literary devices. Provide detailed insights about the author's writing style, plot structure, and symbolic elements. Consider the historical and cultural context of the work.""",
            
            """You are a creative writing instructor. Examine this text excerpt and provide feedback on the author's use of language, pacing, dialogue, and descriptive techniques. Identify strengths and areas for improvement, and suggest how similar techniques could be applied in other creative works.""",
            
            """You are a book editor working on a comprehensive analysis. Review this text for narrative flow, character consistency, plot development, and thematic elements. Provide detailed notes on structure, style, and content that would be useful for editorial review.""",
            
            """You are a literature professor preparing lecture notes. Analyze this passage for its literary merit, examining the author's use of symbolism, metaphor, character development, and plot advancement. Consider how this excerpt fits within the broader context of the work and genre.""",
            
            """You are a script adaptation consultant. Evaluate this text for its potential adaptation to screen or stage. Consider dialogue, visual elements, character interactions, and dramatic tension. Provide recommendations for how key scenes could be translated to visual media."""
        ]
        
        import random
        system_prompt = random.choice(system_prompts)
        
        full_prompt = f"{system_prompt}\n\nText to analyze:\n\n{book_chunk}\n\nPlease provide your detailed analysis:"
        
        return full_prompt
    
    def get_token_count(self, text: str) -> int:
        """Get accurate token count for text"""
        return len(self.encoding.encode(text))

def test_book_loader():
    """Test the book loader functionality"""
    loader = BookChunkLoader()
    
    # Test different chunk sizes
    test_sizes = [1000, 5000, 10000, 20000]
    
    for size in test_sizes:
        chunk = loader.get_chunk_by_tokens(size)
        actual_tokens = loader.get_token_count(chunk)
        
        print(f"\nTarget: {size:,} tokens")
        print(f"Actual: {actual_tokens:,} tokens ({actual_tokens/size*100:.1f}% of target)")
        print(f"Text preview: {chunk[:200]}...")
        
        # Test creating analysis prompt
        prompt = loader.create_analysis_prompt(chunk)
        prompt_tokens = loader.get_token_count(prompt)
        print(f"Full prompt tokens: {prompt_tokens:,}")

if __name__ == "__main__":
    test_book_loader()
