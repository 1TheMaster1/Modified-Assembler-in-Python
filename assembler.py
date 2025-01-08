import re
import sys
import tkinter as tk
from tkinter import filedialog,messagebox

directive_list = ['START','END','BYTE','RESB','WORD','RESW','BASE','USE','LTORG','EQU','*']
literal_check = []
flags = {'n':{'check': 0},'i':{'check': 0},'x':{'check': 0},'b':{'check': 0},'p':{'check': 0},'e':{'check': 0}}
hex_dict = {chr(i): {'value': hex(i).upper()} for i in range(65, 91)}
block_dict = {'DEFAULT':{'counter': 0x0000, 'check': 0},'DEFAULTB':{'counter': 0x0000, 'check': 0},'CDATA':{'counter': 0x0000, 'check': 0},'CBLKS':{'counter': 0x0000, 'check': 0}}
instruction_dict = {}
label_dict = {}
literal_dict = {}
literal_address = {}
register_dict = {}
flags_dict = {}
base = {'BASE': {'name': '', 'counter': ''}}
EQU_dict = {}
file_path = ""

# Global variable to store the file path
file_path = ""

# Function to open a file dialog and save the selected file path
def select_file():
    global file_path
    file_path = filedialog.askopenfilename(title="Select Input File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    print(f"Selected file path: {file_path}")  # For demonstration, print the selected path
    root.destroy()  # Close the Tkinter window after selection

# Function to create the GUI
def create_gui():
    global root
    root = tk.Tk()
    root.title("File Selector")

    label = tk.Label(
        root,
        text="SIC/XE Assembler\n\nSelect an assembly file to process",
        padx=60,
        pady=20
    )
    select_button = tk.Button(root, text="Select Input File", command=select_file)
    label.pack()
    select_button.pack(padx=20,pady=20)
    
    # Start the Tkinter main loop
    root.mainloop()

def EQU(location_counter, block_name, line):
    words = [] #line.split()
    if words[1] == "EQU":
        if words[2] == "*":
            label_dict[words[0]] = {"value": location_counter, "block": block_name, "expression": "*"}
        else:
            label_dict[words[0]] = {"value": 0x0000, "block": block_name, "expression": words[2]}
    with open("Output/out_pass1.txt", "a") as file:
        file.write(f"{label_dict[words[0]]['value']:04X}    {line}")


def unidentified_symbol(symbol):
    with open("Output/symbTable", "r") as file:
        for line in file:
            words = line.split()
            if words[0] == "Symbol":
                continue
            if symbol not in label_dict:
                file_clearing()
                sys.exit(f"Error: {symbol} is an unidentified symbol")

def calculate_pc(locatinCounter,label):
    new_location = int(locatinCounter,16) + 3
    if label in label_dict:
       Disp = label_dict[label]['counter'] - new_location
       Disp_type = 'PC'
       if Disp < -2045 or Disp > 2045:
           Disp = label_dict[label]['counter'] - base["BASE"]['counter']
           Disp_type = 'BASE'
       
    elif label in literal_dict:
        Disp = literal_address[label]['Address'] - new_location
        Disp_type = 'PC'
        if Disp < -2045 or Disp > 2045:
           Disp = literal_address[label]['Address'] - base["BASE"]['counter']
           Disp_type = 'BASE'
    
      
    
    return Disp,Disp_type
    
def literal__function():
    with open("Intermediate/literals.txt", "r") as file:
        for line in file:
            clear_line = line.strip()            
            words = clear_line.split()
            if words[0] == "Name":
                continue
            counter = int(words[2],16) + block_dict[words[3]]['counter']  
            with open("Output/symbTable.txt", "a") as file:
                file.write(f"{words[0]:<9} {counter:04X}\n")
#                label_dict[words[0]] = {"counter": f"{counter:04X}"}

def intermediate(input_path):
    with open(input_path, "r") as file:
        for line in file:
            if ";" in line:
                line = line.split(";")[0].upper()  # Remove comments starting with ";" and make sure all letters are capital 
                line += "\n"
            else:
                line = line.upper()
            words = line.split()           # Split into words

            if not line.strip():
                continue
    
            if words[0].isdigit():
                words.pop(0)
                line = re.sub(r"^\d+\s{1}", "", line)

            with open("Intermediate/intermediate.txt", "a") as file:
                file.write(f"{line}")    

def intermediate_pass1():
    end_line = None
    block_name = 'DEFAULT'
    with open("Output/out_pass1.txt", "r") as file:
        for line in file:
            clear_line = line.strip()            
            words = clear_line.split()
            
            if words[0] == "LTORG" or words[1] == "START" or words[0] == "BASE":
                with open("Intermediate/intermediate_pass1.txt", "a") as file:
                    file.write(f"{line}")
                continue

            if words[1] == "END":
                end_line = f"{"":<16}{words[1]:<8} {words[2]}\n"
                continue
            
            if (words[1] not in directive_list and words[1] not in instruction_dict and not words[1].startswith("+")) or words[1] == "*":                
                words.pop(1)
            
            if words[1] == "USE":
                if len(words) == 2:
                    words.append("DEFAULT")
                with open("Intermediate/intermediate_pass1.txt", "a") as file:
                    file.write(f"{line}")
                block_name = words[2]
            else:
                num = int(words[0],16)
                num += block_dict[block_name]['counter']
                if len(words) == 2:
                    hex_num = f"{num:04X}"
                    with open("Intermediate/intermediate_pass1.txt", "a") as file:
                        file.write(f"{hex_num:<16}{words[1]}\n")
                if len(words) == 3:
                    hex_num = f"{num:04X}"
                    with open("Intermediate/intermediate_pass1.txt", "a") as file:
                        file.write(f"{hex_num:<16}{words[1]:<8} {words[2]}\n")  
    with open("Intermediate/intermediate_pass1.txt", "a") as file:
        file.write(f"{end_line}\n")                              

# Function to process a single line
def process_line(line, location_counter, block_name):
    if ";" in line:
        line = line.split(";")[0].upper()  # Remove comments starting with ";" and make sure all letters are capital 
        line += "\n"
    else:
        line = line.upper()
    words = line.split()           # Split into words

    if not line.strip():
        return location_counter, block_name
    
    if words[0].isdigit():
        words.pop(0)
        line = re.sub(r"^\d+\s{1}", "", line)

    if "START" in words:
        with open("Output/out_pass1.txt", "a") as file:
            file.write(f"        {line}")
    elif words[0] == "USE" or words[0] == "LTORG" or words[0] == "BASE" or words[0] == "END":
        pass
    else:    
        with open("Output/out_pass1.txt", "a") as file:
            file.write(f"{location_counter:04X}    {line}")

    # If the line contains a label, split the label and the instruction
    if words[0] not in directive_list and words[0] not in instruction_dict and not words[0].startswith("+"):
        label = words[0]
        label_dict[label] = {"counter": location_counter, "block": block_name}
        words.pop(0)

    # Now, process the instruction
    if words[0] in directive_list:
        # For directives
        if words[0] == "START":
            # Starting address is specified after the `START` directive
            location_counter = int(words[1])
            label_dict.popitem()
        elif words[0] == "BYTE":
            operand = words[1]
            if operand.startswith("X"):  # Hexadecimal constant
                location_counter += len(operand[2:-1]) // 2  # Each pair of hex digits is 1 byte
            elif operand.startswith("C"):  # Character constant
                location_counter += len(operand[2:-1])  # Each character is 1 byte
        elif words[0] == "WORD":
            location_counter += 0x03  # `WORD` takes 3 bytes
        elif words[0] == "RESB":
            location_counter += int(words[1])  # `RESB` reserves bytes
        elif words[0] == "RESW":
            location_counter += 0x03 * int(words[1])  # `RESW` reserves words (3 bytes each)
        elif words[0] == "END":
            block_dict[block_name]['counter'] = location_counter # Record last location counter for final block
            with open("Output/out_pass1.txt", "a") as file:
                file.write(f"{location_counter:04X}    {line}\n")
            if literal_dict:
                for item in literal_dict:
                    if item not in literal_check:
                        literal_check.append(item)
                        with open("Intermediate/literals.txt", "a") as file:
                            file.write(f"{item:<5}\t{literal_dict[item]['value']:<5}\t{location_counter:04X}\t{block_name}\n") 
                        with open("Output/out_pass1.txt", "a") as file:
                            file.write(f"{location_counter:04X}    *       {item}\n")
                        location_counter += len(literal_dict[item]['value']) // 2
                    literal_dict.clear
        elif words[0] == "USE":
            if len(words) == 1:
                words.append("DEFAULT")
            if words[1] not in block_dict:
                file_clearing()
                sys.exit(f"Error: {words[1]} is an unidentified block")
            block_dict[block_name]['counter'] = location_counter # Record last location counter for previous block
            location_counter = block_dict[words[1]]['counter']
            block_name = words[1]
            block_dict[words[1]]['check'] = 1       
            with open("Output/out_pass1.txt", "a") as file:
                file.write(f"{location_counter:04X}    {line}")
        elif words[0] == "LTORG":
            with open("Output/out_pass1.txt", "a") as file:
                file.write(f"        {line}")
            for item in literal_dict:
                if item not in literal_check:
                    literal_check.append(item)
                    with open("Intermediate/literals.txt", "a") as file:
                        file.write(f"{item:<5}\t{literal_dict[item]['value']:<5}\t{location_counter:04X}\t{block_name}\n") 
                    with open("Output/out_pass1.txt", "a") as file:
                        file.write(f"{location_counter:04X}    *       {item}\n")
                    location_counter += len(literal_dict[item]['value']) // 2
                literal_dict.clear
        elif words[0] == "BASE":
            base["BASE"]["name"] = words[1] 
            with open("Output/out_pass1.txt", "a") as file:
                file.write(f"        {line}")
                
    elif words[0] in instruction_dict or words[0].startswith("+"):
        # For other instructions
        if words[0].startswith("+"):
            location_counter += 0x04
        elif instruction_dict[words[0]]['format'] == '4F':
            location_counter += 0x04
        elif instruction_dict[words[0]]['format'] == '3/4':
            location_counter += 0x03
        elif instruction_dict[words[0]]['format'] == '2':
            location_counter += 0x02
        elif instruction_dict[words[0]]['format'] == '1':
            location_counter += 0x01
                
        if len(words) > 1 and words[1].startswith("="):
            operand = words[1]
            if operand.startswith("=X"):    # Hexadecimal constant
                value = operand[3:-1]
            elif operand.startswith("=C"):  # Character constant
                value = hex_dict[operand[3]]['value'][2:]
                i = 4
                while operand[i] != '\'': 
                    value += hex_dict[operand[i]]['value'][2:]
                    i += 1
            if words[1] not in literal_dict:
                literal_dict[words[1]] = {"value": value}
            
#    if block_dict['DEFAULT']['check'] == 1 and block_dict['DEFAULTB']['check'] == 1 and block_dict['CDATA']['check'] == 1 and block_dict['CBLKS']['check'] == 1:
#        file_clearing()
#        sys.exit("Error: Can not use more than three blocks")

    return location_counter, block_name

def import_insructions():
    with open("Config/instructions.txt", "r") as file:
        # Process each line in the file
        for line in file:
            # Strip leading/trailing whitespaces and split the line into parts
            parts = line.strip().split()
            instruction = parts[0]  # The instruction (e.g., ADD)
            format = parts[1]       # The format (e.g., 3/4)
            opcode = parts[2]       # The opcode (e.g., 18)

            # Add the instruction to the dictionary
            instruction_dict[instruction] = {"format": format, "opcode": opcode}

def import_register():
    with open("Config/registers.txt", "r") as file:
        # Process each line in the file
        for line in file:
            # Strip leading/trailing whitespaces and split the line into parts
            parts = line.strip().split()
            register = parts[0]  
            number = parts[1]      
            register_dict[register] = {"Number": number}
def import_literals():
    with open("Output/symbTable.txt", "r") as file:
        for line in file:
            parts = line.strip().split()
            if parts[0].startswith('='):
                literal = parts[0]  
                address = parts[1]
                if literal == "Name":
                    continue      
                literal_address[literal] = {"Address": int(address,16)}
def import_flags():
    with open("Config/flags.txt", "r") as file:
        for line in file:
            parts = line.strip().split()
            Flag = parts[0]  
            Number = parts[1]
            flags_dict[Flag] = {"Number": Number}
    


def file_clearing():
    # Clear out_pass1.txt
    with open("Output/out_pass1.txt", "w") as file:
        pass 
    # Clear out_pass2.txt
    with open("Output/out_pass2.txt", "w") as file:
        pass
    # Clear symbTable.txt
    with open("Output/symbTable.txt", "w") as file:
        pass 
    # Clear HTME.txt
    with open("Output/HTME.txt", "w") as file:
        pass
    # Clear blocks.txt
    with open("Intermediate/blocks.txt", "w") as file:
        pass
    # Clear literals.txt
    with open("Intermediate/literals.txt", "w") as file:
        pass
    # Clear intermediate.txt
    with open("Intermediate/intermediate.txt", "w") as file:
        pass
     # Clear intermediate_pass1.txt
    with open("Intermediate/intermediate_pass1.txt", "w") as file:
        pass  
      # Clear intermediate_pass2.txt
    with open("Intermediate/intermediate_pass2.txt", "w") as file:
        pass  

# Main function to read from a file and produce pass1
def pass1(input_path):
    # Initial variables and initialization of some files
    location_counter = 0x0000
    block_name = 'DEFAULT'
    block_count = 0
    length = 0x0000
    with open("Intermediate/blocks.txt", "a") as file:
        file.write(f" Name     Number  Adderss  Length\n")
    with open("Intermediate/literals.txt", "a") as file:
        file.write(f" Name\tValue\tAddress\n")

    # Open the file and read it line by line
    with open(input_path, "r") as file:
        for line in file:
            location_counter, block_name = process_line(line, location_counter, block_name)

    # Write the blocks and their addresses
    for key in block_dict:
        if block_dict[key]['check'] == 1:
            with open("Intermediate/blocks.txt", "a") as file:
                file.write(f"{key}   \t{block_count}      {(length):04X}     {block_dict[key]['counter']:04X}\n")
                temp = length 
                length += block_dict[key]['counter']
                block_dict[key]['counter'] = temp
                block_count += 1  

    # Write the labels and their locations
    with open("Output/symbTable.txt", "a") as file:
        file.write(f"Symbol \tLocation\n")
        for label in label_dict:
            block = label_dict[label]['block']
            file.write(f"{label:<9} {label_dict[label]['counter'] + block_dict[block]['counter']:04X}\n")
            label_dict[label]['counter'] =  label_dict[label]['counter'] + block_dict[block]['counter']

    base["BASE"]['counter'] = label_dict[base["BASE"]['name']]['counter']          

def pass2():
    with open("Intermediate/intermediate_pass1.txt", "r") as input_file, open("Intermediate/intermediate_pass2.txt", "a") as output_file:
        for line in input_file:
            # Process each line to extract the instruction and find the opcode
            words = line.split()
            try:
                if len(words)>1 and words[1].startswith('+'):
                    New_word = words[1].replace('+',"")
                    opcode = instruction_dict[New_word]['opcode']
                    indexed = words[2].split(",")
                    if len(indexed) > 1:
                        xpbe = '9' 
                    else:
                       xpbe = '1'
                    if words[2].startswith('#'):
                       opcode= int(opcode,16) + int('0x01',16)  # Convert opcode to int before adding
                       label = words[2].replace('#',"") 
                    elif words[2].startswith('@'):
                        label = words[2].replace('@',"")
                        opcode= int(opcode,16) + int('0x02',16)  # Convert opcode to int before adding
                    else:
                        label = words[2] 
                        opcode= int(opcode,16) + int('0x03',16)        

                    if label[0].isdigit():
                           operand_code = int(label)
                           xpbe = '0'
                    else:
                           if label not in label_dict and label not in literal_dict:
                                    raise Exception(f"{label} not found in SymbleTable")
                           operand_code = label_dict[label]['counter']
                    output_file.write(f"{line.rstrip():<40}\t{(opcode):02X}{xpbe}{(operand_code):05X}\n")


                elif len(words)>1 and words[1] in instruction_dict:
                    if instruction_dict[words[1]]['format'] == '1':
                         opcode = instruction_dict[words[1]]['opcode']
                         output_file.write(f"{line.rstrip():<40}\t{opcode}\n")  # Append opcode to the line
                    elif instruction_dict[words[1]]['format'] == '2':
                         oprands = words[2].split(',')
                         if len(oprands) <2:
                             oprands.append('A')
                         opcode = instruction_dict[words[1]]['opcode']
                         output_file.write(f"{line.rstrip():<40}\t{opcode}{register_dict[oprands[0]]['Number']}{register_dict[oprands[1]]['Number']}\n")  # Append opcode to the line
                    elif instruction_dict[words[1]]['format'] == '3/4':
                         opcode = instruction_dict[words[1]]['opcode']

                         if words[2].startswith('#'):
                            opcode= int(opcode,16) + int('0x01',16)  # Convert opcode to int before adding
                            label = words[2].replace('#',"")
                         elif words[2].startswith('@'):
                             label = words[2].replace('@',"")
                             opcode= int(opcode,16) + int('0x02',16)  # Convert opcode to int before adding
                         else:
                             label = words[2] 
                             opcode= int(opcode,16) + int('0x03',16)        

                         if label[0].isdigit():
                                operand_code = int(label)
                                xbpe = '0'
                         else:
                                if label not in label_dict and label not in literal_dict:
                                    raise Exception(f"{label} not found in SymbleTable")
                                operand_code,Disp_type = calculate_pc(words[0],label) 
                                indexed = words[2].split(",")
                                if len(indexed) > 1 and Disp_type == "PC":
                                    xbpe = 'a' 
                                elif len(indexed) > 1 and Disp_type == "BASE":
                                    xbpe = 'c'
                                elif len(indexed) == 1 and Disp_type == "BASE":
                                    xbpe = '4'
                                else:
                                   xbpe = '2'
                         output_file.write(f"{line.rstrip():<40}\t{(opcode):02X}{xbpe.upper()}{(operand_code):03X}\n")  # Append opcode to the line

                    elif instruction_dict[words[1]]['format'] == '4F':

                         oprands = words[2].split(",")
                         if len(oprands) == 3:
                             opcode = instruction_dict[words[1]]['opcode']
                             Reg = int(register_dict[oprands[0]]['Number'],16)
                             lab = hex(label_dict[oprands[1]]['counter'])[2:].zfill(5)
                             if oprands[1] not in label_dict and label not in literal_dict:
                                    raise Exception(f"{label} not found in SymbleTable")
                             
                             Flag =int(flags_dict[oprands[2]]['Number'],16)
                             Reg_bin = bin(Reg)[2:].zfill(4)


                             opcode= int(opcode,16) + int(Reg_bin[:-2],2)  # Convert opcode to int before adding
                             FlagAndReg = hex(int(Reg_bin[2:].zfill(2) + bin(int(Flag))[2:].zfill(2),2))[2:].zfill(1)


                             output_file.write(f"{line.rstrip():<40}\t{hex(opcode)[2:].upper()}{FlagAndReg}{lab}\n")

                         elif len(oprands) == 2:
                             opcode = instruction_dict[words[1]]['opcode']
                             lab = hex(label_dict[oprands[0]]['counter'])[2:].zfill(5).upper()
                             if oprands[0] not in label_dict and label not in literal_dict:
                                    raise Exception(f"{label} not found in SymbleTable")
                             Flag = flags_dict[oprands[1]]['Number'] 
                             
                             output_file.write(f"{line.rstrip():<40}\t{opcode}{Flag}{lab}\n")

                elif  len(words)>1 and words[1].startswith('='):
                        operand = words[1]
                        operand = operand.replace('=',"")

                        if operand.startswith("X"):  # Hexadecimal constant
                            opcode = operand[2:-1]
                            opcode_str = str(opcode)
                        elif operand.startswith("C"):  # Character constant
                            operand = operand[2:-1]
                            opcode_str = ""
                            for op in operand:
                                opcode_str += hex(ord(op))[2:].upper()

                        output_file.write(f"{line.rstrip():<40}\t{opcode_str}\n")  # Append opcode to the line

                elif len(words)>1 and words[1] in directive_list:
                    if words[1] == 'BYTE':
                        operand = words[2]
                        if operand.startswith("X"):  # Hexadecimal constant
                            opcode = operand[2:-1]
                        elif operand.startswith("C"):  # Character constant
                            opcode = operand[2:-1] # Each character is 1 byte
                        output_file.write(f"{line.rstrip():<40}\t{opcode}\n")  # Append opcode to the line
                    elif words[1] == 'WORD':
                        opcode = int(words[2])
                        output_file.write(f"{line.rstrip():<40}\t{(opcode):06X}\n")  # Append opcode to the line
                if words and (words[0] in directive_list or(words[1] in directive_list and words[1] not in ["BYTE", "WORD"] and  not(words[1].startswith('=')) )):
                     output_file.write(f"{line.rstrip():<40}\n")
            except Exception as ex:
                print("Pass two fail")
                messagebox.showerror("showerror", f"Pass two fail: {ex}") 

def HTME_process_line(line,Tstart,Trecord,Mrecord):
    clear_line = line.strip()            
    words = clear_line.split()
    length = 0x0000    
    if words[0] == "LTORG":
        words.append("Hello")

    if words[1] == "START":
        with open("Intermediate/blocks.txt", "r") as file:
            for line in file:
                clear_line = line.strip()            
                words_block = clear_line.split()
                if words_block[3] == "Length":
                    continue
                length += int(words_block[3],16)
        with open("Output/HTME.txt", "a") as file:
            file.write(f"H {words[0]:x<6} {int(words[2],16):06X} {length:06X}\n")
    elif (words[1] == "USE" or words[1] == "RESB" or words[1] == "RESW") and Trecord != "None":
        with open("Output/HTME.txt", "a") as file:
            T = Tstart + " " + f"{len(Trecord.replace(" ", ""))//2:02X}" + " " + Trecord
            file.write(f"{T}\n")
            Tstart = "None"
            Trecord = "None"
    elif words[0] == "END":
        with open("Output/HTME.txt", "a") as file:
            T = Tstart + " " + f"{len(Trecord.replace(" ", ""))//2:02X}" + " " + Trecord
            file.write(f"{T}\n")  
            file.write(f"{Mrecord}")
            file.write(f"E {int(words[1]):06X}")
    elif Trecord == "None" and (words[1] in ["BYTE","WORD"] or words[1] in instruction_dict or words[1].startswith("+") or words[1].startswith("=")):
        Tstart = "T " + words[0].zfill(6)
        num = len(words)
        Trecord = words[num - 1]
    elif Trecord != "None" and (words[1] in ["BYTE","WORD"] or words[1] in instruction_dict or words[1].startswith("+") or words[1].startswith("=")):
        num = len(words)
        temp = Trecord + " " + words[num - 1]
        if len(temp.replace(" ", ""))//2 > 30:
            with open("Output/HTME.txt", "a") as file:
                T = Tstart + " " + f"{len(Trecord.replace(" ", ""))//2:02X}" + " " + Trecord
                file.write(f"{T}\n")
                Tstart = "None"
                Trecord = "None"
        else:
            Trecord = temp

    if words[0] != "LTORG" and not words[1].startswith("=") and words[0] != "BASE" and words[0] != "END" and words[1] not in directive_list and (words[1].startswith("+") or instruction_dict[words[1]]['format'] == "4F") :
        Mrecord += "M " + f"{int(words[0],16)+1:06X}" + " " + "05" + "\n"  

    return Tstart,Trecord,Mrecord 

def HTME():
    Tstart = "None"
    Trecord = "None"
    Mrecord = ""
    # Open the file and read it line by line
    with open("Intermediate/intermediate_pass2.txt", "r") as file:
        for line in file:
            Tstart,Trecord,Mrecord = HTME_process_line(line,Tstart,Trecord,Mrecord)  

def write_pass2():
    lines = []
    # Specify the file to read
    file_name = "Intermediate/intermediate_pass2.txt"

    # Define the position to start reading from 
    start_position = 40  # Start reading from the 11th character (0-based index)

    # Open the file and process each line
    with open(file_name, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            # Remove newline characters
#            line = line.strip()
        
            # Extract the substring from the specified position to the end
            if len(line) >= start_position:
                substring = line[start_position:]
                lines.append(substring)
            else:
                lines.append("")
    with open("Output/out_pass1.txt", "r") as read_file, open("Output/out_pass2.txt", "w") as write_file:
        i = 0
        for line in read_file:
            line = line.rstrip()
            write_file.write(f"{line:<36}{lines[i]}")
            i += 1

def main():
    create_gui()  # Call the GUI to select the file path
    file_clearing()
    import_insructions()
    import_register()
    import_flags()
    intermediate(file_path)
    pass1(file_path)
    intermediate_pass1()
    literal__function()
    import_literals()
    pass2()
    write_pass2()
    HTME()

main()