class TItem:
    def __init__(self, value, style=None):
        self.value = value
        self.style = style

    def __str__(self):
        return str(self.value)


class TLine:
    def __init__(self, values: []):
        self.value = values

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
        return 'Tline(%s)' % ', '.join([str(x) for x in self.value])


class Table:
    def __init__(self, data: [[]]):
        self.data: [TLine] = []
        self.html: str = ''
        for line in data:
            items = []
            for item in line:
                items.append(TItem(item))
            self.data.append(TLine(items))

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
        return str(self.data)

    def get_html(self):
        self.html = ''
        for line in self.data:
            self.html += '<tr>'
            for item in line:
                class_ = f' style="{item.style}"' if item.style else ''
                self.html += f'<td{class_}>{item}</td>'
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
