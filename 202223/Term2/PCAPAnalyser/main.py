# Rafferty Simms N0990815 - 202223 - Term 2 - PCAP Analyser - ISYS20301

# DECLARATION OF OWNERSHIP ----------------------------------------------

# 1. I am aware of the University’s rules on plagiarism and collusion and I understand
# that, if I am found to have broken these rules, it will be treated as Academic
# Misconduct and dealt with accordingly. I understand that if I lend this piece of work
# to another student and they copy all or part of it, either with or without my
# knowledge or permission, I shall be guilty of collusion.

# 2. In submitting this work I confirm that I am aware of, and am abiding by, the
# University’s expectations for proof-reading.

# 3. I understand that I must submit this coursework by the time and date published. I
# also understand that if this coursework is submitted late it will, if submitted within 5
# working days of the deadline date and time, be given a pass mark as a maximum
# mark. If received more than 5 working days after the deadline date and time, it will
# receive a mark of 0%. For referred or repeat coursework, I understand that if the
# coursework is not submitted by the published date and time, a mark of 0% will be
# automatically awarded.

# 4. I understand that it is entirely my responsibility to ensure that I hand in my full and
# complete coursework and that any missing pages handed in after the deadline will
# be disregarded.

# 5. I understand that the above rules apply even in the eventuality of computer or
# other information technology failures.

import csv
import datetime
import gzip
import hashlib
import io
import mimetypes
import os
import re
import struct
import sys

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

# DHCP options that have been individually identified (Known Options)
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

# All possible DHCP Message Types as per RFC 2131 (in order of id number)
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

# Popular Search Engine domains to check for in HTTP Requests
POPULAR_SEARCH_ENGINES = (
    "www.bing.com",
    "www.yahoo.com",
    "www.ask.com",
)

# Menu options to display for the command-line interface
OPTIONS_MENU = (
    "\n"
    " 1. Analyse a Packet\n"
    " 2. Search for Domain(s)/URL(s)\n"
    " 3. Find Search Engine(s)\n"
    " 4. Export File Objects\n"
    " 5. Exit"
)

# Read file with list of malicious MD5 hashes
with open("malicious_hashes.txt", "r") as f:
    KNOWN_MALICIOUS_HASHES = f.read().splitlines()

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

    # Loop until the user enters a valid number
    while True:
        try:  # Try to convert the user's input to an integer
            user_input = int(input(f"\n[?] {message}: "))
        except ValueError:  # If the user's input is not a number
            print("\nError: Invalid input. Please try again.")
        else:  # If the user's input is a number
            if user_input < min_value or user_input > max_value:
                print(f"\nError: Please enter a number between {min_value} and {max_value}")
                continue
            else:
                break
    return user_input  # Return the user's input


def process_packets(pcap_data: bytes, endianness: str) -> None:
    """Produce a list of tuples containing the header and data of each packet.

    Args:
        pcap_data (bytes): All data from the PCAP file.
        endianness (str): Endianness of the PCAP file.
    """
    packets = []
    # Skip the global header of the PCAP file
    pointer = 24
    # While the pointer is not at the end of the PCAP file
    while pointer < len(pcap_data):
        # Unpack the header of the packet
        header = struct.unpack(
            f"{'<' if endianness == 'little' else '>'}IIII",
            pcap_data[pointer : pointer + 16],
        )
        # Increment the pointer to the start of the packet data
        pointer += 16
        # Append the header and data of the packet to the list
        packets.append((header, pcap_data[pointer : pointer + header[2]]))
        # Increment the pointer to the start of the next packet header
        pointer += header[2]
    # Return the list of packets
    return packets


def parse_url_parameters(url_string: str) -> dict:
    """Parse the parameters of a URL into a dictionary with key-value pairs.

    Args:
        url_string (str): URL query string to deconstruct.

    Returns:
        dict: Dictionary of key-value pairs from the URL.
    """
    return dict(
        map(  # Map the key-value URL parameters to a dictionary
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
    # Determine the endianness symbol based on the endianness of the PCAP file
    endianness_symbol = ">" if endianness == "big" else "<"
    # Unpack the global header into a tuple of values
    global_header = struct.unpack(endianness_symbol + "IHHIIII", header_data)
    # Return the global header as a dictionary
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
    if magic_number == "a1b2c3d4":  # big endian
        return "big"
    elif magic_number == "d4c3b2a1":  # little endian
        return "little"
    else:  # invalid magic number
        raise ValueError("Invalid magic number")


# ANALYSING PACKETS (PART 2) --------------------------------------------


def inspect_packet(packet_num: int, packet: tuple[tuple[int], bytes]) -> None:
    """Inspect a packet from a packet tuple and output results.

    Args:
        packet (tuple[tuple[int], bytes]): tuple containing the packet header and data.
    """
    # Unpack the packet header and data
    packet_header, packet_data = packet
    # Convert the timestamp to a Unix timestamp
    unix_timestamp = packet_header[0] + packet_header[1] / 1000000

    # Extract the source and destination ports from the packet data
    src_port = int.from_bytes(packet_data[36:38], byteorder="big")
    dst_port = int.from_bytes(packet_data[34:36], byteorder="big")

    # Print the packet information to the console
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

    # If the source or destination port indicates a DHCP packet
    if (src_port == 67 or dst_port == 67) or (src_port == 68 or dst_port == 68):
        # Parse the DHCP options from the packet data
        dhcp_options = parse_dhcp_options(packet_data)
        longest_name = max(len(opt["name"]) for opt in KNOWN_DHCP_OPTIONS.values())
        # Filter out unknown DHCP options from the list of known options
        known_options = [opt for opt in dhcp_options if opt[0] in KNOWN_DHCP_OPTIONS]
        # Print the number of DHCP options detected in the packet data
        print(f"\n[!] DHCP Frame Detected with {len(dhcp_options)} Options\n")

        # If no known DHCP options were detected
        if len(known_options) == 0:
            # Print a message to the console and return
            print("    No known DHCP options detected.")
            return

        # Print the known DHCP options
        for num, data in known_options:
            # Slice the data based on the start and end indexes of the option
            s = KNOWN_DHCP_OPTIONS[num].get("start", 0)
            e = KNOWN_DHCP_OPTIONS[num].get("end", None)
            # Format the value of the DHCP option based on its type
            value = format_dhcp_option_value(
                KNOWN_DHCP_OPTIONS[num],
                data[s:e],
            )
            # Get the name of the DHCP option and print the name and value to the console
            option_name = KNOWN_DHCP_OPTIONS[num]["name"]
            print(f"    {option_name.ljust(longest_name + 3, '.')} {value}")

        # If there are any unknown DHCP options
        if len(known_options) != len(dhcp_options):
            # Print the number of unknown options to the console
            print(f"\n    ... {len(dhcp_options) - len(known_options)} unknown options")


def format_dhcp_option_value(option: dict, value: bytes) -> bytes or str:
    """Decode the value of a DHCP option based on its type.

    Args:
        option (dict): Information about the DHCP option to based upon.
        value (bytes): Value extracted from the DHCP packet data for the option.

    Returns:
        bytes | str: Decoded value of the DHCP option if it is a known type.
    """

    if option["type"] == "ip_address":  # if the type is an ip address
        # Convert octets from hex to decimal and join them with a dot
        value = ".".join(str(octet) for octet in value)
    elif option["type"] == "message_type":  # if the type is a message type
        # Get the message type from the DHCP_MESSAGE_TYPES list
        value = DHCP_MESSAGE_TYPES[value[0] - 1]
    elif option["type"] == "string":  # if the type is a string
        # Decode the value from bytes to a string
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
    pointer = 282  # DHCP options start at byte 283 in the packet data (0-indexed)
    # Iterate through option data until the end of the packet data is reached or the end option is reached
    while pointer < len(packet_data):
        # Get the option code and data from the current option
        option_code = packet_data[pointer]
        if option_code == 255:  # if the option code is 255 (end option)
            # Break out of the loop
            break

        # Get the option data from the packet data
        option_data = packet_data[pointer + 2 : pointer + 2 + packet_data[pointer + 1]]
        # Append the option code and data to the list of DHCP options
        dhcp_options.append((option_code, option_data))
        # Increment the pointer to the next option
        pointer += 2 + packet_data[pointer + 1]

    # Return the list of DHCP options
    return dhcp_options


# INVESTIGATING DOMAIN NAMES (PART 3) --------------------------------------------


def prompt_top_level_domain() -> str:
    """Prompt the user to input a Top-Level Domain to investigate.

    Returns:
        str: Top-Level Domain input by the user.
    """
    while True:
        # Prompt the user to input a Top-Level Domain
        top_level_domain = input("\n[?] Enter a Top-Level Domain: ").strip(".").lower()
        if re.match(r"^[a-z.]{2,}$", top_level_domain):  # if valid Top-Level Domain
            return top_level_domain
        # If the Top-Level Domain is invalid
        print("\nError: Invalid Top-Level Domain. Please try again.")


def find_url_occurrences(top_level_domain: str, pcap_data: bytes) -> dict:
    """Find all occurrences of a domain ending with a specified TLD in a packet's data.

    Args:
        top_level_domain (str): Top-Level Domain that the domain must end with.
        pcap_data (bytes): PCAP data to search for the domain in.

    Returns:
        list[str]: List of URLs containing the Top-Level Domain.
    """
    # Find all domains ending with the specified Top-Level Domain
    regex = f"http[s]?://([a-zA-Z0-9-.]+?\.{top_level_domain})\W"
    # Find all subdirectories of the domains
    visited_domains = {}
    # Iterate through the domains found
    for domain in set(re.findall(regex.encode(), pcap_data)):
        # Find all subdirectories of the domain
        subdirectories = map(
            lambda d: d.decode().strip(),
            re.findall(
                domain + b"(/(?!http[s]?://)[-a-zA-Z0-9@:%._+~#=?&/]+)",
                pcap_data,
            ),
        )
        # Add the domain and subdirectories to the dictionary
        visited_domains[domain.decode()] = set(subdirectories)
    # Return the dictionary of domains and subdirectories
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
    # Iterate through the list of popular search engine domains
    for domain in POPULAR_SEARCH_ENGINES:
        # Find all paths that are not URLs to other domains that are requested to the search engine domain
        regex = rf"http[s]?://{domain}(/(?!http[s]?://)[-a-zA-Z0-9@:%._+~#=?&/]+)"
        search_engine_uses = re.findall(regex.encode(), pcap_data)
        # If the search engine domain was used in the PCAP file
        if len(search_engine_uses) > 0:
            # Add the search engine domain and query paths to the dictionary
            search_engines[domain] = list(map(lambda u: u.decode(), search_engine_uses))
    # Return the dictionary of search engine domains and query paths
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
    # Iterate through the packets in the PCAP file
    for header, data in packets:
        # If the packet is an HTTP packet with a "Referer" header that matches the specified URL
        if re.search(rf"Referer: http[s]?://\S+{re.escape(referer_url)}".encode(), data):
            # Add the packet to the list of packets with a "Referer" header that matches the specified URL
            refered_packets.append((header, data))
    return refered_packets


def inspect_search_request(packets: list) -> set[str]:
    refered_pages = set()
    # Iterate through the packets in the PCAP file
    for _, data in packets:
        # Get the page that the search engine request was made to
        page = re.search(b"GET (\S+)\W", data)
        if page is not None:  # If the packet is an HTTP GET request
            # Get the domain that the search engine request was made to
            host_domain = re.search(b"Host:\W(\S+)", data).group(1).decode()
            # Add the page that the search engine request was made to to the list of pages
            refered_pages.add(host_domain + page.group(1).decode())
    return refered_pages


# EXPORTING HTTP FILE OBJECTS (PART 5) -------------------------------------------


def get_object_packets(packets: list[tuple]) -> list:
    """Get all packets related to a file object request (HTTP GET request and TCP Segment packets)

    Args:
        packets (list[tuple]): List of captured packets from the PCAP file

    Returns:
        list: List of packets associated with a file object request
    """

    objects = []
    # Iterate through all packets in the PCAP file
    for i, (_, data) in enumerate(packets):
        # Attempt to get the URL path of the HTTP request
        url_path = re.search(b"GET (\S+)\W", data)
        # If the URL path is not None, then this is an HTTP GET request
        if url_path is not None:
            # Decode the URL path from bytes to a string
            url_path = url_path.group(1).decode()
            # Get the sequence number of the HTTP request packet
            seq_num = int.from_bytes(data[38:42], byteorder="big")
            # Get the TCP Header Length
            tcp_header_length = int(data[46] / 4)
            # Get the acknowledgement number of the HTTP response (sequence number + length of data)
            ack_num = seq_num + len(data[34 + tcp_header_length :])

            # Get the numbers of all TCP Segment packets holding file object data

            related_packet_nums = get_related_packets(packets, i, ack_num)
            # Get all packets related to the file object request using the packet numbers
            related_packets = [packets[i] for i in related_packet_nums]

            # Check if the file object request was successful based on the HTTP response code
            if not is_successful_request(related_packets):
                # If the request was not successful, skip the file object
                continue

            # Get the Content-Type of the file object (i.e. image/jpeg)
            content_type = get_content_type(related_packets)
            # Extract the file object name from the URL path
            object_name = os.path.basename(url_path.split("?")[0]) or "unknown"
            # Get the file extension of the object based on the Content-Type (i.e. .jpg)
            file_extension = mimetypes.guess_extension(content_type) or ""

            # If the object name does not already have a file extension
            if not object_name.endswith(file_extension):
                # Add the file extension to the object name (i.e. image.jpg)
                object_name += file_extension

            # Add the request packet number, object name, and related packets to the list of objects
            request_packet_num = related_packet_nums[0] + 1
            objects.append((request_packet_num, object_name, related_packets))

    # Return the list of file object information
    return objects


def export_http_objects(objects: list) -> dict[str, list[str, list]]:
    """Export all valid HTTP file objects within a given PCAP file

    Args:
        packets (list): List of packets from a given PCAP file

    Returns:
        dict[str, list[str, list]]: Dictionary of unique file objects containing the file name, hash, and associated packets
    """

    # Dictionary holding md5 hashes, names, and request packets of all exported objects
    exported_objects = {}
    # Iterate through the list of all found file object information
    for req_num, obj_name, obj_packets in objects:
        # Join the data from all packets holding file object data
        obj_data = b""
        for packet in obj_packets:
            tcp_header_length = int(packet[1][46] / 4)
            obj_data += packet[1][34 + tcp_header_length :]

        # Separate the HTTP header from the object data
        http_header, obj_data = obj_data.split(b"\r\n\r\n", 1)
        # Check the HTTP header for if the Transfer-Encoding type is "chunked"
        is_chunked = bool(re.search(b"Transfer-Encoding: chunked", http_header))
        # If the response is chunked, remove chunk headers, joining chunk data together
        if is_chunked:
            obj_data = process_chunked_data(obj_data)

        # If the directory to export objects to does not exist
        if not os.path.exists("exported_objects"):
            # Create the directory to export objects to
            os.mkdir("exported_objects")

        # Build the "relative object name" prepending req_num (e.g. 0001_image.png)
        max_req_num_len = len(str(max([req_num for req_num, _, _ in objects])))
        obj_name = f"{req_num:0>{max_req_num_len}}_{obj_name}"

        # If the Content-Encoding of the object is gzip
        if re.search(b"Content-Encoding: gzip", http_header):
            compressed_object = io.BytesIO(obj_data)
            try:
                # Attempt to decompress the object with the gzip library
                with gzip.GzipFile(fileobj=compressed_object) as gz:
                    obj_data = gz.read()
            except:
                # If the decompression fails, skip exporting the object
                continue

        # Calculate the md5 hash of the object
        obj_hash = hashlib.md5(obj_data).hexdigest()

        # If the file object has already been exported
        if obj_hash in exported_objects:
            # Add the request number to the file object record
            exported_objects[obj_hash][1].append(req_num)
            # Skip exporting the file object
            continue

        # Write the file object data to a file in the exported_objects directory
        with open(f"exported_objects/{obj_name}", "wb") as file:
            file.write(obj_data)

        # Add the file object to the exported_objects dictionary
        exported_objects[obj_hash] = [obj_name, [req_num]]

    # If any objects were found and exported
    if len(exported_objects) > 0:
        # Print the number of exported objects and the path to the exported_objects directory
        export_path = os.path.abspath("exported_objects")
        print(f"\n[+] Exported {len(exported_objects)} File Objects to {export_path}")
    else:
        # If no objects were found, print a message to the user
        print("\n[-] No File Objects Found")

    # Return the dictionary of exported object information (md5 hash, name, and request packet numbers)
    return exported_objects


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
    # Iterate through all packets after the initial GET request
    for i, (_, data) in enumerate(packets[req_num + 1 :], req_num + 1):
        # If the ACK number of the packet matches the ACK number of the HTTP response (i.e. the packet is a TCP Segment)
        if ack_num == int.from_bytes(data[42:46], byteorder="big"):
            # Add the packet number to the list of related packets
            related_packets.append(i)

    # If the first packet in the list of related packets is empty
    tcp_header_length = int(packets[related_packets[0]][1][46] / 4)
    if not packets[related_packets[0]][1][34 + tcp_header_length :]:
        # Remove the empty packet from the list of related packets
        return related_packets[1:]
    else:
        # Return the list of related packets
        return related_packets


def is_successful_request(packets: list[tuple]) -> bool:
    """Check that the HTTP request was successful (HTTP 200 OK)

    Args:
        packets (list[tuple]): Packets associated with the GET request

    Returns:
        int: A boolean value indicating whether the HTTP request was successful.
    """
    # Iterate through all packets associated with the HTTP request
    for _, data in packets:
        # If the HTTP response code is 200 (OK)
        if re.search(b"HTTP/\S+\W(200)\W", data) is not None:
            # Return True
            return True
    # If the HTTP response code is not 200 (OK), return False
    return False


def get_content_type(packets: list[tuple]) -> str or None:
    """Get the content type of a HTTP GET request.

    Args:
        packets (list[tuple]): Packets associated with the GET request

    Returns:
        str | None: String of the content type of the GET request or None if no content type is found.
    """

    # Iterate through all packets associated with the HTTP request
    for _, data in packets:
        # Search for the Content-Type header in the HTTP response
        content_type = re.search(b"Content-Type:\W(\S+)", data)
        # If the Content-Type header is found and the content type is not None
        if content_type is not None:
            # Return the content type
            return content_type.group(1).decode().split(";")[0]


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
    # Loop until all chunks have been processed

    while True:
        # Add the chunk data up to the point of current chunk_size to chunks list
        chunks.append(chunk_data[: int(chunk_size, 16)])

        # Separate next chunk header from chunk data

        chunk_size, *chunk_data = chunk_data[int(chunk_size, 16) + 2 :].split(b"\x0d\x0a", 1)

        # If there is no remaining chunk data, break
        if not chunk_data:
            break
        # Join the remaining chunk data together to process the next chunk
        chunk_data = b"".join(chunk_data)

    # Join all chunks together to get the complete file object data
    return b"".join(chunks)


def save_object_records(exported_objects: dict) -> None:
    """Save the exported object records to a CSV file

    Args:
        exported_objects (dict): Dictionary containing records of all exported objects
    """

    # Create and open a CSV file to write the exported object records to
    with open("exported_objects.csv", "w", newline="") as csvfile:
        # Create a CSV writer object with a comma delimiter
        writer = csv.writer(csvfile, delimiter=",")
        # Write the header row of the CSV file with the column names
        writer.writerow(["Hash", "Name", "Packets"])
        # Iterate through all exported objects and write the object records to the CSV file
        for hash, (name, packets) in exported_objects.items():
            writer.writerow([hash, name, ", ".join([str(p) for p in packets])])

    # Output the path of the exported object records file to the console
    print(f"\n[+] Exported Object Records to {os.path.abspath('exported_objects.csv')}")


# OPTION HANDLERS ----------------------------------------------------------------


def analyse_packet_handler(packets: list) -> None:
    """Handles the user input "1" to analyse a packet.

    Args:
        packets (list): List of packets captured in the PCAP file
    """
    # Prompt the user to enter a packet number
    packet_num = prompt_number_input("Enter a Packet Number", 1, len(packets))
    # Analyse the packet, outputting the results to the console
    inspect_packet(packet_num, packets[packet_num - 1])


def domain_search_handler(pcap_data: bytes) -> None:
    """Handles the user input "2" to search for domains.

    Args:
        pcap_data (bytes): PCAP file data as bytes
    """
    # Prompt the user to enter a top-level domain
    top_level_domain = prompt_top_level_domain()
    # Search for domains ending in the top-level domain
    matching_domains = find_url_occurrences(top_level_domain, pcap_data)

    # If no domains ending in the top-level domain are found
    if (matches := len(matching_domains)) == 0:
        # Output a message to the console
        print(f'\n[!] Found no domains ending in ".{top_level_domain}"')
        return
    else:  # Otherwise, output the number of domains found
        print(f'\n[!] Found {matches} domain(s) ending ".{top_level_domain}"')

    # Iterate through all domains ending in the top-level domain and output the results to the console
    for domain, subdirs in matching_domains.items():
        print(f"\n    {domain}")
        for subdir in subdirs:
            print(f"{' ' * 12}{subdir}")


def find_search_engine_handler(pcap_data: bytes, packets: bytes) -> None:
    """Handles the user input "3" to find popular search engines.

    Args:
        pcap_data (bytes): PCAP file data as bytes
        packets (bytes): List of packets captured in the PCAP file
    """
    # Find all popular search engines in the PCAP file
    search_engines = find_search_engines(pcap_data)

    # If no popular search engines are found
    if len(search_engines) == 0:
        # Output a message to the console
        print("\n[!] Found no popular Search Engines")
        return

    # Otherwise, output the number of popular search engines found
    print(f"\n[!] Found {len(search_engines)} popular Search Engine(s)\n")
    # Output the popular search engines to the console
    for i, (search_engine, uses) in enumerate(search_engines.items(), 1):
        print(f"    {i}) {search_engine} [{len(uses)} Appearance(s), {len(set(uses))} Unique]")

    # Prompt the user to enter a search engine number to inspect
    search_engine_num = prompt_number_input("Inspect Search Engine (0 to cancel)", 0, i)
    if search_engine_num == 0:
        return

    # Get the selected search engine and its requests
    selected, requests = list(search_engines.items())[search_engine_num - 1]
    unique_requests = sorted(set(requests), key=requests.index)

    # Output the selected search engine and its requests to the console
    print(f'\n[!] Requests made with "{selected}" Search Engine')

    # Iterate through all requests made with the selected search engine and output the results to the console
    for i, request in enumerate(unique_requests, 1):
        subdir, query_string = request.split("?")
        parameters = parse_url_parameters(query_string)
        print(f"\n    {i}) {subdir}")
        for key, value in parameters.items():
            print(f"{' ' * 12}{key.ljust(10, '.')} '{value.replace('+', ' ')}'")

    # Prompt the user to enter a search request number to inspect
    request_num = prompt_number_input("Inspect Search Request (0 to cancel)", 0, i)
    if request_num == 0:
        return

    # Get the packets associated with the selected search request
    selected_request = unique_requests[request_num - 1]
    refered_packets = get_refered_packets(packets, selected_request)

    # Get the pages refered by the selected search request
    refered_pages = inspect_search_request(refered_packets)

    # If no pages are refered by the selected search request
    if len(refered_pages) == 0:
        # Output a message to the console and return
        print(f"\n[!] Found no pages refered by request {request_num}")
        return
    # Otherwise, output the number of pages refered by the selected search request
    print(f"\n[!] Found {len(refered_pages)} page(s) refered by request {request_num}\n")
    # Output the pages refered by the selected search request to the console
    for i, page in enumerate(refered_pages, 1):
        print(f"    {page}")


def export_file_object_handler(packets: list) -> None:
    """Handles the user input "4" to export file objects.

    Args:
        packets (list): List of packets captured in the PCAP file
    """

    # Get the numbers of all packets associated with HTTP file objects, in order
    objects = get_object_packets(packets)

    # Process and Export all HTTP file objects based on the lists containing associated packet numbers
    exported_objects = export_http_objects(objects)

    # Find any potentially malicious file objects based on their hash
    malicious_hashes = [h for h in exported_objects if h in KNOWN_MALICIOUS_HASHES]
    # If any potentially malicious file objects were found, output them to the console
    if len(malicious_hashes) > 0:
        print(f"\n[!] Found {len(malicious_hashes)} Potentially Malicious File Object(s)")
        for hash in malicious_hashes:
            print(
                f"\n    Hash (md5).... {hash}"
                f"\n    Name.......... {exported_objects[hash][0]}"
                f"\n    Packet(s)..... {', '.join([str(p) for p in exported_objects[hash][1]])}"
            )

    # Save the exported object records to a CSV file for further analysis
    save_object_records(exported_objects)


# MAIN ---------------------------------------------------------------------------


def main(pcap_file_path: str) -> None:
    """Primary function to run the program and handle user input.

    Args:
        pcap_file_path (str): Path of the PCAP file to analyse passed as a command line argument
    """
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
            export_file_object_handler(packets)
        elif option == 5:
            return

        input("\nPress Enter to continue...")


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
