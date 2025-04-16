"""
GPU Verification Script

This script checks if PyTorch can properly access the GPU
and shows information about CUDA availability.
"""

import torch
from transformers import pipeline
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gpu():
    """Check if GPU is available and print device information."""
    logger.info("Checking GPU availability...")
    
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        logger.info(f"✅ CUDA is available! Found {device_count} GPU(s).")
        
        for i in range(device_count):
            logger.info(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            logger.info(f"  Total memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
            logger.info(f"  CUDA capability: {torch.cuda.get_device_capability(i)}")
        
        # Set default device
        torch.cuda.set_device(0)
        logger.info(f"Default device set to: {torch.cuda.current_device()}")
        
        # Clear cache
        torch.cuda.empty_cache()
        logger.info("CUDA cache cleared")
    else:
        logger.warning("❌ CUDA is not available. PyTorch will use CPU.")
        return False
    
    return True

def test_model_on_gpu():
    """Test loading a small model on GPU vs CPU and compare speeds."""
    logger.info("Testing model loading and inference on GPU vs CPU...")
    
    test_text = "This is a test sentence to analyze sentiment. I'm very happy with the results!"
    
    # Test on GPU
    if torch.cuda.is_available():
        logger.info("Loading sentiment model on GPU...")
        start_time = time.time()
        try:
            sentiment_pipeline_gpu = pipeline("sentiment-analysis", 
                                             model="distilbert-base-uncased-finetuned-sst-2-english", 
                                             device=0)
            gpu_load_time = time.time() - start_time
            logger.info(f"✅ Model loaded on GPU in {gpu_load_time:.2f} seconds")
            
            # Run inference
            start_time = time.time()
            result_gpu = sentiment_pipeline_gpu(test_text)
            gpu_inference_time = time.time() - start_time
            logger.info(f"GPU inference time: {gpu_inference_time:.4f} seconds")
            logger.info(f"GPU result: {result_gpu}")
        except Exception as e:
            logger.error(f"Error using GPU: {e}")
    
    # Test on CPU
    logger.info("Loading sentiment model on CPU...")
    start_time = time.time()
    sentiment_pipeline_cpu = pipeline("sentiment-analysis", 
                                     model="distilbert-base-uncased-finetuned-sst-2-english", 
                                     device=-1)
    cpu_load_time = time.time() - start_time
    logger.info(f"Model loaded on CPU in {cpu_load_time:.2f} seconds")
    
    # Run inference
    start_time = time.time()
    result_cpu = sentiment_pipeline_cpu(test_text)
    cpu_inference_time = time.time() - start_time
    logger.info(f"CPU inference time: {cpu_inference_time:.4f} seconds")
    logger.info(f"CPU result: {result_cpu}")
    
    # Compare if both were run
    if torch.cuda.is_available():
        try:
            speedup = cpu_inference_time / gpu_inference_time
            logger.info(f"GPU is {speedup:.2f}x faster than CPU for inference")
        except:
            logger.error("Could not compare speeds due to GPU test failure")

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("GPU VERIFICATION SCRIPT")
    logger.info("="*50)
    
    # Check PyTorch version
    logger.info(f"PyTorch version: {torch.__version__}")
    
    if check_gpu():
        # Try to create a tensor on GPU
        try:
            logger.info("Creating test tensor on GPU...")
            x = torch.tensor([1.0, 2.0, 3.0], device='cuda')
            logger.info(f"✅ Test tensor created on GPU: {x}")
            logger.info(f"Tensor device: {x.device}")
        except Exception as e:
            logger.error(f"Error creating tensor on GPU: {e}")
    
    # Test model loading and inference
    test_model_on_gpu()
    
    logger.info("="*50)
    logger.info("VERIFICATION COMPLETE")
    logger.info("="*50) 