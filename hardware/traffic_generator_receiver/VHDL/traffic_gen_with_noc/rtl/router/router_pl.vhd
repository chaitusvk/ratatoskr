-------------------------------------------------------------------------------
-- Title      : Router with buffered outputs (pipeline stage)
-- Project    : 
-------------------------------------------------------------------------------
-- File       : router_pl.vhd
-- Author     : Lennart Bamberg  <lennart@t440s>
-- Company    : 
-- Created    : 2018-11-23
-- Last update: 2018-11-28
-- Platform   : 
-- Standard   : VHDL'93/02
-------------------------------------------------------------------------------
-- Description: 
-------------------------------------------------------------------------------
-- Copyright (c) 2018 
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 2018-11-23  1.0      lennart Created
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use work.NOC_3D_PACKAGE.all;



entity router_pl is

  generic (
    port_num                     : integer       := 7;
    Xis                          : natural       := 1;
    Yis                          : natural       := 1;
    Zis                          : natural       := 1;
    header_incl_in_packet_length : boolean       := true;
    -- integer vector of range "0 to port_num-1"
    port_exist                   : integer_vec   := (0, 1, 2, 3, 4, 5, 6);
    vc_num_vec                   : integer_vec   := (4 ,4 ,4 ,4 ,4 ,4 ,4 );
    vc_num_out_vec               : integer_vec   := (4 ,4 ,4 ,4 ,4 ,4 ,4 );
    -- integer vector of range "0 to port_num-1, 0 to max_vc_num-1"                                   
    vc_depth_array               : vc_prop_int_array := ((4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) );
    vc_depth_out_array           : vc_prop_int_array := ((4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) ,(4 ,4 ,4 ,4 ) );
    rout_algo                    : string        := "DXYU"
    );

  port (
    -- Inputs
    clk, rst           : in  std_logic;
    data_rx            : in  flit_vector(port_num-1 downto 0);
    vc_write_rx_vec    : in  std_logic_vector(int_vec_sum(vc_num_vec)-1 downto 0);
    incr_rx_vec        : in  std_logic_vector(int_vec_sum(vc_num_out_vec)-1 downto 0);
    -- Outputs
    data_tx_pl         : out flit_vector(port_num-1 downto 0);
    vc_write_tx_pl_vec : out std_logic_vector(int_vec_sum(vc_num_out_vec)-1 downto 0);
    incr_tx_pl_vec     : out std_logic_vector(int_vec_sum(vc_num_vec)-1 downto 0));
end entity router_pl;

architecture structural of router_pl is
  signal vc_transfer_vec        : std_logic_vector(int_vec_sum(vc_num_vec)-1 downto 0);
  signal valid_data_vc_vec      : std_logic_vector(int_vec_sum(vc_num_vec)-1 downto 0);
  signal data_transfer, data_tx : flit_vector(port_num-1 downto 0);
  signal header                 : header_inf_vector(int_vec_sum(vc_num_vec)-1 downto 0);
  signal crossbar_ctrl          : std_logic_vector(port_num*bit_width(port_num-1)-1 downto 0);
  signal vc_write_tx_vec        : std_logic_vector(int_vec_sum(vc_num_out_vec)-1 downto 0);
begin  -- architecture structural

  INBUT_BUFFS : for i in 0 to port_num-1 generate
    constant ur_vc : natural := upper_range(vc_num_vec, i);
    constant lr_vc : natural := lower_range(vc_num_vec, i);
  begin
    vc_input_buffer_i : entity work.vc_input_buffer
      generic map (
        vc_num   => vc_num_vec(i),
        vc_depth => vc_depth_array(i))
      port map (
        clk           => clk,
        rst           => rst,
        data_rx       => data_rx(i),
        vc_write_rx   => vc_write_rx_vec(ur_vc downto lr_vc),
        vc_transfer   => vc_transfer_vec(ur_vc downto lr_vc),
        valid_data_vc => valid_data_vc_vec(ur_vc downto lr_vc),
        data_transfer => data_transfer(i),
        header        => header(ur_vc downto lr_vc));
  end generate;

  XBAR : entity work.crossbar
    generic map (
      port_num   => port_num,
      port_exist => port_exist,
      rout_algo  => rout_algo)
    port map (
      crossbar_in   => data_transfer,
      crossbar_ctrl => crossbar_ctrl,
      crossbar_out  => data_tx);

  OUT_PL_REG : for i in 0 to port_num-1 generate
    constant ur_vc_out : natural := upper_range(vc_num_out_vec, i);
    constant lr_vc_out : natural := lower_range(vc_num_out_vec, i);
    constant ur_vc     : natural := upper_range(vc_num_vec, i);
    constant lr_vc     : natural := lower_range(vc_num_vec, i);
  begin
    output_register_i : entity work.output_register
      generic map (
        vc_num     => vc_num_vec(i),
        vc_num_out => vc_num_out_vec(i))
      port map (
        clk            => clk,
        rst            => rst,
        data_tx        => data_tx(i),
        vc_write_tx    => vc_write_tx_vec(ur_vc_out downto lr_vc_out),
        incr_tx        => vc_transfer_vec(ur_vc downto lr_vc),
        data_tx_pl     => data_tx_pl(i),
        vc_write_tx_pl => vc_write_tx_pl_vec(ur_vc_out downto lr_vc_out),
        incr_tx_pl     => incr_tx_pl_vec(ur_vc downto lr_vc));
  end generate;

  CTRL_ARB : entity work.arbiter
    generic map (
      port_num                     => port_num,
      port_exist                   => port_exist,
      Xis                          => Xis,
      Yis                          => Yis,
      Zis                          => Zis,
      header_incl_in_packet_length => header_incl_in_packet_length,
      rout_algo                    => rout_algo,
      vc_num_vec                   => vc_num_vec,
      vc_num_out_vec               => vc_num_out_vec,
      vc_depth_array               => vc_depth_array,
      vc_depth_out_array           => vc_depth_out_array)
    port map (
      clk               => clk,
      rst               => rst,
      header            => header,
      valid_data_vc_vec => valid_data_vc_vec,
      incr_rx_vec       => incr_rx_vec,
      crossbar_ctrl     => crossbar_ctrl,
      vc_transfer_vec   => vc_transfer_vec,
      vc_write_tx_vec   => vc_write_tx_vec);



end architecture structural;
