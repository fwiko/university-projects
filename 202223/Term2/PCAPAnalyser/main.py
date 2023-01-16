import os
import re
import sys
import struct
import datetime
import mimetypes
import hashlib
import gzip
import io
import csv

# CONSTANTS -------------------------------------------------------------------

# all possible PCAP data link types - taken from https://www.tcpdump.org/linktypes.html
DATA_LINK_TYPES = {
    1: "ETHERNET",
    3: "AX25",
    6: "IEEE802.5",
    7: "ARCNET BSD",
    8: "SLIP",
    9: "PPP",
    10: "FDDI",
    50: "PPP HDLC",
    51: "PPP ETHER",
    100: "ATM RFC1483",
    101: "RAW",
    104: "C HDLC",
    105: "IEEE802.11",
    107: "FRELAY",
    108: "LOOP",
    113: "LINUX SLL",
    114: "LTALK",
    117: "PFLOG",
    119: "IEEE802.11 PRISM",
    122: "IP OVER FC",
    123: "SUNATM",
    127: "IEEE802.11 RADIOTAP",
    129: "ARCNET LINUX",
    138: "APPLE IP OVER IEEE1394",
    139: "MTP2 WITH PHDR",
    140: "MTP2",
    141: "MTP3",
    142: "SCCP",
    143: "DOCSIS",
    144: "LINUX IRDA",
    147: "USER0",
    148: "USER1",
    149: "USER2",
    150: "USER3",
    151: "USER4",
    152: "USER5",
    153: "USER6",
    154: "USER7",
    155: "USER8",
    156: "USER9",
    157: "USER10",
    158: "USER11",
    159: "USER12",
    160: "USER13",
    161: "USER14",
    162: "USER15",
    163: "IEEE802.11 AVS",
    165: "BACNET MS/TP",
    166: "PPP PPPD",
    169: "GPRS LLC",
    170: "GPF T",
    171: "GPF F",
    177: "LINUX LAPD",
    182: "MFR",
    187: "BLUETOOTH HCI H4",
    189: "USB LINUX",
    192: "PPI",
    195: "IEEE802.15.4 WITH FCS",
    196: "SITA",
    197: "ERF",
    201: "BLUETOOTH HCI H4 WITH PHDR",
    202: "AX25 KISS",
    203: "LAPD",
    204: "PPP WITH DIR",
    205: "C_HDLC WITH DIR",
    206: "FRELAY WITH DIR",
    207: "DLT IPMB LINUX",
    209: "IPMB LINUX",
    210: "FLEXRAY",
    212: "LIN",
    215: "IEEE802.15.4 NONASK PHY",
    220: "USB LINUX MMAPPED",
    224: "FC 2",
    225: "FC 2 WITH FRAME DELIMS",
    226: "IPNET",
    227: "CAN SOCKETCAN",
    228: "IPV4",
    229: "IPV6",
    230: "IEEE802.15.4 NOFCS",
    231: "DBUS",
    235: "DVB CI",
    236: "MUX27010",
    237: "STANAG 5066 D-PDU",
    239: "NFLOG",
    240: "NETANALYZER",
    241: "NETANALYZER TRANSPARENT",
    242: "IPOIB",
    243: "MPEG 2 TS",
    244: "NG40",
    245: "NFC LLCP",
    247: "INFINIBAND",
    248: "SCTP",
    249: "USBPCAP",
    250: "RTAC_SERIAL",
    251: "BLUETOOTH LE LL",
    253: "NETLINK",
    254: "BLUETOOTH LINUX MONITOR",
    255: "BLUETOOTH BREDR BB",
    256: "BLUETOOTH LE LL WITH PHDR",
    257: "PROFIBUS DL",
    258: "PKTAP",
    259: "EPON",
    260: "IPMI HPM 2",
    261: "ZWAVE R1 R2",
    262: "ZWAVE R3",
    263: "WATTSTOPPER DLM",
    264: "ISO 14443",
    265: "RDS",
    266: "USB DARWIN",
    268: "SDLC",
    270: "LORATAP",
    271: "VSOCK",
    272: "NORDIC BLE",
    273: "DOCSIS31_XRA31",
    274: "ETHERNET MPACKET",
    275: "DISPLAYPORT AUX",
    276: "LINUX SLL2",
    278: "OPENVIZSLA",
    279: "EBHSCR",
    280: "VPP_DISPATCH",
    281: "DSA TAG BRCM",
    282: "DSA TAG BRCM PREPEND",
    283: "IEEE802.15.4 TAP",
    284: "DSA TAG DSA",
    285: "DSA TAG EDSA",
    286: "ELEE",
    287: "Z WAVE SERIAL",
    288: "USB 2.0",
    289: "ATSC ALP",
    290: "ETW",
    292: "ZBOSS NCP",
    293: "USB 2.0 LOW SPEED",
    294: "USB 2.0 FULL SPEED",
    295: "USB 2.0 HIGH SPEED",
    296: "AUERSWALD LOG",
}

# DHCP options that have been individually identified and parsed
KNOWN_DHCP_OPTIONS = {
    1: {
        "name": "Subnet Mask",
        "type": "ip_address",
    },
    3: {
        "name": "Router",
        "type": "ip_address",
    },
    28: {
        "name": "Broadcast Address",
        "type": "ip_address",
    },
    53: {
        "name": "Message Type",
        "type": "message_type",
    },
    81: {
        "name": "Client Fully Qualified Domain Name",
        "start": 3,
        "type": "string",
    },
}

# all possible DHCP Message Types as per RFC 2131 (in order of id number)
DHCP_MESSAGE_TYPES = (
    "Discover",
    "Offer",
    "Request",
    "Decline",
    "ACK",
    "NAK",
    "Release",
    "Inform",
)

# popular Search Engines to check for in HTTP Requests
POPULAR_SEARCH_ENGINES = (
    "www.google.com",
    "www.bing.com",
    "www.yahoo.com",
    "www.ask.com",
)

OPTIONS_MENU = (
    "\n"
    " 1. Analyse a Packet\n"
    " 2. Search for Domain(s)/URL(s)\n"
    " 3. Find Search Engine(s)\n"
    " 4. Export File Objects\n"
    " 5. Exit"
)

# UTILITY ---------------------------------------------------------------


def load_pcap(pcap_file_path: str) -> bytes:
    """Load a PCAP file into memory, returning the raw bytes.

    Args:
        pcap_file_path (str): Path of the PCAP file to load.

    Returns:
        bytes: Bytes of the loaded PCAP file.
    """
    with open(pcap_file_path, "rb") as pcap_file:
        return pcap_file.read()


def prompt_number_input(message: str, min_value: int, max_value: int) -> int:
    """Prompt the user to enter a number within a given range.

    Args:
        message (str): Message to display to the user.
        min_value (int): Minimum value that the user can enter.
        max_value (int): Maximum value that the user can enter.

    Returns:
        int: Number entered by the user within the given range.
    """

    while True:
        try:
            user_input = int(input(f"\n[?] {message}: "))
        except ValueError:
            print("\nError: Invalid input. Please try again.")
        else:
            if user_input < min_value or user_input > max_value:
                print(
                    f"\nError: Please enter a number between {min_value} and {max_value}"
                )
                continue
        return user_input


def process_packets(pcap_data: bytes, endianness: str) -> None:
    """Produce a list of tuples containing the header and data of each packet.

    Args:
        pcap_data (bytes): All data from the PCAP file.
        endianness (str): Endianness of the PCAP file.
    """
    packets = []
    pointer = 24
    while pointer < len(pcap_data):
        header = struct.unpack(
            f"{'<' if endianness == 'little' else '>'}IIII",
            pcap_data[pointer : pointer + 16],
        )
        pointer += 16
        packets.append((header, pcap_data[pointer : pointer + header[2]]))
        pointer += header[2]
    return packets


def parse_url_parameters(url_string: str) -> dict:
    """Parse the parameters of a URL into a dictionary with key-value pairs.

    Args:
        url_string (str): URL query string to deconstruct.

    Returns:
        dict: Dictionary of key-value pairs from the URL.
    """
    return dict(
        map(
            lambda param: param.split("="),
            url_string.split("&"),
        )
    )


# ANALYSING THE PCAP GLOBAL HEADER (PART 1) ------------------------------


def parse_global_header(header_data: bytes, endianness: str) -> dict:
    """Parse the global header of the PCAP file into a dictionary of key-value pairs

    Args:
        header_data (bytes): Raw bytes holding the Global Header data.
        endianness (str): Endianness of the PCAP file (little or big).

    Returns:
        dict: Dictionary of decoded Global Header values.
    """
    endianness_symbol = ">" if endianness == "big" else "<"  # endianness symbol
    global_header = struct.unpack(endianness_symbol + "IHHIIII", header_data)
    return {
        "magic_number": global_header[0],
        "version_number": f"{global_header[1]}.{global_header[2]}",
        "time_zone": global_header[3],
        "timestamp_accuracy": global_header[4],
        "snapshot_length": global_header[5],
        "data_link_type": global_header[6],
    }


def get_endianness(magic_number: str) -> str:
    """Get the endianness of the PCAP file based on the magic number.

    Args:
        magic_number (str): Hexadecimal string magic number of the PCAP file.

    Raises:
        ValueError: If the magic number is invalid (not a1b2c3d4 or d4c3b2a1).

    Returns:
        str: String representing the endianness of the PCAP file (little or big).
    """
    if magic_number == "a1b2c3d4":
        return "big"
    elif magic_number == "d4c3b2a1":
        return "little"
    else:
        raise ValueError("Invalid magic number")


# ANALYSING PACKETS (PART 2) --------------------------------------------


def inspect_packet(packet_num: int, packet: tuple[tuple[int], bytes]) -> None:
    """Inspect a packet from a packet tuple and output results.

    Args:
        packet (tuple[tuple[int], bytes]): tuple containing the packet header and data.
    """
    packet_header, packet_data = packet
    unix_timestamp = packet_header[0] + packet_header[1] / 1000000

    src_port = int.from_bytes(packet_data[36:38], byteorder="big")
    dst_port = int.from_bytes(packet_data[34:36], byteorder="big")

    print(
        f"\n[+] Packet {packet_num} Information\n\n"
        f"    Unix Timestamp.............. {unix_timestamp}\n"
        f"    Date and Time............... {datetime.datetime.fromtimestamp(unix_timestamp)}\n"
        f"    Packet Length............... {packet_header[2]} Bytes\n"
        f"    Source MAC Address.......... {packet_data[6:12].hex(':')}\n"
        f"    Destination MAC Address..... {packet_data[:6].hex(':')}\n"
        f"    Source IP Address........... {'.'.join(str(octet) for octet in packet_data[26:30])}\n"
        f"    Destination IP Address...... {'.'.join(str(octet) for octet in packet_data[30:34])}\n"
        f"    Source Port................. {src_port}\n"
        f"    Destination Port............ {dst_port}"
    )

    if (src_port == 67 or dst_port == 67) or (src_port == 68 or dst_port == 68):
        dhcp_options = parse_dhcp_options(packet_data)
        longest_name = max(len(opt["name"]) for opt in KNOWN_DHCP_OPTIONS.values())
        known_options = [opt for opt in dhcp_options if opt[0] in KNOWN_DHCP_OPTIONS]

        print(f"\n[!] DHCP Frame Detected with {len(dhcp_options)} Options\n")

        if len(known_options) == 0:
            print("    No known DHCP options detected.")
            return

        for num, data in known_options:
            s = KNOWN_DHCP_OPTIONS[num].get("start", 0)
            e = KNOWN_DHCP_OPTIONS[num].get("end", None)
            value = format_dhcp_option_value(
                KNOWN_DHCP_OPTIONS[num],
                data[s:e],
            )

            option_name = KNOWN_DHCP_OPTIONS[num]["name"]
            print(f"    {option_name.ljust(longest_name + 3, '.')} {value}")

        if len(known_options) != len(dhcp_options):
            print(f"\n    ... {len(dhcp_options) - len(known_options)} unknown options")


def format_dhcp_option_value(option: dict, value: bytes) -> bytes | str:
    """Decode the value of a DHCP option based on its type.

    Args:
        option (dict): Information about the DHCP option to based upon.
        value (bytes): Value extracted from the DHCP packet data for the option.

    Returns:
        bytes | str: Decoded value of the DHCP option if it is a known type.
    """
    if option["type"] == "ip_address":
        value = ".".join(str(octet) for octet in value)
    elif option["type"] == "message_type":
        value = DHCP_MESSAGE_TYPES[value[0] - 1]
    elif option["type"] == "string":
        value = value.decode("utf-8")

    return value


def parse_dhcp_options(packet_data: bytes) -> list[tuple[int, bytes]]:
    """Parse the DHCP options from a packet into a list of tuples.

    Args:
        packet_data (bytes): DHCP packet data to parse options from.

    Returns:
        list[tuple[int, bytes]]: List of tuples containing the DHCP option number and data.
    """
    dhcp_options = []
    pointer = 282
    while pointer < len(packet_data):
        option_code = packet_data[pointer]
        if option_code == 255:
            break
        option_data = packet_data[pointer + 2 : pointer + 2 + packet_data[pointer + 1]]
        dhcp_options.append((option_code, option_data))
        pointer += 2 + packet_data[pointer + 1]

    return dhcp_options


# INVESTIGATING DOMAIN NAMES (PART 3) --------------------------------------------


def prompt_top_level_domain() -> str:
    """Prompt the user to input a Top-Level Domain to investigate.

    Returns:
        str: Top-Level Domain input by the user.
    """
    while True:
        top_level_domain = input("\n[?] Enter a Top-Level Domain: ").strip(".").lower()
        if re.match(r"^[a-z]{2,}$", top_level_domain):
            return top_level_domain
        print("\nError: Invalid Top-Level Domain. Please try again.")


def find_url_occurrences(top_level_domain: str, pcap_data: bytes) -> dict:
    """Find all occurrences of a domain ending with a specified TLD in a packet's data.

    Args:
        top_level_domain (str): Top-Level Domain that the domain must end with.
        pcap_data (bytes): PCAP data to search for the domain in.

    Returns:
        list[str]: List of URLs containing the Top-Level Domain.
    """
    regex = f"http[s]?://([a-zA-Z0-9-.]+?\.{top_level_domain})\W"
    visited_domains = {}
    for domain in set(re.findall(regex.encode(), pcap_data)):
        subdirectories = map(
            lambda d: d.decode().strip(),
            re.findall(
                domain + b"(/(?!http[s]?://)[-a-zA-Z0-9@:%._+~#=?&/]+)",
                pcap_data,
            ),
        )
        visited_domains[domain.decode()] = set(subdirectories)

    return visited_domains


# INVESTIGATING SEARCH ENGINES (PART 4) ------------------------------------------


def find_search_engines(pcap_data: bytes) -> dict[str, set[str]]:
    """Find any uses of popular search engines based on a list of known search engine domains.

    Args:
        pcap_data (bytes): PCAP data to search for search engine domains in.

    Returns:
        dict[str, set[str]]: Dictionary of search engine domains and the query paths made to them.
    """
    search_engines = {}
    for domain in POPULAR_SEARCH_ENGINES:
        regex = rf"http[s]?://{domain}(/(?!http[s]?://)[-a-zA-Z0-9@:%._+~#=?&/]+)"
        search_engine_uses = re.findall(regex.encode(), pcap_data)
        if len(search_engine_uses) > 0:
            search_engines[domain] = list(map(lambda u: u.decode(), search_engine_uses))

    return search_engines


def get_refered_packets(packets: list, referer_url: str) -> list:
    """Get all HTTP packets with a "Referer" header that matches a specified URL.

    Args:
        packets (list): List of processed packets from the given PCAP file
        referer_url (str): URL to match the "Referer" header to.

    Returns:
        list: List of packets with a "Referer" header that matches the specified URL.
    """
    refered_packets = []
    for header, data in packets:
        if re.search(
            rf"Referer: http[s]?://\S+{re.escape(referer_url)}".encode(), data
        ):
            refered_packets.append((header, data))

    return refered_packets


def inspect_search_request(packets: list) -> set[str]:
    refered_pages = set()
    for header, data in packets:
        page = re.search(b"GET (\S+)\W", data)
        if page:
            host_domain = re.search(b"Host:\W(\S+)", data).group(1).decode()
            refered_pages.add(host_domain + page.group(1).decode())

    return refered_pages


# EXPORTING HTTP FILE OBJECTS (PART 5) -------------------------------------------


def get_related_packets(packets: list[tuple], req_num: int, ack_num: int) -> list:
    """Get all packets related to a specified HTTP request based on the ACK number of the responses.

    Args:
        packets (list[tuple]): Packets captured in the PCAP file
        req_num (int): Number of the initial GET request packet
        ack_num (int): Acknowledgement number of the HTTP response

    Returns:
        list: List of packets related to the specified HTTP request.
    """
    related_packets = []
    for i, (header, data) in enumerate(packets[req_num + 1 :], req_num + 1):
        if ack_num == int.from_bytes(data[42:46], byteorder="big"):
            related_packets.append(i)

    if not packets[related_packets[0]][1][54:]:
        return related_packets[1:]
    else:
        return related_packets


def is_successful_request(packets: list[tuple]) -> bool:
    """Check that the HTTP request was successful (HTTP 200 OK)

    Args:
        packets (list[tuple]): Packets associated with the GET request

    Returns:
        int: A boolean value indicating whether the HTTP request was successful.
    """
    for i, (header, data) in enumerate(packets):
        if re.search(b"HTTP/\S+\W(200)\W", data) is not None:
            return True
    return False


def get_content_type(packets: list[tuple]) -> str | None:
    """Get the content type of a HTTP GET request.

    Args:
        packets (list[tuple]): Packets associated with the GET request

    Returns:
        str | None: String of the content type of the GET request or None if no content type is found.
    """
    for header, data in packets:
        content_type = re.search(b"Content-Type:\W(\S+)", data)
        if content_type is not None:
            return content_type.group(1).decode().split(";")[0]


def get_file_object_packets(packets: list[tuple]) -> list:
    """Get all packets related to a file object request (HTTP GET request and TCP Segment packets)

    Args:
        packets (list[tuple]): List of captured packets from the PCAP file

    Returns:
        list: List of packets associated with a file object request
    """
    file_object_packets = []
    for i, (header, data) in enumerate(packets):
        url_path = re.search(b"GET (\S+)\W", data)
        if url_path is not None:

            # Get the sequence number of the HTTP request packet and the ACK number of the response packet
            seq_num = int.from_bytes(data[38:42], byteorder="big")
            ack_num = seq_num + len(data[54:])

            # Get all TCP Segment packets related to this file object request
            related_packet_nums = get_related_packets(packets, i, ack_num)
            related_packets = [packets[i] for i in related_packet_nums]

            # If the request was not successful (i.e. 200 OK), skip this file object
            if not is_successful_request(related_packets):
                continue

            # Get the contet type, file name, and file extension of the file object
            content_type = get_content_type(related_packets)
            file_object_name = (
                os.path.basename(url_path.group(1).decode().split("?")[0]) or "unknown"
            )
            file_extension = mimetypes.guess_extension(content_type) or ""

            # If the file object name does not have a file extension, add the file extension
            if not file_object_name.endswith(file_extension):
                file_object_name += file_extension

            # Add the file object to the list of file objects
            file_object_packets.append(
                (related_packet_nums[0] + 1, file_object_name, related_packets)
            )

            # if not re.match("[A-Za-z0-9._-]", file_object_name):
            #     file_object_name = "unknown"

    return file_object_packets


def process_chunked_data(object_data: bytes) -> bytes:
    """Process chunked data of a file object, removing chunk headers.

    Args:
        object_data (bytes): Chunked data of a file object

    Returns:
        bytes: Processed file object data (without chunk headers)
    """

    chunks = []
    # Separate the first chunk header from the remaining chunk headers and data
    chunk_size, chunk_data = object_data.split(b"\x0d\x0a", 1)

    while True:  # Loop until all chunks have been processed

        # Append the chunk data up to the point of current chunk_size to chunks list
        chunks.append(chunk_data[: int(chunk_size, 16)])

        # Separate next chunk header from chunk data (move to next chunk if there is one)
        chunk_size, *chunk_data = chunk_data[int(chunk_size, 16) + 2 :].split(
            b"\x0d\x0a", 1
        )

        # If there is no remaining chunk data, break
        if not chunk_data:
            break

        # Join the remaining chunk data together to process the next chunk
        chunk_data = b"".join(chunk_data)

    # Join all chunks together to get the complete file object data
    return b"".join(chunks)


def export_http_file_objects(packets: list) -> dict[str, list[str, list]]:
    """Export all valid HTTP file objects within a given PCAP file

    Args:
        packets (list): List of packets from a given PCAP file

    Returns:
        dict[str, list[str, list]]: Dictionary of unique file objects containing the file name, hash, and associated packets
    """

    # Get all packets containing HTTP file objects (e.g. images, PDFs, etc.)
    file_objects = get_file_object_packets(packets)

    # Keep track of file hashes to avoid duplicates (e.g. same file requested multiple times)
    exported_objects = {}

    # Iterate over all retreived file objects
    for req_num, object_name, object_packets in file_objects:

        # Fetch and Join the data from all packets relating to the file object
        object_data = b""
        for packet in object_packets:
            object_data += packet[1][54:]

        # Separate the HTTP header from the file object data
        http_header, object_data = object_data.split(b"\r\n\r\n", 1)

        # Check the HTTP header to see if the file object is chunked (i.e. sent in multiple packets as chunks)
        is_chunked = bool(re.search(b"Transfer-Encoding: chunked", http_header))

        # If the response is chunked, process the chunks (Remove chunk size and chunk data headers, joining all chunks together)
        if is_chunked:
            object_data = process_chunked_data(object_data)

        # If the directory to export files to does not exist, create it
        if not os.path.exists("exported_objects"):
            os.mkdir("exported_objects")

        # Create the relative object name adding the packet number of the request (e.g. 0001_image.png)
        relative_object_name = f"{req_num:0>{len(str(len(packets)))}}_{object_name}"

        # If the file object is a gzip, inflate it
        if re.search(b"Content-Encoding: gzip", http_header):
            compressed_object = io.BytesIO(object_data)
            try:  # Attempt to decompress the file object with gzip library
                with gzip.GzipFile(fileobj=compressed_object) as gz:
                    object_data = gz.read()
            except:  # If the inflation fails, skip exporting the file object
                continue

        # Calculate the MD5 hash of the file object data to check for duplicates
        file_object_hash = hashlib.md5(object_data).hexdigest()

        # If the file object has already been exported, skip it
        if file_object_hash in exported_objects:
            exported_objects[file_object_hash][1].append(req_num)
            continue

        # Write the file object data to a file in the exported_objects directory
        with open(f"exported_objects/{relative_object_name}", "wb") as file:
            file.write(object_data)

        # Add the file object to the exported_objects dictionary
        exported_objects[file_object_hash] = [relative_object_name, [req_num]]

    # Output a message displaying the number of file objects exported and the directory they were exported to
    if len(exported_objects) > 0:
        export_path = os.path.abspath("exported_objects")
        print(f"\n[+] Exported {len(exported_objects)} File Objects to {export_path}")
    else:
        print("\n[-] No File Objects Found")

    return exported_objects


def save_exported_object_records(exported_objects: dict) -> None:
    """Save the exported object records to a CSV file

    Args:
        exported_objects (dict): Dictionary containing records of all exported objects
    """

    # Example.csv gets created in the current working directory
    with open("exported_objects.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(["Hash", "Name", "Packets"])
        for hash, (name, packets) in exported_objects.items():
            writer.writerow([hash, name, ", ".join([str(p) for p in packets])])


# OPTION HANDLERS ----------------------------------------------------------------


def analyse_packet_handler(packets: list) -> None:
    packet_num = prompt_number_input("Enter a Packet Number", 1, len(packets))
    inspect_packet(packet_num, packets[packet_num - 1])


def domain_search_handler(pcap_data: bytes) -> None:
    top_level_domain = prompt_top_level_domain()
    matching_domains = find_url_occurrences(top_level_domain, pcap_data)

    if (matches := len(matching_domains)) == 0:
        print(f'\n[!] Found no domains ending in ".{top_level_domain}"')
        return
    else:
        print(f'\n[!] Found {matches} domain(s) ending ".{top_level_domain}"')

    for domain, subdirs in matching_domains.items():
        print(f"\n    {domain}")
        for subdir in subdirs:
            print(f"{' ' * 12}{subdir}")


def find_search_engine_handler(pcap_data: bytes, packets: bytes) -> None:
    search_engines = find_search_engines(pcap_data)

    if len(search_engines) == 0:
        print("\n[!] Found no popular Search Engines")
        return

    print(f"\n[!] Found {len(search_engines)} popular Search Engine(s)\n")
    for i, (search_engine, uses) in enumerate(search_engines.items(), 1):
        print(
            f"    {i}) {search_engine} [{len(uses)} Appearance(s), {len(set(uses))} Unique]"
        )

    search_engine_num = prompt_number_input("Inspect Search Engine (0 to cancel)", 0, i)
    if search_engine_num == 0:
        return

    selected, requests = list(search_engines.items())[search_engine_num - 1]
    unique_requests = sorted(set(requests), key=requests.index)

    print(f'\n[!] Requests made with "{selected}" Search Engine')

    for i, request in enumerate(unique_requests, 1):
        subdir, query_string = request.split("?")
        parameters = parse_url_parameters(query_string)
        print(f"\n    {i}) {subdir}")
        for key, value in parameters.items():
            print(f"{' ' * 12}{key.ljust(10, '.')} '{value.replace('+', ' ')}'")

    request_num = prompt_number_input("Inspect Search Request (0 to cancel)", 0, i)
    if request_num == 0:
        return

    selected_request = unique_requests[request_num - 1]
    refered_packets = get_refered_packets(packets, selected_request)

    refered_pages = inspect_search_request(refered_packets)

    if len(refered_pages) == 0:
        print(f"\n[!] Found no pages refered by request {request_num}")
        return

    print(
        f"\n[!] Found {len(refered_pages)} page(s) refered by request {request_num}\n"
    )
    for i, page in enumerate(refered_pages, 1):
        print(f"    {page}")


# MAIN ---------------------------------------------------------------------------


def main(pcap_file_path: str) -> None:
    pcap_data = load_pcap(pcap_file_path)
    print(f'[*] Analysing PCAP file "{os.path.basename(pcap_file_path)}"')

    # Get the Hexadecimal Magic Number of the PCAP file
    magic_number = pcap_data[:4].hex()

    # Determine the Endianness of the PCAP file
    try:
        endianness = get_endianness(magic_number)
    except ValueError:
        print("Error: Invalid PCAP file. Please try again.")
        sys.exit(1)

    # Parse the Global Header of the PCAP file
    global_header = parse_global_header(pcap_data[:24], endianness)
    # Process all packets in the PCAP file
    packets = process_packets(pcap_data, endianness)

    # Output PCAP Global Header Information
    print(
        "\n"
        f"    Global Header Length.... {len(pcap_data[:24])} Bytes\n"
        f"    Magic Number............ 0x{magic_number} ({endianness.title()}-Endian)\n"
        f"    Version Number.......... {global_header['version_number']} {'(Latest)' if global_header['version_number'] == '2.4' else ''}\n"
        f"    Snapshot Length......... {global_header['snapshot_length']} ({'All Information Captured' if global_header['snapshot_length'] == 65535 else 'Maximum Packet Size'})\n"
        f"    Data Link Type.......... {global_header['data_link_type']} ({DATA_LINK_TYPES.get(global_header['data_link_type'], 'UNKNOWN')})\n"
        f"    Captured Packets........ {len(packets)}",
    )

    # Accept user input based on options specified in OPTIONS_MENU
    while True:
        print(OPTIONS_MENU)
        option = prompt_number_input("Select an option", 1, 5)

        if option == 1:  # Inspect a Packet
            analyse_packet_handler(packets)
        elif option == 2:  # Find Occurrences of a Domain
            domain_search_handler(pcap_data)
        elif option == 3:  # Find Popular Search Engines and Requests
            find_search_engine_handler(pcap_data, packets)
        elif option == 4:  # Export HTTP File Objects and Hashes
            exported_object_records = export_http_file_objects(packets)
            save_exported_object_records(exported_object_records)
        elif option == 5:
            break


if __name__ == "__main__":
    try:  # unpack pcap file path from command line arguments
        pcap_file_path, *_ = sys.argv[1:]
    except ValueError:  # if there are not enough arguments
        print(f"Usage: python {os.path.basename(sys.argv[0])} <pcap_file_path>")
        sys.exit(1)

    if not os.path.isfile(pcap_file_path):  # if the file does not exist
        print(f'Error: File "{pcap_file_path}" does not exist')
        sys.exit(1)

    main(pcap_file_path)  # run the main function
