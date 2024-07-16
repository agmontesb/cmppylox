import tkinter as tk

import common
from vm import interpret


class Frontend(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("My App")
        self.attributes('-zoomed', True)

        self.input = tk.Text(self, height=10, font=('Courier', 11))
        self.input.pack(side=tk.BOTTOM, fill=tk.X)
        self.input.bind("<Return>", self.on_input)
        self.input.bind("<Control-Return>", self.on_input)
        self.input.bind('<BackSpace>', self.backspace)
        self.input.bind('<Delete>', self.delete)
        self.input.bind('<Up>', self.history)
        self.input.bind('<Down>', self.history)
        self.input.bind('<Control-c>', self.clear_prompt)
        self.input.bind('<braceleft>', self.braceleft)
        # self.input.bind('<Key>', self.Key)
        self.input.insert(tk.INSERT, '>>> ')

        self.output = tk.Text(self, font=('Courier', 11))
        self.output.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.history_list = []
        self.history_index = len(self.history_list)
        common.out_file = self

    def braceleft(self, event: tk.Event):
        wdg = event.widget
        wdg.insert(tk.INSERT, '{}')
        wdg.mark_set(tk.INSERT, 'insert-1c')
        return 'break'

    def clear_prompt(self, event: tk.Event):
        wdg = event.widget
        wdg.delete('1.0', tk.END)
        wdg.insert(tk.INSERT, '>>> ')
        return 'break'

    def delete(self, event: tk.Event):
        wdg = event.widget
        line, col = map(int, wdg.index(tk.INSERT).split('.'))
        if wdg.index(f'{line}.end') == wdg.index(tk.INSERT):
            wdg.delete(f'{line}.end', f'{line + 1}.4')
            return 'break'
        wdg.delete('insert')
        return 'break'

    def backspace(self, event: tk.Event):
        wdg = event.widget
        if wdg.index(tk.INSERT) == '1.4':
            return 'break'
        line, col = map(int, wdg.index(tk.INSERT).split('.'))
        if col <= 4:
            wdg.delete(f'{line-1}.end-1c', f'{line}.end')
            return 'break'
        wdg.delete('insert-1c')
        return 'break'

    def Key(self, event: tk.Event):
        wdg = event.widget
        print(event.keycode)

    def history(self, event: tk.Event):
        wdg = event.widget
        line, col = map(int, wdg.index(tk.INSERT).split('.'))
        last_line = int(wdg.index(tk.END).split('.')[0]) - 1
        if (event.keysym == 'Up' and line > 1) or (event.keysym == 'Down' and line < last_line):  # Up
            return
        if len(self.history_list) == 0 or (self.history_index == 1 + len(self.history_list) and col > 4):
            return 'break'
        self.history_index += -1 if event.keysym == 'Up' else 1
        self.history_index = max(1, min(self.history_index, 1 + len(self.history_list)))
        wdg.delete('1.0', tk.END)
        content = self.history_list[self.history_index - 1] if self.history_index <= len(self.history_list) else '>>> '
        wdg.insert(tk.INSERT, content)
        last_line = int(wdg.index(tk.END).split('.')[0]) - 1
        wdg.mark_set(tk.INSERT, f'{last_line}.end')
        return 'break'

    def on_input(self, event: tk.Event):
        wdg:tk.Text = event.widget
        currentline, endline = map(lambda x: int(wdg.index(x).split('.')[0]), (tk.INSERT, tk.END))
        with_control = event.state & 0x4
        if with_control or currentline != endline - 1: # Control key 0x4
            indent = wdg.get('1.0', tk.INSERT).count('{') - wdg.get('1.0', tk.INSERT).count('}')
            wdg.insert(tk.INSERT, '\n... ' + indent * '    ')
            pos = wdg.index(tk.INSERT)
            if wdg.get(pos) == '}':
                wdg.insert(tk.INSERT, '\n... ' + (indent - 1) * '    ')
            wdg.mark_set(tk.INSERT, pos)
            return 'break'
        raw_text = wdg.get("1.0", tk.END)
        wdg.delete("1.0", tk.END)
        wdg.insert(tk.INSERT, '>>> ')
        self.history_list.append(raw_text.strip())
        self.history_index = 1 + len(self.history_list)
        self.write(raw_text)
        text = '\n'.join([x[4:] for x in raw_text.splitlines()]) # Skip the prompt sig
        if not text:
            self.destroy()
        interpret(text + '\n')
        return 'break'

    def write(self, text):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)

    def run(self):
        self.mainloop()


def main():
    app = Frontend()
    app.run()


if __name__ == '__main__':
    main()