"""Tests for transform_execution_service module - TDD RED phase."""
import asyncio
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, AsyncMock, patch

import pandas as pd
import pytest
import httpx

from app.models.transform import Transform
from app.models.dataset import Dataset, ColumnSchema


# ============================================================================
# Test Fixtures
# ============================================================================


def create_mock_transform(
    transform_id: str = "transform_123",
    owner_id: str = "user_123",
    input_dataset_ids: list[str] | None = None,
    output_dataset_id: str | None = None,
    code: str = "def transform(df): return df",
) -> Transform:
    """Create a mock Transform instance."""
    if input_dataset_ids is None:
        input_dataset_ids = ["dataset_input_1"]

    now = datetime.now(timezone.utc)
    return Transform(
        id=transform_id,
        name="Test Transform",
        owner_id=owner_id,
        input_dataset_ids=input_dataset_ids,
        output_dataset_id=output_dataset_id,
        code=code,
        created_at=now,
        updated_at=now,
    )


def create_mock_dataset(
    dataset_id: str = "dataset_123",
    owner_id: str = "user_123",
    s3_path: str = "datasets/dataset_123/data/part-0000.parquet",
    row_count: int = 100,
) -> Dataset:
    """Create a mock Dataset instance."""
    now = datetime.now(timezone.utc)
    return Dataset(
        id=dataset_id,
        name="Test Dataset",
        source_type="csv",
        row_count=row_count,
        schema=[
            ColumnSchema(name="col1", data_type="string", nullable=False),
            ColumnSchema(name="col2", data_type="int64", nullable=True),
        ],
        owner_id=owner_id,
        s3_path=s3_path,
        column_count=2,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def mock_dynamodb() -> MagicMock:
    """Create mock DynamoDB resource."""
    return MagicMock()


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Create mock S3 client."""
    return MagicMock()


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        "col1": ["a", "b", "c"],
        "col2": [1, 2, 3],
    })


# ============================================================================
# TransformExecutionResult Tests
# ============================================================================


class TestTransformExecutionResult:
    """Test suite for TransformExecutionResult dataclass."""

    def test_result_creation(self) -> None:
        """Test TransformExecutionResult can be created with required fields."""
        from app.services.transform_execution_service import TransformExecutionResult

        result = TransformExecutionResult(
            output_dataset_id="dataset_out_123",
            row_count=100,
            column_names=["col1", "col2"],
            execution_time_ms=150.5,
        )

        assert result.output_dataset_id == "dataset_out_123"
        assert result.row_count == 100
        assert result.column_names == ["col1", "col2"]
        assert result.execution_time_ms == 150.5

    def test_result_immutability(self) -> None:
        """Test TransformExecutionResult is immutable (frozen dataclass)."""
        from app.services.transform_execution_service import TransformExecutionResult

        result = TransformExecutionResult(
            output_dataset_id="dataset_out_123",
            row_count=100,
            column_names=["col1", "col2"],
            execution_time_ms=150.5,
        )

        # Attempt to modify should raise error
        with pytest.raises((AttributeError, Exception)):
            result.output_dataset_id = "modified"  # type: ignore


# ============================================================================
# TransformExecutionService Tests
# ============================================================================


class TestTransformExecutionService:
    """Test suite for TransformExecutionService."""

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test successful transform execution with single input dataset."""
        from app.services.transform_execution_service import (
            TransformExecutionService,
            TransformExecutionResult,
        )

        # Setup
        transform = create_mock_transform(
            input_dataset_ids=["dataset_input_1"],
        )
        input_dataset = create_mock_dataset(
            dataset_id="dataset_input_1",
            s3_path="datasets/dataset_input_1/data/part-0000.parquet",
        )

        # Mock DatasetRepository
        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo.create = AsyncMock(
                return_value=create_mock_dataset(dataset_id="dataset_output_1")
            )
            mock_repo_cls.return_value = mock_repo

            # Mock ParquetReader
            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                # Mock Executor API call
                with patch("httpx.AsyncClient") as mock_client_cls:
                    executor_response = {
                        "data": sample_dataframe.to_dict(orient="records"),
                        "columns": ["col1", "col2"],
                        "row_count": 3,
                    }
                    mock_response = MagicMock()
                    mock_response.json.return_value = executor_response
                    mock_response.raise_for_status = MagicMock()

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    # Mock ParquetConverter
                    with patch(
                        "app.services.transform_execution_service.ParquetConverter"
                    ) as mock_converter_cls:
                        mock_converter = MagicMock()
                        mock_converter.convert_and_save.return_value = MagicMock(
                            s3_path="datasets/dataset_output_1/data/part-0000.parquet"
                        )
                        mock_converter_cls.return_value = mock_converter

                        # Mock TransformRepository
                        with patch(
                            "app.services.transform_execution_service.TransformRepository"
                        ) as mock_transform_repo_cls:
                            mock_transform_repo = MagicMock()
                            mock_transform_repo.update = AsyncMock(return_value=transform)
                            mock_transform_repo_cls.return_value = mock_transform_repo

                            # Execute
                            service = TransformExecutionService()
                            result = await service.execute(
                                transform=transform,
                                dynamodb=mock_dynamodb,
                                s3=mock_s3_client,
                            )

                            # Verify
                            assert isinstance(result, TransformExecutionResult)
                            assert result.output_dataset_id is not None
                            assert result.row_count == 3
                            assert result.column_names == ["col1", "col2"]
                            assert result.execution_time_ms >= 0

    @pytest.mark.asyncio
    async def test_execute_input_dataset_not_found(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test execute raises error when input dataset not found."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform(
            input_dataset_ids=["nonexistent_dataset"],
        )

        # Mock DatasetRepository to return None
        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=None)
            mock_repo_cls.return_value = mock_repo

            service = TransformExecutionService()

            with pytest.raises(ValueError, match="Input dataset .* not found"):
                await service.execute(
                    transform=transform,
                    dynamodb=mock_dynamodb,
                    s3=mock_s3_client,
                )

    @pytest.mark.asyncio
    async def test_execute_input_dataset_no_s3_path(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
    ) -> None:
        """Test execute raises error when input dataset has no s3_path."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform(
            input_dataset_ids=["dataset_no_path"],
        )
        input_dataset = create_mock_dataset(
            dataset_id="dataset_no_path",
            s3_path=None,  # type: ignore
        )
        # Manually set s3_path to None
        input_dataset = Dataset(
            id="dataset_no_path",
            name="Test Dataset",
            source_type="csv",
            row_count=100,
            schema=[ColumnSchema(name="col1", data_type="string", nullable=False)],
            owner_id="user_123",
            s3_path=None,
            column_count=1,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo_cls.return_value = mock_repo

            service = TransformExecutionService()

            with pytest.raises(ValueError, match="Input dataset .* has no data"):
                await service.execute(
                    transform=transform,
                    dynamodb=mock_dynamodb,
                    s3=mock_s3_client,
                )

    @pytest.mark.asyncio
    async def test_execute_multiple_input_datasets(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute with multiple input datasets."""
        from app.services.transform_execution_service import (
            TransformExecutionService,
            TransformExecutionResult,
        )

        transform = create_mock_transform(
            input_dataset_ids=["dataset_1", "dataset_2"],
            code="def transform(df1, df2): return df1.merge(df2)",
        )
        dataset_1 = create_mock_dataset(
            dataset_id="dataset_1",
            s3_path="datasets/dataset_1/data/part-0000.parquet",
        )
        dataset_2 = create_mock_dataset(
            dataset_id="dataset_2",
            s3_path="datasets/dataset_2/data/part-0000.parquet",
        )

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()

            async def get_by_id_side_effect(dataset_id: str, dynamodb: Any) -> Dataset | None:
                if dataset_id == "dataset_1":
                    return dataset_1
                elif dataset_id == "dataset_2":
                    return dataset_2
                return None

            mock_repo.get_by_id = AsyncMock(side_effect=get_by_id_side_effect)
            mock_repo.create = AsyncMock(
                return_value=create_mock_dataset(dataset_id="dataset_output_1")
            )
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls:
                    executor_response = {
                        "data": sample_dataframe.to_dict(orient="records"),
                        "columns": ["col1", "col2"],
                        "row_count": 3,
                    }
                    mock_response = MagicMock()
                    mock_response.json.return_value = executor_response
                    mock_response.raise_for_status = MagicMock()

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    with patch(
                        "app.services.transform_execution_service.ParquetConverter"
                    ) as mock_converter_cls:
                        mock_converter = MagicMock()
                        mock_converter.convert_and_save.return_value = MagicMock(
                            s3_path="datasets/dataset_output_1/data/part-0000.parquet"
                        )
                        mock_converter_cls.return_value = mock_converter

                        with patch(
                            "app.services.transform_execution_service.TransformRepository"
                        ) as mock_transform_repo_cls:
                            mock_transform_repo = MagicMock()
                            mock_transform_repo.update = AsyncMock(return_value=transform)
                            mock_transform_repo_cls.return_value = mock_transform_repo

                            service = TransformExecutionService()
                            result = await service.execute(
                                transform=transform,
                                dynamodb=mock_dynamodb,
                                s3=mock_s3_client,
                            )

                            # Verify
                            assert isinstance(result, TransformExecutionResult)
                            # Verify executor was called with multiple datasets
                            call_args = mock_client.post.call_args
                            assert call_args is not None
                            json_body = call_args[1]["json"]
                            assert "datasets" in json_body
                            assert len(json_body["datasets"]) == 2

    @pytest.mark.asyncio
    async def test_execute_executor_retry_on_5xx(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute retries on 5xx errors from Executor API."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform()
        input_dataset = create_mock_dataset(dataset_id="dataset_input_1")

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls, \
                     patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    # First 2 calls fail with 500, third succeeds
                    mock_500_response = MagicMock()
                    mock_500_response.status_code = 500
                    mock_500_response.text = "Internal Server Error"
                    mock_500_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "500 Internal Server Error",
                        request=MagicMock(),
                        response=mock_500_response,
                    )

                    executor_response = {
                        "data": sample_dataframe.to_dict(orient="records"),
                        "columns": ["col1", "col2"],
                        "row_count": 3,
                    }
                    mock_success_response = MagicMock()
                    mock_success_response.json.return_value = executor_response
                    mock_success_response.raise_for_status = MagicMock()

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(
                        side_effect=[
                            mock_500_response,
                            mock_500_response,
                            mock_success_response,
                        ]
                    )
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    with patch(
                        "app.services.transform_execution_service.ParquetConverter"
                    ) as mock_converter_cls:
                        mock_converter = MagicMock()
                        mock_converter.convert_and_save.return_value = MagicMock(
                            s3_path="datasets/output/data/part-0000.parquet"
                        )
                        mock_converter_cls.return_value = mock_converter

                        with patch(
                            "app.services.transform_execution_service.TransformRepository"
                        ) as mock_transform_repo_cls:
                            mock_transform_repo = MagicMock()
                            mock_transform_repo.update = AsyncMock(return_value=transform)
                            mock_transform_repo_cls.return_value = mock_transform_repo

                            mock_repo.create = AsyncMock(
                                return_value=create_mock_dataset(dataset_id="output")
                            )

                            service = TransformExecutionService()
                            result = await service.execute(
                                transform=transform,
                                dynamodb=mock_dynamodb,
                                s3=mock_s3_client,
                            )

                            # Should have succeeded after retries
                            assert result is not None
                            # Should have called post 3 times
                            assert mock_client.post.call_count == 3
                            # Should have slept between retries
                            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_executor_fails_after_max_retries(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute raises error after max retries exceeded."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform()
        input_dataset = create_mock_dataset(dataset_id="dataset_input_1")

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls, \
                     patch("asyncio.sleep", new_callable=AsyncMock):
                    # All calls fail with timeout
                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(
                        side_effect=httpx.TimeoutException("Timeout")
                    )
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    service = TransformExecutionService()

                    with pytest.raises(RuntimeError, match="Executor failed after"):
                        await service.execute(
                            transform=transform,
                            dynamodb=mock_dynamodb,
                            s3=mock_s3_client,
                        )

    @pytest.mark.asyncio
    async def test_execute_no_retry_on_4xx(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute does not retry on 4xx errors (client errors)."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform()
        input_dataset = create_mock_dataset(dataset_id="dataset_input_1")

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls, \
                     patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    # Return 400 error (should not retry)
                    mock_400_response = MagicMock()
                    mock_400_response.status_code = 400
                    mock_400_response.text = "Bad Request: Invalid transform code"
                    mock_400_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "400 Bad Request",
                        request=MagicMock(),
                        response=mock_400_response,
                    )

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_400_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    service = TransformExecutionService()

                    with pytest.raises(RuntimeError, match="Executor returned client error"):
                        await service.execute(
                            transform=transform,
                            dynamodb=mock_dynamodb,
                            s3=mock_s3_client,
                        )

                    # Should have called post only once (no retry)
                    assert mock_client.post.call_count == 1
                    # Should not have slept
                    mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_updates_transform_output_dataset_id(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute updates Transform.output_dataset_id after success."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform(
            transform_id="transform_to_update",
            output_dataset_id=None,
        )
        input_dataset = create_mock_dataset(dataset_id="dataset_input_1")

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo.create = AsyncMock(
                return_value=create_mock_dataset(dataset_id="new_output_dataset")
            )
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls:
                    executor_response = {
                        "data": sample_dataframe.to_dict(orient="records"),
                        "columns": ["col1", "col2"],
                        "row_count": 3,
                    }
                    mock_response = MagicMock()
                    mock_response.json.return_value = executor_response
                    mock_response.raise_for_status = MagicMock()

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    with patch(
                        "app.services.transform_execution_service.ParquetConverter"
                    ) as mock_converter_cls:
                        mock_converter = MagicMock()
                        mock_converter.convert_and_save.return_value = MagicMock(
                            s3_path="datasets/new_output_dataset/data/part-0000.parquet"
                        )
                        mock_converter_cls.return_value = mock_converter

                        with patch(
                            "app.services.transform_execution_service.TransformRepository"
                        ) as mock_transform_repo_cls:
                            mock_transform_repo = MagicMock()
                            mock_transform_repo.update = AsyncMock(return_value=transform)
                            mock_transform_repo_cls.return_value = mock_transform_repo

                            service = TransformExecutionService()
                            result = await service.execute(
                                transform=transform,
                                dynamodb=mock_dynamodb,
                                s3=mock_s3_client,
                            )

                            # Verify TransformRepository.update was called
                            mock_transform_repo.update.assert_called_once()
                            call_args = mock_transform_repo.update.call_args
                            assert call_args[0][0] == "transform_to_update"
                            assert "output_dataset_id" in call_args[0][1]
                            # Verify the output_dataset_id matches the result
                            assert call_args[0][1]["output_dataset_id"] == result.output_dataset_id

    @pytest.mark.asyncio
    async def test_execute_creates_output_dataset_with_correct_owner(
        self,
        mock_dynamodb: MagicMock,
        mock_s3_client: MagicMock,
        sample_dataframe: pd.DataFrame,
    ) -> None:
        """Test execute creates output dataset with Transform's owner_id."""
        from app.services.transform_execution_service import TransformExecutionService

        transform = create_mock_transform(
            owner_id="transform_owner_user",
        )
        input_dataset = create_mock_dataset(
            dataset_id="dataset_input_1",
            owner_id="different_owner",  # Different from transform owner
        )

        with patch(
            "app.services.transform_execution_service.DatasetRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id = AsyncMock(return_value=input_dataset)
            mock_repo.create = AsyncMock(
                return_value=create_mock_dataset(
                    dataset_id="output_dataset",
                    owner_id="transform_owner_user",
                )
            )
            mock_repo_cls.return_value = mock_repo

            with patch(
                "app.services.transform_execution_service.ParquetReader"
            ) as mock_reader_cls:
                mock_reader = MagicMock()
                mock_reader.read_full.return_value = sample_dataframe
                mock_reader_cls.return_value = mock_reader

                with patch("httpx.AsyncClient") as mock_client_cls:
                    executor_response = {
                        "data": sample_dataframe.to_dict(orient="records"),
                        "columns": ["col1", "col2"],
                        "row_count": 3,
                    }
                    mock_response = MagicMock()
                    mock_response.json.return_value = executor_response
                    mock_response.raise_for_status = MagicMock()

                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(return_value=mock_response)
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client_cls.return_value = mock_client

                    with patch(
                        "app.services.transform_execution_service.ParquetConverter"
                    ) as mock_converter_cls:
                        mock_converter = MagicMock()
                        mock_converter.convert_and_save.return_value = MagicMock(
                            s3_path="datasets/output/data/part-0000.parquet"
                        )
                        mock_converter_cls.return_value = mock_converter

                        with patch(
                            "app.services.transform_execution_service.TransformRepository"
                        ) as mock_transform_repo_cls:
                            mock_transform_repo = MagicMock()
                            mock_transform_repo.update = AsyncMock(return_value=transform)
                            mock_transform_repo_cls.return_value = mock_transform_repo

                            service = TransformExecutionService()
                            await service.execute(
                                transform=transform,
                                dynamodb=mock_dynamodb,
                                s3=mock_s3_client,
                            )

                            # Verify DatasetRepository.create was called with correct owner
                            mock_repo.create.assert_called_once()
                            create_call_args = mock_repo.create.call_args
                            dataset_dict = create_call_args[0][0]
                            assert dataset_dict["owner_id"] == "transform_owner_user"
