# 1. あなたのv1イメージをベースにする
FROM scr.svc.stanford.edu/masarus/containers/bioinfo_example:latest

# 2. 【v3からの成功】'reseek' を 'bioinfo_example' 環境に mamba でインストール
RUN micromamba install -n bioinfo_example -y -c conda-forge -c bioconda reseek

# 3. 【v2からの成功】'parasail' を 'bioinfo_example' 環境に pip でインストール
RUN micromamba run -n bioinfo_example pip install parasail
