"""
カスタム例外クラスのテスト
"""
import pytest

from app.exceptions import DatasetFileNotFoundError


class TestDatasetFileNotFoundError:
    """DatasetFileNotFoundErrorのテスト"""

    def test_create_with_s3_path_only(self):
        """s3_pathのみで生成できること"""
        s3_path = "s3://bucket/path/to/file.parquet"
        error = DatasetFileNotFoundError(s3_path=s3_path)

        assert error.s3_path == s3_path
        assert error.dataset_id is None
        assert "Dataset file not found: s3://bucket/path/to/file.parquet" in str(error)

    def test_create_with_s3_path_and_dataset_id(self):
        """s3_path + dataset_idで生成できること"""
        s3_path = "s3://bucket/path/to/file.parquet"
        dataset_id = "12345"
        error = DatasetFileNotFoundError(s3_path=s3_path, dataset_id=dataset_id)

        assert error.s3_path == s3_path
        assert error.dataset_id == dataset_id
        assert "Dataset file not found: s3://bucket/path/to/file.parquet" in str(error)
        assert "(dataset_id: 12345)" in str(error)

    def test_attributes_are_accessible(self):
        """属性アクセス (s3_path, dataset_id) ができること"""
        s3_path = "s3://test-bucket/data.parquet"
        dataset_id = "999"
        error = DatasetFileNotFoundError(s3_path=s3_path, dataset_id=dataset_id)

        # 属性が正しく設定されていることを確認
        assert hasattr(error, "s3_path")
        assert hasattr(error, "dataset_id")
        assert error.s3_path == s3_path
        assert error.dataset_id == dataset_id

    def test_is_subclass_of_runtime_error(self):
        """RuntimeErrorのサブクラスであることの確認"""
        s3_path = "s3://bucket/file.parquet"
        error = DatasetFileNotFoundError(s3_path=s3_path)

        # RuntimeErrorのサブクラスであることを確認
        assert isinstance(error, RuntimeError)

        # 通常のRuntimeErrorとしてキャッチできることを確認
        try:
            raise error
        except RuntimeError as e:
            assert isinstance(e, DatasetFileNotFoundError)
