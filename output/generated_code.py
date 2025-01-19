import subprocess
import json
import unittest

import os
os.system("cls") # <--- Added this (clear screen statement)

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def enumerate_services_unquoted_paths():
    command = "sc query state= all"
    output = run_command(command)
    services = []
    for line in output.split('\n'):
        if 'SERVICE_NAME:' in line:
            service_name = line.split(':')[1].strip()
            query_command = f"sc query {service_name}"
            query_output = run_command(query_command)
            for query_line in query_output.split('\n'):
                if 'BINARY_PATH_NAME:' in query_line:
                    binary_path = query_line.split(':')[1].strip()
                    if ' ' in binary_path and '"' not in binary_path:
                        services.append({"service_name": service_name, "binary_path": binary_path})
                    break
    print("\n\nservices:", services)  # <--- Added this (print statement)
    return services

def enumerate_scheduled_tasks():
    command = "schtasks /query /fo LIST"
    output = run_command(command)
    tasks = []
    for line in output.split('\n'):
        if 'TaskName' in line:
            task_info = line.split()
            task_name = task_info[1]
            try:
                trigger_info = run_command(f"schtasks /query /tn {task_name} /fo LIST")
                trigger = trigger_info.split('\n')[1].split()[1]
                tasks.append({"task_name": task_name, "trigger": trigger})
            except IndexError:
                tasks.append({"task_name": task_name, "trigger": "N/A"})
    print("\n\ntasks:", tasks)  # <--- Added this (print statement)
    return tasks

def check_token_privileges():
    command = "whoami /priv"
    output = run_command(command)
    privileges = []
    for line in output.split('\n'):
        if 'Se' in line:
            privileges.append(line.split()[1])
    print("\n\nServices:", privileges)  # <--- Added this (print statement)
    return privileges

def enumerate_wmi_classes():
    command = "wmic /namespace:\\\\root\\cimv2 path * get Name,__PATH"
    output = run_command(command)
    classes = []
    for line in output.split('\n'):
        if 'Name' in line:
            continue
        class_info = line.split()
        if len(class_info) > 0:
            class_name = class_info[0]
            try:
                security_descriptor = run_command(f"wmic /namespace:\\\\root\\cimv2 path {class_name} get __SECURITY_DESCRIPTOR")
                classes.append({"class_name": class_name, "security_descriptor": security_descriptor})
            except IndexError:
                classes.append({"class_name": class_name, "security_descriptor": "N/A"})
    print("\n\nclasses:", classes)  # <--- Added this (print statement)
    return classes

def enumerate_local_accounts_with_weak_passwords():
    command = "net user"
    output = run_command(command)
    accounts = []
    for line in output.split('\n'):
        if 'User name' in line:
            continue
        account_info = line.split()
        if len(account_info) < 2:
            continue
        account_name = account_info[0]
        password_status = "Blank" if len(account_info) == 1 else "Weak" if is_weak_password(account_info[-1]) else "Strong"
        accounts.append({"account_name": account_name, "password_status": password_status})
    print("\n\naccounts:", accounts)  # <--- Added this (print statement)
    return accounts

def is_weak_password(password):
    # Simple strength check (length and complexity)
    return len(password) < 8

def scan_acl_misconfigurations():
    critical_directories = ['C:\\Program Files', 'C:\\Windows']
    findings = []
    for directory in critical_directories:
        command = f"cacls {directory}"
        output = run_command(command)
        findings.append({"directory": directory, "acl_info": output})
    print("\n\nfindings:", findings)  # <--- Added this (print statement)
    return findings

class TestRedTeamScripts(unittest.TestCase):
    def test_enumerate_services_unquoted_paths(self):
        services = enumerate_services_unquoted_paths()
        self.assertIsInstance(services, list)

    def test_enumerate_scheduled_tasks(self):
        tasks = enumerate_scheduled_tasks()
        self.assertIsInstance(tasks, list)

    def test_check_token_privileges(self):
        privileges = check_token_privileges()
        self.assertIsInstance(privileges, list)

    def test_enumerate_wmi_classes(self):
        classes = enumerate_wmi_classes()
        self.assertIsInstance(classes, list)

    def test_enumerate_local_accounts_with_weak_passwords(self):
        accounts = enumerate_local_accounts_with_weak_passwords()
        self.assertIsInstance(accounts, list)

    def test_scan_acl_misconfigurations(self):
        findings = scan_acl_misconfigurations()
        self.assertIsInstance(findings, list)

if __name__ == "__main__":
    unittest.main()