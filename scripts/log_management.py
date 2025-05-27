#!/usr/bin/env python3
"""
Log Management Script for Invoice Management System
==================================================

This script provides utilities for managing, viewing, and analyzing logs
from both the application and Docker containers.
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime, timedelta
import glob
import gzip
from collections import defaultdict

class LogManager:
    """Comprehensive log management for the invoice system."""
    
    def __init__(self, logs_dir="logs"):
        self.logs_dir = logs_dir
        self.ensure_logs_dir()
    
    def ensure_logs_dir(self):
        """Ensure logs directory exists."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            print(f"Created logs directory: {self.logs_dir}")
    
    def list_log_files(self):
        """List all available log files."""
        print("\n📁 Available Log Files:")
        print("=" * 50)
        
        # Application logs
        app_logs = glob.glob(os.path.join(self.logs_dir, "*.log*"))
        if app_logs:
            print("\n🔧 Application Logs:")
            for log_file in sorted(app_logs):
                size = os.path.getsize(log_file)
                size_mb = size / (1024 * 1024)
                mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                print(f"  • {os.path.basename(log_file)} ({size_mb:.1f}MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Container logs (if available)
        try:
            containers = subprocess.check_output(
                ["docker", "ps", "--format", "{{.Names}}"], 
                text=True
            ).strip().split('\n')
            
            if containers and containers[0]:
                print("\n🐳 Container Logs:")
                for container in containers:
                    if container.startswith('azure-invoice-'):
                        print(f"  • {container}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("\n🐳 Container Logs: Docker not available")
    
    def tail_logs(self, log_type="app", lines=50, follow=False):
        """Tail application or container logs."""
        if log_type == "app":
            log_file = os.path.join(self.logs_dir, "invoice_app.log")
            if not os.path.exists(log_file):
                print(f"❌ Log file not found: {log_file}")
                return
            
            cmd = ["tail"]
            if follow:
                cmd.append("-f")
            cmd.extend(["-n", str(lines), log_file])
            
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                print("\n👋 Stopped following logs")
        
        elif log_type.startswith("container:"):
            container_name = log_type.split(":", 1)[1]
            cmd = ["docker", "logs"]
            if follow:
                cmd.append("-f")
            cmd.extend(["--tail", str(lines), container_name])
            
            try:
                subprocess.run(cmd)
            except (subprocess.CalledProcessError, KeyboardInterrupt):
                print(f"\n👋 Stopped following logs for {container_name}")
    
    def analyze_errors(self, hours=24):
        """Analyze recent errors from logs."""
        error_log = os.path.join(self.logs_dir, "errors.log")
        
        if not os.path.exists(error_log):
            print("❌ No error log found")
            return
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        errors_by_type = defaultdict(int)
        recent_errors = []
        
        try:
            with open(error_log, 'r') as f:
                for line in f:
                    try:
                        # Parse timestamp
                        timestamp_str = line.split(' - ')[0]
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if timestamp > cutoff_time:
                            recent_errors.append(line.strip())
                            
                            # Categorize error
                            if "AI" in line:
                                errors_by_type["AI Services"] += 1
                            elif "Redis" in line or "redis" in line:
                                errors_by_type["Redis"] += 1
                            elif "Database" in line or "Cosmos" in line:
                                errors_by_type["Database"] += 1
                            elif "Network" in line or "Connection" in line:
                                errors_by_type["Network"] += 1
                            else:
                                errors_by_type["Application"] += 1
                    
                    except (ValueError, IndexError):
                        continue
        
        except Exception as e:
            print(f"❌ Error reading error log: {e}")
            return
        
        print(f"\n🔍 Error Analysis (Last {hours} hours)")
        print("=" * 50)
        
        if not recent_errors:
            print("✅ No errors found in the specified time period!")
            return
        
        print(f"\n📊 Error Summary:")
        for error_type, count in sorted(errors_by_type.items()):
            print(f"  • {error_type}: {count} errors")
        
        print(f"\n📝 Recent Errors (Last 5):")
        for error in recent_errors[-5:]:
            print(f"  {error}")
    
    def generate_log_report(self, output_file=None):
        """Generate a comprehensive log report."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.logs_dir, f"log_report_{timestamp}.txt")
        
        with open(output_file, 'w') as f:
            f.write("Invoice Management System - Log Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # System info
            f.write("System Information:\n")
            f.write("-" * 20 + "\n")
            try:
                uptime = subprocess.check_output(["uptime"], text=True).strip()
                f.write(f"System Uptime: {uptime}\n")
            except:
                f.write("System Uptime: Not available\n")
            
            # Log file sizes
            f.write("\nLog Files:\n")
            f.write("-" * 10 + "\n")
            for log_file in glob.glob(os.path.join(self.logs_dir, "*.log")):
                size_mb = os.path.getsize(log_file) / (1024 * 1024)
                f.write(f"{os.path.basename(log_file)}: {size_mb:.1f}MB\n")
            
            # Container status
            f.write("\nContainer Status:\n")
            f.write("-" * 16 + "\n")
            try:
                containers = subprocess.check_output(
                    ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], 
                    text=True
                ).strip()
                f.write(containers + "\n")
            except:
                f.write("Docker information not available\n")
        
        print(f"📊 Log report generated: {output_file}")
    
    def cleanup_old_logs(self, days=30):
        """Clean up log files older than specified days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        cleaned_files = []
        
        for log_file in glob.glob(os.path.join(self.logs_dir, "*.log.*")):
            try:
                mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if mod_time < cutoff_time:
                    os.remove(log_file)
                    cleaned_files.append(log_file)
            except Exception as e:
                print(f"⚠️ Could not remove {log_file}: {e}")
        
        if cleaned_files:
            print(f"🧹 Cleaned up {len(cleaned_files)} old log files:")
            for file in cleaned_files:
                print(f"  • {os.path.basename(file)}")
        else:
            print(f"✅ No log files older than {days} days found")
    
    def export_container_logs(self):
        """Export all container logs to files."""
        try:
            containers = subprocess.check_output(
                ["docker", "ps", "--format", "{{.Names}}"], 
                text=True
            ).strip().split('\n')
            
            exported = []
            for container in containers:
                if container.startswith('azure-invoice-'):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = os.path.join(self.logs_dir, f"{container}_{timestamp}.log")
                    
                    try:
                        with open(output_file, 'w') as f:
                            subprocess.run(
                                ["docker", "logs", container],
                                stdout=f,
                                stderr=subprocess.STDOUT
                            )
                        exported.append(output_file)
                    except Exception as e:
                        print(f"⚠️ Could not export logs for {container}: {e}")
            
            if exported:
                print(f"📤 Exported container logs:")
                for file in exported:
                    print(f"  • {os.path.basename(file)}")
            else:
                print("❌ No container logs exported")
                
        except Exception as e:
            print(f"❌ Error exporting container logs: {e}")

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Invoice Management System Log Manager")
    parser.add_argument("--logs-dir", default="logs", help="Logs directory path")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    subparsers.add_parser("list", help="List all log files")
    
    # Tail command
    tail_parser = subparsers.add_parser("tail", help="Tail logs")
    tail_parser.add_argument("--type", default="app", help="Log type (app, container:name)")
    tail_parser.add_argument("--lines", type=int, default=50, help="Number of lines to show")
    tail_parser.add_argument("-f", "--follow", action="store_true", help="Follow log output")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze errors")
    analyze_parser.add_argument("--hours", type=int, default=24, help="Hours to analyze")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate log report")
    report_parser.add_argument("--output", help="Output file path")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old logs")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Days to keep")
    
    # Export command
    subparsers.add_parser("export", help="Export container logs")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    log_manager = LogManager(args.logs_dir)
    
    if args.command == "list":
        log_manager.list_log_files()
    elif args.command == "tail":
        log_manager.tail_logs(args.type, args.lines, args.follow)
    elif args.command == "analyze":
        log_manager.analyze_errors(args.hours)
    elif args.command == "report":
        log_manager.generate_log_report(args.output)
    elif args.command == "cleanup":
        log_manager.cleanup_old_logs(args.days)
    elif args.command == "export":
        log_manager.export_container_logs()

if __name__ == "__main__":
    main() 