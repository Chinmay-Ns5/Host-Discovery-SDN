# topology.py (4-host stable dynamic simulation)

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo


class FourHostTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch, protocols='OpenFlow10')

        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')

        # h4 initially has NO IP (simulates host not yet joined)
        h4 = self.addHost('h4', mac='00:00:00:00:00:04')

        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)


def run():
    net = Mininet(
        topo=FourHostTopo(),
        controller=None,
        switch=OVSKernelSwitch,
        autoSetMacs=False
    )

    net.addController(
        'c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )

    net.start()

    # Make h4 "offline" initially
    net.get('h4').cmd('ip link set h4-eth0 down')

    info('\n*** h4 is OFFLINE initially\n')
    info('*** To activate h4 run:\n')
    info('*** h4 ip link set h4-eth0 up\n')
    info('*** h4 ip addr add 10.0.0.4/24 dev h4-eth0\n\n')

    CLI(net)
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
