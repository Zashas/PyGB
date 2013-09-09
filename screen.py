#coding: utf-8
import pygame

class Screen(object):
    def __init__(self, memory):
        self.memory = memory
        self.window = pygame.display.set_mode((160, 144))
        pygame.display.set_caption('PyGB')

        self.screen_buffer = [[(0,0,0)]*256 for x in xrange(256)] #256x256 RGB pixels
        self.clock = 0

    def write_pixel(self, pos, color):  #(x,y) & (r,g,b)
        self.window.set_at(pos, color)

    """Special GPU registers"""

    @property
    def LCDC_display(self):
        return self.memory.read_byte(0xFF40) & 128

    @LCDC_display.setter
    def LCDC_display(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~128&255) | value)

    @property
    def LCDC_window_tile_map(self):
        return self.memory.read_byte(0xFF40) & 64

    @LCDC_window_tile_map.setter
    def LCDC_window_tile_map(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~64&255) | value)

    @property
    def LCDC_window_display(self):
        return self.memory.read_byte(0xFF40) & 32

    @LCDC_window_display.setter
    def LCDC_display(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~32&255) | value)

    @property
    def LCDC_tile_data(self):
        return self.memory.read_byte(0xFF40) & 16

    @LCDC_tile_data.setter
    def LCDC_tile_data(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~16&255) | value)

    @property
    def LCDC_bg_tile_map(self):
        return self.memory.read_byte(0xFF40) & 8

    @LCDC_bg_tile_map.setter
    def LCDC_bg_tile_map(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~8&255) | value)

    @property
    def LCDC_sprite_size(self):
        return self.memory.read_byte(0xFF40) & 4

    @LCDC_sprite_size.setter
    def LCDC_sprite_size(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~4&255) | value)

    @property
    def LCDC_sprite_display(self):
        return self.memory.read_byte(0xFF40) & 2

    @LCDC_sprite_display.setter
    def LCDC_sprite_display(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~2&255) | value)

    @property
    def LCDC_bg_display(self):
        return self.memory.read_byte(0xFF40) & 1

    @LCDC_bg_display.setter
    def LCDC_bg_display(self, value):
        self.memory.write_byte(0xFF40, self.memory.read_byte(0xFF40) & (~1&255) | value)

    @property
    def LCDS_coincidence_interrupt(self):
        self.memory.read_byte(0xFF41) & 64

    @LCDS_coincidence_interrupt.setter
    def LCDS_coincidence_interrupt(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~64&255) | value)

    @property
    def LCDS_OAM_interrupt(self):
        self.memory.read_byte(0xFF41) & 32

    @LCDS_OAM_interrupt.setter
    def LCDS_OAM_interrupt(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~32&255) | value)

    @property
    def LCDS_VBLANK_interrupt(self):
        self.memory.read_byte(0xFF41) & 16

    @LCDS_VBLANK_interrupt.setter
    def LCDS_VBLANK_interrupt(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~16&255) | value)

    @property
    def LCDS_HBLANK_interrupt(self):
        self.memory.read_byte(0xFF41) & 8

    @LCDS_HBLANK_interrupt.setter
    def LCDS_HBLANK_interrupt(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~8&255) | value)

    @property
    def LCDS_coincidence_flag(self):
        self.memory.read_byte(0xFF41) & 4

    @LCDS_coincidence_flag.setter
    def LCDS_coincidence_flag(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~4&255) | value)

    @property
    def LCDS_mode_flag(self):
        return self.memory.read_byte(0xFF41) & 3

    @LCDS_mode_flag.setter
    def LCDS_mode_flag(self, value):
        self.memory.write_byte(0xFF41, self.memory.read_byte(0xFF41) & (~3&255) | value)

    @property
    def scroll_y(self):
        return self.memory.read_byte(0xFF42)

    @scroll_y.setter
    def scroll_y(self, value):
        self.memory.write_byte(0xFF42, value)

    @property
    def scroll_x(self):
        return self.memory.read_byte(0xFF43)

    @scroll_x.setter
    def scroll_x(self, value):
        self.memory.write_byte(0xFF43, value)

    @property
    def LY(self):
        return self.memory.read_byte(0xFF44)

    @LY.setter
    def LY(self, value):
        self.memory.write_byte(0xFF44, value)

    @property
    def LYC(self):
        return self.memory.read_byte(0xFF45)

    @LYC.setter
    def LYC(self, value):
        self.memory.write_byte(0xFF45, value)

    def sync_clock(self, cycles):
        self.clock += cycles
        if self.clock < 80 and self.LCDS_mode_flag != 2 and self.LY < 144:
            self.LCDS_mode_flag = 2 #Scanline in OAM
            self.scanline_OAM()
        elif self.clock >= 80 and self.LCDS_mode_flag == 2:
            self.LCDS_mode_flag = 3 #Scanline in VRAM
            self.scanline_VRAM()
        elif self.clock >= 172 and self.LCDS_mode_flag == 3:
            self.LCDS_mode_flag = 0 #Horizontal blanking
        elif self.clock >= 456 and self.LCDS_mode_flag == 0:
            self.LY = self.LY + 1
            self.LCDS_coincidence_flag = 1 if self.LY == self.LYC else 0
            self.clock -= 456
            if self.LY == 144:
                self.LCDS_mode_flag = 1 #Vertical blanking
                self.memory.interrupt_VBLANK_flag = 1
                self.update_screen()
        elif self.clock >= 456 and self.LCDS_mode_flag == 1:
            self.LY = self.LY + 1 if self.LY < 153 else 0
            self.LCDS_coincidence_flag = 1 if self.LY == self.LYC else 0
            self.clock -= 456

    def update_screen(self):
        for y in xrange(144):
            for x in xrange(160):
                self.write_pixel((x, y), self.screen_buffer[(y+self.scroll_y)&255][(x+self.scroll_x)&255])

        pygame.display.flip()

    def scanline_OAM(self):
        pass

    def scanline_VRAM(self):
        map_nb, set_nb = self.LCDC_bg_tile_map, self.LCDC_tile_data
        tiles_nb = self.memory[0x9800:0x9BFF] if map_nb == 0 else self.memory[0x9C00:0x9FFF] #0 : 0x9800 - 0x9BFF, 1 : 0x9C00 - 0x9FFF
        #print tiles_nb
