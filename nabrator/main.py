'''
Currently only looks at Daemon Root logs.
'''
import re
import datetime

from nabrator.utils import parser, patterns as pt

# root = "./nABRs/Device/DeviceFilter/1810-2071818"
root = "/Users/puya/dev/avigilon/nabrator/tests/nABRs/Device/ConnectionIssue/1810-2067759"
# root = "./nABRs/Device/ConnectionIssue/1810-2070795"


def table_print(count, devices, outfile, columns=[]):
    # total_drops = packet_drop_counts.sum()
    total_count = sum([count[mac]
                       if mac in devices.index else 0 for mac in count.keys()])

    outfile.write("-"*(57 + 18*len(columns))+"\n")
    for mac, count in count.iteritems():
        # this check is done since device might have been removed e.g.
        # 2018-08-05 04:15:02 WARN  : DataStoreEngine::CleanupVolumes : Device entity 1.0018850100f8.cam00 marked for removal, data cleared.
        if mac in devices.index:
            name = devices.loc[mac]["name"][0:15]
            mfr = devices.loc[mac]["mfr"][0:10]
            model = devices.loc[mac]["model"][0:10]
            descriptor = "{0:15.15} ({1:5.5}-{2:15.15})".format(name,
                                                                mfr, model)
            row = "| {0:35.35}".format(descriptor)
            for column_name in columns:
                column_value = devices.loc[mac][column_name]
                row += " | {0:15.15}".format(column_value)
            row += " | {0:<7} | {1:4.1f}% |\n".format(
                count, count*1.0/total_count*100)
            outfile.write(row)
        elif mac == "server":
            descriptor = "server"
            row = "| {0:35.35}".format("Server")
            for column_name in columns:
                row += " | {0:15.15}".format("NA")
            row += " | {0:<7} | {1:4.1f}% |\n".format(
                count, count*1.0/total_count*100)
            outfile.write(row)
    outfile.write("-"*(57 + 18*len(columns))+"\n")


def escalation(root, outfile):
    outfile.write("Escalation Notes:\n")
    outfile.write("---------------------------------------\n")
    for f in pt.system_info_files:
        file_name_pattern = f["file"]
        files_found = parser.find_files(file_name_pattern, root=root)
        if files_found:
            file_name = files_found[0]
            with open(file_name) as file_handle:
                text_file = file_handle.read()
            start_pos = 0
            for tidbit in f["info"]:
                p = re.compile(tidbit)
                m = p.search(text_file, start_pos)
                if m:
                    start_pos = m.end()
                    descriptor, value = list(m.groupdict().items())[0]
                    outfile.write("{0}: {1}\n".format(descriptor, value))
        else:
            outfile.write("{0} not found.\n".format(file_name_pattern))

    # Find previous ACC Versions:
    admin_panel_root_files = parser.find_files("AdminPanel.Root", root=root)
    acc_version_re = pt.log_components["admin_panel_root"]["acc_version"]
    previous_acc_versions = []
    for file_name in admin_panel_root_files:
        with open(file_name) as fh:
            for line in fh:
                acc_version_match = re.search(acc_version_re, line)
                if acc_version_match:
                    acc_version = acc_version_match.groups()[0]
                    if acc_version not in previous_acc_versions:
                        previous_acc_versions.append(acc_version)

    if previous_acc_versions:
        outfile.write("Previous_ACC_Versions: {0}\n".format(
            previous_acc_versions))
    outfile.write("---------------------------------------\n")


if __name__ == "__main__":
    print("Running nABRator. Please wait...\n")

    with open("result.txt", 'w+') as f:
        f.write(datetime.datetime.now().strftime(pt.datetime)+"\n\n")

    logs = parser.find_files(pt.files["daemon_root"], root)
    devconn_files = parser.find_files(pt.files["devconn"], root)
    devices = parser.parse_devconn(devconn_files)

    f_count = parser.get_count("fatal", logs, devices=devices)
    e_count = parser.get_count("error", logs, devices=devices)
    n_count = parser.get_count("network", logs, devices=devices)

    columns = "mac,ip"

    with open("result.txt", 'a+') as f:
        f.write(
            "------------------------------------------------------------------------------\n")
        escalation(root, f)
        f.write(
            "------------------------------------------------------------------------------\n")
        if n_count.empty:
            f.write("No packet drops found.\n")
            f.write(
                "------------------------------------------------------------------------------\n")
        else:
            f.write("\nPacket drops statistics:\n")
            table_print(n_count, devices, f, columns.split(","))
        if f_count.empty:
            f.write("No FATAL logs found.\n")
            f.write(
                "------------------------------------------------------------------------------\n")
        else:
            f.write("\nFATAL logs statistics:\n")
            table_print(f_count, devices, f, columns.split(","))
        if e_count.empty:
            f.write("No ERROR logs found.\n")
            f.write(
                "------------------------------------------------------------------------------\n")
        else:
            f.write("\nERROR logs statistics:\n")
            table_print(e_count, devices, f, columns.split(","))
    print("Please see results.txt and filtered.txt for output.\n")
