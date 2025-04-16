"""
Test Prototype Module for AI Studio

This module provides a simple prototype implementation for testing the AI Studio system.
It demonstrates how to create custom prototypes that can be triggered by the action executor.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path to import AI Studio modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AI Studio modules
from infra.db import log_action

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestPrototype:
    """
    Test Prototype for AI Studio.
    
    This class demonstrates how to create a custom prototype that can be
    triggered by the action executor.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the test prototype.
        
        Args:
            data_path (str, optional): Path to JSON data file
        """
        self.data = None
        
        if data_path and os.path.exists(data_path):
            with open(data_path, 'r') as f:
                self.data = json.load(f)
        
        logger.info("Test prototype initialized")
    
    def run(self) -> Dict[str, Any]:
        """
        Run the test prototype.
        
        Returns:
            dict: Result of the prototype execution
        """
        logger.info("Running test prototype")
        
        # Log action
        log_action('test_prototype', 'run', "Test prototype executed")
        
        # Process data
        result = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
            'message': 'Test prototype executed successfully'
        }
        
        if self.data:
            result['input_data'] = self.data
            
            # Example: If the data contains a contract, add it to the result
            if 'contract' in self.data:
                result['contract_address'] = self.data['contract'].get('address')
                result['contract_source'] = self.data['contract'].get('source')
        
        # Save result to file
        output_path = os.path.join("memory", "prompt_outputs", f"prototype_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Test prototype result saved to {output_path}")
        
        return result

def main():
    """
    Main entry point for the test prototype.
    """
    # Parse command line arguments
    data_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Create and run the prototype
    prototype = TestPrototype(data_path)
    result = prototype.run()
    
    # Print result
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
