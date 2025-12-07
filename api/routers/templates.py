"""Template management API endpoints."""
import sys
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models import (
    ErrorResponse,
    TemplateContent,
    TemplateCreate,
    TemplateInfo,
    TemplateUpdate,
)
from lib.template_manager import TemplateManager

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("/", response_model=List[TemplateInfo], tags=["templates"])
async def list_templates():
    """
    List all available templates.

    Returns a list of template names and their paths.
    """
    try:
        template_manager = TemplateManager()
        template_names = template_manager.list_templates()

        templates = []
        for name in template_names:
            template_file = template_manager.template_dir / f"{name}.yaml.j2"
            templates.append(
                TemplateInfo(
                    name=name,
                    path=str(template_file),
                    exists=template_file.exists(),
                )
            )

        return templates

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing templates: {str(e)}",
        )


@router.get("/{name}", response_model=TemplateContent, tags=["templates"])
async def get_template(name: str):
    """
    Get template content.

    Returns the full content of a specific template.
    """
    try:
        template_manager = TemplateManager()
        template_file = template_manager.template_dir / f"{name}.yaml.j2"

        if not template_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Template '{name}' not found",
            )

        content = template_file.read_text()

        return TemplateContent(
            name=name,
            content=content,
            path=str(template_file),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting template: {str(e)}",
        )


@router.post(
    "/",
    response_model=TemplateContent,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    tags=["templates"],
)
async def create_template(template: TemplateCreate):
    """
    Create a new template.

    Creates a new template file with the specified name and content.
    """
    try:
        template_manager = TemplateManager()
        template_file = template_manager.template_dir / f"{template.name}.yaml.j2"

        if template_file.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Template '{template.name}' already exists",
            )

        # Validate template name
        if not template.name or "/" in template.name or ".." in template.name:
            raise HTTPException(
                status_code=400,
                detail="Invalid template name",
            )

        # Write template file
        template_file.write_text(template.content)

        return TemplateContent(
            name=template.name,
            content=template.content,
            path=str(template_file),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating template: {str(e)}",
        )


@router.put(
    "/{name}",
    response_model=TemplateContent,
    responses={404: {"model": ErrorResponse}},
    tags=["templates"],
)
async def update_template(name: str, template: TemplateUpdate):
    """
    Update an existing template.

    Updates the content of an existing template.
    """
    try:
        template_manager = TemplateManager()
        template_file = template_manager.template_dir / f"{name}.yaml.j2"

        if not template_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Template '{name}' not found",
            )

        # Write updated content
        template_file.write_text(template.content)

        return TemplateContent(
            name=name,
            content=template.content,
            path=str(template_file),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating template: {str(e)}",
        )


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    tags=["templates"],
)
async def delete_template(name: str):
    """
    Delete a template.

    Removes a template file from the filesystem.
    """
    try:
        template_manager = TemplateManager()
        template_file = template_manager.template_dir / f"{name}.yaml.j2"

        if not template_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Template '{name}' not found",
            )

        template_file.unlink()

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting template: {str(e)}",
        )


@router.post(
    "/{name}/render",
    response_model=dict,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    tags=["templates"],
)
async def render_template(name: str, context: dict):
    """
    Render a template with the provided context.

    Returns the rendered template as Kubernetes resources.
    """
    try:
        template_manager = TemplateManager()

        # Check if template exists
        template_file = template_manager.template_dir / f"{name}.yaml.j2"
        if not template_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Template '{name}' not found",
            )

        # Render template
        resources = template_manager.render_to_resources(name, context)

        return {
            "template": name,
            "resources": resources,
            "count": len(resources),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error rendering template: {str(e)}",
        )

