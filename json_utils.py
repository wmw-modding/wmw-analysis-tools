

def make_json_friendly(data : list | dict | set):
    if isinstance(data, set):
        return make_json_friendly(list(data))
    
    elif isinstance(data, list):
        return [make_json_friendly(value) for value in data]
    
    elif isinstance(data, dict):
        for key in data:
            data[key] = make_json_friendly(data[key])
            
        return data
    
    else:
        return data

def list_to_set(data : list | dict | set):
    if isinstance(data, list):
        return {list_to_set(value) for value in data}
    
    elif isinstance(data, dict):
        for key in data:
            data[key] = list_to_set(data[key])
            
        return data
    
    else:
        return data