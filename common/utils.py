from pathlib import Path
from typing import Any


class JsonDict(dict[str, Any]):
    pass


class CsvWriter:
    def __init__(self, file_name: str, file_path: Path, header: list[str] = None, delimiter: str = ','):
        file_path.mkdir(parents=True, exist_ok=True)
        self.file_path = file_path / f'{file_name}.csv'
        self.delimiter = delimiter
        self.header = self.delimiter.join([str(col_name) for col_name in header]) + '\n' if header else None
        self._create_file()

    def _create_file(self):
        with open(self.file_path, 'a+') as file:
            if not self.header:
                return

            lines = self.read()
            if len(lines) == 0:
                self.write_row([self.header], file)
                return

            if str(lines[0]) != self.header:
                raise ValueError('Different headers in files')

    def write_rows(self, table_data: [list[list]]) -> None:
        with open(self.file_path, 'a') as file:
            for table_row in table_data:
                self.write_row(table_row, file)

    def write_row(self, row: list, file=None) -> None:
        row_to_string = self.delimiter.join([str(val).strip() for val in row]) + '\n'
        if file:
            file.write(row_to_string)
        else:
            with open(self.file_path, 'a') as file:
                file.write(row_to_string)

    def read(self, start_row=0, limit: int = None) -> list:
        with open(self.file_path, 'r') as file:
            lines: list = file.readlines()
            if len(lines) == 0:
                return []
            end_row = len(lines) if not limit else min(len(lines), start_row + limit)
            return lines[start_row:end_row]
