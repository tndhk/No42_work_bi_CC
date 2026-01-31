"""BI Executor - Python コード実行サービス"""
import time

import pandas as pd
from fastapi import FastAPI, HTTPException

from app.api_models import ExecuteCardRequest, ExecuteCardResponse, ExecuteErrorResponse
from app.runner import CardRunner

app = FastAPI(title="BI Executor")

runner = CardRunner(timeout_seconds=10, max_memory_mb=2048)


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
