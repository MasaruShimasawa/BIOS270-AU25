# 1. あなたのv1イメージをベースにする
FROM scr.svc.stanford.edu/masarus/containers/bioinfo_example:latest

# --- これ以降のコマンドは 'mambauser' として実行されます ---

# 2. 'curl' を 'base' 環境にインストール (これはOK)
RUN micromamba install -y -p /opt/conda -c conda-forge curl ca-certificates

# 3. 'parasail' を 'bioinfo_example' 環境にインストール (これもOK)
RUN micromamba run -n bioinfo_example pip install parasail

# 4. 'curl' を使って /tmp にダウンロード (これもOK)
RUN micromamba run -n base \
    curl -L https://github.com/sokrypton/reseek/releases/download/v1.0.0/reseek-linux-amd64 -o /tmp/reseek

# 5. 【修正点 1/3】
# これからシステムフォルダを操作するため、'root' (管理者) ユーザーに切り替える
USER root

# 6. 【修正点 2/3】
# 'root' として /tmp/reseek を /usr/local/bin/ に移動し、権限を付与する
RUN mv /tmp/reseek /usr/local/bin/reseek \
    && chmod +x /usr/local/bin/reseek

# 7. 【修正点 3/3】
# セキュリティのため、デフォルトの 'mambauser' に戻す
USER mambauser
