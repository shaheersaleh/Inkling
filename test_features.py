#!/usr/bin/env python3
"""
Test script for the new features:
1. LLaMA3 text cleaning
2. Multi-subject classification
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.text_extraction import TextExtractionService
from app.services.ai_classification import SubjectClassificationService

def test_text_cleaning():
    print("=== Testing Text Cleaning ===")
    
    text_service = TextExtractionService()
    
    # Test with sample OCR-like text
    messy_text = """
    Machne lerning
    is a typ of
    artificial intlligence
    
    Uses algorthms to
    learn from data
    
    Applcations includ:
    - image recogntion
    - natural languge processing
    """
    
    print(f"Original text:\n{messy_text}\n")
    
    # Test basic formatting
    basic_formatted = text_service.format_to_sentences(messy_text)
    print(f"Basic formatting:\n{basic_formatted}\n")
    
    # Test LLaMA3 cleaning
    if text_service.ollama_enabled:
        llama_cleaned = text_service.clean_text_with_llama(messy_text)
        print(f"LLaMA3 cleaned:\n{llama_cleaned}\n")
    else:
        print("LLaMA3 not available for text cleaning\n")

def test_multi_subject_classification():
    print("=== Testing Multi-Subject Classification ===")
    
    classification_service = SubjectClassificationService()
    
    if not classification_service.enabled:
        print("Classification service not enabled")
        return
    
    # Test text that could belong to multiple subjects
    mixed_text = """
    Today we learned about machine learning algorithms like neural networks and decision trees.
    The gradient descent optimization technique is crucial for training models.
    
    In English class, we studied Shakespeare's Romeo and Juliet.
    The themes of love and tragedy are prominent throughout the play.
    We also analyzed the use of iambic pentameter in the sonnets.
    
    Deep learning models like transformers have revolutionized natural language processing.
    BERT and GPT are examples of transformer architectures.
    """
    
    available_subjects = ["english", "deep learning", "machine learning"]
    
    print(f"Text to classify:\n{mixed_text}\n")
    print(f"Available subjects: {available_subjects}\n")
    
    results = classification_service.classify_multi_subject_text(mixed_text, available_subjects)
    
    print("Classification results:")
    for i, result in enumerate(results, 1):
        print(f"\nNote {i}:")
        print(f"Subject: {result['subject']}")
        print(f"Title: {result['title']}")
        print(f"Content: {result['content'][:200]}...")

def main():
    app = create_app()
    
    with app.app_context():
        test_text_cleaning()
        print("\n" + "="*50 + "\n")
        test_multi_subject_classification()

if __name__ == "__main__":
    main()
