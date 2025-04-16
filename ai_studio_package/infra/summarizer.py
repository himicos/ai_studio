"""
Module for managing the summarization pipeline singleton.
"""

import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch

logger = logging.getLogger(__name__)

class SummarizationPipelineSingleton:
    _instance = None
    _pipeline = None
    _tokenizer = None
    _model = None
    _model_name = "facebook/bart-large-cnn"  # Default summarization model

    def __new__(cls):
        if cls._instance is None:
            logger.info(f"Creating new SummarizationPipelineSingleton instance...")
            cls._instance = super(SummarizationPipelineSingleton, cls).__new__(cls)
            cls._initialize_pipeline()
        return cls._instance

    @classmethod
    def _initialize_pipeline(cls):
        if cls._pipeline is None:
            try:
                logger.info(f"Initializing summarization pipeline with model: {cls._model_name}")
                device_num = 0 if torch.cuda.is_available() else -1 # Use GPU 0 if available, else CPU
                device_name = "cuda:0" if device_num == 0 else "cpu"
                logger.info(f"Attempting to load summarization model on device: {device_name}")

                # Load tokenizer and model separately for more control if needed
                cls._tokenizer = AutoTokenizer.from_pretrained(cls._model_name)
                cls._model = AutoModelForSeq2SeqLM.from_pretrained(cls._model_name)
                
                cls._pipeline = pipeline(
                    "summarization", 
                    model=cls._model,
                    tokenizer=cls._tokenizer, 
                    device=device_num
                )
                logger.info(f"Summarization pipeline initialized successfully on {device_name}.")
                
            except Exception as e:
                logger.error(f"Failed to initialize summarization pipeline: {e}", exc_info=True)
                # Set to None so subsequent calls know it failed
                cls._pipeline = None
                cls._tokenizer = None
                cls._model = None

    @classmethod
    def get_pipeline(cls):
        """Returns the initialized summarization pipeline."""
        if cls._instance is None:
            cls() # Initialize if not already done
        return cls._pipeline

    @classmethod
    def get_tokenizer(cls):
        """Returns the initialized tokenizer."""
        if cls._instance is None:
            cls()
        return cls._tokenizer
        
    @classmethod
    def get_model_name(cls):
        """Returns the name of the model used."""
        return cls._model_name

# Example of how to get the pipeline:
# summarizer = SummarizationPipelineSingleton.get_pipeline()
# if summarizer:
#     # Use the summarizer
#     pass 