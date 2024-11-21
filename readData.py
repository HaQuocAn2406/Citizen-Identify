from Crypto.Cipher import DES, DES3
from Crypto.Util.Padding import pad, unpad
from Crypto.Util.strxor import strxor
import binascii
from binascii import unhexlify
import hashlib
from smartcard.System import readers
from smartcard.util import toHexString
import sys
import os
import binascii
def calculate_check_digit(data):
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(data):
        if char.isdigit():
            value = int(char)
        elif char.isalpha():
            value = ord(char.upper()) - 55  # A=10, B=11, ..., Z=35
        elif char == '<':
            value = 0
        else:
            raise ValueError(f"Invalid character {char} in MRZ data")
        total += value * weights[i % 3]
    return total % 10

def mac_calculate(data: str, key: str):
    data = unhexlify(data)
    key = unhexlify(key)
    # Apply ISO/IEC 9797-1 padding method 2 (0x80 followed by 0x00s to reach multiple of 8 bytes)
    data_pad = pad(data, 8, style='iso7816')
    # Initialize IV for CBC mode
    iv = b'\x00' * 8

    # Split KMAC into two 8-byte keys for two-key 3DES
    key1, key2 = key[:8], key[8:16]

    # Step 1: Encrypt using DES with key1
    cipher1 = DES.new(key1, DES.MODE_CBC, iv)
    mac_stage1 = cipher1.encrypt(data_pad)

    # Step 2: Decrypt the last 8 bytes of mac_stage1 using DES with key2
    cipher2 = DES.new(key2, DES.MODE_CBC, iv)
    mac_stage2 = cipher2.decrypt(mac_stage1[-8:])

    # Step 3: Encrypt the output of step 2 using DES with key1 again
    cipher3 = DES.new(key1, DES.MODE_CBC, iv)
    final_mac = cipher3.encrypt(mac_stage2)

    # Extract the last 8 bytes of the final output as the MAC
    mac_result = final_mac[-8:]
    return mac_result

def send_apdu(command):
    try:
        # Get the first available card reader
        r = readers()[0]
        connection = r.createConnection()
        connection.connect()
        # Send the command to the card and receive the response
        res, sw1, sw2 = connection.transmit(command)

        # Print the APDU command and the response
        print("Command (APDU):", toHexString(command))
        if sw1 == 0x90 or sw1 == 0x69:
            print("Command Send Success")
        print("Response:", toHexString(res))
        print("SW1:", hex(sw1))
        print("SW2:", hex(sw2))
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
    return res

def generate_random_bytes(byte_length):
    # Generate random bytes using os.urandom
    return os.urandom(byte_length)

def encrypt_3DES(data: bytes, key: bytes):
    s = unhexlify(data)
    # kenc = unhexlify(kenc_hex)

    # Set the zero IV for CBC mode
    iv = b'\x00' * 8

    # Use PyCryptodome's DES3 module in CBC mode
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    encrypted_output = cipher.encrypt(s)
    return encrypted_output

def generate_3des_key(Kseed, c):
    # Step 1: Concatenate Kseed and c
    D = Kseed + c
    # print("Concatenated D:", D)  # Should print the concatenated result
    # Step 2: Calculate the SHA-1 hash of D
    D_bytes = bytes.fromhex(D)  # Convert hexadecimal string to bytes
    sha1_hash = hashlib.sha1(D_bytes).hexdigest().upper()
    # print("SHA-1 hash of D:", sha1_hash)
    # Step 3: Form DES keys Ka and Kb
    Ka = sha1_hash[:16]  # First 16 hex characters for Ka
    Kb = sha1_hash[16:32]  # Next 16 hex characters for Kb
    # print("Ka:", Ka)
    # print("Kb:", Kb)
    # Step 4: Adjust parity bits

    def set_odd_parity(byte):
        byte = int(byte, 16)
        parity = bin(byte).count('1') % 2
        if parity == 0:  # Even number of 1-bits, need to adjust
            byte ^= 0x01  # Toggle the least significant bit to adjust parity
        return format(byte, '02X')
    Ka_bytes = [Ka[i:i+2] for i in range(0, len(Ka), 2)]
    Kb_bytes = [Kb[i:i+2] for i in range(0, len(Kb), 2)]
    Ka_adjusted = ''.join([set_odd_parity(byte) for byte in Ka_bytes])
    Kb_adjusted = ''.join([set_odd_parity(byte) for byte in Kb_bytes])
    # print("Adjusted Ka with parity bits:", Ka_adjusted)
    # print("Adjusted Kb with parity bits:", Kb_adjusted)
    # 3DES key is the concatenation of Ka and Kb
    three_des_key = Ka_adjusted + Kb_adjusted
    # print("3DES Key:", three_des_key)
    return three_des_key

def decrypt_3DES(resp_data:bytes, kenc: bytes):  # giải mã Eic
    s = unhexlify(resp_data)

    # kenc = unhexlify(kenc_hex)

    # Set the zero IV for CBC mode
    iv = b'\x00' * 8

    # Use PyCryptodome's DES3 module in CBC mode
    cipher = DES3.new(kenc, DES3.MODE_CBC, iv)
    encrypted_output = cipher.decrypt(s)
    # print("Data Decrypt: ",encrypted_output.hex().upper())
    return encrypted_output

def xor_hex_strings(hex1, hex2):
    # Convert hex strings to bytes
    bytes1 = bytes.fromhex(hex1)
    bytes2 = bytes.fromhex(hex2)

    # Perform XOR operation
    xor_result = bytes(a ^ b for a, b in zip(bytes1, bytes2))

    # Convert the result back to hex string
    return xor_result.hex().upper()

def hex_to_ascii(hex_string):
    # Convert hex string to bytes
    byte_data = binascii.unhexlify(hex_string)
    # Decode bytes to ASCII
    ascii_string = byte_data.decode('ascii', errors='ignore')
    return ascii_string

def incremented_ssc(SSC):
    incremented_ssc = hex(int(SSC.hex(), 16) + 1)[2:].upper()
    incremented_ssc = incremented_ssc.zfill(len(SSC))
    return incremented_ssc

def build_do87(data, key):
    # Convert hex strings to bytes
    data_bytes = binascii.unhexlify(data)
    key_bytes = binascii.unhexlify(key)
    iv = b'\x00' * 8
    cipher = DES3.new(key_bytes, DES3.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(data_bytes)
    # print(encrypted_data.hex())
    do87 = b"\x87" + asn1_len(b"\x01" + encrypted_data) + \
        b"\x01" + encrypted_data
    # do87 = '87'+format(length, '02X') + '01'+encrypted_data.hex().upper()
    return do87

def compute_key(key_seed: bytes, key_type: str, alg: str) -> bytes:
    if key_type == "enc":
        c = b"\x00\x00\x00\x01"
    elif key_type == "mac":
        c = b"\x00\x00\x00\x02"
    elif key_type == "pace":
        c = b"\x00\x00\x00\x03"
    else:
        raise ValueError('key_type must either be "enc" or "mac"')
    D = key_seed + c

    if alg == "3DES":
        hash_of_D = hashlib.sha1(D).digest()
        key_a = hash_of_D[:8]
        key_b = hash_of_D[8:16]
        return DES3.adjust_key_parity(key_a + key_b)  # set parity bits
    if alg == "AES-128":
        return hashlib.sha1(D).digest()[:16]
    if alg == "AES-192":
        return hashlib.sha256(D).digest()[:24]
    if alg == "AES-256":
        return hashlib.sha256(D).digest()
    else:
        raise ValueError("[-] Unknown encryption algorithm!")

def asn1_len(value_bytes: bytes) -> bytes:
    length = len(value_bytes)
    if length < 128:
        return bytes([length])

    length_bytes = length.to_bytes(
        (length.bit_length() + 7) // 8, byteorder="big")

    length_of_length_bytes = bytes([(1 << 7) | len(length_bytes)])
    return length_of_length_bytes + length_bytes

def len2int(first_n_bytes: bytes) -> int:
    """
    Gets the asn1length and returns it as integer as explained in 9303-10 p14.
    """
    if not first_n_bytes[1] >> 7:
        data_len = first_n_bytes[1] + 2
    else:
        length_of_length = (1 << 7) ^ first_n_bytes[1]
        data_len = (int.from_bytes(first_n_bytes[2 : length_of_length + 2], byteorder="big")+ length_of_length+ 2)
    return data_len

def extract_tagged_values(data, tag):
    result = []
    i = 0
    while i < len(data):
        if data[i] == tag:  # Found the tag
            length = data[i + 1]  # Length of the data
            result.extend(data[i:i + 2 + length])  # Add tag, length, and data to the result
            i += 2 + length  # Move the index past this block
        else:
            i += 1  # Move to the next byte
    return result

def extract_tag_data(data,tag):
    if data[0] != tag:
        raise ValueError("Not a DO '87' structure")
    # Length field starts after the tag
    length_byte = data[1]
    lenDO99= 4
    if length_byte <= 0x7F:  # Short form
        length = length_byte
        offset = 2  # Tag + Length = 2 bytes
    elif length_byte > 0x80:  # Long form
        num_length_bytes = length_byte - 0x80  # Number of subsequent length bytes
        length = int.from_bytes(data[2:2 + num_length_bytes], byteorder='big')
        offset = 2 + num_length_bytes  # Tag + Length bytes
    else:
        raise ValueError("Invalid length encoding")
    output = data[:length+offset]
    output_withoutTag=data[offset:length+offset]
    do99=data[len(output):len(output)+lenDO99]
    return output,output_withoutTag,do99

def read(ssc,cla,ins,p1,p2,le=b''):
    payload = b""
    Le = le
    headerReadBinary=cla+ins+p1+p2
    CmdHeaderReadBinary = pad(headerReadBinary, 8, style='iso7816')
    do97 = b"\x97" + asn1_len(Le) + Le
    M = CmdHeaderReadBinary+do97
    N = pad(bytes.fromhex(ssc)+M, 8, style='iso7816')
    CC = mac_calculate(unpad(N, 8, style='iso7816').hex(), K_mac_NEW)
    do8e = b"\x8E" + asn1_len(CC) + CC
    payload = do97+do8e
    protected_apdu = headerReadBinary+bytes([len(payload)]) + payload + b'\x00'
    res = send_apdu(list(protected_apdu))
    ssc = incremented_ssc(bytes.fromhex(ssc))
    do87,data_87,do99 = extract_tag_data(bytes(res),0x87)
    # toHexString(list(do87))
    print(f'DO87: {do87.hex().upper()}')
    # res = bytes(res).hex().replace(toHexString(list(do87)),'')
    # print(res)
    # do99,data_99 = extract_tag_data(bytes.fromhex(res),0x99)
    print(f'DO99: {do99.hex().upper()}')
    K = ssc + do87.hex() + do99.hex()
    K = pad(bytes.fromhex(K),8,style='iso7816')
    CC = mac_calculate(unpad(K, 8, style='iso7816').hex(), K_mac_NEW)
    data = decrypt_3DES(data_87[1:].hex(),bytes.fromhex(K_enc_NEW))
    data_len =len2int(data)
    return ssc,unpad(data,8,style='iso7816'),data_len

def save_image_from_bytes(image_bytes, output_path):
    if image_bytes[:2] == b'\xFF\xD8' and image_bytes[-2:] == b'\xFF\xD9':
        with open(output_path, 'wb') as f:
            f.write(image_bytes)
        print(f"Image Save At: {output_path}")
    else:
        print("Wrong Format.")

def read_EF(data,SSC):
    inc_ssc = incremented_ssc(SSC)
    # res_tes = read(inc_ssc,b'\x0C',b'\xA4',b'02',b'0C')
    payload = b""
    header = '0CA4020C'
    CmdHeader = pad(bytes.fromhex(header),8,style='iso7816')
    Data = data  # EF.DG2
    DataWitPad = pad(bytes.fromhex(Data),8,style='iso7816')
    key = DES3.new(unhexlify(K_enc_NEW), DES.MODE_CBC, b'\0'*8)
    EncryptedData = (key.encrypt(DataWitPad)).hex()
    # Compute DO'87'
    do87 = build_do87(DataWitPad.hex(), K_enc_NEW)
    payload += do87
    # do87 = b"\x87" + asn1_len(b"\x01" + CC) + b"\x01" + CC
    M = CmdHeader+do87
    # inc_ssc = incremented_ssc(SSC)
    N = pad(bytes.fromhex(inc_ssc)+M, 8, style='iso7816')
    print(N.hex())
    CC = mac_calculate(unpad(N, 8, style='iso7816').hex(), K_mac_NEW)
    DO8E = b"\x8E" + asn1_len(CC) + CC
    payload += DO8E
    # totalLength = len(do87+DO8E)
    # print(totalLength)
    ProtectedAPDU = bytes.fromhex(header)+bytes([len(payload)])+payload+b"\x00"
    # print("incremented_ssc: ", inc_ssc)
    # print("CmdHeader: ", CmdHeader.hex())
    # print("Data: ", DataWitPad.hex())
    # print("EncryptedData: ", EncryptedData)
    # print("DO'87':", do87)
    # print("M: ", M.upper())
    # print("SSC +1: ", inc_ssc)
    # print(N.hex().upper())
    # print("CC: ", CC.hex().upper())
    # print("DO'8E': ", DO8E)
    # print("ProtectedAPDU: ",ProtectedAPDU)
    send_apdu(list(ProtectedAPDU))
    # respone = bytes.fromhex('990290008E08FA855A5D4C50A8ED9000')   #Test Data
    ########################
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    ssc,data_res,data_len = read(inc_ssc,b'\x0c',b'\xB0',b'\x00',b'\x00',b'\x04')
    # print(data_res.hex())
    # print(data_len)
    offset = 4
    blocksize = 0xe7 # 231
    blocksize = 164 # use a small block size in order to obtain more granual progress bar update
    count = 0 
    while offset < data_len:
        count = count+ 1
        print(f'{count}')
        le = bytes([ min(blocksize, data_len - offset) ])
        ssc = incremented_ssc(bytes.fromhex(ssc))
        ssc,decrypted_data,decrypted_data_len = read(ssc,b'\x0c',b'\xB0',bytes([offset >> 8]),bytes([offset & 0xFF]),le)
        if decrypted_data == b"":
            print(" No reply from card")
            break
        data_res += decrypted_data
        offset += len(decrypted_data)
        print(data_res.hex().upper())
    return data_res,ssc

# Input real data
# document_number = '202033433'
# date_of_birth = '020624'
# date_of_expire = '270624'
def getMRZandImage(Document_number,Date_of_birth,Date_of_expire):
    global K_enc_NEW, K_mac_NEW
    document_number = Document_number
    date_of_birth = Date_of_birth
    date_of_expire = Date_of_expire
    # document_number = '044003903'
    # date_of_birth = '440306'
    # date_of_expire = '991231'
    RND_IFD = generate_random_bytes(8)
    K_IFD = generate_random_bytes(16)
    mrz_code = document_number+str(calculate_check_digit(document_number))+date_of_birth+str(
        calculate_check_digit(date_of_birth))+date_of_expire+str(calculate_check_digit(date_of_expire))
    sha1_hash = hashlib.sha1(mrz_code.encode()).digest()
    Kseed = sha1_hash[:16]
    K_enc = compute_key(Kseed, 'enc', '3DES')
    K_mac = compute_key(Kseed, 'mac', '3DES')

    LDS_APPLICATON = [0x00, 0xA4, 0x04, 0x0C, 0x07,
                    0xA0, 0x00, 0x00, 0x02, 0x47, 0x10, 0x01]
    GET_CHALLENGE = [0x00, 0x84, 0x00, 0x00, 0x08]
    send_apdu(LDS_APPLICATON)  # SELECT LDS_APPLICATON COMMAND
    # Input Real Data
    RND_IC = bytes(send_apdu(GET_CHALLENGE))  # GET RND_IC
    S = str(RND_IFD.hex())+RND_IC.hex()+str(K_IFD.hex())
    E_IFD = encrypt_3DES(S, K_enc)
    M_IFD = mac_calculate(E_IFD.hex(), K_mac.hex())
    print("MRZ Full Code:", mrz_code)
    print("MRZ Encryp:", sha1_hash.hex())
    print("Kseed:", Kseed.hex().upper())
    print("K_enc:", K_enc.hex())
    print("K_mac:", K_mac.hex())
    print("RND_IC: ", RND_IC.hex().upper())
    print("RND_IFD: ", RND_IFD.hex().upper())
    print("K_IFD: ", K_IFD.hex().upper())
    print("S: ", S.upper())
    print("E_IFD: ", E_IFD.hex().upper())
    print("M_IFD: ", M_IFD.hex().upper())
    cmd_data = E_IFD+M_IFD
    print("AUTHENTICATE Key: ", cmd_data.hex().upper())
    EXTERNAL_AUTHENTICATE = [0x00, 0x82, 0x00, 0x00, 0x28]+list(cmd_data)+[0x28]
    response_from_IC = toHexString(send_apdu(EXTERNAL_AUTHENTICATE))
    response_from_IC = "".join(response_from_IC.split())
    E_ic = response_from_IC[:64]
    R = decrypt_3DES(E_ic, K_enc)
    K_IC = R[-16:]
    K_seed_NEW = xor_hex_strings(K_IFD.hex(), K_IC.hex())
    K_enc_NEW = generate_3des_key(K_seed_NEW, '00000001')
    K_mac_NEW = generate_3des_key(K_seed_NEW, '00000002')
    print("response_from_IC:", response_from_IC)
    print("E_ic:", E_ic.upper())
    print("R: ", R.hex().upper())
    print("K_IC:", K_IC.hex().upper())
    print("K seed NEW: ", K_seed_NEW)
    print("K_enc_NEW:", K_enc_NEW)
    print("K_mac_NEW:", K_mac_NEW)
    SSC = RND_IC[-4:]+RND_IFD[-4:]
    #################################
    print("SSC: ", SSC.hex().upper())
    data_res,ssc = read_EF('0102',SSC)
    im_start = data_res.find(b"\xFF\xD8\xFF\xE0")
    if im_start == -1:
            im_start = data_res.find(b"\x00\x00\x00\x0C\x6A\x50")
    image = data_res[im_start:]
    save_image_from_bytes(image, 'output.jpg')
    mrz_from_ic,ssc = read_EF('0101',bytes.fromhex(ssc))
    ascii_string = hex_to_ascii(mrz_from_ic[5:].hex())
    print("ASCII String:", ascii_string)
