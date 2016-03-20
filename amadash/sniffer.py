from __future__ import unicode_literals, print_function, absolute_import, division

import socket, sys

try:
    import pcap
    pcap_is_available = True
except ImportError:
    pcap_is_available = False

ETH_P_ALL = 0x0003
ETHERNET_HEADER_LENGTH = 14


def abort(msg):
    sys.stderr.write('{}\n'.format(msg))
    sys.exit(1)


class BaseSniffer(object):
    def __init__(self, interface):
        self.interface = interface
        self.is_running = True

    def bytes_to_mac(self, a):
        return '{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}'.format(*a[0:6])

    def mac_to_bytes(self, mac):
        return mac.replace(':', '').lower().decode('hex')

    def parse_ethernet_header(self, packet):
        dst_mac = self.bytes_to_mac(packet[0:6])
        src_mac = self.bytes_to_mac(packet[6:12])
        eth_protocol = socket.ntohs((packet[13] << 8) + packet[12])

        return dst_mac, src_mac, eth_protocol

    def shutdown(self):
        self.is_running = False


class SocketSniffer(BaseSniffer):
    '''An inefficient fallback sniffer.'''

    def __init__(self, *args, **kwargs):
        super(SocketSniffer, self).__init__(*args, **kwargs)
        try:
            self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL))
            if self.interface:
                self.sock.bind((self.interface, ETH_P_ALL))
        except Exception as e:
            abort('Socket could not be created: {}'.format(e))

    def sniff(self, macs, callback):
        sock = self.sock
        mac_bytes = set(map(self.mac_to_bytes, macs))
        packet = bytearray(ETHERNET_HEADER_LENGTH)
        while self.is_running:
            try:
                sock.recvfrom_into(packet)
            except:
                packet.zfill(0)

            if packet[6:12] in mac_bytes:
                dst_mac, src_mac, eth_protocol = self.parse_ethernet_header(packet)
                callback(dst_mac, src_mac, eth_protocol)

    def sniff_broadcast(self, callback):
        sock = self.sock
        broadcast_mac = self.mac_to_bytes('ff:ff:ff:ff:ff:ff')
        packet = bytearray(ETHERNET_HEADER_LENGTH)
        while self.is_running:
            try:
                sock.recvfrom_into(packet)
            except:
                packet.zfill(0)

            if packet[0:6] == broadcast_mac:
                dst_mac, src_mac, eth_protocol = self.parse_ethernet_header(map(ord, packet))
                callback(src_mac, eth_protocol)


class PCAPSniffer(BaseSniffer):
    '''Efficient method of monitoring network traffic for the given MAC addresses.'''

    def __init__(self, *args, **kwargs):
        super(PCAPSniffer, self).__init__(*args, **kwargs)

        try:
            self.pc = pcap.pcap(self.interface, snaplen=ETHERNET_HEADER_LENGTH, immediate=True, timeout_ms=1000, promisc=False)
            self.pc.setfilter('broadcast')  # Limit what we listen to to just be broadcast packets
        except Exception as e:
            abort('Could not initialize packet capture interface: {}'.format(e))

    def sniff(self, macs, callback):
        pc = self.pc
        mac_bytes = set(map(self.mac_to_bytes, macs))
        while self.is_running:
            try:
                _, packet = pc.next()
            except:
                packet = None

            if packet and packet[6:12] in mac_bytes:
                dst_mac, src_mac, eth_protocol = self.parse_ethernet_header(map(ord, packet))
                callback(src_mac, eth_protocol)

    def sniff_broadcast(self, callback):
        pc = self.pc
        broadcast_mac = self.mac_to_bytes('ff:ff:ff:ff:ff:ff')
        while self.is_running:
            try:
                _, packet = pc.next()
            except:
                packet = None

            if packet and packet[0:6] == broadcast_mac:
                dst_mac, src_mac, eth_protocol = self.parse_ethernet_header(map(ord, packet))
                callback(src_mac, eth_protocol)


def get_sniffer(interface, allow_fallback=False):
    '''Initializes a sniffer object, preferring the PCAP version.'''

    if pcap_is_available:
        return PCAPSniffer(interface)
    elif allow_fallback:
        return SocketSniffer(interface)

    raise Exception('No packet capture method available. Consider installing libpcap or enabling fallback capture method.')

