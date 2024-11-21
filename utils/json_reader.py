# -*- coding=utf-8 -*-

# ------------------------------------------------------------------
# File Name:        json_reader.py
# Author:           Han Xudong
# Version:          1.0.1
# Created:          2024/02/21
# Description:      This is a script to read result file from Abaqus.
# Function List:    None
# History:
#       <author>        <version>       <time>      <desc>
#       Han Xudong      1.0.0           2024/02/21  Created file
#       Han Xudong      1.0.1           2024/08/17  Add description
# ------------------------------------------------------------------

import os
import sys
import json

class JsonReader:
    def __init__(self) -> None:
        '''
        Read JSON class
        This class is designed to read JSON file.
        '''
        pass
    
    def read(self,
             path:str,
             odb:str) -> dict:
        '''
        Read result file from Abaqus

        Args:
            odb: str, result file name
        '''

        # Check if the input parameters are valid
        try:
            if not os.path.exists(path + odb):
                raise FileNotFoundError('\033[31mERROR: ODB FILE NOT FOUND !!!\033[0m')
            if not odb.endswith('.odb'):
                raise ValueError('\033[31mERROR: ODB FILE EXTENSION IS NOT VALID !!!\033[0m')
        except (FileNotFoundError, ValueError) as e:
            print(e)
            sys.exit()

        # Read result.json
        if not os.path.exists(path + odb.replace('.odb', '.json')):
            return dict()
        else:
            with open(path + odb.replace('.odb', '.json'), 'r') as f:
                result = json.load(f)

        return result
    
if __name__ == '__main__':
    # Test json_reader
    print('\033[7m{:=^50s}\033[0m'.format(' JSON READER'))

    # Parameters
    print('{:-^50s}'.format(' INITIALIZATION '))
    path = 'data/example/'
    odb = 'test.odb'
    print('Result file:', odb)
    target = ['SOF1', 'SOF2', 'SOF3', 'SOM1', 'SOM2', 'SOM3']
    print('Target:', target)

    # Read result file
    print('{:-^50s}'.format(' TEST START '))
    json_reader = JsonReader()
    result = json_reader.read(path=path,
                              odb=odb,)
    print('{:-^50s}'.format(' TEST PASSED '))