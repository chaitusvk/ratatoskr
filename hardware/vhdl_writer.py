import os
import glob
import subprocess
import itertools
import string
import noc_heter.func as nocHeter
import numpy as np
from string import Template

class NoCWriter():
    def __init__(self, config):
        self.config = config

        self.out_file = 'full_noc.vhd'
        #########################################################################################
        # 	Network size
        #########################################################################################
        self.noc_x=4
        self.noc_y=4
        self.noc_z=3
        #########################################################################################
        # 	Virtual Channel Number
        #########################################################################################
        self.vc_num=2
        self.vc_xy=[4, 4, 4]    # Horizontal Ports VC numbers (array size = noc_z)
        self.depth_xy=[4, 4, 4] # Horizontal Ports buffer depth (array size = noc_z)
        self.vc_z =[4, 4]       # Up and Down ports VC numbers (array size = noc_z-1)
        self.depth_z=[8, 8]     # Up and Down ports buffer depth (array size = noc_z-1)
        #########################################################################################
        # 	Routing Algorithm (character " is known as \")
        #########################################################################################
        self.flit_size= 32
        self.max_vc_num=4
        self.max_vc_num_out=4
        self.max_x_dim=4
        self.max_y_dim=4
        self.max_z_dim=4
        self.max_packet_len=31
        self.max_port_num=7
        self.rst_lvl=0
        self.max_buffer_depth=8
        self.cf=4
        self.vc_depth_array = nocHeter.ret_2D_int_array(self.max_port_num, self.max_vc_num, self.max_buffer_depth)
        self.vc_depth_array_minus= nocHeter.ret_2D_int_array(self.max_port_num-1, self.max_vc_num, self.max_buffer_depth)
        self.vc_depth_out_array = nocHeter.ret_2D_int_array(self.max_port_num, self.max_vc_num_out, self.max_buffer_depth)
        self.vc_depth_out_array_minus=nocHeter.ret_2D_int_array(self.max_port_num-1, self.max_vc_num_out, self.max_buffer_depth)
        self.max_port_exist = "(0, 1, 2, 3, 4, 5, 6)"
        self.port_exist_wo_down="(0, 1, 2, 3, 4, 5)"
        self.port_exist_wo_up="(0, 1, 2, 3, 4, 6)"
        self.max_vc_num_vec=nocHeter.ret_int_array(self.max_port_num, self.max_vc_num)
        self.max_vc_num_out_vec=nocHeter.ret_int_array(self.max_port_num, self.max_vc_num_out)
        self.vc_num_vec_minus=nocHeter.ret_int_array(self.max_port_num-1, self.max_vc_num)
        self.vc_num_out_vec_minus=nocHeter.ret_int_array(self.max_port_num-1, self.max_vc_num_out)
        self.max_vc_depth=nocHeter.ret_int_array(self.max_vc_num, self.max_buffer_depth)
        self.rout_algo="\"DXYU\""
        self.cf_vec="(1, 2, 4)"
        #########################################################################################
        # 	MAKE VHDL FILES FROM TXT FILES 
        #########################################################################################
        self.subs={ 'flit_size': self.flit_size, 'max_vc_num': self.max_vc_num,'max_vc_num_out': self.max_vc_num_out,
               'max_x_dim': self.max_x_dim, 'max_y_dim': self.max_y_dim, 'max_z_dim': self.max_z_dim,
               'max_packet_len': self.max_packet_len, 'max_port_num': self.max_port_num, 'rst_lvl': self.rst_lvl,
               'max_buffer_depth': self.max_buffer_depth, 'cf': self.cf, 'vc_depth_array': self.vc_depth_array,
               'vc_depth_array_minus': self.vc_depth_array_minus, 'vc_depth_out_array': self.vc_depth_out_array,
               'vc_depth_out_array_minus': self.vc_depth_out_array_minus, 'max_port_exist': self.max_port_exist,
               'port_exist_wo_down': self.port_exist_wo_down, 'port_exist_wo_up': self.port_exist_wo_up,
               'max_vc_num_vec': self.max_vc_num_vec, 'max_vc_num_out_vec': self.max_vc_num_out_vec,
               'vc_num_vec_minus': self.vc_num_vec_minus, 'vc_num_out_vec_minus': self.vc_num_out_vec_minus,
               'max_vc_depth': self.max_vc_depth, 'rout_algo': self.rout_algo, 'cf_vec': self.cf_vec }

    def write_noc_hetero(self):
        if not os.path.exists("full_noc"):
            os.makedirs("full_noc")
        for root, dirs, files in os.walk("noc_heter/template"):
            for file in files:
                if file.endswith(".txt"):
                    text_file = os.path.join(root, file)
                    text_dir = os.path.dirname(text_file)
                    dest_folder = "full_noc/"+os.path.basename(text_dir)
                    if not os.path.exists(dest_folder):
                        os.makedirs(dest_folder)
                    text_file_vhd = text_file[:-3]
                    text_file_vhd += 'vhd'
                    temp_file= open(text_file)
                    scr = Template(temp_file.read())
                    ft = open(text_file_vhd, 'w')
                    ft.write(scr.substitute(self.subs))
                    ft.close()
                    dest_file_vhd = dest_folder+"/"+os.path.basename(text_file_vhd)
                    os.rename(text_file_vhd, dest_file_vhd)
        #########################################################################################
        # 	Number of routers and input/output signals in network entity
        #########################################################################################
        router_num= self.noc_x * self.noc_y * self.noc_z
        io_sig_num=sum(self.vc_xy)*self.noc_x*self.noc_y
        max_vc=max(max(self.vc_xy),max(self.vc_z))
        #########################################################################################
        #       Opening the file and writing the entity and top of the architecture
        #########################################################################################
        ft=open(self.out_file, 'w+')
        ft.write(nocHeter.entity.substitute(router_num=str(router_num),io_sig_num=str(io_sig_num)))
        ft.write(nocHeter.archi_top.substitute(noc_x=str(self.noc_x-1), noc_y=str(self.noc_y-1), noc_z=str(self.noc_z-1), vc_num=str(max_vc)))
        #########################################################################################
        #       Writing the input and output connection signals in architecture
        #########################################################################################
        for z in range(self.noc_z):
          for y in range(self.noc_y):
            for x in range(self.noc_x):
              port_num=7
              if (y == self.noc_y - 1):
                port_num -= 1
              if (x == self.noc_x - 1):
                port_num -= 1
              if (y == 0):
                port_num -= 1
              if (x == 0):
                port_num -= 1
              if (z == self.noc_z - 1):
                port_num -= 1
              if (z == 0):
                port_num -= 1
              ft.write(nocHeter.data_in_tmp.substitute(x=str(x),y=str(y),z=str(z),port_num=str(port_num)))
              vc_num_vec=nocHeter.ret_sum_vc(z=z, vc_xy=self.vc_xy, vc_z=self.vc_z, noc_z=self.noc_z, port_num=port_num)
              vc_num_out_vec=nocHeter.ret_sum_vc(z=z, vc_xy=self.vc_xy, vc_z=self.vc_z, noc_z=self.noc_z, port_num=port_num)
              ft.write(nocHeter.vc_write_rx_vec_tmp.substitute(x=str(x),y=str(y),z=str(z),sum_vc=vc_num_vec))
              ft.write(nocHeter.incr_rx_vec_tmp.substitute(x=str(x),y=str(y),z=str(z),sum_vc=vc_num_out_vec))
              ft.write(nocHeter.vc_write_tx_pl_vec_tmp.substitute(x=str(x),y=str(y),z=str(z),sum_vc=vc_num_out_vec))
              ft.write(nocHeter.incr_tx_pl_vec_tmp.substitute(x=str(x),y=str(y),z=str(z),sum_vc=vc_num_vec))
        #########################################################################################
        #       writing the begin of the architecture
        #########################################################################################
        ft.write("""
        begin
        """)
        ft.close()
        #########################################################################################
        #       writing each router code
        #########################################################################################
        for z in range(self.noc_z):
          for y in range(self.noc_y):
            for x in range(self.noc_x):
              nocHeter.ftwrite_router(x, y, z, self.noc_x, self.noc_y, self.noc_z, self.vc_xy, self.vc_z, self.vc_num, self.depth_xy, self.depth_z, self.rout_algo)
        #########################################################################################
        #       writing end of architecture
        #########################################################################################
        ft=open(self.out_file,"a")
        ft.write("end architecture structural;")


        os.rename("full_noc.vhd", "full_noc/full_noc.vhd")