def f_select_row_col(row_list, col_list, df):
    try:
        return df.iloc[row_list][col_list].reset_index(drop=True)
    except Exception:
        return df


def f_select_row_col_instructions():
    pass
