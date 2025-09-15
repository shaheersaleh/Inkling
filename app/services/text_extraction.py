import os
from google.cloud import vision
from PIL import Image
import io
import logging
import ollama

class TextExtractionService:
    def __init__(self):
        # Initialize Google Cloud Vision client
        # Supports multiple authentication methods:
        # 1. Application Default Credentials (gcloud auth application-default login)
        # 2. Service Account Key (GOOGLE_APPLICATION_CREDENTIALS env var)
        # 3. API Key (GOOGLE_CLOUD_API_KEY env var)
        try:
            # Check if API key is provided
            api_key = os.environ.get('GOOGLE_CLOUD_API_KEY')
            if api_key:
                # Use API key authentication
                from google.cloud.vision_v1.services.image_annotator import ImageAnnotatorClient
                from google.api_core import client_options
                
                client_options_obj = client_options.ClientOptions(api_key=api_key)
                self.client = ImageAnnotatorClient(client_options=client_options_obj)
            else:
                # Use default authentication (ADC or service account)
                self.client = vision.ImageAnnotatorClient()
            
            self.enabled = True
        except Exception as e:
            logging.warning(f"Google Cloud Vision not configured: {e}")
            self.enabled = False
        
        # Initialize Ollama for text cleaning
        self.ollama_enabled = True
        try:
            ollama.list()
        except Exception as e:
            logging.warning(f"Ollama not available for text cleaning: {e}")
            self.ollama_enabled = False
    
    def extract_text_from_image(self, image_path):
        """
        Extract text from an image using Google Cloud Vision API
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            tuple: (extracted_text, confidence_score)
        """
        if not self.enabled:
            return "Text extraction service not available", 0.0
        
        try:
            # Read and process the image
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform text detection using batch annotation
            features = [vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION)]
            request = vision.AnnotateImageRequest(image=image, features=features)
            
            response = self.client.batch_annotate_images(requests=[request])
            annotations = response.responses[0]
            
            if annotations.error.message:
                raise Exception(f'API Error: {annotations.error.message}')
            
            if not annotations.text_annotations:
                return "No text found in image", 0.0
            
            # Get the full text (first annotation contains all text)
            full_text = annotations.text_annotations[0].description
            confidence = 0.95  # Default confidence for text detection
            
            # Use LLaMA3 for text cleaning if available, otherwise use basic formatting
            if self.ollama_enabled:
                formatted_text = self.clean_text_with_llama(full_text)
            else:
                formatted_text = self.format_to_sentences(full_text)
            
            return formatted_text, confidence
            
        except Exception as e:
            logging.error(f"Error extracting text from image: {e}")
            return f"Error extracting text: {str(e)}", 0.0
    
    def clean_text_with_llama(self, text: str) -> str:
        """
        Use LLaMA3 to clean and format extracted text into proper sentences
        
        Args:
            text (str): Raw extracted text from OCR
            
        Returns:
            str: Cleaned and formatted text
        """
        if not text or not text.strip() or not self.ollama_enabled:
            return self.format_to_sentences(text)
        
        try:
            prompt = f"""
            You are a text cleaning assistant. The following text was extracted from a handwritten note using OCR. Clean it up and format it into proper, readable sentences while preserving all the meaningful content.

            Rules:
            1. Fix spelling errors and OCR mistakes
            2. Form complete, grammatically correct sentences
            3. Preserve all the original meaning and information
            4. Use proper punctuation and capitalization
            5. Remove any nonsensical OCR artifacts
            6. If bullet points or lists are detected, format them properly
            7. Do NOT add any new information or interpretation
            8. Return ONLY the cleaned text with NO prefixes, explanations, or additional commentary

            Raw text to clean:
            {text}

            Cleaned text:"""

            response = ollama.chat(
                model="llama3",
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            cleaned_text = response['message']['content'].strip()
            
            # Remove common prefixes that LLaMA might add
            prefixes_to_remove = [
                "Here is the cleaned text:",
                "Here's the cleaned text:",
                "Cleaned text:",
                "The cleaned text is:",
                "Here is the text:",
                "Here's the text:"
            ]
            
            for prefix in prefixes_to_remove:
                if cleaned_text.startswith(prefix):
                    cleaned_text = cleaned_text[len(prefix):].strip()
                    break
            
            # Fallback to basic formatting if LLaMA response is empty or too different
            if not cleaned_text or len(cleaned_text) < len(text) * 0.3:
                logging.warning("LLaMA3 text cleaning produced insufficient output, falling back to basic formatting")
                return self.format_to_sentences(text)
            
            return cleaned_text
            
        except Exception as e:
            logging.error(f"Error cleaning text with LLaMA3: {e}")
            # Fallback to basic sentence formatting
            return self.format_to_sentences(text)
    
    def format_to_sentences(self, text: str) -> str:
        """
        Convert extracted text to proper sentence form
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Formatted text in sentence form
        """
        if not text or not text.strip():
            return ""
        
        # Clean up the text
        text = text.strip()
        
        # Split by newlines and clean each line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Join lines with spaces and handle punctuation
        combined_text = ' '.join(lines)
        
        # Fix common OCR issues
        combined_text = combined_text.replace('  ', ' ')  # Remove double spaces
        combined_text = combined_text.replace(' .', '.')  # Fix spaced periods
        combined_text = combined_text.replace(' ,', ',')  # Fix spaced commas
        
        # Ensure proper sentence ending
        if combined_text and not combined_text[-1] in '.!?':
            combined_text += '.'
        
        # Capitalize first letter
        if combined_text:
            combined_text = combined_text[0].upper() + combined_text[1:]
        
        return combined_text
    
    def preprocess_image(self, image_path, output_path=None):
        """
        Preprocess image for better text extraction
        
        Args:
            image_path (str): Path to the input image
            output_path (str): Path to save preprocessed image (optional)
            
        Returns:
            str: Path to the preprocessed image
        """
        try:
            # Open and preprocess the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Enhance contrast and sharpness if needed
                # For now, just save as is - can add more preprocessing later
                
                if output_path:
                    img.save(output_path, 'JPEG', quality=95)
                    return output_path
                else:
                    # Save with _processed suffix
                    base, ext = os.path.splitext(image_path)
                    processed_path = f"{base}_processed{ext}"
                    img.save(processed_path, 'JPEG', quality=95)
                    return processed_path
                    
        except Exception as e:
            logging.error(f"Error preprocessing image: {e}")
            return image_path  # Return original path if preprocessing fails
