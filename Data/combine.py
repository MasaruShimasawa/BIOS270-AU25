import argparse
import h5py
import numpy as np
import sys
import os
import sqlite3
import pandas as pd

# (インポート文は前回のままでOK)
print("Successfully imported sqlite3 and pandas.")


# --- 定数（Constants）---
DATA_PATH = "/farmshare/home/classes/bios/270/data/processed_bacteria_data"
DB_PATH = os.path.join(DATA_PATH, "bacteria.db")
H5_PATH = os.path.join(DATA_PATH, "protein_embeddings.h5")

# HDF5内のIDデータセット名
H5_PROTEIN_ID_DATASET = 'protein_ids'
# ★ H5_EMBEDDINGS_DATASET = 'embeddings'  <-- この定数はもう使いません

EMBEDDING_DIM = 164

# --- HDF5用のヘルパー関数 (変更なし) ---
def create_protein_index_map(h5_file):
    print("Creating protein ID to index map from HDF5 file...")
    try:
        protein_ids_dataset = h5_file[H5_PROTEIN_ID_DATASET][:]
    except KeyError:
        print(f"Error: Dataset '{H5_PROTEIN_ID_DATASET}' not found in {H5_PATH}.", file=sys.stderr)
        sys.exit(1)
    protein_index_map = {pid.decode('utf-8'): i for i, pid in enumerate(protein_ids_dataset)}
    print(f"Map created with {len(protein_index_map)} entries.")
    return protein_index_map


def main():
    # --- ステップ1: 引数の処理 (変更なし) ---
    parser = argparse.ArgumentParser(description="Extract protein embeddings for a given record and metric.")
    parser.add_argument("record_id", type=str, help="The record ID to query (e.g., 'NC_000913.3')")
    parser.add_argument("metric", type=str, choices=['mean', 'mean_mid'], help="The metric to use ('mean' or 'mean_mid')")
    args = parser.parse_args()

    print(f"--- Starting process ---")
    print(f"Record ID: {args.record_id}")
    print(f"Metric:    {args.metric}")

    # --- ★ステップ2: SQLiteデータベースのクエリ (修正) ---
    conn = None 
    try:
        print("Connecting to DB directly in read-only mode...")
        db_uri = f'file:{DB_PATH}?mode=ro'
        conn = sqlite3.connect(db_uri, uri=True) 
        
        # ★★★ 修正点 ★★★
        # gff テーブルから、 'record_id' だけで絞り込む
        # 'metric' はSQLクエリでは使わない
        sql_query = f"""
        SELECT protein_id 
        FROM gff 
        WHERE record_id = '{args.record_id}'
        """
        
        print(f"Executing query: {sql_query.strip()}")
        df = pd.read_sql(sql_query, conn)
        
        # ★ 'protein_id' が見つからなかった場合に備えて dropna().unique() を追加
        protein_id_list = df['protein_id'].dropna().unique().tolist()

    except sqlite3.OperationalError as e:
        if "no such table: gff" in str(e):
             print("-> エラー: 'gff' テーブルが見つかりません。", file=sys.stderr)
        else:
             print(f"Error querying DB: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

    
    if not protein_id_list:
        print("No protein IDs found for this record_id. Exiting.")
        return 

    N = len(protein_id_list)
    print(f"Found {N} unique protein IDs in the database.")

    # --- ステップ3, 4, 5 (HDF5処理と保存) ---
    try:
        with h5py.File(H5_PATH, 'r') as hf:
            
            # ステップ3: インデックス辞書を作成 (変更なし)
            protein_to_index_map = create_protein_index_map(hf)
            
            # ★★★ 修正点 ★★★
            # ユーザーが入力した 'metric' の値 ('mean' or 'mean_mid') を
            # HDF5のデータセット名として直接使う
        # ★★★ 修正点 ★★★
            # 入力引数 ('mean') を HDF5内の実際の名前 ('mean_embeddings') にマッピング
            dataset_name_to_use = None
            if args.metric == 'mean':
                dataset_name_to_use = 'mean_embeddings'
            elif args.metric == 'mean_mid':
                dataset_name_to_use = 'mean_mid_embeddings'
            
            # マッピングした名前でデータセットにアクセス
            try:
                embeddings_dataset = hf[dataset_name_to_use]
                print(f"Successfully accessed HDF5 dataset: '{dataset_name_to_use}' (mapped from '{args.metric}')")
                
            except KeyError:
                print(f"Error: Dataset '{dataset_name_to_use}' not found in {H5_PATH}.", file=sys.stderr)
                print(f"HDF5ファイルの内容を再確認してください。", file=sys.stderr)
                return
            # ★★★ 修正完了 ★★★

            # ステップ4: 行列の構築 (変更なし)
            print("Building output matrix...")
            h5_indices_to_fetch = []
            for protein_id in protein_id_list:
                if protein_id in protein_to_index_map:
                    h5_indices_to_fetch.append(protein_to_index_map[protein_id])
                else:
                    print(f"Warning: Protein ID '{protein_id}' (from DB) not found in HDF5 protein_ids list. Skipping.", file=sys.stderr)
            
            if not h5_indices_to_fetch:
                print("Error: None of the protein IDs from the DB were found in the HDF5 file.", file=sys.stderr)
                return
            # ★★★ 修正点 ★★★
            # h5py に渡すため、インデックスリストを昇順にソート
            print(f"Sorting {len(h5_indices_to_fetch)} indices for HDF5 access...")
            h5_indices_to_fetch.sort()
            # ★★★ 修正完了 ★★★
            # ステップ5: データの抽出と保存
            output_matrix = embeddings_dataset[h5_indices_to_fetch, :]
            final_shape = output_matrix.shape
            print(f"Successfully built matrix. Shape: {final_shape}")

            output_filename = f"{args.record_id}_{args.metric}.npy"
            np.save(output_filename, output_matrix)
            print(f"\nSuccessfully saved matrix to: {output_filename}")

    except FileNotFoundError:
        print(f"Error: HDF5 file not found at {H5_PATH}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
