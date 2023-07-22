from enum import IntEnum


class MemoryLayout(IntEnum):
    PROGRAM_BEGIN = 0x00
    PROGRAM_END = 0x4F
    DATA_BEGIN = 0x50
    DATA_END = 0x5F
    SYSTEM_BEGIN = 0x60
    SYSTEM_END = 0x7F
    STACK_BEGIN = 0x80
    STACK_END = 0xFF


class SystemLayout(IntEnum):
    KEY_STATE_BEGIN = 0x60
    KEY_STATE_END = 0x64
    REGISTER_BEGIN = 0x64
    REGISTER_END = 0x70
    NUMERIC_LED = 0x71
    BINARY_LED = 0x72  # - 0x73 (without MSB)
    WAIT_COUNT = 0x74


class Register(IntEnum):
    SP = 0x64  # - 0x65
    Z2 = 0x66
    B2 = 0x67
    Y2 = 0x68
    A2 = 0x69
    PC = 0x6A  # - 0x6B
    B = 0x6C
    Z = 0x6D
    Y = 0x6E
    A = 0x6F
    F = 0x70


class Opcode(IntEnum):
    # gmc-4 compatible instruction

    INK = 0x0
    OUTN = 0x1
    ABYZ = 0x2
    AY = 0x3
    ST = 0x4
    LD = 0x5
    ADD = 0x6
    SUB = 0x7
    LDI = 0x8
    ADDI = 0x9
    LDYI = 0xA
    ADDYI = 0xB
    CPI = 0xC
    CPYI = 0xD
    SCALL = 0xE
    JMPF = 0xF

    # orange-4 extension instruction

    CALL = 0xF60
    RET = 0xF61
    PUSHA = 0xF62
    POPA = 0xF63
    PUSHB = 0xF64
    POPB = 0xF65
    PUSHY = 0xF66
    POPY = 0xF67
    PUSHZ = 0xF68
    POPZ = 0xF69
    IOCTRL = 0xF70
    OUT = 0xF71
    IN = 0xF72


class ServiceCall(IntEnum):
    TURN_OFF_NUMERIC_LED = 0x0
    TURN_ON_REGISTER = 0x1
    TURN_OFF_REGISTER = 0x2
    INVERT_ALL_BITS = 0x4
    SWAP_AUX_REGISTERS = 0x5
    RIGHT_SHIFT = 0x6
    BEEP_END_SE = 0x7
    BEEP_ERROR_SE = 0x8
    BEEP_LONG_SE = 0x9
    BEEP_SHORT_SE = 0xA
    BEEP_SOUND_SCALE = 0xB
    WAIT = 0xC
    TURN_ON_MEMORY = 0xD
    DECIMAL_SUB = 0xE
    DECIMAL_ADD = 0xF


class VirtualMachine:
    HZ = 1000

    def __init__(self, data: list[int]):
        assert len(data) == 0x80
        self.data = data
        self.last_inst = ""
        self.set_reg(Register.SP, 0xFF)

    def prese_key(self, key: int) -> None:
        assert 0x0 <= key <= 0xF
        if key <= 0x3:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 0,
                self.get_mem(SystemLayout.KEY_STATE_BEGIN + 0) | (1 << (key - 0x0)),
            )
        elif key <= 0x7:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 1,
                self.get_mem(SystemLayout.KEY_STATE_BEGIN + 1) | (1 << (key - 0x4)),
            )
        elif key <= 0xB:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 2,
                self.get_mem(SystemLayout.KEY_STATE_BEGIN + 2) | (1 << (key - 0x8)),
            )
        else:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 3,
                self.get_mem(SystemLayout.KEY_STATE_BEGIN + 3) | (1 << (key - 0xC)),
            )

    def release_key(self, key: int) -> None:
        assert 0x0 <= key <= 0xF
        if key <= 0x3:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 0,
                (self.get_mem(SystemLayout.KEY_STATE_BEGIN + 0) & ~(1 << (key - 0x0)))
                & 0xF,
            )
        elif key <= 0x7:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 1,
                (self.get_mem(SystemLayout.KEY_STATE_BEGIN + 1) & ~(1 << (key - 0x4)))
                & 0xF,
            )
        elif key <= 0xB:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 2,
                (self.get_mem(SystemLayout.KEY_STATE_BEGIN + 2) & ~(1 << (key - 0x8)))
                & 0xF,
            )
        else:
            self.set_mem(
                SystemLayout.KEY_STATE_BEGIN + 3,
                (self.get_mem(SystemLayout.KEY_STATE_BEGIN + 3) & ~(1 << (key - 0xC)))
                & 0xF,
            )

    def release_all_key(self) -> None:
        for i in range(4):
            self.set_mem(SystemLayout.KEY_STATE_BEGIN + i, 0)

    def get_key_state(self, key: int) -> bool:
        assert 0x0 <= key <= 0xF
        if key <= 0x3:
            val = self.get_mem(SystemLayout.KEY_STATE_BEGIN + 0) & (1 << (key - 0x0))
        elif key <= 0x7:
            val = self.get_mem(SystemLayout.KEY_STATE_BEGIN + 1) & (1 << (key - 0x4))
        elif key <= 0xB:
            val = self.get_mem(SystemLayout.KEY_STATE_BEGIN + 2) & (1 << (key - 0x8))
        else:
            val = self.get_mem(SystemLayout.KEY_STATE_BEGIN + 3) & (1 << (key - 0xC))
        return val != 0

    def get_numeric_led(self) -> int:
        return self.get_mem(SystemLayout.NUMERIC_LED)

    def set_numeric_led(self, value: int) -> None:
        assert 0x0 <= value <= 0xF
        self.set_mem(SystemLayout.NUMERIC_LED, value)

    def get_binary_led(self) -> int:
        return self.get_mem(SystemLayout.BINARY_LED) | (
            self.get_mem(SystemLayout.BINARY_LED + 1) << 4
        )

    def set_binary_led(self, value: int) -> None:
        assert 0x0 <= value <= 0x7F
        self.set_mem(SystemLayout.BINARY_LED, value & 0xF)
        self.set_mem(SystemLayout.BINARY_LED + 1, value >> 4)

    def cycle(self) -> None:
        if self.get_mem(SystemLayout.WAIT_COUNT) > 0:
            self.set_mem(
                SystemLayout.WAIT_COUNT, self.get_mem(SystemLayout.WAIT_COUNT) - 1
            )
            return
        opcode = self.get_mem(self.get_reg(Register.PC))
        self._exec_op(opcode)
        self._inc_reg(Register.PC)

    def get_reg(self, register: Register) -> int:
        assert SystemLayout.REGISTER_BEGIN <= register <= SystemLayout.REGISTER_END
        match register:
            case Register.PC:
                return (self.get_mem(Register.PC) << 4) | self.get_mem(Register.PC + 1)
            case Register.SP:
                return (self.get_mem(Register.SP) << 4) | self.get_mem(Register.SP + 1)
            case Register.F:
                return (self.get_mem(Register.F) >> 3) & 0x1
            case _:
                return self.get_mem(register)

    def set_reg(self, register: Register, value: int) -> None:
        assert SystemLayout.REGISTER_BEGIN <= register <= SystemLayout.REGISTER_END
        match register:
            case Register.PC:
                if value < 0:
                    value += 0xFF
                assert value <= 0xFF
                self.set_mem(Register.PC, value >> 4)
                self.set_mem(Register.PC + 1, value & 0xF)
            case Register.SP:
                if value < 0:
                    value += 0xFF
                assert value <= 0xFF
                self.set_mem(Register.SP, value >> 4)
                self.set_mem(Register.SP + 1, value & 0xF)
            case Register.F:
                assert 0x0 <= value <= 0x1
                self.set_mem(Register.F, value << 3)
            case _:
                if value < 0:
                    value += 0xF
                assert value <= 0xF
                self.set_mem(register, value)

    def get_mem(self, addr: int) -> int:
        assert 0x00 <= addr <= 0xFF
        if addr % 2 == 0:
            return (self.data[addr // 2] >> 4) & 0xF
        else:
            return self.data[addr // 2] & 0xF

    def set_mem(self, addr: int, value: int) -> None:
        assert 0x00 <= addr <= 0xFF
        assert 0x0 <= value <= 0xF
        if addr % 2 == 0:
            self.data[addr // 2] &= 0x0F
            self.data[addr // 2] |= value << 4
        else:
            self.data[addr // 2] &= 0xF0
            self.data[addr // 2] |= value

    def _inc_reg(self, register: Register) -> None:
        self.set_reg(register, (self.get_reg(register) + 1) & 0xFF)

    def _dec_reg(self, register: Register) -> None:
        val = self.get_reg(register) - 1
        if val == -1:
            val = 0xFF
        self.set_reg(register, val)

    def _swap_reg(self, r1: Register, r2: Register) -> None:
        tmp = self.get_reg(r1)
        self.set_reg(r1, self.get_reg(r2))
        self.set_reg(r1, tmp)

    def _push_reg(self, register: Register) -> None:
        self._dec_reg(Register.SP)
        self.set_mem(self.get_reg(Register.SP) + 1, self.get_reg(register))

    def _pop_reg(self, register: Register) -> None:
        self.set_reg(register, self.get_mem(self.get_reg(Register.SP) + 1))
        self._inc_reg(Register.SP)

    def _exec_op(self, opcode: Opcode) -> None:
        assert Opcode.INK <= opcode <= Opcode.JMPF
        match opcode:
            case Opcode.INK:
                self._op_ink()
            case Opcode.OUTN:
                self._op_outn()
            case Opcode.ABYZ:
                self._op_abyz()
            case Opcode.AY:
                self._op_ay()
            case Opcode.ST:
                self._op_st()
            case Opcode.LD:
                self._op_ld()
            case Opcode.ADD:
                self._op_add()
            case Opcode.SUB:
                self._op_sub()
            case Opcode.LDI:
                self._op_ldi()
            case Opcode.ADDI:
                self._op_addi()
            case Opcode.LDYI:
                self._op_ldyi()
            case Opcode.ADDYI:
                self._op_addyi()
            case Opcode.CPI:
                self._op_cpi()
            case Opcode.CPYI:
                self._op_cpyi()
            case Opcode.SCALL:
                self._op_scall()
            case Opcode.JMPF:
                self._op_jmpf()

    def _exec_ex_op(self, opcode: Opcode) -> None:
        assert Opcode.CALL <= opcode <= Opcode.IN
        match opcode:
            case Opcode.CALL:
                self._ex_op_call()
            case Opcode.RET:
                self._ex_op_ret()
            case Opcode.PUSHA:
                self._ex_op_pusha()
            case Opcode.POPA:
                self._ex_op_popa()
            case Opcode.PUSHB:
                self._ex_op_pushb()
            case Opcode.PUSHY:
                self._ex_op_pushy()
            case Opcode.POPY:
                self._ex_op_popy()
            case Opcode.PUSHZ:
                self._ex_op_pushz()
            case Opcode.POPZ:
                self._ex_op_popz()
            case Opcode.IOCTRL:
                self._ex_op_ioctrl()
            case Opcode.OUT:
                self._ex_op_out()
            case Opcode.IN:
                self._ex_op_in()

    def _op_ink(self) -> None:
        self.last_inst = "ink"
        for key in range(0x10):
            if self.get_key_state(key):
                self.set_reg(Register.A, key)
                self.set_reg(Register.F, 0)
                return
        self.set_reg(Register.F, 1)

    def _op_outn(self) -> None:
        self.last_inst = "outn"
        self.set_numeric_led(self.get_reg(Register.A))
        self.set_reg(Register.F, 1)
        self.set_reg(Register.F, 1)

    def _op_abyz(self) -> None:
        self.last_inst = "abyz"
        self._swap_reg(Register.A, Register.B)
        self._swap_reg(Register.Y, Register.Z)
        self.set_reg(Register.F, 1)

    def _op_ay(self) -> None:
        self.last_inst = "ay"
        self._swap_reg(Register.A, Register.Y)
        self.set_reg(Register.F, 1)

    def _op_st(self) -> None:
        self.last_inst = "st"
        self.set_mem(self.get_reg(Register.Y) + 50, self.get_reg(Register.A))
        self.set_reg(Register.F, 1)

    def _op_ld(self) -> None:
        self.last_inst = "ld"
        self.set_reg(Register.A, self.get_mem(self.get_reg(Register.Y) + 50))
        self.set_reg(Register.F, 1)

    def _op_add(self) -> None:
        self.last_inst = "add"
        val = self.get_mem(self.get_reg(Register.Y) + 50) + self.get_reg(Register.A)
        self.set_reg(Register.A, val & 0xF)
        self.set_reg(Register.F, val >> 4)

    def _op_sub(self) -> None:
        self.last_inst = "sub"
        val = self.get_mem(self.get_reg(Register.Y) + 50) - self.get_reg(Register.A)
        if val < 0:
            val += 0x10
            self.set_reg(Register.F, 1)
        else:
            self.set_reg(Register.F, 0)
        self.set_reg(Register.A, val & 0xF)

    def _op_ldi(self) -> None:
        self._inc_reg(Register.PC)
        val = self.get_mem(self.get_reg(Register.PC))
        self.set_reg(Register.A, val)
        self.set_reg(Register.F, 1)
        self.last_inst = f"ldi 0x{val:x}"

    def _op_addi(self) -> None:
        self._inc_reg(Register.PC)
        add = self.get_mem(self.get_reg(Register.PC))
        val = self.get_reg(Register.A) + add
        self.set_reg(Register.A, val & 0xF)
        self.set_reg(Register.F, val >> 4)
        self.last_inst = f"addi 0x{add:x}"

    def _op_ldyi(self) -> None:
        self._inc_reg(Register.PC)
        val = self.get_mem(self.get_reg(Register.PC))
        self.set_reg(Register.Y, val)
        self.set_reg(Register.F, 1)
        self.last_inst = f"ldyi 0x{val:x}"

    def _op_addyi(self) -> None:
        self._inc_reg(Register.PC)
        add = self.get_mem(self.get_reg(Register.PC))
        val = self.get_reg(Register.Y) + add
        self.set_reg(Register.Y, val & 0xF)
        self.set_reg(Register.F, val >> 4)
        self.last_inst = f"addyi 0x{add:x}"

    def _op_cpi(self) -> None:
        self._inc_reg(Register.PC)
        val = self.get_mem(self.get_reg(Register.PC))
        if self.get_reg(Register.A) == val:
            self.set_reg(Register.F, 0)
        else:
            self.set_reg(Register.F, 1)
        self.last_inst = f"cpi 0x{val:x}"

    def _op_cpyi(self) -> None:
        self._inc_reg(Register.PC)
        val = self.get_mem(self.get_reg(Register.PC))
        if self.get_reg(Register.Y) == val:
            self.set_reg(Register.F, 0)
        else:
            self.set_reg(Register.F, 1)
        self.last_inst = f"cpyi 0x{val:x}"

    def _op_scall(self) -> None:
        self._inc_reg(Register.PC)
        val = self.get_mem(self.get_reg(Register.PC))
        self._scall(val)
        self.last_inst = f"scall 0x{val:x}"

    def _op_jmpf(self) -> None:
        self._inc_reg(Register.PC)
        addr_high = self.get_mem(self.get_reg(Register.PC))
        self._inc_reg(Register.PC)
        addr_low = self.get_mem(self.get_reg(Register.PC))
        addr = (addr_high << 4) | addr_low
        if addr < MemoryLayout.SYSTEM_BEGIN or addr >= MemoryLayout.STACK_BEGIN:
            if self.get_reg(Register.F) == 0:
                self.set_reg(Register.F, 1)
            else:
                self.set_reg(Register.PC, addr - 1)
            self.last_inst = f"jmpf 0x{addr:x}"
        else:
            self._exec_ex_op(0xF00 | addr)

    def _ex_op_call(self) -> None:
        self._inc_reg(Register.PC)
        addr_high = self.get_mem(self.get_reg(Register.PC))
        self._inc_reg(Register.PC)
        addr_low = self.get_mem(self.get_reg(Register.PC))
        addr = (addr_high << 4) | addr_low
        ret_addr = self.get_reg(Register.PC)
        self._dec_reg(Register.SP)
        self._dec_reg(Register.SP)
        self.set_mem(self.get_reg(Register.SP) + 1, ret_addr >> 4)
        self.set_mem(self.get_reg(Register.SP) + 2, ret_addr & 0xF)
        self.set_reg(Register.PC, addr - 1)
        self.set_reg(Register.F, 1)
        self.last_inst = f"call 0x{addr:x}"

    def _ex_op_ret(self) -> None:
        ret_addr = (self.get_mem(self.get_reg(Register.SP) + 1) << 4) | self.get_mem(
            self.get_reg(Register.SP) + 2
        )
        self._inc_reg(Register.SP)
        self._inc_reg(Register.SP)
        self.set_reg(Register.PC, ret_addr)
        self.set_reg(Register.F, 1)
        self.last_inst = "ret"

    def _ex_op_pusha(self) -> None:
        self._push_reg(Register.A)
        self.set_reg(Register.F, 1)
        self.last_inst = "pusha"

    def _ex_op_popa(self) -> None:
        self._pop_reg(Register.A)
        self.set_reg(Register.F, 1)
        self.last_inst = "popa"

    def _ex_op_pushb(self) -> None:
        self._push_reg(Register.B)
        self.set_reg(Register.F, 1)
        self.last_inst = "pushb"

    def _ex_op_popb(self) -> None:
        self._pop_reg(Register.B)
        self.set_reg(Register.F, 1)
        self.last_inst = "popb"

    def _ex_op_pushy(self) -> None:
        self._push_reg(Register.Y)
        self.set_reg(Register.F, 1)
        self.last_inst = "pushy"

    def _ex_op_popy(self) -> None:
        self._pop_reg(Register.Y)
        self.set_reg(Register.F, 1)
        self.last_inst = "popy"

    def _ex_op_pushz(self) -> None:
        self._push_reg(Register.Z)
        self.set_reg(Register.F, 1)
        self.last_inst = "pushz"

    def _ex_op_popz(self) -> None:
        self._pop_reg(Register.Z)
        self.set_reg(Register.F, 1)
        self.last_inst = "popz"

    def _ex_op_ioctrl(self) -> None:
        print("Unimpl: ioctrl")
        self.set_reg(Register.F, 1)
        self.last_inst = "ioctrl"

    def _ex_op_out(self) -> None:
        print("Unimpl: out")
        self.set_reg(Register.F, 1)
        self.last_inst = "out"

    def _ex_op_in(self) -> None:
        print("Unimple: in")
        self.set_reg(Register.F, 1)
        self.last_inst = "in"

    def _scall(self, srv: ServiceCall) -> None:
        match srv:
            case ServiceCall.TURN_OFF_NUMERIC_LED:
                print("Unimpl srv: 0")
                self.set_reg(Register.F, 1)
            case ServiceCall.TURN_ON_REGISTER:
                val = self.get_reg(Register.Y)
                self.set_binary_led((self.get_binary_led() | (1 << val)) & 0x7F)
                self.set_reg(Register.F, 1)
            case ServiceCall.TURN_OFF_REGISTER:
                val = self.get_reg(Register.Y)
                self.set_binary_led((self.get_binary_led() & ~(1 << val)) & 0x7F)
                self.set_reg(Register.F, 1)
            case ServiceCall.INVERT_ALL_BITS:
                self.set_reg(Register.A, (~self.get_reg(Register.A)) & 0xF)
                self.set_reg(Register.F, 1)
            case ServiceCall.SWAP_AUX_REGISTERS:
                self._swap_reg(Register.A, Register.A2)
                self._swap_reg(Register.B, Register.B2)
                self._swap_reg(Register.Y, Register.Y2)
                self._swap_reg(Register.Z, Register.Z2)
                self.set_reg(Register.F, 1)
            case ServiceCall.RIGHT_SHIFT:
                val = self.get_reg(Register.A)
                self.set_reg(Register.A, val >> 1)
                self.set_reg(Register.F, val & 1)
            case ServiceCall.BEEP_END_SE:
                print("BEEP: END")
                self.set_reg(Register.F, 1)
            case ServiceCall.BEEP_ERROR_SE:
                print("BEEP: ERROR")
                self.set_reg(Register.F, 1)
            case ServiceCall.BEEP_SHORT_SE:
                print("BEEP: SHORT")
                self.set_reg(Register.F, 1)
            case ServiceCall.BEEP_LONG_SE:
                print("BEEP: LONG")
                self.set_reg(Register.F, 1)
            case ServiceCall.BEEP_SOUND_SCALE:
                val = self.get_reg(Register.A)
                print(f"BEEP: {val:X}")
                self.set_reg(Register.F, 1)
            case ServiceCall.WAIT:
                val = self.get_reg(Register.A) + 1
                # wait = val * self.HZ / 10
                # self.set_mem(SystemLayout.WAIT_COUNT, wait)
                self.set_reg(Register.F, 1)
            case ServiceCall.TURN_ON_MEMORY:
                val = self.get_mem(0x5E) | ((self.get_mem(0x5F) & 0x7) << 4)
                self.set_binary_led((self.get_binary_led() | (1 << val)) & 0x7F)
                self.set_reg(Register.F, 1)
            case ServiceCall.DECIMAL_SUB:
                print("Unimpl srv: E")
                self.set_reg(Register.F, 1)
            case ServiceCall.DECIMAL_ADD:
                print("Umimpl srv F")
                self.set_reg(Register.F, 1)
