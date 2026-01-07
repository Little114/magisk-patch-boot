# @酷安Little114
# 感谢我自己写了这个脚本方便我自己也方便了大家,希望大家多多支持这个项目,在电脑上修补boot是真的方便好用!!!
import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_boot_patch import BootPatcher
from cli_utils import (
    retTypeAndMachine, 
    parseMagiskApk, 
    getMagiskApkVersion,
    convertVercode2Ver
)

VERSION = "4.1.0-cli"
AUTHOR = "Little"

class MagiskPatcherCLI:
    def __init__(self):
        self.setup_parser()
        
    def setup_parser(self):
        self.parser = argparse.ArgumentParser(
            description=f'Magisk Patcher CLI v{VERSION} - 命令行版Magisk boot镜像修补工具',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f'''
示例用法:
  # 基本用法
  python magiskpatcher_cli.py boot.img --magisk magisk.apk
  
  # 指定架构
  python magiskpatcher_cli.py boot.img --magisk magisk.apk --arch arm64
  
  # 禁用验证和加密
  python magiskpatcher_cli.py boot.img --magisk magisk.apk --no-verity --no-encrypt
  
  # 修补recovery镜像
  python magiskpatcher_cli.py recovery.img --magisk magisk.apk --recovery
  
作者: {AUTHOR}
            '''
        )
        
        
        self.parser.add_argument('boot_image', help='要修补的boot镜像文件路径')
        
        
        self.parser.add_argument('--magisk', '-m', required=True, 
                               help='Magisk APK文件路径')
        self.parser.add_argument('--arch', '-a', choices=['arm', 'arm64', 'x86', 'x86_64'], 
                               default='arm64', help='目标设备架构 (默认: arm64)')
        self.parser.add_argument('--output', '-o', 
                               help='输出文件路径 (默认: patched_boot.img)')
        
        
        self.parser.add_argument('--no-verity', action='store_false', dest='keep_verity',
                                help='禁用dm-verity验证')
        self.parser.add_argument('--no-encrypt', action='store_false', dest='keep_forceencrypt',
                                help='禁用强制加密')
        self.parser.add_argument('--patch-vbmeta', action='store_true', 
                               help='修补vbmeta标志')
        self.parser.add_argument('--recovery', action='store_true',
                               help='修补recovery镜像而不是boot镜像')
        self.parser.add_argument('--legacy-sar', action='store_true',
                               help='传统SAR设备支持')
        
        
        self.parser.add_argument('--verbose', '-v', action='store_true',
                               help='详细输出模式')
        self.parser.add_argument('--version', action='version', 
                               version=f'Magisk Patcher CLI v{VERSION}')
    
    def run(self):

        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(0)
            
        args = self.parser.parse_args()
        
        
        print("正在清理之前的临时文件...")
        temp_files = ["new-boot.img", "stock_boot.img", "ramdisk.cpio", "ramdisk.cpio.orig", 
                     "kernel", "config", "debug_nt", "magisk32", "magisk64", "magiskinit", "stub.apk"
                     ,"config.orig","cpio","magisk32.xz","magisk64.xz","stub.xz"]
        for temp_file in temp_files:
            if os.path.isfile(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"删除 {temp_file}")
                except Exception as e:
                    print(f"无法删除 {temp_file}: {e}")
        print("启动清理完成")
        
        
        import logging
        if args.verbose:
            logging.basicConfig(level=logging.INFO, format='%(message)s')
        else:
            logging.basicConfig(level=logging.WARNING, format='%(message)s')
        
        print(f"=== Magisk Patcher CLI v{VERSION} ===")
        print(f"作者: {AUTHOR}")
        print("-" * 50)
        
        
        if not os.path.isfile(args.boot_image):
            print(f"错误: boot镜像文件不存在: {args.boot_image}")
            sys.exit(1)
            
        if not os.path.isfile(args.magisk):
            print(f"错误: Magisk APK文件不存在: {args.magisk}")
            sys.exit(1)
        
        
        os_type, arch = retTypeAndMachine()
        print(f"系统环境: {os_type} {arch}")
        print(f"目标架构: {args.arch}")
        
        
        magisk_version = getMagiskApkVersion(args.magisk)
        if magisk_version:
            version_str = convertVercode2Ver(magisk_version)
            
            if isinstance(version_str, bytes):
                try:
                    version_str = version_str.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        version_str = version_str.decode('latin-1')
                    except:
                        version_str = str(version_str)
            print(f"Magisk版本: {version_str}")
        else:
            print("警告: 无法检测Magisk版本，可能不是有效的Magisk APK")
        
        
        print("正在提取Magisk文件...")
        parseMagiskApk(args.magisk, arch=args.arch, log=sys.stdout)
        
        
        if os_type == 'windows':
            
            magiskboot_path = "magiskboot.exe"
            if not os.path.isfile(magiskboot_path):
                
                magiskboot_path = os.path.join("bin", "windows", arch, "magiskboot.exe")
                if not os.path.isfile(magiskboot_path):
                    print(f"错误: 找不到magiskboot工具")
                    print("请确保当前目录或bin/windows/目录下有magiskboot.exe文件")
                    sys.exit(1)
        else:
            magiskboot_path = "bin/magiskboot"
            if not os.path.isfile(magiskboot_path):
                print("警告: 找不到magiskboot工具，将从APK中提取...")
        
        
        patcher = BootPatcher(
            magiskboot_path,
            keep_verity=args.keep_verity,
            keep_forceencrypt=args.keep_forceencrypt,
            patchvbmeta_flag=args.patch_vbmeta,
            recovery_mode=args.recovery,
            legacysar=args.legacy_sar,
            log=sys.stdout
        )
        
        
        print("\n开始修补boot镜像...")
        success = patcher.patch(args.boot_image)
        
        if success:
            output_file = args.output or "magisk_boot.img"
            if os.path.isfile("new-boot.img"):
                
                if os.path.isfile(output_file):
                    try:
                        os.remove(output_file)
                        print(f"删除已存在的输出文件: {output_file}")
                    except Exception as e:
                        print(f"无法删除已存在的输出文件 {output_file}: {e}")
                
                os.rename("new-boot.img", output_file)
                print(f"\n修补完成! 输出文件: {output_file}")
            else:
                print("\n修补完成! 输出文件: new-boot.img")
            
            # 清理临时文件，只保留magisk_boot.img
            print("正在清理临时文件...")
            temp_files = ["new-boot.img", "stock_boot.img", "ramdisk.cpio", "ramdisk.cpio.orig", 
                         "kernel", "config", "debug_nt", "magisk32", "magisk64", "magiskinit", "stub.apk"]
            for temp_file in temp_files:
                if os.path.isfile(temp_file):
                    try:
                        os.remove(temp_file)
                        print(f"删除 {temp_file}")
                    except Exception as e:
                        print(f"无法删除 {temp_file}: {e}")
            print("临时文件清理完成")
            print("请在脚本目录中寻找magisk_boot.img")
        else:
            print("\n修补失败!")
            sys.exit(1)

def find_magisk_apk():
    
    apk_patterns = [
        "*.apk",
        "magisk*.apk",
        "*magisk*.apk",
        "Kitsune*.apk",
        "Alpha*.apk",
        "Delta*.apk"
    ]
    
    for pattern in apk_patterns:
        for file in Path(".").glob(pattern):
            if file.is_file():
                return str(file)
    
    return None

def auto_patch_with_drag_drop(boot_image_path):
    
    print("=== Magisk Patcher CLI 快速模式 ===")
    print("检测到拖放文件:", boot_image_path)
    print("正在查找Magisk APK文件...")
    
    
    magisk_apk = find_magisk_apk()
    if not magisk_apk:
        print("错误: 在当前目录中找不到Magisk APK文件")
        print("请确保目录中包含以下文件之一:")
        print("  - magisk.apk")
        print("  - Kitsune Mask*.apk")
        print("  - Alpha*.apk")
        print("  - Delta*.apk")
        print("  - 或其他Magisk APK文件")
        input("按回车键退出...")
        sys.exit(1)
    
    print(f"找到Magisk APK: {magisk_apk}")

    arch = "arm64" 
    print(f"使用默认架构: {arch}")
    
    
    sys.argv = [sys.argv[0], boot_image_path, "--magisk", magisk_apk, "--arch", arch]
    
    
    cli = MagiskPatcherCLI()
    cli.run()
    
    
    input("\n修补完成! 按回车键退出...")

def main():
    
    try:
        
        if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
            boot_file = sys.argv[1]
            
            if boot_file.lower().endswith(('.img', '.bin', '.boot', '.recovery')):
                auto_patch_with_drag_drop(boot_file)
                return
        
        
        cli = MagiskPatcherCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        if '--verbose' in sys.argv or '-v' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
