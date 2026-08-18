"""K2 sigcomm21 artifact CloudLab profile with selectable node type."""
import geni.portal as portal
import geni.rspec.igext as IG
import geni.rspec.emulab

AUTHOR_DUT = "urn:publicid:IDN+utah.cloudlab.us+image+heartbeat-PG0:xl170-centos7-ubuntu20:2"
AUTHOR_GEN = "urn:publicid:IDN+utah.cloudlab.us+image+heartbeat-PG0:xl170-centos7-ubuntu20.node-1:5"
STOCK_DUT = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
STOCK_GEN = "urn:publicid:IDN+emulab.net+image+emulab-ops//CENTOS7-64-STD"
RESTORE_IMG = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"

NODES = ["xl170", "c6525-25g", "sm110p", "r6615", "d7615", "c6525-100g", "c6620", "d760p"]
LINK_BANDWIDTH = 25000000

pc = portal.Context()
pc.defineParameter("node_type", "Node type", portal.ParameterType.STRING, NODES[0],
                   legalValues=[(name, name) for name in NODES])
pc.defineParameter("images", "Disk images", portal.ParameterType.STRING, "authors",
                   legalValues=[("authors", "Authors' images (xl170 only)"),
                                ("stock", "Stock Ubuntu 20.04 + CentOS 7"),
                                ("restore", "Ubuntu 22.04 on both nodes")])
pc.defineParameter("same_switch", "Keep both nodes on one switch",
                   portal.ParameterType.BOOLEAN, True, advanced=True)
pc.defineParameter("gen_public_ip", "Routable control IP on node-1",
                   portal.ParameterType.BOOLEAN, False, advanced=True)
params = pc.bindParameters()

if params.images == "authors" and params.node_type != "xl170":
    pc.reportError(portal.ParameterError(
        "Authors' images are xl170 snapshots; select stock or restore images for %s." % params.node_type,
        ["images", "node_type"]))
pc.verifyParameters()

if params.images == "authors":
    dut_img, gen_img = AUTHOR_DUT, AUTHOR_GEN
elif params.images == "stock":
    dut_img, gen_img = STOCK_DUT, STOCK_GEN
else:
    dut_img, gen_img = RESTORE_IMG, RESTORE_IMG

request = pc.makeRequestRSpec()

node0 = request.RawPC("node-0")
node0.hardware_type = params.node_type
node0.disk_image = dut_img
node0.routable_control_ip = True
iface0 = node0.addInterface("interface-0")

node1 = request.RawPC("node-1")
node1.hardware_type = params.node_type
node1.disk_image = gen_img
if params.gen_public_ip:
    node1.routable_control_ip = True
iface1 = node1.addInterface("interface-1")

link = request.Link("link-0", members=[iface0, iface1])
link.bandwidth = LINK_BANDWIDTH
if params.same_switch:
    link.setNoInterSwitchLinks()

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN,
                 "Traffic generator + DUT setup with %s machines (%s images)" %
                 (params.node_type, params.images))
request.addTour(tour)
pc.printRequestRSpec(request)
