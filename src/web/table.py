from typing import Union, List, Tuple, Dict


class TItem:
    def __init__(self, value, style=None):
        self.value = value
        self.style = style

    def __len__(self):
        return len(str(self.value))

    def __str__(self):
        return str(self.value) if not isinstance(self.value, str) else f'"{self.value}"'


class TLine:
    def __init__(self, values: List, is_header=False):
        self.value = values
        self.is_header = is_header

    def __iter__(self):
        self.__i = 0
        return self

    def __next__(self) -> TItem:
        x = self.__i
        self.__i += 1
        if self.__i <= len(self.value):
            return self.value[x]
        raise StopIteration

    def __getitem__(self, item) -> TItem:
        return self.value[item]

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return '%s' % ' | '.join([str(x) for x in self.value])


class Table:
    def __init__(self, data: List[Union[Tuple, List, Dict]]):
        self.data: [TLine] = []
        self.html: str = ''
        if isinstance(data, list):
            if isinstance(data[0], (list, tuple)):
                for line in data:
                    items = []
                    for item in line:
                        items.append(TItem(item))
                    self.data.append(TLine(items))
            elif isinstance(data[0], dict):
                self.data.append(TLine([TItem(key) for key in data[0].keys()], is_header=True))
                for line in data:
                    self.data.append(TLine([TItem(item) for item in line.values()]))
        if not self.data:
            raise ValueError(f'Table parsing error: incorrect argument {data=}')

    def __iter__(self):
        self.__i = 0
        return self

    def __next__(self) -> TLine:
        x = self.__i
        self.__i += 1
        if self.__i <= len(self.data):
            return self.data[x]
        raise StopIteration

    def __getitem__(self, row) -> TLine:
        return self.data[row]

    def __len__(self):
        return len(self.data)

    def __str__(self):
        sep = ' | '
        data_len = len(self.data[0])
        max_col_len = {}
        for i in range(len(self.data[0])):
            if i not in max_col_len:
                max_col_len[i] = 0
            for j in range(len(self.data)):
                col_len = max([len(line) for line in str(self.data[j][i].value).splitlines()])
                max_col_len[i] = max([col_len, max_col_len[i]])
        text = []
        for row in self.data:
            sub_row = {0: {}}
            for i, col in enumerate(row):
                if '\n' in str(col.value):
                    for j, value in enumerate(str(col.value).splitlines()):
                        if j in sub_row and i not in sub_row[j]:
                            sub_row[j][i] = value
                        else:
                            sub_row[j] = {i: value}
                else:
                    sub_row[0][i] = str(col.value) if col.value else ''
            for line in sub_row.values():
                data = {}
                for j, value in line.items():
                    for z in range(data_len):
                        if j not in data and z not in data:
                            data[z] = ' ' * max_col_len[z]
                        else:
                            if row.is_header:
                                data[j] = value.center(max_col_len[j])
                            else:
                                data[j] = value.ljust(max_col_len[j])
                text.append(sep.join(data.values()))
        return '\n'.join(text)

    def get_html(self):
        self.html = ''
        for line in self.data:
            self.html += '<tr>'
            for item in line:
                tag = 'th' if line.is_header else 'td'
                class_ = f' style="{item.style}"' if item.style else ''
                self.html += f'<{tag}{class_}>{item.value}</{tag}>'
            self.html += '</tr>'
        return self.html


if __name__ == '__main__':
    data = [
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 0]
    ]
    table = Table(data)
    for line in table:
        print(line)
        for x in line:
            print(x)
    table[1][4].style = 'color: white'
    print(table.get_html())
