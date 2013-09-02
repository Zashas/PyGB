#coding: utf-8
import pygame

class Screen():
    def __init__(self, memory):
        self.memory = memory
        self.window = pygame.display.set_mode((160, 144))
        pygame.display.set_caption('PyGB')

        self.clock = 0
        self.state = 2 #2 : scanline in OAM, 3 : scanline in VRAM, 1 : vblank, 0 : horizontal blank
        self.current_line = 0

    def inc_current_line(self):
        self.current_line = 0 if self.current_line == 10 else self.current_line + 1
        self.memory.write_byte(0xFF44, self.current_line)

    def write_pixel(self, pos, color):  #(x,y) & (r,g,b)
        window.set_at(pos, color)

    def get_current_tile_map(self):
        return self.memory.read_byte(0xFF40) & 8

    def get_current_tile_set(self):
        return self.memory.read_byte(0xFF40) & 16

    def sync_clock(self, cycles):
        self.clock += cycles
        if self.clock < 80 and self.state != 2:
            self.state = 2 #Scanline in OAM
            if self.current_line == 10:
                self.inc_current_line()
            self.scanline_OAM()
        elif self.clock >= 80 and self.state != 3:
            self.state = 3 #Scanline in VRAM
            self.scanline_VRAM()
        elif self.clock >= 172 and self.state != 0:
            self.state = 0 #Horizontal blanking
        elif self.clock >= 456 and self.state != 1:
            self.inc_current_line()
            if self.current_line == 10:
                self.state = 1 #Vertical blanking
            else:
                self.clock = 0
        elif self.clock >= 70224:
            self.update_screen()
            self.clock -= 70224
            self.state = 2

    def update_screen(self):
        pygame.display.flip()

    def scanline_OAM(self):
        pass

    def scanline_VRAM(self):
        map_nb, set_nb = self.get_current_tile_map(), self.get_current_tile_set()
        tiles_map = self.memory[0x9800:0x9BFF] if map_nb == 0 else self.memory[0x9C00:0x9FFF] #0 : 0x9800 - 0x9BFF, 1 : 0x9C00 - 0x9FFF

