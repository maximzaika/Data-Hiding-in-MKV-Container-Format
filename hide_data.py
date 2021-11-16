import sys

print('|'+('-'*68)+'|' +
      '\n|  Data_Hiding process has been executed successfully. Please follow |' +
      '\n|   the instructions below! Terminating process earlier might leave  |' +
		'\n|        unnecessary files behind, and might not hide your data!     |' +
      '\n|'+('-'*68)+'|')

def text2ascii(a_word):
    '''
    Converts text to ascii with all the required spaces.
    Spaces are later converted using hexadecimal values.
    Input: users text
    Return: text converted to ascii
    '''
    ascii_store = ''
    for i in range(len(a_word)):
        ascii_ = str(ord(a_word[i]))
        if i != len(a_word): #add spaces to ascii's
            ascii_store += ascii_ + ' '
        else:
            ascii_store += ascii_
    return ascii_store

def pumpKey(a_word,k):
    '''
    Whenever the length of the key is less the length of the text. Key size increases to
    to match text size by looping itself
    Input: user word and key
    Return: larger key
    '''
    new_k = ''
    count = 0
    for i in range(len(a_word)):
        if count+1 == len(k):
            new_k += str(k[count])
            count = 0
        else:
            new_k += str(k[count])
            count += 1
    k = new_k
    return k

def encr_ascii(ascii_x, ascii_k, x):
    '''
    Encryption example:
                        1. formula: X_i + K_(i mod(len X)) + 33
                        2. For example X = hello (h in ascii = 104)
                                       K = maxim (m in ascii = 109)
                        3. Iteration 1 ---> X_1 + K_(1 mod(5)) + 33 = 1+1+33 = 35 (35 in ascii = '#')
                        4. Iteration 2 ---> X_2 + K_(2 mod(5)) + 33 = 0+0+33 = 33 (33 in ascii = '!')
                        5. Iteration 3 ---: X_3 + K_(3 mod(5)) + 33 = 4+9+33 = 40 (46 in ascii = '.')
                        6. Ecnrypted text for h ---> #!.
    '''
    encrypt_x = '' #stores encrypted part of the text
    count = 0
    for i in range(len(ascii_x)):
        k_val = int(i % len(x)) # i mod (len X)

        count += 1
        if count > len(ascii_k): # if out of range, restarts the k_val
            k_val = len(ascii_x) - k_val 
            count = 0

        k_mod = int(ascii_k[k_val]) # K_(1 mod (len(x)), K_(2 mod (len(x)) etc.
        encrypt = int(ascii_x[i]) + k_mod + 33 # sum up all the previous combinations
        encrypt_x += str(chr(encrypt)) # gets the ASCII_Char (symbol/digit/letter etc.)

    return encrypt_x

def decr_ascii(encrypt_x, ascii_k, x):
    '''
    Remark: ASCII_Val ---> converted version from ASCII_Char (from encryption)
    Decryption example:
                        1.  formula: ASCII_Val - K_(i mod(len X)) + 33
                        2.  For example from ecnryption function we get: #!(
                        2.1 # = 35, ! = 33, . = 46
                        3.  Iteration 1 ---> 35 - K_(1 mod(5)) - 33 = 35-1-33 = 1
                        4.  Iteration 2 ---> 33 - K_(2 mod(5)) - 33 = 35-0-33 = 0
                        5.  Iteration 3 ---: 46 - K_(3 mod(5)) - 33 = 46-9-33 = 4
                        6.  Ecnrypted text for 104 ---> h (for hello)
    '''
    decrypt_x = ''
    count = 0
    for i in range(len(encrypt_x)):
        ascii_ = ord(encrypt_x[i]) #get ascii value
        k_val = int(i % len(x)) # i mod (len X)

        count += 1
        if count > len(ascii_k): # if out of range, restarts the k_val
            k_val = len(ascii_x) - k_val
            count = 0

        k_mod = int(ascii_k[k_val]) # K_(1 mod (len(x)), K_(2 mod (len(x)) etc.
        decrypt = ascii_ - k_mod - 33  # minus all the previous combinations
        decrypt_x += str(decrypt)

    return decrypt_x

def convert2hex(store_a_word):
    '''
    counts how many times the letter has been converted to hexadecimal.
    If the counter becomes the same size as the word, then it gets added
    to the list hex_list, and then hex_word resets. Repeats the process
    Input: users text
    Return: the list hexadecimal values
    '''
    hex_word = ''
    hex_list = []
    for i in range(len(store_a_word)): # stores the list of hexes
        count = 0
        for letter in store_a_word[i]:
            count += 1 
            hex_word += hex(ord(letter))[2:]

            if count == len(store_a_word[i]):
                count = 0
                hex_list.append(hex_word)
                hex_word = ''

    combined_hex = '' #stores the combination of hexes from hex_list
    for i in range(len(hex_list)):
        combined_hex += hex_list[i]

    return combined_hex

def get_timecodes(file_timecode):
    '''
    Reads the file, identifies all the available timecodes
    Input: XML file
    Return: all the timecodes in the form of the table
    '''
    with open(file_timecode) as file_timecode:
        all_timecodes = [] # stores the timecodes
        
        for line in file_timecode:
            if '<timecode>' in line: #identifies if the <timecode> is inside the text
                word = '' #stores the combination of symbols/digits as full timecode
                for x in range(len(line)):
                    if (line[x] not in '<timecode>') and (line[x] not in '</timecode>'):
                        word += line[x].rstrip() #combines the symbols/digits with the timecode

                all_timecodes.append(word) #stores the timecode in the table

        return all_timecodes

def return_timecodes(all_timecodes):
    '''
    Called: user needs to type 'help' to call this function
    Input: Identified timecodes are taken as the input
    Return: 7 rows of timecodes
    '''
    print('|'+('-'*68)+'|' +
          '\n|   The following timecodes have been detected in the file. Select   |' +
          '\n|      one of the following timecodes to hide your data inside.      |' + 
          '\n|'+('-'*68)+'|')
    
    max_size = 0
    for i in range(len(all_timecodes)):
	if len(all_timecodes[i]) > max_size:
	    max_size = len(all_timecodes[i])
    
    word = ''
    count = 0 # used to create the columns (in this case 7)
    for i in range(len(all_timecodes)):
        while len(all_timecodes[i]) != max_size: # add proper spaces if the length of the timecode <=6
            all_timecodes[i] += ' '

        word += '| ' + all_timecodes[i] + ' |' # combines all the timecodes

        count += 1
        if count == 7: #prints 7 values at the time, resets word, count
            print(word)
            word = ''
            count = 0

    print('|'+('-'*68)+'|')

def hide_data(file, timecode, hexa_word):
    with open(file) as f_old, open(".hidden_data.xml", "w") as f_new:
        accessed_timecode = False
        for line in f_old:
            f_new.write(line)
            
            if (timecode in line) and (len(line) == 26+len(timecode)): #finds the exact timecode
                accessed_timecode = True

            if (accessed_timecode == True) and ('<data>' in line): #hide the encrypted data after <data> in hexadecimal form
                for i in range(len(hexa_word)):
                    f_new.write(hexa_word[i])
                accessed_timecode = False

    print('|'+('-'*68)+'|' +
          '\n|   The data has been successfully hidden. The file is currently     |' +
          '\n|   processing by the system. The processing time depends on the     |' +
          '\n|  MKV file size, and as well as on compatability of your hardware.  |' +
          '\n|      Use the [Hidden Text, Encryption Key, Timecode] to verify     |' +
          '\n|         the existence of your hidden text inside the file.         |' +
          '\n|'+('-'*68)+'|')
                
def main(file):
    #user's input
    a_word = input('  Enter the text or word that needs to be inserted\n  in the following format \'word\' and press [ENTER]: ') #gets encrypted
    k = input('  Enter the key that will be used to decrypt your text or words\n  in the following format \'key\' and press [ENTER]: ') #used to decrypt
    k = str(k)

    #when key is smaller than a text, it increases the key size
    if len(k) < len(a_word):
        k = pumpKey(a_word,k)

    #convert to ascii
    ascii_a_word = text2ascii(a_word)
    ascii_k = text2ascii(k)

    #convert to hexadecimal
    ascii_a_word = convert2hex(ascii_a_word)
    ascii_k = convert2hex(ascii_k)
    
    #if the size of ascii_k is still < ascii_a_word then need to pump
    if len(ascii_k) < len(ascii_a_word):
        ascii_k = pumpKey(ascii_a_word,ascii_k)
        
    #encrypts the converted to ascii text
    encrypt_a_word = encr_ascii(ascii_a_word, ascii_k, a_word)

    #convert encrypted text to hexadecimal
    hex_list = convert2hex(encrypt_a_word) # calls the function to convert the text to hexadecimal
    hexa_word = ''
    for i in range(len(hex_list)):
        hexa_word += hex_list[i] #gets pure hexadecimal word

    while True:
        all_timecodes = get_timecodes(file) #shows all the available timecodes to the user
        select_timecode = input('\n  Select a timecode where the data needs to be hidden,\n  or type \'help\' to display the timecodes: ') #place where the data gets inserted
    
        if select_timecode not in all_timecodes and select_timecode != 'help': # no timecode
            print('|'+('-'*68)+'|' +
          			'\n|               Selected time code is not found, try again!          |' +
          			'\n|'+('-'*68)+'|')

        elif select_timecode == 'help': #shows timecodes
            return_timecodes(all_timecodes)
                    
        else:
            hide_data(file, select_timecode, hexa_word) #process to hide the data
            break

file = sys.argv[1]
main(file)
    
