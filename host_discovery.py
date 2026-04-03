from pox.core import core
from pox.lib.revent import EventMixin
import pox.openflow.libopenflow_01 as of
from pox.lib.packet import ethernet
from pox.lib.addresses import EthAddr, IPAddr
import time

log = core.getLogger()

host_db = {}

def dpid_to_str(dpid):
    return "%016x" % dpid

def print_host_db():
    log.info("=" * 65)
    log.info("HOST DATABASE (%d host(s))" % len(host_db))
    log.info("-" * 65)
    log.info("%-18s %-15s %-18s %s" % ("MAC", "IP", "DPID", "Port"))
    log.info("-" * 65)
    for mac, info in host_db.items():
        ip = info["ip"] if info["ip"] else "Unknown"
        dpid = dpid_to_str(info["dpid"])
        port = info["port"]
        log.info("%-18s %-15s %-18s %s" % (mac, ip, dpid, port))
    log.info("=" * 65)

class HostDiscovery(EventMixin):
    def __init__(self):
        self.listenTo(core.openflow)
        log.info("HostDiscovery started")

    def _handle_ConnectionUp(self, event):
        dpid = dpid_to_str(event.dpid)
        log.info("Switch connected: %s" % dpid)

        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.match = of.ofp_match()
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        event.connection.send(msg)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        src_mac = str(packet.src)
        in_port = event.port
        dpid = event.dpid
        src_ip = None

        if EthAddr(src_mac).is_multicast:
            return

        if packet.type == ethernet.ARP_TYPE:
            arp_pkt = packet.payload
            if arp_pkt and arp_pkt.protosrc != IPAddr("0.0.0.0"):
                src_ip = str(arp_pkt.protosrc)

        elif packet.type == ethernet.IP_TYPE:
            ip_pkt = packet.payload
            if ip_pkt:
                src_ip = str(ip_pkt.srcip)

        now = time.time()

        if src_mac not in host_db:
            host_db[src_mac] = {
                "mac": src_mac,
                "ip": src_ip,
                "dpid": dpid,
                "port": in_port,
                "first_seen": now,
                "last_seen": now,
            }

            log.info("NEW HOST DETECTED")
            log.info("MAC: %s" % src_mac)
            log.info("IP: %s" % (src_ip if src_ip else "Unknown"))
            log.info("DPID: %s PORT: %d" % (dpid_to_str(dpid), in_port))
            print_host_db()

        else:
            entry = host_db[src_mac]
            changed = False

            if src_ip and entry["ip"] != src_ip:
                entry["ip"] = src_ip
                changed = True

            if entry["dpid"] != dpid or entry["port"] != in_port:
                entry["dpid"] = dpid
                entry["port"] = in_port
                changed = True

            entry["last_seen"] = now

            if changed:
                log.info("HOST UPDATED: %s" % src_mac)
                print_host_db()

        msg = of.ofp_packet_out()
        msg.data = event.ofp
        msg.in_port = in_port
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        event.connection.send(msg)

def launch():
    core.registerNew(HostDiscovery)
    log.info("Host Discovery Running")
