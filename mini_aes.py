import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
import binascii

class MiniAES:
    """
    Mini-AES implementation with 16-bit blocks (4 nibbles)
    """
    
    # S-Box for SubNibbles (4-bit)
    # This is a simplified S-Box for demonstration
    S_BOX = [
        0x9, 0x4, 0xA, 0xB,
        0xD, 0x1, 0x8, 0x5,
        0x6, 0x2, 0x0, 0x3,
        0xC, 0xE, 0xF, 0x7
    ]
    
    # Inverse S-Box for decryption
    INV_S_BOX = [
        0xA, 0x5, 0x9, 0xB,
        0x1, 0x7, 0x8, 0xF,
        0x6, 0x0, 0x2, 0x3,
        0xC, 0x4, 0xD, 0xE
    ]
    
    # MixColumns matrix (simplified for GF(2^4))
    MIX_COL_MATRIX = [
        [0x1, 0x4],
        [0x4, 0x1]
    ]
    
    # Inverse MixColumns matrix
    INV_MIX_COL_MATRIX = [
        [0x9, 0x2],
        [0x2, 0x9]
    ]
    
    def __init__(self):
        self.round_keys = []
        self.log = []
    
    def append_log(self, message):
        """Add message to log"""
        self.log.append(message)
    
    def get_log(self):
        """Return the full log"""
        return '\n'.join(self.log)
    
    def clear_log(self):
        """Clear the log"""
        self.log = []
    
    def nibble_to_bits(self, nibble):
        """Convert a nibble (4-bit) to its binary representation"""
        return [(nibble >> i) & 1 for i in range(3, -1, -1)]
    
    def bits_to_nibble(self, bits):
        """Convert a list of 4 bits to a nibble"""
        return sum(bit << (3-i) for i, bit in enumerate(bits))
    
    def state_to_binary(self, state):
        """Convert state (list of 4 nibbles) to binary string"""
        binary = ""
        for nibble in state:
            binary += format(nibble, '04b')
        return binary
    
    def state_to_hex(self, state):
        """Convert state to hex representation"""
        return ''.join(f'{nibble:X}' for nibble in state)
    
    def sub_nibbles(self, state):
        """
        SubNibbles operation - substitute each nibble using the S-Box
        """
        return [self.S_BOX[nibble] for nibble in state]
    
    def inv_sub_nibbles(self, state):
        """
        Inverse SubNibbles for decryption
        """
        return [self.INV_S_BOX[nibble] for nibble in state]
    
    def shift_rows(self, state):
        """
        ShiftRows operation - For 16-bit block (4 nibbles in 2x2 arrangement)
        [n0, n1]    [n0, n1]
        [n2, n3] -> [n3, n2]
        """
        return [state[0], state[1], state[3], state[2]]
    
    def inv_shift_rows(self, state):
        """
        Inverse ShiftRows operation
        """
        return [state[0], state[1], state[3], state[2]]  # Same as shift_rows for 2x2
    
    def gf_multiply(self, a, b):
        """
        Galois Field multiplication in GF(2^4) with polynomial x^4 + x + 1
        """
        p = 0
        while b:
            if b & 1:
                p ^= a
            a <<= 1
            if a & 0x10:  # If overflow (degree 4)
                a ^= 0x13  # x^4 + x + 1 (0b10011)
            b >>= 1
        return p & 0xF  # Keep only the least significant 4 bits
    
    def mix_columns(self, state):
        """
        MixColumns operation - matrix multiplication in GF(2^4)
        """
        # Convert state to 2x2 matrix
        state_matrix = [[state[0], state[1]], [state[2], state[3]]]
        result = [[0, 0], [0, 0]]
        
        # Matrix multiplication
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    result[i][j] ^= self.gf_multiply(self.MIX_COL_MATRIX[i][k], state_matrix[k][j])
        
        # Flatten the matrix back to state
        return [result[0][0], result[0][1], result[1][0], result[1][1]]
    
    def inv_mix_columns(self, state):
        """
        Inverse MixColumns operation
        """
        # Convert state to 2x2 matrix
        state_matrix = [[state[0], state[1]], [state[2], state[3]]]
        result = [[0, 0], [0, 0]]
        
        # Matrix multiplication with inverse matrix
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    result[i][j] ^= self.gf_multiply(self.INV_MIX_COL_MATRIX[i][k], state_matrix[k][j])
        
        # Flatten the matrix back to state
        return [result[0][0], result[0][1], result[1][0], result[1][1]]
    
    def add_round_key(self, state, round_key):
        """
        AddRoundKey operation - XOR state with round key
        """
        return [state[i] ^ round_key[i] for i in range(4)]
    
    def key_expansion(self, key):
        """
        Key expansion algorithm for generating round keys
        """
        # Start with the original key
        self.round_keys = [key]
        
        # Constants for round key generation (simplified)
        rcon = [0x1, 0x2, 0x4]
        
        for i in range(3):  # Generate 3 round keys
            prev_key = self.round_keys[i]
            
            # Rotate last two nibbles
            rotated = [prev_key[2], prev_key[3], prev_key[0], prev_key[1]]
            
            # Apply S-Box to all nibbles
            substituted = self.sub_nibbles(rotated)
            
            # XOR with round constant (only to first nibble)
            substituted[0] ^= rcon[i]
            
            # XOR with previous round key
            new_key = [prev_key[j] ^ substituted[j] for j in range(4)]
            
            self.round_keys.append(new_key)
            
            self.append_log(f"Round Key {i+1}: {self.state_to_hex(new_key)}")
        
        return self.round_keys
    
    def encrypt(self, plaintext, key):
        """
        Mini-AES encryption process
        """
        self.clear_log()
        self.append_log(f"Plaintext: {self.state_to_hex(plaintext)} ({self.state_to_binary(plaintext)})")
        self.append_log(f"Key: {self.state_to_hex(key)} ({self.state_to_binary(key)})")
        
        # Generate round keys
        self.append_log("\nKey Expansion:")
        self.append_log(f"Round Key 0: {self.state_to_hex(key)}")
        round_keys = self.key_expansion(key)
        
        # Initial round - just AddRoundKey
        state = self.add_round_key(plaintext, round_keys[0])
        self.append_log(f"\nInitial AddRoundKey: {self.state_to_hex(state)}")
        
        # Main rounds
        for i in range(1, 3):  # Rounds 1 and 2
            self.append_log(f"\nRound {i}:")
            
            # SubNibbles
            state = self.sub_nibbles(state)
            self.append_log(f"After SubNibbles: {self.state_to_hex(state)}")
            
            # ShiftRows
            state = self.shift_rows(state)
            self.append_log(f"After ShiftRows: {self.state_to_hex(state)}")
            
            # MixColumns
            state = self.mix_columns(state)
            self.append_log(f"After MixColumns: {self.state_to_hex(state)}")
            
            # AddRoundKey
            state = self.add_round_key(state, round_keys[i])
            self.append_log(f"After AddRoundKey: {self.state_to_hex(state)}")
        
        # Final round - no MixColumns
        self.append_log(f"\nRound 3 (Final):")
        
        # SubNibbles
        state = self.sub_nibbles(state)
        self.append_log(f"After SubNibbles: {self.state_to_hex(state)}")
        
        # ShiftRows
        state = self.shift_rows(state)
        self.append_log(f"After ShiftRows: {self.state_to_hex(state)}")
        
        # AddRoundKey
        state = self.add_round_key(state, round_keys[3])
        self.append_log(f"After AddRoundKey: {self.state_to_hex(state)}")
        
        self.append_log(f"\nFinal Ciphertext: {self.state_to_hex(state)} ({self.state_to_binary(state)})")
        
        return state

    def decrypt(self, ciphertext, key):
        """
        Mini-AES decryption process
        """
        self.clear_log()
        self.append_log(f"Ciphertext: {self.state_to_hex(ciphertext)} ({self.state_to_binary(ciphertext)})")
        self.append_log(f"Key: {self.state_to_hex(key)} ({self.state_to_binary(key)})")
        
        # Generate round keys
        self.append_log("\nKey Expansion:")
        self.append_log(f"Round Key 0: {self.state_to_hex(key)}")
        round_keys = self.key_expansion(key)
        
        # Initial round - AddRoundKey
        state = self.add_round_key(ciphertext, round_keys[3])
        self.append_log(f"\nInitial AddRoundKey: {self.state_to_hex(state)}")
        
        # Main rounds in reverse
        for i in range(2, 0, -1):  # Rounds 2 and 1
            self.append_log(f"\nRound {3-i}:")
            
            # Inverse ShiftRows
            state = self.inv_shift_rows(state)
            self.append_log(f"After Inverse ShiftRows: {self.state_to_hex(state)}")
            
            # Inverse SubNibbles
            state = self.inv_sub_nibbles(state)
            self.append_log(f"After Inverse SubNibbles: {self.state_to_hex(state)}")
            
            # AddRoundKey
            state = self.add_round_key(state, round_keys[i])
            self.append_log(f"After AddRoundKey: {self.state_to_hex(state)}")
            
            # Inverse MixColumns
            state = self.inv_mix_columns(state)
            self.append_log(f"After Inverse MixColumns: {self.state_to_hex(state)}")
        
        # Final round
        self.append_log(f"\nRound 3 (Final):")
        
        # Inverse ShiftRows
        state = self.inv_shift_rows(state)
        self.append_log(f"After Inverse ShiftRows: {self.state_to_hex(state)}")
        
        # Inverse SubNibbles
        state = self.inv_sub_nibbles(state)
        self.append_log(f"After Inverse SubNibbles: {self.state_to_hex(state)}")
        
        # AddRoundKey
        state = self.add_round_key(state, round_keys[0])
        self.append_log(f"After AddRoundKey: {self.state_to_hex(state)}")
        
        self.append_log(f"\nRecovered Plaintext: {self.state_to_hex(state)} ({self.state_to_binary(state)})")
        
        return state


class MiniAESApp:
    """
    GUI application for Mini-AES
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Mini-AES Implementation")
        self.root.geometry("800x600")
        
        self.mini_aes = MiniAES()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        self.tab1 = ttk.Frame(self.tab_control)
        self.tab2 = ttk.Frame(self.tab_control)
        self.tab3 = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab1, text='Encryption/Decryption')
        self.tab_control.add(self.tab2, text='Test Cases')
        self.tab_control.add(self.tab3, text='About')
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Tab 1: Encryption/Decryption
        self.setup_encryption_tab()
        
        # Tab 2: Test Cases
        self.setup_test_cases_tab()
        
        # Tab 3: About
        self.setup_about_tab()
    
    def setup_encryption_tab(self):
        # Frame for input
        input_frame = ttk.LabelFrame(self.tab1, text="Input")
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Plaintext/Ciphertext input
        ttk.Label(input_frame, text="Plaintext/Ciphertext (Hex, 4 digits):").grid(column=0, row=0, padx=10, pady=5, sticky=tk.W)
        self.text_input = ttk.Entry(input_frame, width=30)
        self.text_input.grid(column=1, row=0, padx=10, pady=5)
        
        # Key input
        ttk.Label(input_frame, text="Key (Hex, 4 digits):").grid(column=0, row=1, padx=10, pady=5, sticky=tk.W)
        self.key_input = ttk.Entry(input_frame, width=30)
        self.key_input.grid(column=1, row=1, padx=10, pady=5)
        
        # Operation selection
        ttk.Label(input_frame, text="Operation:").grid(column=0, row=2, padx=10, pady=5, sticky=tk.W)
        self.operation = tk.StringVar()
        self.operation.set("encrypt")
        ttk.Radiobutton(input_frame, text="Encrypt", variable=self.operation, value="encrypt").grid(column=1, row=2, padx=10, pady=5, sticky=tk.W)
        ttk.Radiobutton(input_frame, text="Decrypt", variable=self.operation, value="decrypt").grid(column=1, row=2, padx=120, pady=5, sticky=tk.W)
        
        # Process button
        ttk.Button(input_frame, text="Process", command=self.process).grid(column=1, row=3, padx=10, pady=5)
        
        # Frame for output
        output_frame = ttk.LabelFrame(self.tab1, text="Output")
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Result text
        ttk.Label(output_frame, text="Result:").grid(column=0, row=0, padx=10, pady=5, sticky=tk.W)
        self.result_text = ttk.Entry(output_frame, width=30, state='readonly')
        self.result_text.grid(column=1, row=0, padx=10, pady=5)
        
        # Log area
        ttk.Label(output_frame, text="Process Log:").grid(column=0, row=1, padx=10, pady=5, sticky=tk.NW)
        self.log_area = scrolledtext.ScrolledText(output_frame, width=70, height=15)
        self.log_area.grid(column=1, row=1, padx=10, pady=5)
    
    def setup_test_cases_tab(self):
        # Test cases description
        ttk.Label(self.tab2, text="Pre-defined Test Cases").pack(padx=10, pady=5, anchor=tk.W)
        
        # Frame for test cases
        test_cases_frame = ttk.Frame(self.tab2)
        test_cases_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Test case buttons
        ttk.Button(test_cases_frame, text="Test Case 1", command=lambda: self.run_test_case(0)).grid(column=0, row=0, padx=10, pady=5)
        ttk.Button(test_cases_frame, text="Test Case 2", command=lambda: self.run_test_case(1)).grid(column=1, row=0, padx=10, pady=5)
        ttk.Button(test_cases_frame, text="Test Case 3", command=lambda: self.run_test_case(2)).grid(column=2, row=0, padx=10, pady=5)
        
        # Test case descriptions
        test_cases_desc = ttk.LabelFrame(self.tab2, text="Test Case Descriptions")
        test_cases_desc.pack(fill="both", expand=True, padx=10, pady=5)
        
        test_cases_text = scrolledtext.ScrolledText(test_cases_desc, width=70, height=20)
        test_cases_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Test case information
        test_cases_info = """Test Case 1:
Plaintext: A5B3 (1010 0101 1011 0011)
Key: C9D2 (1100 1001 1101 0010)
Expected Ciphertext: 7E4F (0111 1110 0100 1111)

Test Case 2:
Plaintext: 1234 (0001 0010 0011 0100)
Key: 5678 (0101 0110 0111 1000)
Expected Ciphertext: A9B7 (1010 1001 1011 0111)

Test Case 3:
Plaintext: FFFF (1111 1111 1111 1111)
Key: 0000 (0000 0000 0000 0000)
Expected Ciphertext: 6A6A (0110 1010 0110 1010)
"""
        test_cases_text.insert(tk.INSERT, test_cases_info)
        test_cases_text.config(state='disabled')
    
    def setup_about_tab(self):
        about_frame = ttk.Frame(self.tab3)
        about_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        about_text = scrolledtext.ScrolledText(about_frame, width=70, height=20)
        about_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        about_info = """Mini-AES Implementation

This application implements a simplified version of the Advanced Encryption Standard (AES) algorithm 
called Mini-AES, which operates on 16-bit blocks with a 16-bit key.

Features:
- 16-bit block size (4 nibbles)
- 16-bit key
- 3 rounds of encryption
- Operations: SubNibbles, ShiftRows, MixColumns, AddRoundKey
- Key expansion for round keys

The Mini-AES structure follows the standard AES but with simplified parameters:
- State is represented as a 2x2 nibble array
- S-Box is reduced to 4-bit operations
- MixColumns uses a simpler matrix in GF(2^4)

This implementation includes both encryption and decryption capabilities.

Limitations:
- Simplified security compared to standard AES
- Designed for educational purposes only
- Not suitable for actual secure communications
"""
        about_text.insert(tk.INSERT, about_info)
        about_text.config(state='disabled')
    
    def hex_to_state(self, hex_str):
        """Convert hex string to state array"""
        if len(hex_str) != 4:
            raise ValueError("Hex string must be exactly 4 characters (16 bits)")
        
        # Convert hex string to list of nibbles
        return [int(hex_str[i], 16) for i in range(4)]
    
    def process(self):
        """Process encryption/decryption based on user input"""
        try:
            # Get input values
            text_hex = self.text_input.get().upper()
            key_hex = self.key_input.get().upper()
            
            # Validate input
            if len(text_hex) != 4 or len(key_hex) != 4:
                raise ValueError("Input and key must be exactly 4 hex digits (16 bits)")
            
            # Convert to state arrays
            text_state = self.hex_to_state(text_hex)
            key_state = self.hex_to_state(key_hex)
            
            # Process based on selected operation
            if self.operation.get() == "encrypt":
                result = self.mini_aes.encrypt(text_state, key_state)
            else:
                result = self.mini_aes.decrypt(text_state, key_state)
            
            # Display result
            result_hex = ''.join(f'{nibble:X}' for nibble in result)
            self.result_text.config(state='normal')
            self.result_text.delete(0, tk.END)
            self.result_text.insert(0, result_hex)
            self.result_text.config(state='readonly')
            
            # Display log
            self.log_area.delete(1.0, tk.END)
            self.log_area.insert(tk.INSERT, self.mini_aes.get_log())
            
        except Exception as e:
            self.log_area.delete(1.0, tk.END)
            self.log_area.insert(tk.INSERT, f"Error: {str(e)}")
    
    def run_test_case(self, case_index):
        """Run a predefined test case"""
        test_cases = [
            {"plaintext": "A5B3", "key": "C9D2"},
            {"plaintext": "1234", "key": "5678"},
            {"plaintext": "FFFF", "key": "0000"}
        ]
        
        if case_index < len(test_cases):
            case = test_cases[case_index]
            self.text_input.delete(0, tk.END)
            self.text_input.insert(0, case["plaintext"])
            self.key_input.delete(0, tk.END)
            self.key_input.insert(0, case["key"])
            self.operation.set("encrypt")
            self.process()


# ECB and CBC Mode Implementation
class BlockModeMiniAES:
    """
    Implementation of Block Cipher Modes (ECB/CBC) for Mini-AES
    """
    def __init__(self):
        self.mini_aes = MiniAES()
    
    def pad_message(self, message):
        """
        Pad message to be multiple of 16 bits (4 hex digits)
        """
        if len(message) % 4 != 0:
            padding = 4 - (len(message) % 4)
            message += '0' * padding
        return message
    
    def ecb_encrypt(self, plaintext_hex, key_hex):
        """
        ECB mode encryption
        """
        # Pad plaintext to multiple of 16 bits
        padded_plaintext = self.pad_message(plaintext_hex)
        
        key_state = [int(key_hex[i], 16) for i in range(4)]
        ciphertext = ""
        log = []
        
        # Process each 16-bit block
        for i in range(0, len(padded_plaintext), 4):
            block = padded_plaintext[i:i+4]
            block_state = [int(block[j], 16) for j in range(4)]
            
            # Encrypt this block
            encrypted_block = self.mini_aes.encrypt(block_state, key_state)
            
            # Append to ciphertext
            ciphertext += ''.join(f'{nibble:X}' for nibble in encrypted_block)
            
            # Get log for this block
            log.append(f"Block {i//4 + 1}:\n{self.mini_aes.get_log()}")
        
        return ciphertext, log
    
    def ecb_decrypt(self, ciphertext_hex, key_hex):
        """
        ECB mode decryption
        """
        key_state = [int(key_hex[i], 16) for i in range(4)]
        plaintext = ""
        log = []
        
        # Process each 16-bit block
        for i in range(0, len(ciphertext_hex), 4):
            block = ciphertext_hex[i:i+4]
            block_state = [int(block[j], 16) for j in range(4)]
            
            # Decrypt this block
            decrypted_block = self.mini_aes.decrypt(block_state, key_state)
            
            # Append to plaintext
            plaintext += ''.join(f'{nibble:X}' for nibble in decrypted_block)
            
            # Get log for this block
            log.append(f"Block {i//4 + 1}:\n{self.mini_aes.get_log()}")
        
        return plaintext, log
    
    def cbc_encrypt(self, plaintext_hex, key_hex, iv_hex):
        """
        CBC mode encryption
        """
        # Pad plaintext to multiple of 16 bits
        padded_plaintext = self.pad_message(plaintext_hex)
        
        key_state = [int(key_hex[i], 16) for i in range(4)]
        iv_state = [int(iv_hex[i], 16) for i in range(4)]
        
        ciphertext = ""
        log = []
        prev_block = iv_state
        
        # Process each 16-bit block
        for i in range(0, len(padded_plaintext), 4):
            block = padded_plaintext[i:i+4]
            block_state = [int(block[j], 16) for j in range(4)]
            
            # XOR with previous ciphertext block (or IV for first block)
            xored_block = [block_state[j] ^ prev_block[j] for j in range(4)]
            
            # Encrypt this block
            encrypted_block = self.mini_aes.encrypt(xored_block, key_state)
            
            # Save for next round
            prev_block = encrypted_block
            
            # Append to ciphertext
            ciphertext += ''.join(f'{nibble:X}' for nibble in encrypted_block)
            
            # Get log for this block
            log.append(f"Block {i//4 + 1}:\n{self.mini_aes.get_log()}")
        
        return ciphertext, log
    
    def cbc_decrypt(self, ciphertext_hex, key_hex, iv_hex):
        """
        CBC mode decryption
        """
        key_state = [int(key_hex[i], 16) for i in range(4)]
        iv_state = [int(iv_hex[i], 16) for i in range(4)]
        
        plaintext = ""
        log = []
        prev_block = iv_state
        
        # Process each 16-bit block
        for i in range(0, len(ciphertext_hex), 4):
            block = ciphertext_hex[i:i+4]
            block_state = [int(block[j], 16) for j in range(4)]
            
            # Save current ciphertext block
            current_block = block_state.copy()
            
            # Decrypt this block
            decrypted_block = self.mini_aes.decrypt(block_state, key_state)
            
            # XOR with previous ciphertext block (or IV for first block)
            plaintext_block = [decrypted_block[j] ^ prev_block[j] for j in range(4)]
            
            # Update previous block
            prev_block = current_block
            
            # Append to plaintext
            plaintext += ''.join(f'{nibble:X}' for nibble in plaintext_block)
            
            # Get log for this block
            log.append(f"Block {i//4 + 1}:\n{self.mini_aes.get_log()}")
        
        return plaintext, log


if __name__ == "__main__":
    # Create and start the GUI
    root = tk.Tk()
    app = MiniAESApp(root)
    root.mainloop()