def f_split_table(row_groups, col_groups, df_table):
    subtables = {}

    all_rows = set(range(df_table.shape[0]))
    grouped_rows = set(sum(row_groups, []))
    if all_rows != grouped_rows:
        missing_rows = all_rows - grouped_rows
        raise ValueError(f"Missing Rows: {missing_rows}")

    all_cols = set(range(df_table.shape[1]))
    grouped_cols = set(sum(col_groups, []))
    if all_cols != grouped_cols:
        missing_cols = all_cols - grouped_cols
        raise ValueError(f"Missing Cols: {missing_cols}")

    for i, rows in enumerate(row_groups):
        for j, cols in enumerate(col_groups):
            sub_df = df_table.iloc[rows, cols].reset_index(drop=True)
            subtables[(i, j)] = sub_df

    return subtables