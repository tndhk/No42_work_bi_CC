"""Dataset API routes."""
from typing import Any
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.api.deps import get_current_user, get_dynamodb_resource, get_s3_client
from app.models.dataset import Dataset, DatasetUpdate
from app.models.user import User
from app.repositories.dataset_repository import DatasetRepository
from app.services.dataset_service import DatasetService

router = APIRouter()


@router.get("", response_model=list[Dataset])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> list[Dataset]:
    """List all datasets owned by current user.

    Args:
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        List of datasets
    """
    repo = DatasetRepository()
    datasets = await repo.list_by_owner(current_user.id, dynamodb)
    return datasets


@router.post("", response_model=Dataset, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    encoding: str | None = Form(None),
    delimiter: str = Form(","),
    partition_column: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> Dataset:
    """Create a new dataset by importing CSV file.

    Args:
        file: CSV file to upload
        name: Dataset name
        description: Optional description
        encoding: Optional encoding (auto-detected if None)
        delimiter: Column delimiter (default: comma)
        partition_column: Optional column to partition by
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client

    Returns:
        Created dataset

    Raises:
        HTTPException: 422 if validation fails
    """
    # Validate name
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty",
        )

    # Read file bytes
    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File cannot be empty",
        )

    # Import CSV via service
    service = DatasetService()

    try:
        dataset = await service.import_csv(
            file_bytes=file_bytes,
            name=name.strip(),
            owner_id=current_user.id,
            dynamodb=dynamodb,
            s3_client=s3_client,
            encoding=encoding,
            delimiter=delimiter,
            partition_column=partition_column,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return dataset


@router.get("/{dataset_id}", response_model=Dataset)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Dataset:
    """Get dataset by ID.

    Args:
        dataset_id: Dataset ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Dataset instance

    Raises:
        HTTPException: 404 if not found
    """
    repo = DatasetRepository()
    dataset = await repo.get_by_id(dataset_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    return dataset


@router.put("/{dataset_id}", response_model=Dataset)
async def update_dataset(
    dataset_id: str,
    update_data: DatasetUpdate,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> Dataset:
    """Update dataset.

    Args:
        dataset_id: Dataset ID
        update_data: Update fields
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Returns:
        Updated dataset

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = DatasetRepository()
    dataset = await repo.get_by_id(dataset_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    # Check ownership
    if dataset.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this dataset",
        )

    # Update dataset
    update_dict = update_data.model_dump(exclude_unset=True)

    updated_dataset = await repo.update(dataset_id, update_dict, dynamodb)

    if not updated_dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found after update",
        )

    return updated_dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
) -> None:
    """Delete dataset.

    Args:
        dataset_id: Dataset ID
        current_user: Authenticated user
        dynamodb: DynamoDB resource

    Raises:
        HTTPException: 403 if not owner, 404 if not found
    """
    repo = DatasetRepository()
    dataset = await repo.get_by_id(dataset_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    # Check ownership
    if dataset.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this dataset",
        )

    # Delete dataset
    await repo.delete(dataset_id, dynamodb)


@router.get("/{dataset_id}/preview")
async def get_dataset_preview(
    dataset_id: str,
    max_rows: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    dynamodb: Any = Depends(get_dynamodb_resource),
    s3_client: Any = Depends(get_s3_client),
) -> dict[str, Any]:
    """Get dataset preview.

    Args:
        dataset_id: Dataset ID
        max_rows: Maximum rows to return (1-1000, default: 100)
        current_user: Authenticated user
        dynamodb: DynamoDB resource
        s3_client: S3 client

    Returns:
        Preview data with columns, rows, total_rows, preview_rows

    Raises:
        HTTPException: 404 if not found, 422 if max_rows invalid
    """
    repo = DatasetRepository()
    dataset = await repo.get_by_id(dataset_id, dynamodb)

    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    # Get preview via service
    service = DatasetService()

    try:
        preview = await service.get_preview(
            dataset=dataset,
            s3_client=s3_client,
            max_rows=max_rows,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return preview
