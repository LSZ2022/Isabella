import ftplib
import nmap
import socket
import requests
from speech_engine import SpeechEngine
from bs4 import BeautifulSoup

class ServerSecurityChecker:
    def __init__(self, speak):
        self.speak = speak

    def CheckServerSecurity(self, target_ip):
        results = {
            "target": target_ip,
            "open_ports": [],
            "vulnerabilities": [],
            "security_risks": [],
            "recommendations": []
        }
        try:
            print("Starting port scanning...")
            open_ports = self.port_scan(target_ip)
            results["open_ports"] = open_ports
            print(f"Open ports found: {', '.join(map(str, open_ports))}")
            print("Starting service identification...")
            services = self.identify_services(target_ip, open_ports)
            results["services"] = services
            print(f"Identified services: {services}")
            print("Starting vulnerability scanning...")
            vulnerabilities = self.scan_vulnerabilities(target_ip, services)
            results["vulnerabilities"] = vulnerabilities
            print("Starting web application security testing...")
            web_vulns = self.web_security_test(f"http://{target_ip}")
            results["vulnerabilities"].extend(web_vulns)
            print("Performing security risk assessment...")
            risks, recommendations = self.assess_security_risks(results)
            results["security_risks"] = risks
            results["recommendations"] = recommendations
            report = self.generate_security_report(results)
            self.speak(report)
            return results
        except Exception as e:
            print(f"Error occurred during security scan: {str(e)}")
            self.speak("Security scan failed")
            return None

    def port_scan(self, target_ip):
        try:
            nm = nmap.PortScanner()
            nm.scan(target_ip, arguments='-T4 -F')
            open_ports = []
            for host in nm.all_hosts():
                if 'tcp' in nm[host]:
                    for port in nm[host]['tcp']:
                        if nm[host]['tcp'][port]['state'] == 'open':
                            open_ports.append(port)
            return open_ports
        except:
            return self.basic_port_scan(target_ip)

    def basic_port_scan(self, target_ip, ports=[21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3389, 8080]):
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((target_ip, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        return open_ports

    def identify_services(self, target_ip, ports):
        services = {}
        try:
            nm = nmap.PortScanner()
            for port in ports:
                nm.scan(target_ip, str(port), arguments='-sV')
                for host in nm.all_hosts():
                    if 'tcp' in nm[host] and port in nm[host]['tcp']:
                        service_info = nm[host]['tcp'][port]
                        services[port] = {
                            "name": service_info.get('name', 'unknown'),
                            "product": service_info.get('product', ''),
                            "version": service_info.get('version', ''),
                            "cpe": service_info.get('cpe', '')
                        }
        except:
            default_services = {
                21: "FTP",
                22: "SSH",
                23: "Telnet",
                25: "SMTP",
                80: "HTTP",
                443: "HTTPS",
                3389: "RDP"
            }
            for port in ports:
                services[port] = {"name": default_services.get(port, "Unknown")}
        return services

    def scan_vulnerabilities(self, target_ip, services):
        vulnerabilities = []
        for port, service in services.items():
            service_name = service.get("name", "").lower()
            version = service.get("version", "")
            if port == 21:
                try:
                    ftp = ftplib.FTP(target_ip, timeout=3)
                    ftp.login()
                    vulnerabilities.append({
                        "port": port,
                        "service": "FTP",
                        "severity": "Medium",
                        "description": "FTP anonymous access is enabled",
                        "recommendation": "Disable FTP anonymous access or use SFTP instead"
                    })
                    ftp.quit()
                except:
                    pass
            if port in [80, 443] and service_name == "http":
                if "Apache" in service.get("product", "") and "2.2" in version:
                    vulnerabilities.append({
                        "port": port,
                        "service": "HTTP",
                        "severity": "High",
                        "description": f"Detected outdated Apache version: {version}",
                        "recommendation": "Upgrade to the latest version of Apache HTTP Server"
                    })
            if port == 445:
                vulnerabilities.append({
                    "port": port,
                    "service": "SMB",
                    "severity": "Critical",
                    "description": "SMB service is open and may be vulnerable to attacks such as EternalBlue",
                    "recommendation": "Disable SMBv1 or ensure the system is patched"
                })
        return vulnerabilities

    def web_security_test(self, url):
        vulnerabilities = []
        try:
            response = requests.get(url)
            headers = response.headers
            if 'X-Content-Type-Options' not in headers:
                vulnerabilities.append({
                    "type": "Web Security",
                    "severity": "Low",
                    "description": "缺少X-Content-Type-Options头",
                    "recommendation": "添加 'X-Content-Type-Options: nosniff' 头"
                })
            if 'X-Frame-Options' not in headers:
                vulnerabilities.append({
                    "type": "Web Security",
                    "severity": "Medium",
                    "description": "缺少X-Frame-Options头",
                    "recommendation": "添加 'X-Frame-Options: SAMEORIGIN' 头"
                })
        except Exception as e:
            print(f"Error during web security test: {str(e)}")
        return vulnerabilities

    def assess_security_risks(self, results):
        risks = []
        recommendations = []
        # 这里可以根据具体的漏洞情况进行风险评估和建议生成
        for vuln in results["vulnerabilities"]:
            risks.append(vuln["description"])
            recommendations.append(vuln["recommendation"])
        return risks, recommendations

    def generate_security_report(self, results):
        report = f"Security report for {results['target']}:\n"
        report += f"Open ports: {', '.join(map(str, results['open_ports']))}\n"
        report += "Vulnerabilities:\n"
        for vuln in results["vulnerabilities"]:
            report += f"  - {vuln['description']} (Severity: {vuln['severity']})\n"
            report += f"    Recommendation: {vuln['recommendation']}\n"
        report += "Security risks:\n"
        for risk in results["security_risks"]:
            report += f"  - {risk}\n"
        report += "Recommendations:\n"
        for rec in results["recommendations"]:
            report += f"  - {rec}\n"
        return report