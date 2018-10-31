import os
#import pytest
import pexpect
import sys

TFTP_DIR = "/ws/jliang/tftpd"
DIR_PREFIX = "/ws/jliang/projects/2018.1/xilinx-zcu102-2018.1/"
DTB_PMU_HW = DIR_PREFIX + "images/linux/zynqmp-qemu-multiarch-pmu.dtb"
DTB_HW = DIR_PREFIX + "images/linux/zynqmp-qemu-multiarch-arm.dtb"
DTB = DIR_PREFIX + "/pre-built/linux/images/system.dtb"
R5_ELF = "/ws/jliang/tftpd/rpmsg-ehco.out"
ATF = DIR_PREFIX + "pre-built/linux/images/bl31.elf"
UBOOT_ELF = DIR_PREFIX + "pre-built/linux/images/u-boot.elf"
PMU_ROM= DIR_PREFIX + "pre-built/linux/images/pmu_rom_qemu_sha3.elf"
PMU_ELF = DIR_PREFIX + "pre-built/linux/images/pmufw.elf"
MACHINE_FILE_DIR = "openamp-qemu-zcu102.machinefile"
REMOTEPORT_FILE = MACHINE_FILE_DIR + "/qemu-rport-_pmu@0"
RPU_FW = "/ws/jliang/tftpd/rpmsg-echo.out"
LINUX_PROMPT="~\#"

def launch_linux_uboot(qemu):
    qemu.expect("U-Boot ")
    ret = qemu.expect(["ZynqMP>", "BOOTP broadcast"])
    if ret == 1:
        qemu.send('\003')
        qemu.expect("ZynqMP>")
    qemu.send("setenv serverip 10.0.2.2\n")
    qemu.expect("ZynqMP>");
    qemu.send("dhcp\n")
    qemu.expect("ZynqMP>");
    qemu.send("tftpb 80000 Image; tftpb 10000000 rootfs.cpio.ub;\n")
    qemu.expect("ZynqMP>")
    qemu.send("tftpb 14000000 system.dtb;\n")
    qemu.expect("ZynqMP>")
    qemu.send("booti 80000 10000000 14000000\n")
    qemu.expect("login:", timeout=180)
    qemu.send("root\n")
    qemu.expect(LINUX_PROMPT)
    qemu.send("ifdown eth0\n")
    qemu.expect(LINUX_PROMPT)
    qemu.send("ifup eth0\n")
    qemu.expect(LINUX_PROMPT)

def linux_tftp_file(qemu, src, dest):
    qemu.send("tftp -g 10.0.2.2 -l " + dest + " -r " + src + "\n")
    qemu.expect(LINUX_PROMPT)

def launch_pmu_qemu():
    rport_dir = os.path.dirname(REMOTEPORT_FILE)
    if not os.path.exists(rport_dir):
        os.makedirs(rport_dir)
    qemu_cmd = ("qemu-system-microblazeel -M microblaze-fdt " +
                "-serial mon:stdio -serial /dev/null -display none " +
                "-kernel " + PMU_ROM +
                " -device loader,file=" + PMU_ELF +
                " -hw-dtb " + DTB_PMU_HW +
                " -machine-path " + MACHINE_FILE_DIR +
                " -device loader,addr=0xfd1a0074,data=0x1011003,data-len=4" +
                " -device loader,addr=0xfd1a007C,data=0x1010f03,data-len=4")
    qemu = pexpect.spawn("bash", logfile=sys.stdout);
    qemu.expect("\$")
    qemu.send(qemu_cmd +"\n")
    qemu.expect("qemu-system-microblazeel:")
    return qemu

def launch_linux_qemu():
    qemu = pexpect.spawn("bash", logfile=sys.stdout, timeout=10)
    qemu_cmd = ("qemu-system-aarch64 -M arm-generic-fdt " +
                " -serial mon:stdio -serial /dev/null -display none " +
                " -device loader,file=" + ATF + ",cpu-num=0 " +
                " -device loader,file=" + UBOOT_ELF +
                " -gdb tcp::9000 " + " -dtb " + DTB +
                " -net nic -net nic -net nic -net nic,vlan=1" +
                " -net user,vlan=1,tftp=" + TFTP_DIR +
                " -hw-dtb " + DTB_HW + " -machine-path " + MACHINE_FILE_DIR +
                " -global xlnx,zynqmp-boot.cpu-num=0,4 " +
                " -global xlnx,zynqmp-boot.use-pmufw=true -m 4G")
    qemu.send(qemu_cmd + "\n")
    launch_linux_uboot(qemu)
    return qemu

def launch_linux_baremetal_qemu():
    qemu = pexpect.spawn("bash", logfile=sys.stdout, timeout=10)
    qemu_cmd = ("qemu-system-aarch64 -M arm-generic-fdt " +
                " -serial mon:stdio -serial /dev/null -display none " +
                " -device loader,file=" + ATF + ",cpu-num=0 " +
                " -device loader,file=" + RPU_FW + ",cpu-num=4 " +
                " -device loader,file=" + UBOOT_ELF +
                " -gdb tcp::9000 " + " -dtb " + DTB +
                " -net nic -net nic -net nic -net nic,vlan=1" +
                " -hw-dtb " + DTB_HW + " -machine-path " + MACHINE_FILE_DIR +
                " -global xlnx,zynqmp-boot.cpu-num=0,4 " +
                " -global xlnx,zynqmp-boot.use-pmufw=true -m 4G")
    qemu.send(qemu_cmd + "\n")
    return qemu

def test_kernel_load_rpmsg_app_qemu():
    rapp="rpmsg-echo.out"
    qemu_mb = launch_pmu_qemu()
    qemu_linux = launch_linux_qemu()
    qemu_linux.send("mkdir -p /lib/firmware\n")
    qemu_linux.expect(LINUX_PROMPT)
    linux_tftp_file(qemu_linux, rapp, "/lib/firmware/" + rapp)
    qemu_linux.send("ptest-runner rpmsg-echo-test\n")
    ret = qemu_linux.expect(["PASS:", "FAIL", "STOP"], timeout=120)
    assert ret == 0
