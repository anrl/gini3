#!/usr/bin/python2

"""icmp_proxy.py: Configures the switch to create a transparent
   ICMP echo proxy for requests directed to 192.168.2.3 from 192.168.1.2."""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

def configure_icmp_proxy(connection):
    log.info("icmp_proxy: loading...")
    
    msg = of.ofp_flow_mod()
    msg.match.priority = 50
    msg.actions.append(of.ofp_action_output(port = of.OFPP_NORMAL))
    connection.send(msg)

    msg = of.ofp_flow_mod()
    msg.match.priority = 100
    msg.match.dl_type = 0x800
    msg.match.nw_proto = 1
    msg.match.nw_src = IPAddr("192.168.1.2")
    msg.match.nw_dst = IPAddr("192.168.2.3")
    msg.match.tp_src = 8
    msg.actions.append(of.ofp_action_dl_addr.set_dst(
        EthAddr("fe:fd:02:00:00:03")))
    msg.actions.append(of.ofp_action_nw_addr.set_dst(
        IPAddr("192.168.3.4")))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    connection.send(msg)

    msg = of.ofp_flow_mod()
    msg.match.priority = 100
    msg.match.dl_type = 0x800
    msg.match.nw_proto = 1
    msg.match.nw_src = IPAddr("192.168.3.4")
    msg.match.nw_dst = IPAddr("192.168.1.2")
    msg.match.tp_src = 0
    msg.actions.append(of.ofp_action_dl_addr.set_dst(
        EthAddr("fe:fd:02:00:00:01")))
    msg.actions.append(of.ofp_action_nw_addr.set_src(IPAddr("192.168.2.3")))
    msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
    connection.send(msg)

def connection_up(event):
    configure_icmp_proxy(event.connection)

def launch():
    core.openflow.addListenerByName("ConnectionUp", connection_up)
