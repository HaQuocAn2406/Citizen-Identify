from Crypto.Cipher import DES, DES3
from Crypto.Util.Padding import pad
import binascii
from binascii import unhexlify
import hashlib
from smartcard.System import readers
from smartcard.util import toHexString
import sys
import os


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


def mac_calculate(data: str, kmac_hex: str):
    # Convert hex strings to byte arrays
    data = unhexlify(data)
    kmac = unhexlify(kmac_hex)

    # Apply ISO/IEC 9797-1 padding method 2 (0x80 followed by 0x00s to reach multiple of 8 bytes)
    data_pad = pad(data, 8, style='iso7816')

    # Initialize IV for CBC mode
    iv = b'\x00' * 8

    # Split KMAC into two 8-byte keys for two-key 3DES
    key1, key2 = kmac[:8], kmac[8:16]

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
        # print("Response:", toHexString(res))
        print("SW1:", hex(sw1))
        print("SW2:", hex(sw2))
    except Exception as e:
        print("Error:", e)
        sys.exit(1)
    return res


def generate_random_bytes(byte_length):
    # Generate random bytes using os.urandom
    return os.urandom(byte_length)


def calculate_EIFD(s_hex, kenc_hex):
    s = unhexlify(s_hex)
    kenc = unhexlify(kenc_hex)

    # Set the zero IV for CBC mode
    iv = b'\x00' * 8

    # Use PyCryptodome's DES3 module in CBC mode
    cipher = DES3.new(kenc, DES3.MODE_CBC, iv)
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


def decrypt_EIC(resp_data, kenc_hex):  # giải mã Eic
    s = unhexlify(resp_data)
    kenc = unhexlify(kenc_hex)

    # Set the zero IV for CBC mode
    iv = b'\x00' * 8

    # Use PyCryptodome's DES3 module in CBC mode
    cipher = DES3.new(kenc, DES3.MODE_CBC, iv)
    encrypted_output = cipher.decrypt(s)
    # print("Data Decrypt: ",encrypted_output.hex().upper())
    return encrypted_output


def encrypt(data, key):  # giải mã Eic
    s = unhexlify(data)
    kenc = unhexlify(key)

    # Set the zero IV for CBC mode
    iv = b'\x00' * 8

    # Use PyCryptodome's DES3 module in CBC mode
    cipher = DES3.new(kenc, DES3.MODE_CBC, iv)
    encrypted_output = cipher.encrypt(s)
    # print(encrypted_output.hex().upper())
    return encrypted_output


def xor_hex_strings(hex1, hex2):
    # Convert hex strings to bytes
    bytes1 = bytes.fromhex(hex1)
    bytes2 = bytes.fromhex(hex2)

    # Perform XOR operation
    xor_result = bytes(a ^ b for a, b in zip(bytes1, bytes2))

    # Convert the result back to hex string
    return xor_result.hex().upper()


def pad_iso7816(data):
    """
    Pads the input data to a multiple of 8 bytes using ISO 7816-4 padding.

    :param data: Input data as bytes
    :return: Padded data as bytes
    """
    block_size = 8
    padding_length = block_size - (len(data) % block_size)

    # Add 0x80 followed by 0x00 as padding
    padding = b'\x80' + b'\x00' * (padding_length - 1)
    return data + padding


def addpad(toPad):
    size = 8
    padBlock = b'\x80' + b'\x00'*7
    left = size - (len(toPad) % size)
    return (toPad + padBlock[0:left])


def unpad(tounpad):
    i = -1
    while tounpad[i] == 0:
        i -= 1

    if tounpad[i] == 0x80:
        return tounpad[0:i]

    else:
        # Pas de padding
        return tounpad


def build_do8e(mac):
    mac_hex = unhexlify(mac)
    length = len(mac_hex)
    DO8E = '8E'+format(length, '02X') + mac_hex.hex()
    return DO8E


def build_do97(Le: bytes):
    do97 = '9701' + Le.hex()
    return do97


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
    # Build DO'87' (tag '87', length, and encrypted data)
    length = len(encrypted_data)+1
    do87 = '87'+format(length, '02X') + '01'+encrypted_data.hex().upper()
    return do87


def getMRZ(K_enc_NEW: str, K_mac_NEW: str, SSC: bytes):
    ########### SELECT EF.DG1 ###############
    header = '0CA4020C'
    CmdHeader = pad_iso7816(bytes.fromhex(header))
    Data = '0101'  # EF.DG1
    DataWitPad = pad_iso7816(bytes.fromhex(Data))
    key = DES3.new(unhexlify(K_enc_NEW), DES.MODE_CBC, b'\0'*8)
    EncryptedData = (key.encrypt(DataWitPad)).hex()
    # Compute DO'87'
    do87 = build_do87(DataWitPad.hex(), K_enc_NEW)
    M = CmdHeader.hex()+do87
    inc_ssc = incremented_ssc(SSC)
    N = addpad(unhexlify(inc_ssc+M))
    CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
    DO8E = build_do8e(CC.hex())
    totalLength = len(unhexlify(do87+DO8E))
    # print(totalLength)
    ProtectedAPDU = header+format(totalLength, '02X')+do87+DO8E+'00'
    # print("incremented_ssc: ",inc_ssc)
    # print("CmdHeader: ",CmdHeader.hex())
    # print("Data: ",DataWitPad.hex())
    # print("EncryptedData: ",EncryptedData)
    # print("DO'87':", do87)
    # print("M: ",M.upper())
    # print("SSC +1: ",inc_ssc)
    # print(N.hex().upper())
    # print("CC: ",CC.hex().upper())
    # print("DO'8E': ",DO8E)
    # print("ProtectedAPDU: ",ProtectedAPDU)
    ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                     for i in range(0, len(ProtectedAPDU), 2)]
    respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))

    # respone = bytes.fromhex('990290008E08FA855A5D4C50A8ED9000')   #Test Data

    ########################
    # print("Response Of SELECT EL.COM:",respone.hex().upper())

    ################# DECRYPT AND CHECK ###############################
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    DO99 = respone[:4]
    K = inc_ssc+DO99.hex()
    CC_Check = mac_calculate(K, K_mac_NEW)
    # print("K to check Response SELECT EL.COM :",K)
    # print("CC' :",CC_Check.hex().upper())

    ################ READ 4 FRIST BYTES ##########################
    headerReadBinary = '0CB00000'
    CmdHeaderReadBinary = addpad(bytes.fromhex(headerReadBinary))
    do97 = build_do97(b'\x04')
    M = CmdHeaderReadBinary.hex()+do97
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    N = addpad(bytes.fromhex(inc_ssc+M))
    CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
    DO8E = build_do8e(CC.hex())
    totalLength = len(unhexlify(do97+DO8E))
    print(totalLength)
    ProtectedAPDU = headerReadBinary+format(totalLength, '02X')+do97+DO8E+'00'
    # print("CmdHeaderReadBinary: ",CmdHeaderReadBinary.hex().upper())
    # print("DO'97': ",do97)
    # print("M: ",M.upper())
    # print("incremented_ssc: ",inc_ssc)
    # print("N: ",N.hex().upper())
    # print("CC: ",CC.hex().upper())
    # print("DO'8E': ",DO8E.upper())
    # print("ProtectedAPDU: ",ProtectedAPDU.upper())
    ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                     for i in range(0, len(ProtectedAPDU), 2)]
    ################# DECRYPT AND CHECK ###############################
    respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))

    # respone = bytes.fromhex('8709019FF0EC34F9922651990290008E08AD55CC17140B2DED9000')   #Test Data

    # print("respone of read 4 frist bytes: ",respone.hex().upper())
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    do87 = respone[:11]
    do99 = respone[11:15]
    K = bytes.fromhex(inc_ssc)+do87+do99
    CC_decryp = mac_calculate(K.hex(), K_mac_NEW)
    # print("incremented_ssc: ",inc_ssc)
    # print("DO87: ",do87.hex())
    # print("DO99: ",do99.hex())
    # print("K: ",K.hex())
    # print("CC Decrypt: ",CC_decryp.hex().upper())
    data_4 = decrypt_EIC(do87[3:].hex(), K_enc_NEW)
    # print("Data of 4 frist bytes: ",unpad(data_4).hex().upper())
    length_value = int(data_4[1:2].hex(), 16)
    L = (length_value + 2) % 256  # GET LENGHT OF DG
    # print("Length: ",L)

    ################ READ DATA #####################
    headerReadBinary = '0CB00004'
    CmdHeaderReadBinary = addpad(bytes.fromhex(headerReadBinary))
    L = L - 4
    do97 = build_do97(bytes(L))
    M = CmdHeaderReadBinary.hex()+do97
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    N = addpad(bytes.fromhex(inc_ssc+M))
    CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
    DO8E = build_do8e(CC.hex())
    totalLength = len(unhexlify(do97+DO8E))
    # print(totalLength)
    ProtectedAPDU = headerReadBinary+format(totalLength, '02X')+do97+DO8E+'00'
    # print("CmdHeaderReadBinary: ",CmdHeaderReadBinary.hex().upper())
    # print("DO'97': ",do97)
    # print("M: ",M.upper())
    # print("incremented_ssc: ",inc_ssc)
    # print("N: ",N.hex().upper())
    # print("CC: ",CC.hex().upper())
    # print("DO'8E': ",DO8E.upper())
    # print("ProtectedAPDU: ",ProtectedAPDU.upper())
    ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                     for i in range(0, len(ProtectedAPDU), 2)]
    respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))
    # Test Data
    # respone = bytes.fromhex('8709019FF0EC34F9922651990290008E08AD55CC17140B2DED9000')
    ###############
    # print("respone: ",respone.hex().upper())
    inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
    do87 = respone[:99]
    do99 = respone[99:105]
    K = bytes.fromhex(inc_ssc)+do87+do99
    CC_decryp = mac_calculate(K.hex(), K_mac_NEW)
    # print("incremented_ssc: ",inc_ssc)
    # print("DO87: ",do87.hex())
    # print("DO99: ",do99.hex())
    # print("K: ",K.hex())
    # print("CC Decrypt: ",CC_decryp.hex().upper())
    data_18 = decrypt_EIC(do87[3:].hex(), K_enc_NEW)
    # print("Data 18bytes: ",data_18.hex().upper())
    # # print((unpad(data_4).hex()+data_18.hex()))
    data_to_decryp = data_18[1:]
    # # print(data_to_decryp.hex())
    # # Convert hex string to ASCII
    ascii_string = hex_to_ascii(data_to_decryp.hex())
    print("ASCII String:", ascii_string)
    return inc_ssc


# Input real data
document_number = '202033433'
date_of_birth = '020624'
date_of_expire = '270624'
RND_IFD = generate_random_bytes(8)
K_IFD = generate_random_bytes(16)
# Test Data
# document_number = 'L898902C<'
# date_of_birth = '690806'
# date_of_expire='940623'
# RND_IFD = bytes.fromhex('781723860C06C226')
# K_IFD = bytes.fromhex('0B795240CB7049B01C19B33E32804F0B')

mrz_code = document_number+str(calculate_check_digit(document_number))+date_of_birth+str(
    calculate_check_digit(date_of_birth))+date_of_expire+str(calculate_check_digit(date_of_expire))
sha1_hash = hashlib.sha1(mrz_code.encode()).digest()
Kseed = sha1_hash[:16]

K_enc = generate_3des_key(Kseed.hex(), '00000001')
K_enc = K_enc.replace(" ", "")
K_mac = generate_3des_key(Kseed.hex(), '00000002')
K_mac = K_mac.replace(" ", "")
LDS_APPLICATON = [0x00, 0xA4, 0x04, 0x0C, 0x07,
                  0xA0, 0x00, 0x00, 0x02, 0x47, 0x10, 0x01]
GET_CHALLENGE = [0x00, 0x84, 0x00, 0x00, 0x08]
send_apdu(LDS_APPLICATON)  # SELECT LDS_APPLICATON COMMAND
# Input Real Data
RND_IC = bytes(send_apdu(GET_CHALLENGE))  # GET RND_IC
# RND_IC = bytes.fromhex('4608F91988702212')    #Test Data
S = str(RND_IFD.hex())+RND_IC.hex()+str(K_IFD.hex())
E_IFD = calculate_EIFD(S, K_enc)
M_IFD = mac_calculate(E_IFD.hex(), K_mac)
print("MRZ Full Code:", mrz_code)
print("MRZ Encryp:", sha1_hash.hex())
print("Kseed:", Kseed.hex().upper())
print("K_enc:", K_enc)
print("K_mac:", K_mac)
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
# response_from_IC = '46B9342A41396CD7386BF5803104D7CEDC122B9132139BAF2EEDC94EE178534F2F2D235D074D7449'     #Test Data
E_ic = response_from_IC[:64]
R = decrypt_EIC(E_ic, K_enc)
K_IC = R[-16:]
K_seed_NEW = xor_hex_strings(K_IFD.hex(), K_IC.hex())
K_enc_NEW = generate_3des_key(K_seed_NEW, '00000001')
K_enc = K_enc.replace(" ", "")
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
# print("SSC: ",SSC.hex().upper())
# K_enc_NEW K_mac_NEW  SSC
new_SSC = getMRZ(K_enc_NEW, K_mac_NEW, SSC)

############### READ EF.DG2 #############

header = '0CA4020C'
CmdHeader = pad_iso7816(bytes.fromhex(header))
Data = '0102'  # EF.DG2
DataWitPad = pad_iso7816(bytes.fromhex(Data))
key = DES3.new(unhexlify(K_enc_NEW), DES.MODE_CBC, b'\0'*8)
EncryptedData = (key.encrypt(DataWitPad)).hex()
# Compute DO'87'
do87 = build_do87(DataWitPad.hex(), K_enc_NEW)
M = CmdHeader.hex()+do87
inc_ssc = incremented_ssc(bytes.fromhex(new_SSC))
N = addpad(unhexlify(inc_ssc+M))
CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
DO8E = build_do8e(CC.hex())
totalLength = len(unhexlify(do87+DO8E))
print(totalLength)
ProtectedAPDU = header+format(totalLength, '02X')+do87+DO8E+'00'
print("incremented_ssc: ",inc_ssc)
print("CmdHeader: ",CmdHeader.hex())
print("Data: ",DataWitPad.hex())
print("EncryptedData: ",EncryptedData)
print("DO'87':", do87)
print("M: ",M.upper())
print("SSC +1: ",inc_ssc)
print(N.hex().upper())
print("CC: ",CC.hex().upper())
print("DO'8E': ",DO8E)
print("ProtectedAPDU: ",ProtectedAPDU)
ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                 for i in range(0, len(ProtectedAPDU), 2)]
respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))

# respone = bytes.fromhex('990290008E08FA855A5D4C50A8ED9000')   #Test Data

########################
print("Response Of SELECT EL.DG2:",respone.hex().upper())

################# DECRYPT AND CHECK ###############################
inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
DO99 = respone[:4]
K = inc_ssc+DO99.hex()
CC_Check = mac_calculate(K, K_mac_NEW)
print("K to check Response SELECT EL.DG2 :",K)
print("CC' :",CC_Check.hex().upper())

################ READ 4 FRIST BYTES ##########################
headerReadBinary = '0CB00000'
CmdHeaderReadBinary = addpad(bytes.fromhex(headerReadBinary))
do97 = build_do97(b'\x04')
M = CmdHeaderReadBinary.hex()+do97
inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
N = addpad(bytes.fromhex(inc_ssc+M))
CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
DO8E = build_do8e(CC.hex())
totalLength = len(unhexlify(do97+DO8E))
print(totalLength)
ProtectedAPDU = headerReadBinary+format(totalLength, '02X')+do97+DO8E+'00'
print("CmdHeaderReadBinary: ",CmdHeaderReadBinary.hex().upper())
print("DO'97': ",do97)
print("M: ",M.upper())
print("incremented_ssc: ",inc_ssc)
print("N: ",N.hex().upper())
print("CC: ",CC.hex().upper())
print("DO'8E': ",DO8E.upper())
print("ProtectedAPDU: ",ProtectedAPDU.upper())
ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                 for i in range(0, len(ProtectedAPDU), 2)]
################# DECRYPT AND CHECK ###############################
respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))

# respone = bytes.fromhex('8709019FF0EC34F9922651990290008E08AD55CC17140B2DED9000')   #Test Data

print("respone of read 4 frist bytes: ",respone.hex().upper())
inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
do87 = respone[:11]
do99 = respone[11:15]
K = bytes.fromhex(inc_ssc)+do87+do99
CC_decryp = mac_calculate(K.hex(), K_mac_NEW)
print("incremented_ssc: ",inc_ssc)
print("DO87: ",do87.hex())
print("DO99: ",do99.hex())
print("K: ",K.hex())
print("CC Decrypt: ",CC_decryp.hex().upper())
data_4 = decrypt_EIC(do87[3:].hex(), K_enc_NEW)
print("Data of 4 frist bytes: ",unpad(data_4).hex().upper())
length_value = int(data_4[1:2].hex(), 16)
L = (length_value + 2) % 256  # GET LENGHT OF DG
print("Length: ",L)

################ READ DATA #####################
headerReadBinary = '0CB00004'
CmdHeaderReadBinary = addpad(bytes.fromhex(headerReadBinary))
L = L - 4
print(bytes(L).hex())
do97 = build_do97(b'\x80')
M = CmdHeaderReadBinary.hex()+do97
inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
N = addpad(bytes.fromhex(inc_ssc+M))
CC = mac_calculate(unpad(N).hex(), K_mac_NEW)
DO8E = build_do8e(CC.hex())
totalLength = len(unhexlify(do97+DO8E))
# print(totalLength)
ProtectedAPDU = headerReadBinary+format(totalLength, '02X')+do97+DO8E+'00'
print("CmdHeaderReadBinary: ",CmdHeaderReadBinary.hex().upper())
print("DO'97': ",do97)
print("M: ",M.upper())
print("incremented_ssc: ",inc_ssc)
print("N: ",N.hex().upper())
print("CC: ",CC.hex().upper())
print("DO'8E': ",DO8E.upper())
print("ProtectedAPDU: ",ProtectedAPDU.upper())
ProtectedAPDU = [int(ProtectedAPDU[i:i+2], 16)
                 for i in range(0, len(ProtectedAPDU), 2)]
respone = bytes.fromhex(toHexString(send_apdu(ProtectedAPDU)))
# Test Data
# respone = bytes.fromhex('8709019FF0EC34F9922651990290008E08AD55CC17140B2DED9000')
###############
print("respone: ",respone.hex().upper())
inc_ssc = incremented_ssc(bytes.fromhex(inc_ssc))
do87 = respone[:140]
do99 = respone[140:144]
K = bytes.fromhex(inc_ssc)+do87+do99
CC_decryp = mac_calculate(K.hex(), K_mac_NEW)
print("incremented_ssc: ",inc_ssc)
print("DO87: ",do87.hex())
print("DO99: ",do99.hex())
print("K: ",K.hex())
print("CC Decrypt: ",CC_decryp.hex().upper())
data_18 = decrypt_EIC(do87[4:].hex(), K_enc_NEW)
print("Data 18bytes: ",data_18.hex().upper())
print((unpad(data_4).hex()+data_18.hex()))
data_to_decryp = data_18[1:]
# print(data_to_decryp.hex())
# Convert hex string to ASCII
ascii_string = hex_to_ascii(data_to_decryp.hex())
print("ASCII String:", ascii_string)
