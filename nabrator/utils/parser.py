#!/usr/bin/python3
import xml.etree.ElementTree as ET
import csv
import fileinput
import os
import re
from datetime import datetime
from logging import info, warning, error, critical

import pandas as pd

from nabrator.utils import patterns

# definitions
HTTP = 1
HTTPS = 2
RTP = 66


def find_files(ptrn, root="."):
    """
    Starting from root, walks down file tree and compares file names with input type
    Args:
        file_type (string): File type to match
        root (string): root directory to start search. Defaults to "." (optional)

    Returns:
        list: list of matched files
    """
    matched_files = {}

    # TODO remove file_type
    pattern = re.compile(ptrn)

    for (directory_path, directory_names, file_list) in os.walk(root):
        for file_name in file_list:
            if pattern.search(file_name):
                matched_files.setdefault(os.path.abspath(
                    directory_path), []).append(file_name)

    # For now we do not analyse multiple servers separately
    # We flatten all found file lists into the same list

    # for path in matched_files:
    #     print("Found {0} {1} files in {2}".format(len(path), file_type, path))

    # return matched_files

    matched_files_all = []
    for path, files in matched_files.items():
        info("Found {0} {1} files in {2}".format(len(files), ptrn, path))
        for file in files:
            matched_files_all.append(path + "/" + file)

    return matched_files_all


def parse_timelines(timeline_defs, files):
    def get_unfiltered_timelines(timeline_defs, files):
        timelines = {key: [] for key in timeline_defs.keys()}
        with fileinput.input(files) as lines:
            for line in lines:
                date_re = re.compile(patterns.date_time)
                date_m = date_re.search(line)
                if not date_m:
                    continue
                date = date_m.groups()[0]
                line_rest = date_m.string[date_m.end():]
                for timeline_name, timeline_def in timeline_defs.items():
                    timeline_re = re.compile(timeline_def["re"])
                    timeline_m = timeline_re.search(line_rest)
                    if timeline_m:
                        if timeline_def["type"] == "change":
                            value = timeline_m.groups()[0]
                            # timelines.setdefault(
                            #     variable["description"], []).append((date, matched_str))
                        elif timeline_def["type"] == "occurance":
                            value = 1
                            # timelines.setdefault(
                            #     variable["description"], []).append(date)
                        timelines[timeline_name].append((date, value))
        for v in timelines.values():
            v.sort(reverse=True,key=lambda x: datetime.strptime(x[0], patterns.datetime))
        # timelines = {k: v.sort(key=lambda x: x[0]) for k, v in timelines.items()}
        return timelines
    unfiltered_timelines = get_unfiltered_timelines(timeline_defs, files)
    # print(unfiltered_timelines)
    type_lookup = dict(zip(timeline_defs.keys(),
                       [t["type"] for t in timeline_defs.values()]))
    filtered_timelines = {key: [] for key in unfiltered_timelines.keys()}
    for timeline_name, timeline in unfiltered_timelines.items():
        "%Y-%m-%d %H-%M-%S"
        timeline_filtered = []
        timeline_type = type_lookup[timeline_name]
        if timeline_type == "change":
            if len(timeline):
                prev_item = timeline[0]
                # TODO: check against value read from sysinfo
                timeline_filtered.append(prev_item)
                for item in timeline[1:]:
                    if item[1] != prev_item[1]:
                        timeline_filtered.append(item)
                        prev_item = item
        elif timeline_type == "occurance":
            if len(timeline):
                prev_item = timeline[0]
                for item in timeline[1:]:
                    if item[0] == prev_item[0]:
                        prev_item = (prev_item[0], prev_item[1] + 1)
                    else:
                        timeline_filtered.append(prev_item)
                        prev_item = item
                timeline_filtered.append(prev_item)
        filtered_timelines[timeline_name] = timeline_filtered

    return filtered_timelines


def parse_fcp(file_list, fcp_type=""):
    """
    ...
    Args:
        file_list (list): ...
        fcp_type (string): ... (optional)

    Returns:
        DataFrame: ...
    """
    cpu_usage, mem_usage = pd.DataFrame(), pd.DataFrame()

    print("Reading {0} Fcp files".format(fcp_type))

    for file_name in file_list:
        # print("Reading {0}".format(file_name))
        cpu_column_names = ["Date", "CPU Sys", "CPU Proc"]
        mem_column_names = ["Date", "Mem Work", "Mem Virt"]
        with open(file_name) as f:
            column_count = next(f).count(",") + 1
            # print(column_count)
        if column_count == 12:
            cpu_columns, mem_columns = [0, 5, 6], [0, 10, 11]
        else:
            cpu_columns, mem_columns = [0, 6, 7], [0, 11, 12]

        cpu_fcp_df = pd.read_csv(
            file_name, usecols=cpu_columns, parse_dates=True,
            skipinitialspace=True, names=cpu_column_names,
            infer_datetime_format=True, index_col=0, dtype=str)

        mem_fcp_df = pd.read_csv(
            file_name, usecols=mem_columns, parse_dates=True,
            skipinitialspace=True, names=mem_column_names,
            infer_datetime_format=True, index_col=0, dtype=str)

        cpu_usage = cpu_usage.append(cpu_fcp_df, ignore_index=False)
        mem_usage = mem_usage.append(mem_fcp_df, ignore_index=False)

    # print("THIS IS MEM: ", mem_usage['Mem Work'])
    cpu_usage, mem_usage = cpu_usage.sort_index(), mem_usage.sort_index()

    # filter out non-valid cpu usage rows
    cpu_sys_re = re.compile(patterns.fcp["CPU Sys"])
    cpu_proc_re = re.compile(patterns.fcp["CPU Proc"])
    non_valid_rows = []
    for date, (cpu_sys, cpu_proc) in cpu_usage.iterrows():
        if not (bool(cpu_sys_re.fullmatch(cpu_sys)) and
                bool(cpu_proc_re.fullmatch(cpu_proc))):
            non_valid_rows.append(date)
    cpu_usage.drop(non_valid_rows, inplace=True)

    # filter out non-valid memory usage rows
    mem_work_re = re.compile(patterns.fcp["Mem Work"])
    mem_virt_re = re.compile(patterns.fcp["Mem Virt"])
    non_valid_rows = []
    for row in mem_usage.iterrows():
        date, (mem_work, mem_virt) = row
        if not (bool(mem_work_re.fullmatch(mem_work)) and
                bool(mem_virt_re.fullmatch(mem_virt))):
            non_valid_rows.append(date)
    mem_usage.drop(non_valid_rows, inplace=True)

    # print(cpu_usage, mem_usage)

    # convert usage data to usable units
    try:
        cpu_usage['CPU Sys'] = cpu_usage['CPU Sys'].str.rstrip('%').astype(int)
        cpu_usage['CPU Proc'] = cpu_usage['CPU Proc'].str.rstrip(
            '%').astype(int)
        mem_usage['Mem Work'] = mem_usage['Mem Work'].astype(int) / 1000
        mem_usage['Mem Virt'] = mem_usage['Mem Virt'].astype(int) / 1000
    except Exception as e:
        error_msg = "Issue parsing {0} fcp. Type: {1}, Arguments:\n{2!r}"
        print(error_msg.format(fcp_type, type(e).__name__, e.args))

    print("{0} Fcp files have ".format(fcp_type), len(cpu_usage), "CPU lines")
    print("{0} Fcp files have ".format(fcp_type), len(mem_usage), "MEM lines")

    return cpu_usage, mem_usage


def parse_devconn(file_list):
    devices = {}
    # process all devconn files:
    mac_pattern = re.compile(patterns.ids["mac"])
    for file_name in file_list:
        if os.stat(file_name).st_size == 0:
            continue
        tree = ET.parse(file_name)
        root = tree.getroot()
        # process all device entries in each file
        for device_connection in root.iter("DeviceConnection"):
            # read device mac address:
            device_id = device_connection.find("DeviceId").text.lower()
            m_mac = re.search(mac_pattern, device_id)
            if m_mac:
                mac = m_mac.string[m_mac.start():m_mac.end()].replace(":", "")
            else:
                mac = device_connection.find(
                    "PhysicalAddress").text.lower().replace(":", "")
            # read connection type (http or https)
            protocol_type_tag = device_connection.find("ProtocolType")
            # read device ip
            ip_found = False
            if (protocol_type_tag):
                # return the main ip address for device
                for app_endpoint in device_connection.iter("AppEndpoint"):
                    proto_type = int(app_endpoint.find("ProtoType").text)
                    if (proto_type==int(protocol_type_tag.text)):
                        ip = app_endpoint.find("Address").text
                        connection_type = ("Encrypted" if (proto_type == HTTPS) else "Not Encrypted")
                        ip_found = True
                        break
            else:
                # return the http or https ip address for device
                for app_endpoint in device_connection.iter("AppEndpoint"):
                    proto_type = int(app_endpoint.find("ProtoType").text)
                    if proto_type in [HTTP, HTTPS]:
                        ip = app_endpoint.find("Address").text
                        connection_type = ("Encrypted" if (proto_type == HTTPS) else "Not Encrypted")
                        ip_found = True
                        break
            if not ip_found:
                # return first ip address for device
                ip = next(device_connection.iter("AppEndpoint")).find("Address").text
            # read device info
            mfr_tag = device_connection.find("MfrString")
            mfr = mfr_tag.find("Mfr").text
            model = mfr_tag.find("Model").text
            serial = mfr_tag.find("Serial").text
            user_tag = device_connection.find("UserStrings")
            name = user_tag.find("Name").text
            location = user_tag.find("Location").text
            devices[mac] = {"ip": ip, "mac": mac, "connection_type": connection_type,
                            "mfr": mfr, "model": model, "serial": serial,
                            "name": name, "location": location}
    pd_devices = pd.DataFrame.from_dict(devices, orient='index')
    return pd_devices


def get_count(issue, logs, devices):
    """ network connection issue """
    # TODO: break down this function to multiple smaller parts
    # TODO: return a pandas DataFrame instead of a dictionary
    def get_tables(log_objs):
        tables = {}
        # log_ids = [log_obj["id"] for log_obj in log_objs if log_obj["id"] != "mac"]
        # TODO: any value to generalizing to log_ids?
        log_id = "ip"
        id_table = dict(zip(getattr(devices,log_id), devices.mac))
        tables[log_id] = id_table
        return tables
    def trim_id(log_id, id_raw):
        if log_id == "mac":
            return id_raw.replace(":", "").lower()
        else:
            return id_raw.lower()

    # compile lookup tables
    tables = get_tables(patterns.issues[issue])
    count = {}
    with fileinput.input(logs) as lines:
        for line in lines:
            # check against all log objects that indicate network packet
            for log_obj in patterns.issues[issue]:
                log_re = log_obj["re"]
                m_log = re.search(log_re, line)
                # if log line idicates issue
                if m_log:
                    # read device identifier
                    log_id = log_obj["id"]
                    if log_id == "any":
                        m_id = re.search(patterns.ids["mac"], line.lower())
                        if m_id:
                            log_id = "mac"
                        else:
                            m_id = re.search(patterns.ids["ip"], line.lower())
                            if m_id:
                                log_id = "ip"
                            else:
                                log_id = "server"
                                m_id = "server"
                                mac_found = True
                                mac = "server"
                                count.setdefault(mac, 0)
                                count[mac] += 1
                                break
                    else:
                        m_id = re.search(patterns.ids[log_id], line.lower())
                    # if id found
                    if m_id:
                        id_raw = m_id.string[m_id.start():m_id.end()]
                        id = trim_id(log_id, id_raw)
                    else:
                        warning(
                            "Could not read device identifier of type \"{0}\" for log line:\n{1}\n".format(log_id, line))
                        continue
                    # find mac from the device identifier
                    mac_found = False
                    if (log_id=="mac"):
                        mac = id
                        mac_found = bool(mac)
                    elif log_id=="ip":
                        mac = tables["ip"].get(id)
                        mac_found = bool(mac)

                    if (not mac_found):
                        if (id!="0.0.0.0"):
                            # TODO: figure out what is 0.0.0.0 (Null) used for in the logs. e.g. Null IP?
                            # 2018-10-05 07:00:21 WARN  : ? : RTP RX MissingPacket(s) 1 on RtpOverRtsp:0/1/SSRC:1717395308(665d5f6c) from 0.0.0.0/SSRC:3543483746(d3354562) / Thread IoService.TransportCtrl [logNum 74]
                            warning("Could not find mac address for device with \"{0}\"={1} for log line:\n{2}\n".format(log_id, id, line))
                    else:
                        # increment drop count
                        count.setdefault(mac, 0)
                        count[mac] += 1
                    break    
    sr_count = pd.Series(count)
    return sr_count.sort_values(ascending=False)


