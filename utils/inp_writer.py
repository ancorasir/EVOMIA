# -*- coding=utf-8 -*-

# ------------------------------------------------------------------
# File Name:        inp_writer.py
# Author:           Han Xudong
# Version:          1.0.1
# Created:          2024/02/21
# Description:      This is a script to write input file for Abaqus.
# Function List:    None
# History:
#       <author>        <version>       <time>      <desc>
#       Han Xudong      1.0.0           2024/02/21  Created file
#       Han Xudong      1.0.1           2024/08/17  Add description
# ------------------------------------------------------------------

import os
import sys

class InpWriter:
    def __init__(self,
                 inp_template:str='0.inp') -> None:
        '''
        Write input class
        This class is designed to write input file for Abaqus.

        Args:
            inp_template: str, input file template
        '''

        self.inp_template = inp_template
        
    def write(self, 
              inp:str, 
              parameters:dict) -> None:
        '''
        Write input file for Abaqus

        Args:
            inp: str, input file name
            parameters: dict, parameters to be written
        '''

        # Check if the input parameters are valid
        try:
            if not os.path.exists(self.inp_template):
                raise FileNotFoundError('\033[31mERROR: INP TEMPLATE NOT FOUND !!!\033[0m')
            if not inp.endswith('.inp'):
                raise ValueError('\033[31mERROR: INP FILE EXTENSION IS NOT VALID !!!\033[0m')
            if not parameters:
                raise ValueError('\033[31mERROR: PARAMETERS IS EMPTY !!!\033[0m')
        except (FileNotFoundError, ValueError) as e:
            print(e)
            sys.exit()
        
        # Read template
        with open(self.inp_template, 'r') as f:
            lines = f.read()

        # Write input file
        with open(inp, 'w') as f:
            for key, value in parameters.items():
                if key not in lines:
                    print('\033[33mWARNING: %s NOT FOUND\033[0m' % key.upper())
                lines = lines.replace(key, str(value))
            f.write(lines)

if __name__ == '__main__':
    # Test inp_writer
    print('\033[7m{:=^50s}\033[0m'.format(' INP WRITER'))

    # Parameters
    print('{:-^50s}'.format(' INITIALIZATION '))
    inp_template = 'templates/inp/cylinder_linear.inp'
    print('Input file template:', inp_template)
    inp = 'test.inp'
    print('Input file:', inp)
    parameters = {'youngs_modulus': '1.0', 
                  'poisson_ratio': '0.475'}
    print('Parameters:', parameters)

    # Write input file
    print('{:-^50s}'.format(' TEST START '))
    inp_writer = InpWriter(inp_template=inp_template)
    inp_writer.write(inp, parameters)
    print('{:-^50s}'.format(' TEST PASSED '))