import typing

def split_num(string) -> tuple[str,str]:
    if not isinstance(string, str):
        raise TypeError('string must be str')
    
    head = string.rstrip('0123456789')
    tail = string[len(head):]
    return head, tail

def check_type(value : str):
    def check_int(val : str):
        try:
            int(val)
            return True
        except:
            return False
    
    def check_float(val : str):
        try:
            float(val)
            return True
        except:
            return False
    
    types = {
        'string' : lambda val : not check_float(val),
        'float' : check_float,
        'int' : check_int,
        'bit' : lambda val : val in ['0','1', 0,1],
    }
    
    arrays = {
        'comma' : lambda string : string.split(','),
        'spaced' : lambda string : string.split(),
    }
    
    type = []
    is_comma_array = False
    
    for key in arrays:
        array = arrays[key]
        values = array(value)
        if len(values) > 1:
            if key == 'comma':
                type.append(check_type(values[0]))
            
                is_comma_array = True
            
            elif key == 'spaced':
                type = [check_type(val) for val in values]
            
            break
    
    master_type = ''
    
    if len(type) == 0:
        for key in types:
            check = types[key]
            
            is_type = check(value)
            
            print(f'{is_type = }')
            print(f'type = {key}')
            
            if is_type:
                master_type = key
    
    if len(type) == 0:
        if master_type == '':
            print(type)
            master_type = 'string'
        
        type.append(master_type)
    
    type = ' '.join(type)
    if is_comma_array:
        type += ',...'
    
    return type
