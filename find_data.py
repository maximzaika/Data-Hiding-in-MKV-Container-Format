import sys

print('|'+('-'*68)+'|' +
      '\n| Data_Verification process has been executed successfully. Please   |' +
      '\n|  follow the instructions below! Terminating process earlier might  |' +
      '\n|    leave unnecessary files behind, and might not hide your data.   |' +
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

def generate_hexa_table(hexa_word):
    '''
    generates a hexa_table in the format of .XML file
    Input: hexa input
    Return: hexa table
    '''
    hexa_word_table = []
    count_max_word = 0
    count_max_length = 0
    word = ''
    for i in range(len(hexa_word)+1):
	if count_max_word <= 63: #gets maximum length of the word
	    word += hexa_word[count_max_length] #creates a word
	    if (count_max_length + 1) == len(hexa_word): # if the remaining length != 64
	   	hexa_word_table.append(word)
		break
	    count_max_word +=1
	    count_max_length += 1
	    
	else:
	    hexa_word_table.append(word)
	    count_max_word = 0 #resets max length
	    word = ''
	
    return hexa_word_table

def find_data(file, timecode, hexa_word):
    '''
    takes users file, timecode, and the word in hexadecimal format, and compares with the data inside the
    selected timecode.
    Input: key, timecode, plaintext
    Return: Yes - text is found, No - text is not found
    '''
    hexa_table = generate_hexa_table(hexa_word)
    count_hex = 0
    with open(file) as find_data:
        accessed_timecode = False #timecode is not found
        accessed_data = False #data is not found
	data_found = True
	data_found_1 = 'no'
        for line in find_data:
            if (timecode in line) and (len(line) == 26+len(timecode)): #finds the exact timecode
		accessed_timecode = True

            if (accessed_data == True and accessed_timecode == True and data_found == True): #looks for the data inside the table
		word = ''
		for i in range(6,len(line)): #skips 6 spaces infront of the hexadecimal values and create a full hexa word
		    word += line[i]

		if hexa_table[count_hex] in word: #checks if the word inside the the hexa_table
		    count_hex += 1
		    data_found_1 = 'found' #changes the value to found
		    if data_found_1 == 'found' and len(hexa_table) == count_hex: #checks the condition
		    	return '|'+('-'*68)+'|' + '\n|                              SUCCESS!                              |' + '\n|   The verification has been successfully accomplished. The data    |' + '\n|          has been detected inside the selected timecode.           |' + '\n|'+('-'*68)+'|'
		else:
	            data_found_1 = 'not_found' #changes the value to not_found
		    data_found = False
		    if data_found_1 == 'not_found': #checks the condition
                    	return '|'+('-'*68)+'|' + '\n|                               UNSUCCESS!                           |' + '\n|     The verification is unsuccessful! The entered text has not     |' + '\n|  been found. Please, check your text, key, or the timecode again!  |' + '\n|'+('-'*68)+'|'

	    if (accessed_timecode == True) and ('<data>' in line): #skips <data> line
		accessed_data = True
    return '|'+('-'*68)+'|' + '\n|                               UNSUCCESS!                           |' + '\n|     The verification is unsuccessful! The entered text has not     |' + '\n|  been found. Please, check your text, key, or the timecode again!  |' + '\n|'+('-'*68)+'|'

def hex_to_ascii(decrypt_x):
    '''
    uses counter to make sure that 2 values converted to ascii only with spaces
    Input: decrypted text in hexadecimal format
    Return: converted decrypted text to ascii format
    '''
    tmp_ascii = ''
    ascii_ = ''
    count = 0
    for i in range(len(decrypt_x)):
        count += 1
        tmp_ascii += decrypt_x[i]
        if count == 2:
            ascii_ += str(''.join(chr(int(tmp_ascii[i:i+2], 16)) for i in range(0, len(tmp_ascii), 2))) #hex to text
            tmp_ascii = ''
            count = 0
    return ascii_

def main(file):
    #user's input
    a_word = input('  Enter the text that you have entered during\n  the data hiding process in the following format\n  \'word\' and press [ENTER]: ')
    k = input('\n  Enter the key that you have entered during\n  the data hiding process in the following format \n  \'key\' and press [ENTER]: ') #encryption key
    select_timecode = input('\n  Enter the timecode that you have selected during\n  the data hiding process in the following format \n  \'0.00\' and press [ENTER]: ') #gets encrypted

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
    print(find_data(file, select_timecode, hexa_word)) #process to find the data

        
file = sys.argv[1] #runs hidden file
main(file)
    
