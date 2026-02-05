"""
カスタム例外クラスの定義
"""


class DatasetFileNotFoundError(RuntimeError):
    """
    データセットのparquetファイルがS3に存在しない場合に発生する例外。

    RuntimeErrorのサブクラスとして定義することで、
    既存のcatchブロックとの後方互換性を維持する。
    """

    def __init__(self, s3_path: str, dataset_id: str | None = None):
        """
        Args:
            s3_path: S3上のファイルパス
            dataset_id: データセットID（オプショナル）
        """
        self.s3_path = s3_path
        self.dataset_id = dataset_id

        message = f"Dataset file not found: {s3_path}"
        if dataset_id is not None:
            message += f" (dataset_id: {dataset_id})"

        super().__init__(message)
