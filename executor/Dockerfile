FROM python:3.11-slim AS base

# 非rootユーザ作成
RUN groupadd -r executor && useradd -r -g executor executor

# 依存ライブラリインストール
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# アプリケーションコピー
WORKDIR /workspace
COPY --chown=executor:executor app/ /workspace/app/

# 一時ディレクトリのみ書き込み可能
RUN mkdir -p /tmp/workdir && chown executor:executor /tmp/workdir

# 非rootユーザに切り替え
USER executor

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/workspace

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
