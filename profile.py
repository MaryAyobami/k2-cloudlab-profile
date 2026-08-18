"""K2 sigcomm21 artifact CloudLab profile with per-node selectable hardware type."""

import geni.portal as portal
import geni.rspec.igext as IG
import geni.rspec.emulab  # registers setNoInterSwitchLinks on Link

AUTHOR_DUT = "urn:publicid:IDN+utah.cloudlab.us+image+heartbeat-PG0:xl170-centos7-ubuntu20:2"
AUTHOR_GEN = "urn:publicid:IDN+utah.cloudlab.us+image+heartbeat-PG0:xl170-centos7-ubuntu20.node-1:5"
STOCK_DUT = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
STOCK_GEN = "urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD"
STOCK_NEW = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"

NODES = ["xl170", "c6525-25g", "sm110p", "r6615", "d7615", "c6525-100g", "c6620", "d760p"]

IMAGES = [("authors", "Authors' xl170 snapshots"),
          ("stock", "Stock Ubuntu 20.04 + CentOS 7"),
          ("ubuntu22", "Stock Ubuntu 22.04")]


LINK_RATES = [("25000000", "25 Gbps"), ("100000000", "100 Gbps")]

pc = portal.Context()

pc.defineParameter("dut_type", "DUT node type (node-0)", portal.ParameterType.STRING, NODES[0],
                   legalValues=[(n, n) for n in NODES])

pc.defineParameter("dut_images", "DUT disk image", portal.ParameterType.STRING, "authors",
                   legalValues=IMAGES)

pc.defineParameter("gen_type", "Traffic generator node type (node-1)", portal.ParameterType.STRING,
                   NODES[0], legalValues=[(n, n) for n in NODES])

pc.defineParameter("gen_images", "Generator disk image", portal.ParameterType.STRING, "authors",
                   legalValues=IMAGES)

pc.defineParameter("link_rate", "Experiment link rate", portal.ParameterType.STRING,
                   LINK_RATES[0][0], legalValues=LINK_RATES)

pc.defineParameter("same_switch", "Keep both nodes on one switch",
                   portal.ParameterType.BOOLEAN, True, advanced=True)

pc.defineParameter("gen_public_ip", "Routable control IP on node-1",
                   portal.ParameterType.BOOLEAN, False, advanced=True)

params = pc.bindParameters()


for role, ntype, imgs in (("DUT", params.dut_type, params.dut_images),
                          ("generator", params.gen_type, params.gen_images)):
    if imgs == "authors" and ntype != "xl170":
        pc.reportWarning(portal.ParameterWarning(
            "Authors' images are xl170 snapshots; on %s (%s) CloudLab may refuse to map them. "
            "Use ubuntu22 and switch OS via GRUB if it does." % (ntype, role), []))


if params.same_switch and params.dut_type != params.gen_type:
    pc.reportWarning(portal.ParameterWarning(
        "DUT and generator are different node types; same-switch placement will likely fail. "
        "Disable 'Keep both nodes on one switch' if mapping is refused.", ["same_switch"]))
pc.verifyParameters()


def image_for(choice, role_default):
    if choice == "authors":
        return role_default
    if choice == "ubuntu22":
        return STOCK_NEW
    return STOCK_DUT if role_default is AUTHOR_DUT else STOCK_GEN


request = pc.makeRequestRSpec()

node0 = request.RawPC("node-0")
node0.hardware_type = params.dut_type
node0.disk_image = image_for(params.dut_images, AUTHOR_DUT)
node0.routable_control_ip = True
iface0 = node0.addInterface("interface-0")

node1 = request.RawPC("node-1")
node1.hardware_type = params.gen_type
node1.disk_image = image_for(params.gen_images, AUTHOR_GEN)
if params.gen_public_ip:
    node1.routable_control_ip = True
iface1 = node1.addInterface("interface-1")

link = request.Link("link-0", members=[iface0, iface1])
link.bandwidth = int(params.link_rate)
if params.same_switch:
    link.setNoInterSwitchLinks()

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN,
                 "K2 latency/throughput setup: DUT on %s, T-Rex traffic generator on %s, "
                 "%s link" % (params.dut_type, params.gen_type,
                              dict(LINK_RATES)[params.link_rate]))
request.addTour(tour)

pc.printRequestRSpec(request)
