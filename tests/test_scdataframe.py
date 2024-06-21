"""
Tests cosmicqc SCDataFrame module
"""

import pathlib

import cosmicqc
import pandas as pd
import plotly
from cosmicqc.scdataframe import SCDataFrame
from pyarrow import parquet


def test_SCDataFrame_with_dataframe(
    tmp_path: pathlib.Path,
    basic_outlier_dataframe: pd.DataFrame,
    basic_outlier_csv: str,
    basic_outlier_csv_gz: str,
    basic_outlier_tsv: str,
    basic_outlier_parquet: str,
):
    # Tests SCDataFrame with pd.DataFrame input.
    sc_df = SCDataFrame(data=basic_outlier_dataframe)

    # test that we ingested the data properly
    assert sc_df.data_source == "pandas.DataFrame"
    assert sc_df.equals(basic_outlier_dataframe)

    # test export
    basic_outlier_dataframe.to_parquet(
        control_path := f"{tmp_path}/df_input_example.parquet"
    )
    sc_df.export(test_path := f"{tmp_path}/df_input_example1.parquet")

    assert parquet.read_table(control_path).equals(parquet.read_table(test_path))

    # Tests SCDataFrame with pd.Series input.
    sc_df = SCDataFrame(data=basic_outlier_dataframe.loc[0])

    # test that we ingested the data properly
    assert sc_df.data_source == "pandas.Series"
    assert sc_df.equals(pd.DataFrame(basic_outlier_dataframe.loc[0]))

    # Tests SCDataFrame with CSV input.
    sc_df = SCDataFrame(data=basic_outlier_csv)
    expected_df = pd.read_csv(basic_outlier_csv)

    # test that we ingested the data properly
    assert sc_df.data_source == basic_outlier_csv
    assert sc_df.equals(expected_df)

    # test export
    sc_df.export(test_path := f"{tmp_path}/df_input_example.csv", index=False)

    pd.testing.assert_frame_equal(expected_df, pd.read_csv(test_path))

    # Tests SCDataFrame with CSV input.
    sc_df = SCDataFrame(data=basic_outlier_csv_gz)
    expected_df = pd.read_csv(basic_outlier_csv_gz)

    # test that we ingested the data properly
    assert sc_df.data_source == basic_outlier_csv_gz
    assert sc_df.equals(expected_df)

    # test export
    sc_df.export(test_path := f"{tmp_path}/df_input_example.csv.gz", index=False)

    pd.testing.assert_frame_equal(
        expected_df, pd.read_csv(test_path, compression="gzip")
    )

    # Tests SCDataFrame with TSV input.
    sc_df = SCDataFrame(data=basic_outlier_tsv)
    expected_df = pd.read_csv(basic_outlier_tsv, delimiter="\t")

    # test that we ingested the data properly
    assert sc_df.data_source == basic_outlier_tsv
    assert sc_df.equals(expected_df)

    # test export
    sc_df.export(test_path := f"{tmp_path}/df_input_example.tsv", index=False)

    pd.testing.assert_frame_equal(expected_df, pd.read_csv(test_path, sep="\t"))

    # Tests SCDataFrame with parquet input.
    sc_df = SCDataFrame(data=basic_outlier_parquet)
    expected_df = pd.read_parquet(basic_outlier_parquet)

    # test that we ingested the data properly
    assert sc_df.data_source == basic_outlier_parquet
    assert sc_df.equals(expected_df)

    # test export
    sc_df.export(test_path := f"{tmp_path}/df_input_example2.parquet")

    assert parquet.read_table(basic_outlier_parquet).equals(
        parquet.read_table(test_path)
    )

    # test SCDataFrame with SCDataFrame input
    copy_sc_df = SCDataFrame(data=sc_df)

    pd.testing.assert_frame_equal(copy_sc_df.data, sc_df.data)


def test_show_report(cytotable_CFReT_data_df: pd.DataFrame):
    """
    Used for testing show report capabilities
    """

    df = cosmicqc.analyze.label_outliers(
        df=cytotable_CFReT_data_df,
        include_threshold_scores=True,
    )

    figures = df.show_report(auto_open=False)

    expected_number_figures = 3
    assert len(figures) == expected_number_figures
    assert (
        next(iter({type(figure) for figure in figures}))
        == plotly.graph_objs._figure.Figure
    )

    df.show_report(
        report_path=(
            report_path := pathlib.Path(__file__).parent
            / "data"
            / "coSMicQC"
            / "show_report"
            / "cosmicqc_example_report.html"
        ),
        auto_open=False,
    )

    assert report_path.is_file()
