import ollama
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime

class SubjectClassificationService:
    def __init__(self):
        self.model_name = "llama3"
        self.enabled = True
        try:
            # Test if Ollama is available
            ollama.list()
        except Exception as e:
            logging.warning(f"Ollama not available: {e}")
            self.enabled = False
    
    def classify_subject(self, text: str, available_subjects: List[str]) -> Optional[str]:
        """
        Classify text into one of the available subjects using Llama3
        
        Args:
            text (str): The text to classify
            available_subjects (List[str]): List of available subject names
            
        Returns:
            Optional[str]: The most appropriate subject name or None
        """
        if not self.enabled or not available_subjects:
            return None
        
        try:
            # Create prompt for subject classification
            subjects_list = ", ".join(available_subjects)
            prompt = f"""
            Given the following text extracted from handwritten notes, classify it into one of these EXACT subjects: {subjects_list}

            Text to classify:
            {text[:1000]}  # Limit text length for better performance

            Instructions:
            - Return ONLY one of these EXACT subject names: {subjects_list}
            - Match the text content to the most relevant subject
            - Consider technical terms, topics, and context
            - If multiple subjects could apply, choose the most dominant one
            - If no subject matches well, return "NONE"
            - Do not add any explanation or extra text

            Available subjects again: {subjects_list}
            
            Subject:"""

            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            predicted_subject = response['message']['content'].strip()
            
            # First try exact match
            if predicted_subject in available_subjects:
                return predicted_subject
            elif predicted_subject.upper() == "NONE":
                return None
            else:
                # Use the enhanced matching logic
                closest_match = self._find_closest_subject_match(predicted_subject, available_subjects)
                if closest_match:
                    logging.info(f"Single classification: mapped '{predicted_subject}' to '{closest_match}'")
                    return closest_match
                
                # Final fallback: use content-based keywords to match
                keywords = self.extract_keywords(text)
                if keywords:
                    for keyword in keywords:
                        keyword_match = self._find_closest_subject_match(keyword, available_subjects)
                        if keyword_match:
                            logging.info(f"Keyword-based match: '{keyword}' -> '{keyword_match}'")
                            return keyword_match
                
                return None
                
        except Exception as e:
            logging.error(f"Error in subject classification: {e}")
            return None
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extract key topics and keywords from text using Llama3
        
        Args:
            text (str): The text to analyze
            
        Returns:
            List[str]: List of extracted keywords
        """
        if not self.enabled:
            return []
        
        try:
            prompt = f"""
            Extract the main keywords and topics from this text. Focus on:
            - Subject-specific terms
            - Important concepts
            - Key topics
            - Technical terms

            Text:
            {text[:1500]}

            Return only a comma-separated list of keywords (maximum 10):
            """

            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            keywords_text = response['message']['content'].strip()
            keywords = [kw.strip() for kw in keywords_text.split(',')]
            
            # Clean and filter keywords
            cleaned_keywords = []
            for keyword in keywords[:10]:  # Limit to 10 keywords
                keyword = keyword.strip().lower()
                if keyword and len(keyword) > 2:
                    cleaned_keywords.append(keyword)
            
            return cleaned_keywords
            
        except Exception as e:
            logging.error(f"Error extracting keywords: {e}")
            return []

    def _find_closest_subject_match(self, predicted_subject: str, available_subjects: List[str]) -> Optional[str]:
        """
        Find the closest matching subject using multiple strategies
        
        Args:
            predicted_subject (str): The subject predicted by AI
            available_subjects (List[str]): List of available subjects
            
        Returns:
            Optional[str]: The closest matching subject or None
        """
        if not predicted_subject or not available_subjects:
            return None
        
        predicted_lower = predicted_subject.lower().strip()
        
        # Strategy 1: Exact match (case insensitive)
        for subject in available_subjects:
            if subject.lower() == predicted_lower:
                return subject
        
        # Strategy 2: Contains match (predicted contains available subject)
        for subject in available_subjects:
            if subject.lower() in predicted_lower:
                return subject
        
        # Strategy 3: Available subject contains predicted
        for subject in available_subjects:
            if predicted_lower in subject.lower():
                return subject
        
        # Strategy 4: Partial word matching
        predicted_words = set(predicted_lower.split())
        best_match = None
        best_score = 0
        
        for subject in available_subjects:
            subject_words = set(subject.lower().split())
            common_words = predicted_words.intersection(subject_words)
            if common_words:
                score = len(common_words) / max(len(predicted_words), len(subject_words))
                if score > best_score and score >= 0.5:  # At least 50% word overlap
                    best_score = score
                    best_match = subject
        
        if best_match:
            return best_match
        
        # Strategy 5: Common subject name mappings
        subject_mappings = {
            'ml': 'machine learning',
            'ai': 'machine learning',
            'artificial intelligence': 'machine learning', 
            'dl': 'deep learning',
            'neural networks': 'deep learning',
            'neural network': 'deep learning',
            'literature': 'english',
            'shakespeare': 'english',
            'poetry': 'english',
            'writing': 'english',
            'math': 'mathematics',
            'calculus': 'mathematics',
            'algebra': 'mathematics',
            'physics': 'physics',
            'chemistry': 'chemistry',
            'biology': 'biology',
            'history': 'history',
            'science': 'general science'
        }
        
        mapped_subject = subject_mappings.get(predicted_lower)
        if mapped_subject:
            for subject in available_subjects:
                if subject.lower() == mapped_subject:
                    return subject
        
        return None

    def classify_multi_subject_text(self, text: str, available_subjects: List[str]) -> List[Dict[str, str]]:
        """
        Analyze text and split it into multiple notes if it contains content for different subjects
        
        Args:
            text (str): The text to analyze and split
            available_subjects (List[str]): List of available subject names
            
        Returns:
            List[Dict]: List of dictionaries with 'subject', 'content', and 'title' keys
        """
        if not self.enabled or not available_subjects or not text.strip():
            return []
        
        try:
            subjects_list = ", ".join(available_subjects)
            current_date = datetime.now().strftime("%A, %B %d, %Y")
            
            prompt = f"""
            Analyze the following text extracted from handwritten notes. Determine if it contains content related to multiple subjects or just one subject.

            Available subjects (use EXACTLY these names): {subjects_list}

            Text to analyze:
            {text}

            Instructions:
            1. If the text relates to only ONE subject:
               - Return a single entry with the EXACT subject name from the list above
               - Use the entire text as content
               - Generate a descriptive title WITHOUT including the subject name

            2. If the text relates to MULTIPLE subjects:
               - Split the text into separate sections for each subject
               - Use EXACTLY the subject names from this list: {subjects_list}
               - Each section should contain only content relevant to that subject
               - Generate appropriate titles for each section WITHOUT subject names
               - Preserve all original content (don't lose any information)

            3. For each note, generate a descriptive title WITHOUT including the subject name. Focus on the main topic or content of that section.

            4. If no subject matches well, use "General" as the subject

            5. CRITICAL: Only use these exact subject names: {subjects_list} or "General"

            IMPORTANT: Return ONLY valid JSON in this EXACT format. Do not include any explanations, prefixes, or additional text:

            [
                {{
                    "subject": "EXACT_SUBJECT_NAME_FROM_LIST",
                    "title": "Descriptive Title Without Subject Name",
                    "content": "Relevant content for this subject"
                }},
                {{
                    "subject": "Another Subject",
                    "title": "Another Title", 
                    "content": "Content for second subject"
                }}
            ]"""

            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            )
            
            response_text = response['message']['content'].strip()
            
            # Clean up the response to ensure valid JSON
            # Remove any text before the first '[' or after the last ']'
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                response_text = response_text[start_idx:end_idx+1]
            
            # Try to parse JSON response
            import json
            try:
                result = json.loads(response_text)
                
                # Validate and clean the result
                validated_result = []
                for item in result:
                    if isinstance(item, dict) and 'subject' in item and 'content' in item:
                        # Validate subject exists and find closest match
                        subject = item['subject']
                        original_subject = subject
                        
                        if subject not in available_subjects and subject != "General":
                            # Try multiple matching strategies for closest match
                            closest_match = self._find_closest_subject_match(subject, available_subjects)
                            if closest_match:
                                subject = closest_match
                                logging.info(f"Mapped subject '{original_subject}' to '{subject}'")
                            else:
                                # If no close match found, try content-based classification
                                content_based_subject = self.classify_subject(item['content'], available_subjects)
                                if content_based_subject:
                                    subject = content_based_subject
                                    logging.info(f"Used content-based classification: '{original_subject}' -> '{subject}'")
                                else:
                                    subject = "General"
                                    logging.info(f"No match found for '{original_subject}', using General")
                        
                        # Generate title if not provided or invalid
                        title = item.get('title', '').strip()
                        
                        # Remove subject prefix completely if it exists
                        if title.startswith(f"{subject} - "):
                            title = title[len(f"{subject} - "):]
                        elif title.startswith(subject):
                            title = title[len(subject):].lstrip(" -")
                        
                        # If no meaningful title, generate one from content
                        if not title or title.lower() in ["notes", subject.lower()]:
                            # Generate a descriptive title from the first few words of content
                            content_words = item['content'].strip().split()
                            if len(content_words) >= 5:
                                title = " ".join(content_words[:6])  # Reduced from 8 to 6 words
                                # Limit title length to 60 characters max
                                if len(title) > 60:
                                    title = title[:57] + "..."
                            else:
                                title = f"{current_date} Notes"
                        else:
                            # Ensure existing title is not too long
                            if len(title) > 60:
                                title = title[:57] + "..."
                        
                        validated_result.append({
                            'subject': subject,
                            'title': title,
                            'content': item['content'].strip()
                        })
                
                return validated_result
                
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON response from LLaMA3: {response_text}")
                # Fallback: treat as single subject
                subject = self.classify_subject(text, available_subjects) or "General"
                content_words = text.strip().split()
                fallback_title = " ".join(content_words[:6]) if len(content_words) >= 5 else f"{current_date} Notes"
                if len(fallback_title) > 60:
                    fallback_title = fallback_title[:57] + "..."
                return [{
                    'subject': subject,
                    'title': fallback_title,
                    'content': text.strip()
                }]
                
        except Exception as e:
            logging.error(f"Error in multi-subject classification: {e}")
            # Fallback: treat as single subject
            subject = self.classify_subject(text, available_subjects) or "General"
            content_words = text.strip().split()
            fallback_title = " ".join(content_words[:6]) if len(content_words) >= 5 else f"{datetime.now().strftime('%A, %B %d, %Y')} Notes"
            if len(fallback_title) > 60:
                fallback_title = fallback_title[:57] + "..."
            return [{
                'subject': subject,
                'title': fallback_title,
                'content': text.strip()
            }]
