#coding: utf-8
import pygame

class Screen():
    def __init__(self, memory):
        self.memory = memory
        self.window = pygame.display.set_mode((160, 144))
        pygame.display.set_caption('PyGB')

        self.screen_buffer = [[(0,0,0)]*256 for x in xrange(256)] #256x256 RGB pixels
        self.clock = 0
        self.state = 1 #2 : scanline in OAM, 3 : scanline in VRAM, 1 : vblank, 0 : horizontal blank
        self.current_line = 0

    def inc_current_line(self):
        self.current_line = 0 if self.current_line == 154 else self.current_line + 1
        self.memory.write_byte(0xFF44, self.current_line)

    def reset_current_line(self):
        self.current_line = 0
        self.memory.write_byte(0xFF44, self.current_line)

    def write_pixel(self, pos, color):  #(x,y) & (r,g,b)
        self.window.set_at(pos, color)

    def get_current_tile_map(self):
        return self.memory.read_byte(0xFF40) & 8

    def get_current_tile_set(self):
        return self.memory.read_byte(0xFF40) & 16

    def get_scrolls(self):
        return (self.memory.read_byte(0xFF42), self.memory.read_byte(0xFF43)) #(y, x)

    def sync_clock(self, cycles):
        self.clock += cycles
        if self.clock < 80 and self.state != 2 and self.current_line < 144:
            self.state = 2 #Scanline in OAM
            self.scanline_OAM()
        elif self.clock >= 80 and self.state == 2:
            self.state = 3 #Scanline in VRAM
            self.scanline_VRAM()
        elif self.clock >= 172 and self.state == 3:
            self.state = 0 #Horizontal blanking
        elif self.clock >= 456 and self.state == 0:
            self.inc_current_line()
            self.clock -= 456
            if self.current_line == 144:
                self.state = 1 #Vertical blanking
                self.update_screen()
        elif self.clock >= 456 and self.state == 1:
            self.inc_current_line()
            self.clock -= 456

    def update_screen(self):
        scroll_y, scroll_x = self.get_scrolls()
        for y in xrange(144):
            for x in xrange(160):
                self.write_pixel((x, y), self.screen_buffer[(y+scroll_y)&255][(x+scroll_x)&255])

        pygame.display.flip()

    def scanline_OAM(self):
        pass

    def scanline_VRAM(self):
        map_nb, set_nb = self.get_current_tile_map(), self.get_current_tile_set()
        tiles_nb = self.memory[0x9800:0x9BFF] if map_nb == 0 else self.memory[0x9C00:0x9FFF] #0 : 0x9800 - 0x9BFF, 1 : 0x9C00 - 0x9FFF
        print tiles_nb
