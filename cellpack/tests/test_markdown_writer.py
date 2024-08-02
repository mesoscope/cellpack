import pytest
import pandas as pd
from cellpack.autopack.writers.MarkdownWriter import MarkdownWriter


@pytest.fixture
def setup_md_writer(tmp_path):
    title = "Test Report"
    output_path = tmp_path / "output"
    output_image_location = tmp_path / "images"
    report_name = "test_report.md"

    output_path.mkdir(parents=True, exist_ok=True)
    output_image_location.mkdir(parents=True, exist_ok=True)

    writer = MarkdownWriter(title, output_path, output_image_location, report_name)
    return writer, output_path / report_name


def test_add_header(setup_md_writer):
    writer, report_path = setup_md_writer
    writer.add_header("Header Level 2", level=2)
    writer.write_file()

    with open(report_path, "r") as f:
        report = f.read()
    assert "# Header Level 2" in report


def test_add_table(setup_md_writer):
    writer, report_path = setup_md_writer
    header = "Test Table"
    data = {
        "col1": [1, 2, 3],
        "col2": [4, 5, 6],
    }
    df = pd.DataFrame(data)
    writer.add_table(header, df)
    writer.write_file()

    with open(report_path, "r") as f:
        report = f.read()
    assert "Test Table" in report
    assert "|1|4|" in report


def test_add_table_from_csv(setup_md_writer, tmp_path):
    writer, report_path = setup_md_writer
    header = "Test Table"
    data = {
        "col1": [5, 6],
        "col2": [7, 8],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_table.csv"
    df.to_csv(csv_path, index=False)

    writer.add_table_from_csv(header, csv_path)
    writer.write_file()

    with open(report_path, "r") as f:
        report = f.read()
    assert "Test Table" in report
    assert "|5|7|" in report


def test_write_file(setup_md_writer):
    writer, report_path = setup_md_writer
    writer.add_header("Header Level 2", level=2)
    writer.add_header("Header Level 3", level=3)
    writer.add_header("Header Level 4", level=4)
    writer.write_file()

    with open(report_path, "r") as f:
        report = f.read()
    assert "# Header Level 2" in report
    assert "## Header Level 3" in report
    assert "### Header Level 4" in report


def test_add_image(setup_md_writer, tmp_path):
    writer, report_path = setup_md_writer
    header = "Test Image"
    image_text = ["Image 1", "Image 2"]
    filepaths = [tmp_path / "image1.png", tmp_path / "image2.png"]

    for image in filepaths:
        image.touch()

    writer.add_images(header, image_text, filepaths)
    writer.write_file()

    with open(report_path, "r") as f:
        report = f.read()
    assert "Test Image" in report
    assert "![Image 1]" in report
    assert "![Image 2]" in report
