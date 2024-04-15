import os

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer


def count_tokens(corpus, min_df=0.0, max_df=1.0):
    # For filtering play with: max_df, min_df, max_features
    cv = CountVectorizer(input='filename', decode_error='ignore', token_pattern=r"(?u)\b[a-zA-Z]\w+\b", min_df=min_df, max_df=max_df)
    td_matrix = cv.fit_transform(corpus)
    terms = cv.get_feature_names_out()
    return (td_matrix, terms)


def extract_tokens(corpus_dir):
    # Get all files
    documents = []
    for prefix, _, files in os.walk(corpus_dir):
        parts = os.path.basename(os.path.normpath(prefix)).split('_')
        for file in files:
            document = {
                "project": parts[1],
                "local_index": int(parts[0]),
                "hash": parts[2],
                "file": os.path.join(prefix, file)
            }
            documents.append(document)
    sorted_documents = sorted(documents, key=lambda k: (k["project"], k["local_index"]))
    corpus = [doc["file"] for doc in sorted_documents]
    td_matrix, terms = count_tokens(corpus, min_df=0.05, max_df=0.8)
    td_matrix_df = pd.DataFrame(td_matrix.toarray(), columns=terms)
    metadatas = [(doc["project"], doc["hash"]) for doc in sorted_documents]
    metadata_df = pd.DataFrame(metadatas, columns=["0_project", "0_hash"])
    df = pd.concat([metadata_df, td_matrix_df], axis=1)
    df_groups = df.groupby(["0_project", "0_hash"], sort=False)
    sums_df = df_groups.sum().reset_index()
    sums_df["0_project"] = sums_df["0_project"].astype("string")
    sums_df["0_hash"] = sums_df["0_hash"].astype("string")
    # merged_df = commits_df.merge(sums_df, on=["0_project", "0_hash"], how="outer")
    # merged_df = merged_df.fillna(0, downcast="infer")
    return sums_df


def extract_token_differences(corpus_dir):
    document_pairs = []
    for prefix, dirs, files in os.walk(corpus_dir):
        # This is a patch-directory
        if len(dirs) == 0:
            parts = prefix.split(os.path.sep)[-2].split('_')
            # In each patch-directory, pair the two documents
            document_pair = {
                "project": parts[1],
                "local_index": int(parts[0]),
                "hash": parts[2],
                "deleted_file": os.path.join(prefix, "deleted.php"),
                "added_file": os.path.join(prefix, "added.php")
            }
            document_pairs.append(document_pair)
    sorted_document_pairs = sorted(document_pairs, key=lambda k: (k["project"], k["local_index"]))
    metadatas = []
    corpus_deleted = []
    corpus_added = []
    for pair in sorted_document_pairs:
        metadatas.append((pair["project"], pair["hash"]))
        corpus_deleted.append(pair["deleted_file"])
        corpus_added.append(pair["added_file"])
    td_matrix_deleted, terms_deleted = count_tokens(corpus_deleted, min_df=0.05, max_df=0.8)
    td_matrix_added, terms_added = count_tokens(corpus_added, min_df=0.05, max_df=0.8)
    td_matrix_deleted_df = pd.DataFrame(td_matrix_deleted.toarray(), columns=terms_deleted)
    td_matrix_added_df = pd.DataFrame(td_matrix_added.toarray(), columns=terms_added)
    for t in [t for t in terms_added if t not in terms_deleted]:
        td_matrix_deleted_df[t] = 0
    for t in [t for t in terms_deleted if t not in terms_added]:
        td_matrix_added_df[t] = 0
    td_matrix_deleted_df = td_matrix_deleted_df.reindex(sorted(td_matrix_deleted_df.columns), axis=1)
    td_matrix_added_df = td_matrix_added_df.reindex(sorted(td_matrix_added_df.columns), axis=1)
    td_matrix_delta_df = (td_matrix_deleted_df - td_matrix_added_df).abs()

    metadata_df = pd.DataFrame(metadatas, columns=["0_project", "0_hash"])
    df = pd.concat([metadata_df, td_matrix_delta_df], axis=1)
    df_groups = df.groupby(["0_project", "0_hash"], sort=False)
    sums_df = df_groups.sum().reset_index()
    sums_df["0_project"] = sums_df["0_project"].astype("string")
    sums_df["0_hash"] = sums_df["0_hash"].astype("string")
    # merged_df = commits_df.merge(sums_df, on=["0_project", "0_hash"], how="outer")
    # merged_df = merged_df.fillna(0, downcast="infer")
    return sums_df
