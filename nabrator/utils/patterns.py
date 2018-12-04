files = {
    "daemon_root": r"^Daemon\.Root",
    "daemon_device": r"^Daemon\.Device",
    "daemon_fcp": r"^Daemon\.Fcp",
    "daemon_exception": r"^Daemon",
    "client_root": r"^Client\.Root",
    "client_fcp": r"^Client\.Fcp",
    "client_exception": r"^Client\.Exception",
    "devconn": r"_Avigilon_DeviceConnections_devconn\.cfg$",
    "admin_panel_root": r"AdminPanel.Root",
}

fcp = {
    "CPU Sys": r"^(\d|\d\d|100)%$",
    "CPU Proc": r"^(\d|\d\d|100)%$",
    "Mem Work": r"^\d*$",
    "Mem Virt": r"^\d*$",
}

log_components = {
    "date": r"(?P<date>\d\d\d\d-(0[1-9]|1[12])-(0[1-9]|[12]\d|3[01]))",
    "time": r"(?P<time>(((0|1)\d|2[0-4]):([0-5]\d):([0-5]\d)))",
    "level": r"(?P<level>INFO|WARN|ERROR|FATAL)",
    "admin_panel_root": {
        "acc_version": r" : Daemon Version: (?P<acc_version>\d+\.\d+\.\d+\.\d+)",
    },
}

# note - the ip regex depends on regex group parsing to be from left to right in order to work correctly
ids = {
    "ip": r"((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9]))",
    "mac": r"(((\d|[a-f]){12})|(((\d|[a-f]){2}:){5}(\d|[a-f]){2}))",
}

issues = {
    "network": [
        # {"re": r"Metadata items dropped",
        #          "id": "mac",
        #          "desc": "Overloaded network port"},
        #         {"re": r"MissingPacket",
        #          "id": "ip",
        #          "desc": "Unreliable link"},
        {"re": r"Ping failed \(failure count (?P<ping_fail_count>\d+)\)",
         "id": "mac",  # really id is device_id
         "desc": "Unreliable link"}],
    "db": [],
    "info": [
        {"re": r" INFO  : | WARN  : | ERROR : | FATAL : ",
            "id": "any", "desc": "Information level logs"}
    ],
    "warn": [
        {"re": r" WARN  : | ERROR : | FATAL : ",
            "id": "any", "desc": "Warning level logs"}
    ],
    "error": [
        {"re": r" ERROR : | FATAL : ",
            "id": "any", "desc": "Error level logs"}
    ],
    "fatal": [
        {"re": r" FATAL : ",
            "id": "any", "desc": "Fatal level logs"}
    ],
}

timeline_defs = {
    "ACC_Version": {
        "re": r" : Daemon Version: (?P<acc_version>\d+\.\d+\.\d+\.\d+)",
        "type": "change"
    },
    "Server_UUID": {
        "re": r" : Server UUID is (?P<server_uuid>.+)",
        "type": "change"
    },
    "Initialize_Started": {
        "re": r"\*{9} InitializeLicenseService\(\) \*{9}",
        "type": "occurance"
    },
}


# These are group captures and should be accessed via m.groupdict().items()[0] and not from m.string
# You need to read one file at a time and not one line at a time since information is broken between lines
system_info_files = [
    {
        "file": "ipconf",
        # repeated three times to capture up to three NIC information
        "info": [
            r"Ethernet adapter (?P<Adapter_Name>[^:]+):(?!\s*Media State)",
            r"DHCP Enabled[. ]*: (?P<DHCP_Enabled>Yes|No)",
            r"IPv4 Address[. ]*: (?P<IPv4_Address>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Subnet Mask[. ]*: (?P<Subnet_Mask>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Default Gateway[. ]*: (?P<Default_Gateway>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"DNS Servers[. ]*: (?P<DNS_Servers>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Ethernet adapter (?P<Adapter_Name>[^:]+):(?!\s*Media State)",
            r"DHCP Enabled[. ]*: (?P<DHCP_Enabled>Yes|No)",
            r"IPv4 Address[. ]*: (?P<IPv4_Address>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Subnet Mask[. ]*: (?P<Subnet_Mask>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Default Gateway[. ]*: (?P<Default_Gateway>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"DNS Servers[. ]*: (?P<DNS_Servers>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Ethernet adapter (?P<Adapter_Name>[^:]+):(?!\s*Media State)",
            r"DHCP Enabled[. ]*: (?P<DHCP_Enabled>Yes|No)",
            r"IPv4 Address[. ]*: (?P<IPv4_Address>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Subnet Mask[. ]*: (?P<Subnet_Mask>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"Default Gateway[. ]*: (?P<Default_Gateway>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
            r"DNS Servers[. ]*: (?P<DNS_Servers>((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])))",
        ],
    },
    {
        "file": r"ProgramsList",
        "info": [
            r"(?P<OS_Version>Microsoft Windows.*)",
            # r"Avigilon Control Center Client(\r\n|\r|\n)VersionString: (?P<ACC_Client_Version>.+)"
            # r"Avigilon Control Center Server(\r\n|\r|\n)VersionString: (?P<ACC_Server_Version>.+)"
        ],
    },
    {
        "file": r"QuickInfo",
        "info": [
            r"Tempout files in [A-Z]:\\Users\\[^:]*:: (?P<User_Dir_Tempouts>\d+)",
            r"Tempout files in [A-Z]:\\ProgramData\\Avigilon :: (?P<Program_Data_Tempouts>\d+)",

            r"Avigilon Control Center Client : (?P<ACC_Client_Version>.+)",
            r"Avigilon Control Center Server : (?P<ACC_Server_Version>.+)",
            r"ServiceTag : (?P<Service_Tag>.+)",
            r"\.Net Framework Highest Version:: (?P<Net_Framework_Version>.+)",
        ],
    },
]
# TODO do I need the first tuple element?
# TODO: when you use search (and not fullmatch), use groups()[0] to access the capture.

# This format is used for the datetime module
datetime = "%Y-%m-%d %H:%M:%S"
