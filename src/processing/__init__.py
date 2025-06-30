"""
Processing module for Bot-Vea-Connect Azure Functions.

This module contains Azure Functions for document processing workflows:
- BatchStartProcessing: HTTP trigger to start batch processing
- BlobTriggerProcessor: Blob trigger to process uploaded documents
- BatchPushResults: Queue trigger to push results to storage
"""

__version__ = "1.0.0"
__author__ = "Bot-Vea-Connect Team"
