import re

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.containers import Container
from textual.widget import Widget
from textual.widgets import (
    Header,
    Footer,
    TabbedContent,
    Label,
    Static,
    Button,
)

from virtual_machine import VirtualMachine, Register


class Board(Static):
    DEFAULT_CSS = """
    Board {
        align: center middle;
        border: round $accent;
        height: 1fr;
    }
    #board {
        layout: grid;
        grid-size: 5 5;
        grid-gutter: 1 2;
        grid-columns: 1fr;
        grid-rows: 1fr;
        width: 84;
        height: 19;
        align: center middle;
    }
    #numeric_display {
        column-span: 2;
        row-span: 1;
        width: 100%;
        height: 3;
        background: skyblue;
        content-align: center middle;
    }
    #led {
        layout: horizontal;
        column-span: 3;
        row-span: 1;
        width: 100%;
        height: 3;
        align: center middle;
    }
    Button {
        width: 100%;
        height: 100%;
    }
    """

    numeric_value = reactive("")
    led_value = reactive(0)

    def compose(self) -> ComposeResult:
        yield Container(
            Label(self.numeric_value, id="numeric_display"),
            Container(
                Label("⚫︎", id="led-6"),
                Label("⚫︎", id="led-5"),
                Label("⚫︎", id="led-4"),
                Label("⚫︎", id="led-3"),
                Label("⚫︎", id="led-2"),
                Label("⚫︎", id="led-1"),
                Label("⚫︎", id="led-0"),
                id="led",
            ),
            Button("C", variant="success", id="btn-c"),
            Button("D", variant="success", id="btn-d"),
            Button("E", variant="success", id="btn-e"),
            Button("F", variant="success", id="btn-f"),
            Button("ADR", variant="warning", id="btn-adr"),
            Button("8", variant="success", id="btn-8"),
            Button("9", variant="success", id="btn-9"),
            Button("A", variant="success", id="btn-a"),
            Button("B", variant="success", id="btn-b"),
            Button("INC", variant="warning", id="btn-inc"),
            Button("4", variant="success", id="btn-4"),
            Button("5", variant="success", id="btn-5"),
            Button("6", variant="success", id="btn-6"),
            Button("7", variant="success", id="btn-7"),
            Button("RUN", variant="warning", id="btn-run"),
            Button("0", variant="success", id="btn-0"),
            Button("1", variant="success", id="btn-1"),
            Button("2", variant="success", id="btn-2"),
            Button("3", variant="success", id="btn-3"),
            Button("RST", variant="warning", id="btn-rst"),
            id="board",
        )

    def watch_led_value(self, _, new_led) -> None:
        for i in range(7):
            if new_led & (1 << i) == 0:
                self.query_one(f"#led-{i}").styles.color = "white"
            else:
                self.query_one(f"#led-{i}").styles.color = "red"


class VirtualMachineController(Static):
    DEFAULT_CSS = """
        VirtualMachineController {
            align: center middle;
            height: 1fr;
            border: round $accent;
        }
        #virtual_machine_controller {
            layout: grid;
            grid-size: 3 3;
            align: center middle;
            grid-rows: 16 3;
            grid-gutter: 1;
        }
        #memory_view {
            column-span: 2;
            row-span: 1;
            layout: grid;
            grid-size: 17 16;
            grid-gutter: 0 1;
            grid-columns: 3 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
            width: 35;
        }
        #register_view {
            column-span: 1;
            row-span: 1;
            layout: grid;
            grid-size: 1 11;
            grid-rows: 1 1 1 1 1 1 1 1 1 1 1;
            width: 6;
        }
        LastInst {
            column-span: 3;
        }
    """

    class MemoryItem(Widget):
        value = reactive(0, always_update=True)

        def render(self) -> str:
            return f"{self.value:X}"

        def watch_value(self, old, new):
            if old == new:
                self.styles.background = "skyblue 0%"
            else:
                self.styles.background = "skyblue 50%"

    class RegisterItem(Widget):
        reg = reactive("")
        value = reactive(0)

        def __init__(
            self,
            name: str | None = None,
            id: str | None = None,
            classes: str | None = None,
            disabled: bool = False,
            reg: str = "",
        ):
            super().__init__(name=name, id=id, classes=classes, disabled=disabled)
            self.reg = reg

        def render(self) -> str:
            return f"{self.reg:2}: {self.value:X}"

    class LastInst(Widget):
        value = reactive("")

        def render(self) -> str:
            return f"LAST: {self.value}"

    def compose(self) -> ComposeResult:
        memory_labels = []
        for i in range(0x10):
            memory_labels.append(Static(f"{i << 4:02X}:"))
            for j in range(0x10):
                memory_labels.append(self.MemoryItem(id=f"mem-{i:x}-{j:x}"))
        yield Container(
            Container(*memory_labels, id="memory_view"),
            Container(
                self.RegisterItem(reg="A", id="reg-a"),
                self.RegisterItem(reg="B", id="reg-b"),
                self.RegisterItem(reg="Y", id="reg-y"),
                self.RegisterItem(reg="Z", id="reg-z"),
                self.RegisterItem(reg="A'", id="reg-a2"),
                self.RegisterItem(reg="B'", id="reg-b2"),
                self.RegisterItem(reg="Y'", id="reg-y2"),
                self.RegisterItem(reg="Z'", id="reg-z2"),
                self.RegisterItem(reg="F", id="reg-f"),
                self.RegisterItem(reg="PC", id="reg-pc"),
                self.RegisterItem(reg="SP", id="reg-sp"),
                id="register_view",
            ),
            self.LastInst(),
            Button("STEP", id="btn-ctrl-step", variant="primary"),
            Button("RUN", id="btn-ctrl-run", variant="primary"),
            Button("STOP", id="btn-ctrl-stop", variant="primary"),
            id="virtual_machine_controller",
        )

    def update_memory(self, mem) -> None:
        for i in range(0x10):
            for j in range(0x10):
                elem = self.query_one(f"#mem-{i:x}-{j:x}")
                elem.value = mem[i * 0x10 + j]

    def update_register(self, name, value) -> None:
        elem = self.query_one(f"#reg-{name}")
        elem.value = value

    def update_last_inst(self, inst) -> None:
        elem = self.query_one(self.LastInst)
        elem.value = inst


class MonitorPane(Static):
    DEFAULT_CSS = """
    MonitorPane {
        width: 1fr;
        height: 1fr;
    }
    #monitor_pane {
        layout: grid;
        grid-size: 2 1;
        grid-gutter: 1;
        grid-columns: 5fr 3fr;
    }
    """

    def compose(self) -> ComposeResult:
        board = Board()
        controller = VirtualMachineController()
        board.border_title = "BOARD"
        controller.border_title = "CONTROLLER"
        yield Container(board, controller, id="monitor_pane")


class VirtualMachineMonitor(App):
    BINDINGS = [("q", "quit", "Quit")]
    CSS = """
    TabbedContent ContentSwitcher {
        height: 1fr;
    }
    """

    def __init__(self, vm: VirtualMachine):
        super().__init__()
        self.vm = vm

    def step(self):
        self.vm.cycle()
        self.vm.release_all_key()
        self.update()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent("Monitor", "Config"):
            yield MonitorPane()
            yield Label("config")
        yield Footer()

    def on_mount(self) -> None:
        self.update()
        self.runner = self.set_interval(1 / self.vm.HZ, self.step, pause=True)

    def update(self) -> None:
        board = self.query_one(Board)
        board.numeric_value = self.vm.get_numeric_led()
        board.led_value = self.vm.get_binary_led()

        mem = [0] * 0x100
        for i in range(0x100):
            if i % 2 == 0:
                mem[i] = (self.vm.data[i // 2] >> 4) & 0xF
            else:
                mem[i] = self.vm.data[i // 2] & 0xF

        reg_a = self.vm.get_reg(Register.A)
        reg_b = self.vm.get_reg(Register.B)
        reg_y = self.vm.get_reg(Register.Y)
        reg_z = self.vm.get_reg(Register.Z)
        reg_a2 = self.vm.get_reg(Register.A2)
        reg_b2 = self.vm.get_reg(Register.B2)
        reg_y2 = self.vm.get_reg(Register.Y2)
        reg_z2 = self.vm.get_reg(Register.Z2)
        reg_f = self.vm.get_reg(Register.F)
        reg_pc = self.vm.get_reg(Register.PC)
        reg_sp = self.vm.get_reg(Register.SP)

        vmc = self.query_one(VirtualMachineController)
        vmc.update_memory(mem)
        vmc.update_register("a", reg_a)
        vmc.update_register("b", reg_b)
        vmc.update_register("y", reg_y)
        vmc.update_register("z", reg_z)
        vmc.update_register("a2", reg_a2)
        vmc.update_register("b2", reg_b2)
        vmc.update_register("y2", reg_y2)
        vmc.update_register("z2", reg_z2)
        vmc.update_register("f", reg_f)
        vmc.update_register("pc", reg_pc)
        vmc.update_register("sp", reg_sp)
        vmc.update_last_inst(self.vm.last_inst)

    def action_quit(self) -> None:
        self.exit()

    def on_button_pressed(self, event: Button.Pressed):
        if re.match(r"^btn-[0-9a-f]$", event.button.id):
            val = int(event.button.id[4:], 16)
            self.vm.prese_key(val)
        elif re.match(r"^btn-ctrl-", event.button.id):
            cmd = event.button.id[9:]
            match cmd:
                case "step":
                    self.step()
                case "run":
                    self.runner.resume()
                case "stop":
                    self.runner.pause()
        else:
            cmd = event.button.id[4:]
            match cmd:
                case "adr":
                    pass
                case "inc":
                    pass
                case "run":
                    pass
                case "rst":
                    pass