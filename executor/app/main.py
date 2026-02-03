"""BI Executor - Python コード実行サービス"""
import time

import pandas as pd
from fastapi import FastAPI, HTTPException

from app.api_models import (
    ExecuteCardRequest,
    ExecuteCardResponse,
    ExecuteErrorResponse,
    ExecuteTransformRequest,
    ExecuteTransformResponse,
)
from app.runner import CardRunner
from app.transform_runner import TransformRunner

app = FastAPI(title="BI Executor")

runner = CardRunner(timeout_seconds=10, max_memory_mb=2048)
transform_runner = TransformRunner(timeout_seconds=300, max_memory_mb=4096)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/execute/card",
    response_model=ExecuteCardResponse,
    responses={400: {"model": ExecuteErrorResponse}, 408: {"model": ExecuteErrorResponse}},
)
def execute_card(request: ExecuteCardRequest):
    """カードのPythonコードを実行してHTMLを返す"""
    start_time = time.perf_counter()

    # DataFrameを構築
    if request.dataset_rows:
        dataset_df = pd.DataFrame(request.dataset_rows)
    else:
        dataset_df = pd.DataFrame()

    try:
        result = runner.execute(
            code=request.code,
            dataset_df=dataset_df,
            filters=request.filters,
            params=request.params,
        )
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ImportError, PermissionError, SyntaxError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実行エラー: {e}")

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return ExecuteCardResponse(
        html=result.html,
        used_columns=result.used_columns,
        filter_applicable=result.filter_applicable,
        execution_time_ms=elapsed_ms,
    )


@app.post(
    "/execute/transform",
    response_model=ExecuteTransformResponse,
    responses={400: {"model": ExecuteErrorResponse}, 408: {"model": ExecuteErrorResponse}},
)
def execute_transform(request: ExecuteTransformRequest):
    """TransformのPythonコードを実行してDataFrameを返す"""
    # 入力データセットをDataFrameに変換
    input_dfs = {
        dataset_id: pd.DataFrame(rows)
        for dataset_id, rows in request.input_datasets.items()
    }

    try:
        result = transform_runner.execute(
            code=request.code,
            inputs=input_dfs,
            params=request.params,
        )
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ImportError, PermissionError, SyntaxError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"実行エラー: {e}")

    # DataFrameを辞書のリストに変換
    output_rows = result.df.to_dict(orient='records')

    return ExecuteTransformResponse(
        output_rows=output_rows,
        row_count=len(result.df),
        column_names=list(result.df.columns),
        execution_time_ms=result.execution_time_ms,
    )
