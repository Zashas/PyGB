#coding: utf-8

class Z80(object):
    m, t = 0,0 #Two clocks
    registers = {
                'A':0, #A, B, C, D E, H, L and F are all 8bit registers.
                'B':0, #Some can be paired together to form 16bit registers : BC, DE, HL.
                'C':0,
                'D':0,
                'E':0,
                'H':0,
                'L':0,
                'F':0, #Flag with data about the last operation's results
                'SP':0, #Stack pointer
                'PC':0 #Program counter
    }

    def __init__(self, memory):
        self.memory = memory

    @property
    def PC(self):
        return self.registers['PC']

    def incPC(self):
        self.registers['PC'] += 1

    def next_instruction(self): #Executes the following instruction
        pass
