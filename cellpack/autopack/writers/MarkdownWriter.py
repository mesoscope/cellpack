from pathlib import Path

from mdutils.mdutils import MdUtils
import pandas as pd

"""
MarkdownWriter provides a class to write markdown files
"""


class MarkdownWriter(object):
    def __init__(
        self,
        title: str,
        output_path: Path,
        output_image_location: Path,
        report_name: str,
    ):
        self.title = title
        self.output_path = output_path
        self.output_image_location = output_image_location
        self.report_md = MdUtils(
            file_name=str(self.output_path / report_name),
            title=title,
        )

    # level is the header style, can only be 1 or 2
    def add_header(self, header, level: int = 2):
        self.report_md.new_header(level=level, title=header, add_table_of_contents="n")

    def add_table(self, header, table, text_align="center"):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )

        header_row = table.columns.tolist()
        text_list = header_row + [
            item for sublist in table.values.tolist() for item in sublist
        ]

        total_rows = table.shape[0] + 1  # Adding 1 for the header row
        total_columns = table.shape[1]

        self.report_md.new_table(
            columns=total_columns,
            rows=total_rows,
            text=text_list,
            text_align=text_align,
        )

    def add_table_from_csv(self, header, filepath, text_align="center"):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )

        table = pd.read_csv(filepath)

        header_row = table.columns.tolist()
        text_list = header_row + [
            item for sublist in table.values.tolist() for item in sublist
        ]
        total_rows = table.shape[0] + 1  # Adding 1 for the header row
        total_columns = table.shape[1]

        self.report_md.new_table(
            columns=total_columns,
            rows=total_rows,
            text=text_list,
            text_align=text_align,
        )

    # Image text must be a list, if list is not same length as list of filepaths, only 1st item in image_text is used
    def add_images(self, header, image_text, filepaths):
        self.report_md.new_header(
            level=1,
            title=header,
            add_table_of_contents="n",
        )
        if len(image_text) == len(filepaths):
            for i in range(len(filepaths)):
                img_path = f"{self.output_image_location}/{filepaths[i].name}"
                self.report_md.new_line(
                    self.report_md.new_inline_image(
                        text=image_text[i],
                        path=img_path,
                    )
                )
        else:
            for i in range(len(filepaths)):
                img_path = f"{self.output_image_location}/{filepaths[i].name}"
                self.report_md.new_line(
                    self.report_md.new_inline_image(
                        text=image_text[0],
                        path=img_path,
                    )
                )
        self.report_md.new_line("")

    def add_line(self, line):
        self.report_md.new_line(line)

    def add_list(self, list_items):
        self.report_md.new_list(list_items)

    def add_inline_image(self, text, filepath):
        return self.report_md.new_inline_image(text=text, path=str(filepath))

    def write_file(self):
        self.report_md.create_md_file()
