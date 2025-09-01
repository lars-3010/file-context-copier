"""HTTP API service for file-context-copier background operation."""

import logging
import os
import tempfile
from typing import Dict, List, Optional
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    raise ImportError(
        "Service dependencies not installed. Install with: uv pip install -e '.[service]'"
    )

from .core import format_content, process_paths_to_content


class ProcessRequest(BaseModel):
    """Request model for processing files."""
    paths: List[str]
    base_path: str = "."
    exclude_patterns: Optional[str] = None
    output_format: str = "markdown"  # "markdown" or "json"


class ProcessResponse(BaseModel):
    """Response model for processing results."""
    success: bool
    content: Optional[str] = None
    file_count: int = 0
    files_processed: List[str] = []
    error: Optional[str] = None


# Global app instance
app = FastAPI(
    title="File Context Copier API",
    description="HTTP API for processing file contexts in the background",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "File Context Copier API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "file-context-copier"}


@app.post("/process", response_model=ProcessResponse)
async def process_files(request: ProcessRequest) -> ProcessResponse:
    """
    Process files and return formatted content.
    
    Args:
        request: ProcessRequest with paths, base_path, exclude_patterns, etc.
    
    Returns:
        ProcessResponse with formatted content or error message.
    """
    try:
        # Validate base path exists
        if not os.path.exists(request.base_path):
            raise HTTPException(
                status_code=400, 
                detail=f"Base path does not exist: {request.base_path}"
            )

        # Use shared processing function
        content = process_paths_to_content(request.paths, request.base_path, request.exclude_patterns)
        
        if not content:
            return ProcessResponse(
                success=False,
                error="No readable text files found in selection"
            )

        # Format content
        if request.output_format == "json":
            formatted_content = content  # Return raw dict for JSON
        else:
            formatted_content = format_content(content)

        return ProcessResponse(
            success=True,
            content=formatted_content,
            file_count=len(content),
            files_processed=list(content.keys())
        )

    except Exception as e:
        logging.error(f"Error processing files: {e}")
        return ProcessResponse(
            success=False,
            error=str(e)
        )


@app.post("/process-to-file")
async def process_to_file(request: ProcessRequest) -> Dict[str, str]:
    """
    Process files and save to a temporary file, return file path.
    
    Args:
        request: ProcessRequest with processing parameters.
    
    Returns:
        Dictionary with file path and metadata.
    """
    try:
        # Process files using the same logic
        result = await process_files(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.error)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            temp_file.write(result.content)
            temp_file_path = temp_file.name

        return {
            "file_path": temp_file_path,
            "file_count": result.file_count,
            "files_processed": result.files_processed,
            "message": f"Content written to {temp_file_path}"
        }

    except Exception as e:
        logging.error(f"Error processing to file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_service(host: str = "0.0.0.0", port: int = 8000, log_level: str = "info"):
    """Start the FastAPI service."""
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Starting File Context Copier service on {host}:{port}")
    
    uvicorn.run(
        "file_context_copier.service:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False
    )


if __name__ == "__main__":
    start_service()