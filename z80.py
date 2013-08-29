#coding: utf-8

FLAGS = {
        "C":0x10, #Carry
        "H":0x20, #Halfcarry
        "N":0x40, #Substraction
        "Z":0x80, #Zero
}

class Z80(object):
    m, t = 0,0 #Two clocks
    registers = {
                'A':0, #A, B, C, D E, H, L and F are all 8bit registers
                'B':0, #Some can be paired together to form 16bit registers : BC, DE, HL
                'C':0,
                'D':0,
                'E':0,
                'H':0,
                'L':0,
                'F':0, #Flag with data about the last operation's results
                'SP':0, #Stack pointer
                'PC':0 #Program counter, SP and PC are both 16bit registers
    }

    def __init__(self, memory):
        self.memory = memory

    @property
    def PC(self):
        return self.registers['PC']

    def incPC(self, val=1):
        self.registers['PC'] += val

    @property
    def HL(self):
        return (self.registers['H'] << 8) | self.registers['L']

    def update_clocks(self, t, m):
        self.t += t
        self.m += m

    def next_instruction(self): #Executes the following instruction
        opcode = self.memory.read_byte(self.PC)
        self.incPC()
        if opcode == 0xCB:
            opcode = self.memory.read_byte(self.PC)
            print "Executing CB opcode {0}".format(hex(opcode))
            self.incPC()
            self.CB_OPCODES[opcode](self)
        else:
            print "Executing opcode {0}".format(hex(opcode))
            self.OPCODES[opcode](self)

    def reset_flags(self):
        self.registers['F'] = 0

    def set_flag(self, flag, value):
        if value:
            self.registers['F'] |= FLAGS[flag]
        elif self.registers['F'] & FLAGS[flag]:
            self.registers['F'] ^= FLAGS[flag]

    def get_flag(self, flag):
        return self.reg['F'] & FLAGS[flag]

    """ INSTRUCTIONS """

    #INCREMENTATION AND DECREMENTATION INSTRUCTIONS
    def INC(self, r):
        self.registers[r] += 1
        self.registers[r] &= 255

        self.set_flag('H', self.registers[r] & 0x0F == 0) #Set flag if lower nibble is now null
        self.set_flag('Z', self.registers[r] == 0) #Zero flag
        self.set_flag('N', 0)
        self.update_clocks(1, 4)

    def DEC(self, r):
        self.registers[r] -= 1
        self.registers[r] &= 255

        self.set_flag('H', self.registers[r] & 0x0F == 0x0F) #Set flag if lower nibble is full TODO check
        self.set_flag('Z', self.registers[r] == 0) #Zero flag
        self.set_flag('N', 1)
        self.update_clocks(1, 4)

    def INC_addr(self, addr):
        value = self.memory.read_byte(addr)
        value += 1
        value &= 255
        self.memory.write_byte(addr, value)

        self.set_flag('H', value & 0x0F == 0) #Set flag if lower nibble is now null
        self.set_flag('Z', value == 0) #Zero flag
        self.update_clocks(1, 12)

    def DEC_addr(self, addr):
        value = self.memory.read_byte(addr)
        value -= 1
        value &= 255
        self.memory.write_byte(addr, value)

        self.set_flag('H', value & 0x0F == 0x0F) #Set flag if lower nibble is now full
        self.set_flag('Z', value == 0) #Zero flag
        self.set_flag('N', 1)
        self.update_clocks(1, 12)

    def INC16(self, r):
        value = (self.registers[r[0]] << 8) | self.reg[r[0]]
        value += 1
        value &= 0xFFFF

        self.reg[r[0]] = value >> 8  #upper nibble
        self.reg[r[1]] = value & 255 #lower nibble

        self.update_clocks(1, 8)

    def DEC16(self, r):
        value = (self.registers[r[0]] << 8) | self.reg[r[0]]
        value -= 1
        value &= 0xFFFF

        self.reg[r[0]] = value >> 8  #upper nibble
        self.reg[r[1]] = value & 255 #lower nibble

        self.update_clocks(1, 8)

    #LD (load) INSTRUCTIONS

    def LD(self, r1, r2):
        self.registers[r1] = self.registers[r2]
        self.update_clocks(1,4)

    def LD_to_addr(self, dst, src):
        dst_strong, dst_weak = dst[0], dst[1]
        addr = (dst_strong << 8) | dst_weak
        self.memory.write_byte(addr, self.registers[src])
        self.update_clocks(1, 8)

    def LD_from_addr(self, dst, src):
        src_strong, src_weak = src[0], src[1]
        addr = (src_strong << 8) | src_weak
        self.registers[dst] = self.memory.read_byte(addr)
        self.update_clocks(1, 8)

    def LD16_nn(self, r):
        r_strong, r_weak = r[0],r[1]
        self.registers[r_strong] = self.memory.read_byte(self.PC+1)
        self.registers[r_weak] = self.memory.read_byte(self.PC)
        self.incPC(2)
        self.update_clocks(3, 12)

    def LD_to_RAM(self):
        addr = 0xFF00+self.memory.read_byte(self.PC)
        self.memory.write_byte(addr, self.registers['A'])
        self.incPC()
        self.update_clocks(2,12)

    def LD_SP_nn(self):
        self.registers['SP'] = self.memory.read_word(self.PC)
        self.incPC(2)
        self.update_clocks(3, 12)

    #XOR INSTRUCTIONS

    def XOR(self, r):
        self.registers['A'] ^= self.registers[r]
        self.reset_flags()
        self.set_flag('Z', bool(self.registers['A']))
        self.update_clocks(1, 4)

    def XOR_HL(self):
        self.registers['A'] ^= self.memory.read_byte(self.HL)
        self.reset_flags()
        self.set_flag('Z', bool(self.registers['A']))
        self.update_clocks(1, 8)

    def XOR_n(self):
        self.registers['A'] ^= self.memory.read_byte(self.PC)
        self.reset_flags()
        self.set_flag('Z', bool(self.registers['A']))
        self.update_clocks(2, 8)

    """ OPCODES LIST """

    OP_00 = lambda self: self.NOP()
    OP_01 = lambda self: self.LD16_nn('BC')
    OP_02 = lambda self: self.LD_to_addr('BC','A')
    OP_03 = lambda self: self.INC16('BC')
    OP_04 = lambda self: self.INC('B')
    OP_05 = lambda self: self.DEC('B')
    OP_06 = lambda self: self.LD('B','ROM')
    OP_07 = lambda self: self.RLC('A')
    OP_08 = lambda self: self.LD('SP','ROM')
    OP_09 = lambda self: self.ADD16('BC','HL')
    OP_0A = lambda self: self.LD('A','BC')
    OP_0B = lambda self: self.DEC16('BC')
    OP_0C = lambda self: self.INC('C')
    OP_0D = lambda self: self.DEC('C')
    OP_0E = lambda self: self.LD('C','ROM')
    OP_0F = lambda self: self.RRC('A')

    OP_10 = lambda self: setattr(self, 'stop', True)
    OP_11 = lambda self: self.LD16_nn('DE')
    OP_12 = lambda self: self.LD_to_addr('DE','A')
    OP_13 = lambda self: self.INC16('DE')
    OP_14 = lambda self: self.INC('D')
    OP_15 = lambda self: self.DEC('D')
    OP_16 = lambda self: self.LD('D','ROM')
    OP_17 = lambda self: self.RL('A')
    OP_18 = lambda self: self.JR()
    OP_19 = lambda self: self.ADD16('HL','DE')
    OP_1A = lambda self: self.LD('A','DE')
    OP_1B = lambda self: self.DEC16('DE')
    OP_1C = lambda self: self.INC('E')
    OP_1D = lambda self: self.DEC('E')
    OP_1E = lambda self: self.LD('E','ROM')
    OP_1F = lambda self: self.RR('A')

    OP_20 = lambda self: self.JR('NZ')
    OP_21 = lambda self: self.LD16_nn('HL')
    OP_22 = lambda self: self.LDI('HL','A')
    OP_23 = lambda self: self.INC16('HL')
    OP_24 = lambda self: self.INC('H')
    OP_25 = lambda self: self.DEC('H')
    OP_26 = lambda self: self.LD('H','ROM')
    OP_27 = lambda self: self.DAA()
    OP_28 = lambda self: self.JR('Z')
    OP_29 = lambda self: self.ADD16('HL','HL')
    OP_2A = lambda self: self.LDI('A','HL')
    OP_2B = lambda self: self.DEC16('HL')
    OP_2C = lambda self: self.INC('L')
    OP_2D = lambda self: self.DEC('L')
    OP_2E = lambda self: self.LD('L','ROM')
    OP_2F = lambda self: self.CPL()

    OP_30 = lambda self: self.JR('NC')
    OP_31 = lambda self: self.LD_SP_nn()
    OP_32 = lambda self: self.LDD('HL','A')
    OP_33 = lambda self: (self.reg.__setitem__('SP', self.reg['SP']+1&65535)) #INC SP #TODO FLAGS
    OP_34 = lambda self: self.INC_addr(self.HL)
    OP_35 = lambda self: self.DEC_addr(self.HL)
    OP_36 = lambda self: self.LD_HL_n()
    OP_37 = lambda self: (self.set_flag('C',True), self.OP_00())
    OP_38 = lambda self: self.JR('C')
    OP_39 = lambda self: self.ADD16('HL','SP')
    OP_3A = lambda self: self.LDD('A','HL')
    OP_3B = lambda self: (self.reg.__setitem__('SP', self.reg['SP']-1&65535)) #DEC SP #TODO FLAGS
    OP_3C = lambda self: self.INC('A')
    OP_3D = lambda self: self.DEC('A')
    OP_3E = lambda self: self.LD('A','ROM')
    OP_3F = lambda self: (self.set_flag('C',False), self.OP_00())

    OP_40 = lambda self: self.LD('B','B')
    OP_41 = lambda self: self.LD('B','C')
    OP_42 = lambda self: self.LD('B','D')
    OP_43 = lambda self: self.LD('B','E')
    OP_44 = lambda self: self.LD('B','H')
    OP_45 = lambda self: self.LD('B','L')
    OP_46 = lambda self: self.LD_from_addr('B','HL')
    OP_47 = lambda self: self.LD('B','A')
    OP_48 = lambda self: self.LD('C','B')
    OP_49 = lambda self: self.LD('C','C')
    OP_4A = lambda self: self.LD('C','D')
    OP_4B = lambda self: self.LD('C','E')
    OP_4C = lambda self: self.LD('C','H')
    OP_4D = lambda self: self.LD('C','L')
    OP_4E = lambda self: self.LD_from_addr('C','HL')
    OP_4F = lambda self: self.LD('C','A')

    OP_50 = lambda self: self.LD('D','B')
    OP_51 = lambda self: self.LD('D','C')
    OP_52 = lambda self: self.LD('D','D')
    OP_53 = lambda self: self.LD('D','E')
    OP_54 = lambda self: self.LD('D','H')
    OP_55 = lambda self: self.LD('D','L')
    OP_56 = lambda self: self.LD_from_addr('D','HL')
    OP_57 = lambda self: self.LD('D','A')
    OP_58 = lambda self: self.LD('E','B')
    OP_59 = lambda self: self.LD('E','C')
    OP_5A = lambda self: self.LD('E','D')
    OP_5B = lambda self: self.LD('E','E')
    OP_5C = lambda self: self.LD('E','H')
    OP_5D = lambda self: self.LD('E','L')
    OP_5E = lambda self: self.LD_from_addr('E','HL')
    OP_5F = lambda self: self.LD('E','A')

    OP_60 = lambda self: self.LD('H','B')
    OP_61 = lambda self: self.LD('H','C')
    OP_62 = lambda self: self.LD('H','D')
    OP_63 = lambda self: self.LD('H','E')
    OP_64 = lambda self: self.LD('H','H')
    OP_65 = lambda self: self.LD('H','L')
    OP_66 = lambda self: self.LD_from_addr('H','HL')
    OP_67 = lambda self: self.LD('H','A')
    OP_68 = lambda self: self.LD('L','B')
    OP_69 = lambda self: self.LD('L','C')
    OP_6A = lambda self: self.LD('L','D')
    OP_6B = lambda self: self.LD('L','E')
    OP_6C = lambda self: self.LD('L','H')
    OP_6D = lambda self: self.LD('L','L')
    OP_6E = lambda self: self.LD_from_addr('L','HL')
    OP_6F = lambda self: self.LD('L','A')

    OP_70 = lambda self: self.LD_to_addr('HL','B')
    OP_71 = lambda self: self.LD_to_addr('HL','C')
    OP_72 = lambda self: self.LD_to_addr('HL','D')
    OP_73 = lambda self: self.LD_to_addr('HL','E')
    OP_74 = lambda self: self.LD_to_addr('HL','H')
    OP_75 = lambda self: self.LD_to_addr('HL','L')
    OP_76 = lambda self: setattr(self, 'stop',True) #HALT
    OP_77 = lambda self: self.LD_to_addr('HL','A')
    OP_78 = lambda self: self.LD('A','B')
    OP_79 = lambda self: self.LD('A','C')
    OP_7A = lambda self: self.LD('A','D')
    OP_7B = lambda self: self.LD('A','E')
    OP_7C = lambda self: self.LD('A','H')
    OP_7D = lambda self: self.LD('A','L')
    OP_7E = lambda self: self.LD_from_addr('A','HL')
    OP_7F = lambda self: self.LD('A','A')

    OP_80 = lambda self: self.ADD('B')
    OP_81 = lambda self: self.ADD('C')
    OP_82 = lambda self: self.ADD('D')
    OP_83 = lambda self: self.ADD('E')
    OP_84 = lambda self: self.ADD('H')
    OP_85 = lambda self: self.ADD('L')
    OP_86 = lambda self: self.ADD('HL')
    OP_87 = lambda self: self.ADD('A')
    OP_88 = lambda self: self.ADC('B')
    OP_89 = lambda self: self.ADC('C')
    OP_8A = lambda self: self.ADC('D')
    OP_8B = lambda self: self.ADC('E')
    OP_8C = lambda self: self.ADC('H')
    OP_8D = lambda self: self.ADC('L')
    OP_8E = lambda self: self.ADC('HL')
    OP_8F = lambda self: self.ADC('A')

    OP_90 = lambda self: self.SUB('B')
    OP_91 = lambda self: self.SUB('C')
    OP_92 = lambda self: self.SUB('D')
    OP_93 = lambda self: self.SUB('E')
    OP_94 = lambda self: self.SUB('H')
    OP_95 = lambda self: self.SUB('L')
    OP_96 = lambda self: self.SUB('HL')
    OP_97 = lambda self: self.SUB('A')
    OP_98 = lambda self: self.SBC('B')
    OP_99 = lambda self: self.SBC('C')
    OP_9A = lambda self: self.SBC('D')
    OP_9B = lambda self: self.SBC('E')
    OP_9C = lambda self: self.SBC('H')
    OP_9D = lambda self: self.SBC('L')
    OP_9E = lambda self: self.SBC('HL')
    OP_9F = lambda self: self.SBC('A')

    OP_A0 = lambda self: self.AND('B')
    OP_A1 = lambda self: self.AND('C')
    OP_A2 = lambda self: self.AND('D')
    OP_A3 = lambda self: self.AND('E')
    OP_A4 = lambda self: self.AND('H')
    OP_A5 = lambda self: self.AND('L')
    OP_A6 = lambda self: self.AND('HL')
    OP_A7 = lambda self: self.AND('A')
    OP_A8 = lambda self: self.XOR('B')
    OP_A9 = lambda self: self.XOR('C')
    OP_AA = lambda self: self.XOR('D')
    OP_AB = lambda self: self.XOR('E')
    OP_AC = lambda self: self.XOR('H')
    OP_AD = lambda self: self.XOR('L')
    OP_AE = lambda self: self.XOR_HL()
    OP_AF = lambda self: self.XOR('A')

    OP_B0 = lambda self: self.OR('B')
    OP_B1 = lambda self: self.OR('C')
    OP_B2 = lambda self: self.OR('D')
    OP_B3 = lambda self: self.OR('E')
    OP_B4 = lambda self: self.OR('H')
    OP_B5 = lambda self: self.OR('L')
    OP_B6 = lambda self: self.OR('HL')
    OP_B7 = lambda self: self.OR('A')
    OP_B8 = lambda self: self.CP('B')
    OP_B9 = lambda self: self.CP('C')
    OP_BA = lambda self: self.CP('D')
    OP_BB = lambda self: self.CP('E')
    OP_BC = lambda self: self.CP('H')
    OP_BD = lambda self: self.CP('L')
    OP_BE = lambda self: self.CP('HL')
    OP_BF = lambda self: self.CP('A')

    OP_C0 = lambda self: self.RET('NZ')
    OP_C1 = lambda self: self.POP('BC')
    OP_C2 = lambda self: self.JP('NZ')
    OP_C3 = lambda self: self.JP()
    OP_C4 = lambda self: self.CALL('NZ')
    OP_C5 = lambda self: self.PUSH('BC')
    OP_C6 = lambda self: self.ADD('ROM')
    OP_C7 = lambda self: self.RST(0x0)
    OP_C8 = lambda self: self.RET('Z')
    OP_C9 = lambda self: self.RET()
    OP_CA = lambda self: self.JP('Z')
    #CB operations
    OP_CC = lambda self: self.CALL('Z')
    OP_CD = lambda self: self.CALL()
    OP_CE = lambda self: self.ADC('ROM')
    OP_CF = lambda self: self.RST(0x8)

    OP_D0 = lambda self: self.RET('NC')
    OP_D1 = lambda self: self.POP('DE')
    OP_D2 = lambda self: self.JP('NC')
    #OP_D3 XX
    OP_D4 = lambda self: self.CALL('NC')
    OP_D5 = lambda self: self.PUSH('DE')
    OP_D6 = lambda self: self.SUB('ROM')
    OP_D7 = lambda self: self.RST(0x10)
    OP_D8 = lambda self: self.RET('C')
    OP_D9 = lambda self: self.RETI()
    OP_DA = lambda self: self.JP('C')
    #OP_DB XX
    OP_DC = lambda self: self.CALL('C')
    #OP_DD XX
    OP_DE = lambda self: self.SBC('ROM')
    OP_DF = lambda self: self.RST(0x18)


    OP_E0 = lambda self: self.LD_to_RAM()
    OP_E1 = lambda self: self.POP('HL')
    OP_E2 = lambda self: self.LDH_C()
    #OP_E3 XX
    #OP_E4 XX
    OP_E5 = lambda self: self.PUSH('HL')
    OP_E6 = lambda self: self.AND('ROM')
    OP_E7 = lambda self: self.RST(0x20)
    OP_E8 = lambda self: self.ADD_SP()
    OP_E9 = lambda self: self.JP_HL()
    OP_EA = lambda self: self.LD('nn','A')
    #OP_EB XX
    #OP_EC XX
    #OP_ED XX
    OP_EE = lambda self: self.XOR_n()
    OP_EF = lambda self: self.RST(0x28)

    OP_F0 = lambda self: self.LD('A','ROM', 0xFF00)
    OP_F1 = lambda self: self.POP('AF')
    #OP_F2 XX
    OP_F3 = lambda self: self.DI()
    #OP_F4 XX
    OP_F5 = lambda self: self.PUSH('AF')
    OP_F6 = lambda self: self.OR('ROM')
    OP_F7 = lambda self: self.RST(0x30)
    OP_F8 = lambda self: self.ADD_SP(save=True)
    OP_F9 = lambda self: self.LD_SP()
    OP_FA = lambda self: self.LD('A','nn')
    OP_FB = lambda self: self.EI()
    #OP_FC XX
    #OP_FD XX
    OP_FE = lambda self: self.CP('ROM')
    OP_FF = lambda self: (self.reset(), self.reg.__setitem__('PC', 0x38+1))

    CB_00 = lambda self: self.RLC('B')
    CB_01 = lambda self: self.RLC('C')
    CB_02 = lambda self: self.RLC('D')
    CB_03 = lambda self: self.RLC('E')
    CB_04 = lambda self: self.RLC('H')
    CB_05 = lambda self: self.RLC('L')
    CB_06 = lambda self: self.RLC('HL')
    CB_07 = lambda self: self.RRC('A')
    CB_08 = lambda self: self.RRC('B')
    CB_09 = lambda self: self.RRC('C')
    CB_0A = lambda self: self.RRC('D')
    CB_0B = lambda self: self.RRC('E')
    CB_0C = lambda self: self.RRC('H')
    CB_0D = lambda self: self.RRC('L')
    CB_0E = lambda self: self.RRC('HL')
    CB_0F = lambda self: self.RRC('A')

    CB_10 = lambda self: self.RL('B')
    CB_11 = lambda self: self.RL('C')
    CB_12 = lambda self: self.RL('D')
    CB_13 = lambda self: self.RL('E')
    CB_14 = lambda self: self.RL('H')
    CB_15 = lambda self: self.RL('L')
    CB_16 = lambda self: self.RL('HL')
    CB_17 = lambda self: self.RR('A')
    CB_18 = lambda self: self.RR('B')
    CB_19 = lambda self: self.RR('C')
    CB_1A = lambda self: self.RR('D')
    CB_1B = lambda self: self.RR('E')
    CB_1C = lambda self: self.RR('H')
    CB_1D = lambda self: self.RR('L')
    CB_1E = lambda self: self.RR('HL')
    CB_1F = lambda self: self.RR('A')

    CB_20 = lambda self: self.SLA('B')
    CB_21 = lambda self: self.SLA('C')
    CB_22 = lambda self: self.SLA('D')
    CB_23 = lambda self: self.SLA('E')
    CB_24 = lambda self: self.SLA('H')
    CB_25 = lambda self: self.SLA('L')
    CB_26 = lambda self: self.SLA('HL')
    CB_27 = lambda self: self.SRA('A')
    CB_28 = lambda self: self.SRA('B')
    CB_29 = lambda self: self.SRA('C')
    CB_2A = lambda self: self.SRA('D')
    CB_2B = lambda self: self.SRA('E')
    CB_2C = lambda self: self.SRA('H')
    CB_2D = lambda self: self.SRA('L')
    CB_2E = lambda self: self.SRA('HL')
    CB_2F = lambda self: self.SRA('A')

    CB_30 = lambda self: self.SWAP('B')
    CB_31 = lambda self: self.SWAP('C')
    CB_32 = lambda self: self.SWAP('D')
    CB_33 = lambda self: self.SWAP('E')
    CB_34 = lambda self: self.SWAP('H')
    CB_35 = lambda self: self.SWAP('L')
    CB_36 = lambda self: self.SWAP('HL')
    CB_37 = lambda self: self.SWAP('A')
    CB_38 = lambda self: self.SRL('B')
    CB_39 = lambda self: self.SRL('C')
    CB_3A = lambda self: self.SRL('D')
    CB_3B = lambda self: self.SRL('E')
    CB_3C = lambda self: self.SRL('H')
    CB_3D = lambda self: self.SRL('L')
    CB_3E = lambda self: self.SRL('HL')
    CB_3F = lambda self: self.SRL('A')

    CB_40 = lambda self: self.BIT(0,'B')
    CB_41 = lambda self: self.BIT(0,'C')
    CB_42 = lambda self: self.BIT(0,'D')
    CB_43 = lambda self: self.BIT(0,'E')
    CB_44 = lambda self: self.BIT(0,'H')
    CB_45 = lambda self: self.BIT(0,'L')
    CB_46 = lambda self: self.BIT(0,'HL')
    CB_47 = lambda self: self.BIT(0,'A')
    CB_48 = lambda self: self.BIT(1,'B')
    CB_49 = lambda self: self.BIT(1,'C')
    CB_4A = lambda self: self.BIT(1,'D')
    CB_4B = lambda self: self.BIT(1,'E')
    CB_4C = lambda self: self.BIT(1,'H')
    CB_4D = lambda self: self.BIT(1,'L')
    CB_4E = lambda self: self.BIT(1,'HL')
    CB_4F = lambda self: self.BIT(1,'A')

    CB_50 = lambda self: self.BIT(2,'B')
    CB_51 = lambda self: self.BIT(2,'C')
    CB_52 = lambda self: self.BIT(2,'D')
    CB_53 = lambda self: self.BIT(2,'E')
    CB_54 = lambda self: self.BIT(2,'H')
    CB_55 = lambda self: self.BIT(2,'L')
    CB_56 = lambda self: self.BIT(2,'HL')
    CB_57 = lambda self: self.BIT(2,'A')
    CB_58 = lambda self: self.BIT(3,'B')
    CB_59 = lambda self: self.BIT(3,'C')
    CB_5A = lambda self: self.BIT(3,'D')
    CB_5B = lambda self: self.BIT(3,'E')
    CB_5C = lambda self: self.BIT(3,'H')
    CB_5D = lambda self: self.BIT(3,'L')
    CB_5E = lambda self: self.BIT(3,'HL')
    CB_5F = lambda self: self.BIT(3,'A')

    CB_60 = lambda self: self.BIT(4,'B')
    CB_61 = lambda self: self.BIT(4,'C')
    CB_62 = lambda self: self.BIT(4,'D')
    CB_63 = lambda self: self.BIT(4,'E')
    CB_64 = lambda self: self.BIT(4,'H')
    CB_65 = lambda self: self.BIT(4,'L')
    CB_66 = lambda self: self.BIT(4,'HL')
    CB_67 = lambda self: self.BIT(4,'A')
    CB_68 = lambda self: self.BIT(5,'B')
    CB_69 = lambda self: self.BIT(5,'C')
    CB_6A = lambda self: self.BIT(5,'D')
    CB_6B = lambda self: self.BIT(5,'E')
    CB_6C = lambda self: self.BIT(5,'H')
    CB_6D = lambda self: self.BIT(5,'L')
    CB_6E = lambda self: self.BIT(5,'HL')
    CB_6F = lambda self: self.BIT(5,'A')

    CB_70 = lambda self: self.BIT(6,'B')
    CB_71 = lambda self: self.BIT(6,'C')
    CB_72 = lambda self: self.BIT(6,'D')
    CB_73 = lambda self: self.BIT(6,'E')
    CB_74 = lambda self: self.BIT(6,'H')
    CB_75 = lambda self: self.BIT(6,'L')
    CB_76 = lambda self: self.BIT(6,'HL')
    CB_77 = lambda self: self.BIT(6,'A')
    CB_78 = lambda self: self.BIT(7,'B')
    CB_79 = lambda self: self.BIT(7,'C')
    CB_7A = lambda self: self.BIT(7,'D')
    CB_7B = lambda self: self.BIT(7,'E')
    CB_7C = lambda self: self.BIT(7,'H')
    CB_7D = lambda self: self.BIT(7,'L')
    CB_7E = lambda self: self.BIT(7,'HL')
    CB_7F = lambda self: self.BIT(7,'A')

    CB_80 = lambda self: self.RES(0,'B')
    CB_81 = lambda self: self.RES(0,'C')
    CB_82 = lambda self: self.RES(0,'D')
    CB_83 = lambda self: self.RES(0,'E')
    CB_84 = lambda self: self.RES(0,'H')
    CB_85 = lambda self: self.RES(0,'L')
    CB_86 = lambda self: self.RES(0,'HL')
    CB_87 = lambda self: self.RES(0,'A')
    CB_88 = lambda self: self.RES(1,'B')
    CB_89 = lambda self: self.RES(1,'C')
    CB_8A = lambda self: self.RES(1,'D')
    CB_8B = lambda self: self.RES(1,'E')
    CB_8C = lambda self: self.RES(1,'H')
    CB_8D = lambda self: self.RES(1,'L')
    CB_8E = lambda self: self.RES(1,'HL')
    CB_8F = lambda self: self.RES(1,'A')

    CB_90 = lambda self: self.RES(2,'B')
    CB_91 = lambda self: self.RES(2,'C')
    CB_92 = lambda self: self.RES(2,'D')
    CB_93 = lambda self: self.RES(2,'E')
    CB_94 = lambda self: self.RES(2,'H')
    CB_95 = lambda self: self.RES(2,'L')
    CB_96 = lambda self: self.RES(2,'HL')
    CB_97 = lambda self: self.RES(2,'A')
    CB_98 = lambda self: self.RES(3,'B')
    CB_99 = lambda self: self.RES(3,'C')
    CB_9A = lambda self: self.RES(3,'D')
    CB_9B = lambda self: self.RES(3,'E')
    CB_9C = lambda self: self.RES(3,'H')
    CB_9D = lambda self: self.RES(3,'L')
    CB_9E = lambda self: self.RES(3,'HL')
    CB_9F = lambda self: self.RES(3,'A')

    CB_A0 = lambda self: self.RES(4,'B')
    CB_A1 = lambda self: self.RES(4,'C')
    CB_A2 = lambda self: self.RES(4,'D')
    CB_A3 = lambda self: self.RES(4,'E')
    CB_A4 = lambda self: self.RES(4,'H')
    CB_A5 = lambda self: self.RES(4,'L')
    CB_A6 = lambda self: self.RES(4,'HL')
    CB_A7 = lambda self: self.RES(4,'A')
    CB_A8 = lambda self: self.RES(5,'B')
    CB_A9 = lambda self: self.RES(5,'C')
    CB_AA = lambda self: self.RES(5,'D')
    CB_AB = lambda self: self.RES(5,'E')
    CB_AC = lambda self: self.RES(5,'H')
    CB_AD = lambda self: self.RES(5,'L')
    CB_AE = lambda self: self.RES(5,'HL')
    CB_AF = lambda self: self.RES(5,'A')

    CB_B0 = lambda self: self.RES(6,'B')
    CB_B1 = lambda self: self.RES(6,'C')
    CB_B2 = lambda self: self.RES(6,'D')
    CB_B3 = lambda self: self.RES(6,'E')
    CB_B4 = lambda self: self.RES(6,'H')
    CB_B5 = lambda self: self.RES(6,'L')
    CB_B6 = lambda self: self.RES(6,'HL')
    CB_B7 = lambda self: self.RES(6,'A')
    CB_B8 = lambda self: self.RES(7,'B')
    CB_B9 = lambda self: self.RES(7,'C')
    CB_BA = lambda self: self.RES(7,'D')
    CB_BB = lambda self: self.RES(7,'E')
    CB_BC = lambda self: self.RES(7,'H')
    CB_BD = lambda self: self.RES(7,'L')
    CB_BE = lambda self: self.RES(7,'HL')
    CB_BF = lambda self: self.RES(7,'A')

    CB_C0 = lambda self: self.SET(0,'B')
    CB_C1 = lambda self: self.SET(0,'C')
    CB_C2 = lambda self: self.SET(0,'D')
    CB_C3 = lambda self: self.SET(0,'E')
    CB_C4 = lambda self: self.SET(0,'H')
    CB_C5 = lambda self: self.SET(0,'L')
    CB_C6 = lambda self: self.SET(0,'HL')
    CB_C7 = lambda self: self.SET(0,'A')
    CB_C8 = lambda self: self.SET(1,'B')
    CB_C9 = lambda self: self.SET(1,'C')
    CB_CA = lambda self: self.SET(1,'D')
    CB_CB = lambda self: self.SET(1,'E')
    CB_CC = lambda self: self.SET(1,'H')
    CB_CD = lambda self: self.SET(1,'L')
    CB_CE = lambda self: self.SET(1,'HL')
    CB_CF = lambda self: self.SET(1,'A')

    CB_D0 = lambda self: self.SET(2,'B')
    CB_D1 = lambda self: self.SET(2,'C')
    CB_D2 = lambda self: self.SET(2,'D')
    CB_D3 = lambda self: self.SET(2,'E')
    CB_D4 = lambda self: self.SET(2,'H')
    CB_D5 = lambda self: self.SET(2,'L')
    CB_D6 = lambda self: self.SET(2,'HL')
    CB_D7 = lambda self: self.SET(2,'A')
    CB_D8 = lambda self: self.SET(3,'B')
    CB_D9 = lambda self: self.SET(3,'C')
    CB_DA = lambda self: self.SET(3,'D')
    CB_DB = lambda self: self.SET(3,'E')
    CB_DC = lambda self: self.SET(3,'H')
    CB_DD = lambda self: self.SET(3,'L')
    CB_DE = lambda self: self.SET(3,'HL')
    CB_DF = lambda self: self.SET(3,'A')

    CB_E0 = lambda self: self.SET(4,'B')
    CB_E1 = lambda self: self.SET(4,'C')
    CB_E2 = lambda self: self.SET(4,'D')
    CB_E3 = lambda self: self.SET(4,'E')
    CB_E4 = lambda self: self.SET(4,'H')
    CB_E5 = lambda self: self.SET(4,'L')
    CB_E6 = lambda self: self.SET(4,'HL')
    CB_E7 = lambda self: self.SET(4,'A')
    CB_E8 = lambda self: self.SET(5,'B')
    CB_E9 = lambda self: self.SET(5,'C')
    CB_EA = lambda self: self.SET(5,'D')
    CB_EB = lambda self: self.SET(5,'E')
    CB_EC = lambda self: self.SET(5,'H')
    CB_ED = lambda self: self.SET(5,'L')
    CB_EE = lambda self: self.SET(5,'HL')
    CB_EF = lambda self: self.SET(5,'A')

    CB_F0 = lambda self: self.SET(6,'B')
    CB_F1 = lambda self: self.SET(6,'C')
    CB_F2 = lambda self: self.SET(6,'D')
    CB_F3 = lambda self: self.SET(6,'E')
    CB_F4 = lambda self: self.SET(6,'H')
    CB_F5 = lambda self: self.SET(6,'L')
    CB_F6 = lambda self: self.SET(6,'HL')
    CB_F7 = lambda self: self.SET(6,'A')
    CB_F8 = lambda self: self.SET(7,'B')
    CB_F9 = lambda self: self.SET(7,'C')
    CB_FA = lambda self: self.SET(7,'D')
    CB_FB = lambda self: self.SET(7,'E')
    CB_FC = lambda self: self.SET(7,'H')
    CB_FD = lambda self: self.SET(7,'L')
    CB_FE = lambda self: self.SET(7,'HL')
    CB_FF = lambda self: self.SET(7,'A')


    OPCODES = [
            OP_00, OP_01, OP_12, OP_03, OP_04, OP_05, OP_06, OP_07, OP_08, OP_09, OP_0A, OP_0B, OP_0C, OP_0D, OP_0E, OP_0F,
            OP_10, OP_11, OP_12, OP_13, OP_14, OP_15, OP_16, OP_17, OP_18, OP_19, OP_1A, OP_1B, OP_1C, OP_1D, OP_1E, OP_1F,
            OP_20, OP_21, OP_22, OP_23, OP_24, OP_25, OP_26, OP_27, OP_28, OP_29, OP_2A, OP_2B, OP_2C, OP_2D, OP_2E, OP_2F,
            OP_30, OP_31, OP_32, OP_33, OP_34, OP_35, OP_36, OP_37, OP_38, OP_39, OP_3A, OP_3B, OP_3C, OP_3D, OP_3E, OP_3F,
            OP_40, OP_41, OP_42, OP_43, OP_44, OP_45, OP_46, OP_47, OP_48, OP_49, OP_4A, OP_4B, OP_4C, OP_4D, OP_4E, OP_4F,
            OP_50, OP_51, OP_52, OP_53, OP_54, OP_55, OP_56, OP_57, OP_58, OP_59, OP_5A, OP_5B, OP_5C, OP_5D, OP_5E, OP_5F,
            OP_60, OP_61, OP_62, OP_63, OP_64, OP_65, OP_66, OP_67, OP_68, OP_69, OP_6A, OP_6B, OP_6C, OP_6D, OP_6E, OP_6F,
            OP_70, OP_71, OP_72, OP_73, OP_74, OP_75, OP_76, OP_77, OP_78, OP_79, OP_7A, OP_7B, OP_7C, OP_7D, OP_7E, OP_7F,
            OP_80, OP_81, OP_82, OP_83, OP_84, OP_85, OP_86, OP_87, OP_88, OP_89, OP_8A, OP_8B, OP_8C, OP_8D, OP_8E, OP_8F,
            OP_90, OP_91, OP_92, OP_93, OP_94, OP_95, OP_96, OP_97, OP_98, OP_99, OP_9A, OP_9B, OP_9C, OP_9D, OP_9E, OP_9F,
            OP_A0, OP_A1, OP_A2, OP_A3, OP_A4, OP_A5, OP_A6, OP_A7, OP_A8, OP_A9, OP_AA, OP_AB, OP_AC, OP_AD, OP_AE, OP_AF,
            OP_B0, OP_B1, OP_B2, OP_B3, OP_B4, OP_B5, OP_B6, OP_B7, OP_B8, OP_B9, OP_BA, OP_BB, OP_BC, OP_BD, OP_BE, OP_BF,
            OP_C0, OP_C1, OP_C2, OP_C3, OP_C4, OP_C5, OP_C6, OP_C7, OP_C8, OP_C9, OP_CA, None , OP_CC, OP_CD, OP_CE, OP_CF,
            OP_D0, OP_D1, OP_D2, None , OP_D4, OP_D5, OP_D6, OP_D7, OP_D8, OP_D9, OP_DA, None , OP_DC, None , None , OP_DF,
            OP_E0, OP_E1, OP_E2, None , None , OP_E5, OP_E6, OP_E7, OP_E8, OP_E9, OP_EA, None , None , None , None , OP_EF,
            OP_F0, OP_F1, None , OP_F3, None , OP_F5, OP_F6, OP_F7, OP_F8, OP_F9, OP_FA, OP_FB, None , None , None , OP_FF,
    ]

    CB_OPCODES = [
            CB_00, CB_01, CB_12, CB_03, CB_04, CB_05, CB_06, CB_07, CB_08, CB_09, CB_0A, CB_0B, CB_0C, CB_0D, CB_0E, CB_0F,
            CB_10, CB_11, CB_12, CB_13, CB_14, CB_15, CB_16, CB_17, CB_18, CB_19, CB_1A, CB_1B, CB_1C, CB_1D, CB_1E, CB_1F,
            CB_20, CB_21, CB_22, CB_23, CB_24, CB_25, CB_26, CB_27, CB_28, CB_29, CB_2A, CB_2B, CB_2C, CB_2D, CB_2E, CB_2F,
            CB_30, CB_31, CB_32, CB_33, CB_34, CB_35, CB_36, CB_37, CB_38, CB_39, CB_3A, CB_3B, CB_3C, CB_3D, CB_3E, CB_3F,
            CB_40, CB_41, CB_42, CB_43, CB_44, CB_45, CB_46, CB_47, CB_48, CB_49, CB_4A, CB_4B, CB_4C, CB_4D, CB_4E, CB_4F,
            CB_50, CB_51, CB_52, CB_53, CB_54, CB_55, CB_56, CB_57, CB_58, CB_59, CB_5A, CB_5B, CB_5C, CB_5D, CB_5E, CB_5F,
            CB_60, CB_61, CB_62, CB_63, CB_64, CB_65, CB_66, CB_67, CB_68, CB_69, CB_6A, CB_6B, CB_6C, CB_6D, CB_6E, CB_6F,
            CB_70, CB_71, CB_72, CB_73, CB_74, CB_75, CB_76, CB_77, CB_78, CB_79, CB_7A, CB_7B, CB_7C, CB_7D, CB_7E, CB_7F,
            CB_80, CB_81, CB_82, CB_83, CB_84, CB_85, CB_86, CB_87, CB_88, CB_89, CB_8A, CB_8B, CB_8C, CB_8D, CB_8E, CB_8F,
            CB_90, CB_91, CB_92, CB_93, CB_94, CB_95, CB_96, CB_97, CB_98, CB_99, CB_9A, CB_9B, CB_9C, CB_9D, CB_9E, CB_9F,
            CB_A0, CB_A1, CB_A2, CB_A3, CB_A4, CB_A5, CB_A6, CB_A7, CB_A8, CB_A9, CB_AA, CB_AB, CB_AC, CB_AD, CB_AE, CB_AF,
            CB_B0, CB_B1, CB_B2, CB_B3, CB_B4, CB_B5, CB_B6, CB_B7, CB_B8, CB_B9, CB_BA, CB_BB, CB_BC, CB_BD, CB_BE, CB_BF,
            CB_C0, CB_C1, CB_C2, CB_C3, CB_C4, CB_C5, CB_C6, CB_C7, CB_C8, CB_C9, CB_CA, CB_CB, CB_CC, CB_CD, CB_CE, CB_CF,
            CB_D0, CB_D1, CB_D2, CB_D3, CB_D4, CB_D5, CB_D6, CB_D7, CB_D8, CB_D9, CB_DA, CB_DB, CB_DC, CB_DD, CB_DE, CB_DF,
            CB_E0, CB_E1, CB_E2, CB_E3, CB_E4, CB_E5, CB_E6, CB_E7, CB_E8, CB_E9, CB_EA, CB_EB, CB_EC, CB_ED, CB_EE, CB_EF,
            CB_F0, CB_F1, CB_F2, CB_F3, CB_F4, CB_F5, CB_F6, CB_F7, CB_F8, CB_F9, CB_FA, CB_FB, CB_FC, CB_FD, CB_FE, CB_FF,
    ]

