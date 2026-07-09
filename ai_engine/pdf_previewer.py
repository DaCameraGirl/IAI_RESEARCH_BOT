"""
PDF Previewer - Generate preview images from PDF first page
Helps verify document quality before full review
"""

from pathlib import Path
from typing import Optional, Dict
import base64
import io
import requests
from PIL import Image
import fitz  # PyMuPDF


class PDFPreviewer:
    """
    Generate preview images from PDF documents
    Features:
    - First page thumbnail generation
    - Text extraction from first page
    - Metadata extraction
    - Quality assessment
    """
    
    def __init__(
        self,
        preview_width: int = 400,
        preview_height: int = 600,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize PDF previewer
        
        Args:
            preview_width: Preview image width in pixels
            preview_height: Preview image height in pixels
            cache_dir: Directory to cache preview images
        """
        self.preview_width = preview_width
        self.preview_height = preview_height
        
        if cache_dir is None:
            cache_dir = Path(".bob/tmp/pdf_previews")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_preview(
        self,
        pdf_path: Optional[Path] = None,
        pdf_url: Optional[str] = None,
        pdf_bytes: Optional[bytes] = None
    ) -> Dict:
        """
        Generate preview from PDF
        
        Args:
            pdf_path: Path to local PDF file
            pdf_url: URL to PDF file
            pdf_bytes: PDF file bytes
            
        Returns:
            Preview dict with image, text, metadata
        """
        # Load PDF
        if pdf_path:
            doc = fitz.open(pdf_path)
            source = str(pdf_path)
        elif pdf_url:
            # Download PDF
            response = requests.get(pdf_url, timeout=30)
            response.raise_for_status()
            pdf_bytes = response.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            source = pdf_url
        elif pdf_bytes:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            source = "bytes"
        else:
            raise ValueError("Must provide pdf_path, pdf_url, or pdf_bytes")
        
        try:
            # Get first page
            if len(doc) == 0:
                return {
                    'success': False,
                    'error': 'PDF has no pages'
                }
            
            first_page = doc[0]
            
            # Generate preview image
            preview_image = self._render_page_image(first_page)
            
            # Extract text from first page
            first_page_text = first_page.get_text()
            
            # Extract metadata
            metadata = self._extract_metadata(doc)
            
            # Quality assessment
            quality = self._assess_quality(first_page, first_page_text)
            
            return {
                'success': True,
                'source': source,
                'preview_image': preview_image,
                'first_page_text': first_page_text[:1000],  # First 1000 chars
                'metadata': metadata,
                'quality': quality,
                'page_count': len(doc)
            }
        
        finally:
            doc.close()
    
    def _render_page_image(self, page) -> str:
        """Render page to image and return as base64"""
        # Render page to pixmap
        zoom = 2.0  # Higher resolution
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        
        # Resize to preview dimensions
        img.thumbnail((self.preview_width, self.preview_height), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{img_base64}"
    
    def _extract_metadata(self, doc) -> Dict:
        """Extract PDF metadata"""
        metadata = doc.metadata
        
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'keywords': metadata.get('keywords', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', '')
        }
    
    def _assess_quality(self, page, text: str) -> Dict:
        """Assess PDF quality"""
        # Check if page has text
        has_text = len(text.strip()) > 100
        
        # Check if page has images
        image_list = page.get_images()
        has_images = len(image_list) > 0
        
        # Check page dimensions
        rect = page.rect
        width = rect.width
        height = rect.height
        
        # Determine quality
        if has_text and width > 400 and height > 400:
            quality_score = 'high'
        elif has_text or has_images:
            quality_score = 'medium'
        else:
            quality_score = 'low'
        
        return {
            'score': quality_score,
            'has_text': has_text,
            'has_images': has_images,
            'text_length': len(text),
            'image_count': len(image_list),
            'dimensions': {
                'width': width,
                'height': height
            }
        }
    
    def save_preview_html(self, preview: Dict, output_path: Path):
        """Save preview as HTML file for easy viewing"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>PDF Preview</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 20px auto;
            padding: 20px;
        }}
        .preview-image {{
            border: 1px solid #ccc;
            margin: 20px 0;
        }}
        .metadata {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .quality {{
            padding: 10px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .quality.high {{ background: #d4edda; }}
        .quality.medium {{ background: #fff3cd; }}
        .quality.low {{ background: #f8d7da; }}
        .text-preview {{
            background: #f9f9f9;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <h1>PDF Preview</h1>
    
    <div class="quality {preview['quality']['score']}">
        <strong>Quality:</strong> {preview['quality']['score'].upper()}<br>
        <strong>Pages:</strong> {preview['page_count']}<br>
        <strong>Has Text:</strong> {'Yes' if preview['quality']['has_text'] else 'No'}<br>
        <strong>Has Images:</strong> {'Yes' if preview['quality']['has_images'] else 'No'}
    </div>
    
    <h2>First Page Preview</h2>
    <img src="{preview['preview_image']}" class="preview-image" alt="First page preview">
    
    <h2>Metadata</h2>
    <div class="metadata">
        <strong>Title:</strong> {preview['metadata'].get('title', 'N/A')}<br>
        <strong>Author:</strong> {preview['metadata'].get('author', 'N/A')}<br>
        <strong>Creator:</strong> {preview['metadata'].get('creator', 'N/A')}<br>
        <strong>Creation Date:</strong> {preview['metadata'].get('creation_date', 'N/A')}
    </div>
    
    <h2>First Page Text (excerpt)</h2>
    <div class="text-preview">{preview['first_page_text']}</div>
</body>
</html>
"""
        
        output_path.write_text(html, encoding='utf-8')
        print(f"✓ Preview saved: {output_path}")


# Example usage
if __name__ == "__main__":
    previewer = PDFPreviewer()
    
    # Example: Generate preview from URL
    pdf_url = "https://example.com/document.pdf"
    
    try:
        preview = previewer.generate_preview(pdf_url=pdf_url)
        
        if preview['success']:
            print(f"✓ Preview generated")
            print(f"  Quality: {preview['quality']['score']}")
            print(f"  Pages: {preview['page_count']}")
            print(f"  Has text: {preview['quality']['has_text']}")
            
            # Save as HTML
            output_path = Path("preview.html")
            previewer.save_preview_html(preview, output_path)
        else:
            print(f"✗ Failed: {preview['error']}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
